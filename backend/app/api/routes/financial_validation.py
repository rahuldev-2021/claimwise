from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.claims import get_claim_service
from app.api.schemas.financial_validation_requests import FinancialAnalyzeRequest, FinancialPredictRequest
from app.auth.dependencies import CurrentUser, require_permissions
from app.core.config import get_settings
from app.core.exceptions import ClaimNotFoundError
from app.schemas.claim import ClaimInput
from app.services.claim_service import ClaimService
from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.exceptions import FinancialConfigError
from app.modules.financial_validation.features.feature_engineering import extract_inference_features
from app.modules.financial_validation.models.model_registry import ModelRegistry
from app.modules.financial_validation.schemas.prediction import FinancialPredictionResponse
from app.modules.financial_validation.services.financial_validation_service import (
    FinancialValidationService,
    financial_validation_enabled,
)
from app.modules.financial_validation.services.prediction_service import resolve_registry_for_settings
from app.schemas.financial_validation import FinancialValidationResult

router = APIRouter(tags=["financial-validation"])
_settings = get_settings()


def _resolve_claim_for_user(
    request: FinancialPredictRequest,
    user: CurrentUser,
    claim_service: ClaimService,
) -> ClaimInput:
    if request.claim_id:
        return claim_service.get_claim_for_user(request.claim_id.strip(), user)
    if request.claim is not None:
        return request.claim
    raise HTTPException(status_code=422, detail="Provide claim_id or claim body")


@router.get("/financial-validation/health")
def financial_validation_health():
    body = {
        "financial_enabled": _settings.FINANCIAL_ENABLED,
        "config_loaded": False,
        "provisional_config": True,
        "ml_dependencies_available": False,
        "parts_model_loaded": False,
        "labour_model_loaded": False,
        "require_models": _settings.FINANCIAL_REQUIRE_MODELS,
        "experimental_models_enabled": _settings.FINANCIAL_EXPERIMENTAL_MODELS_ENABLED,
    }
    try:
        bundle = load_financial_config(_settings.FINANCIAL_CONFIG_DIR)
        body["config_loaded"] = True
        body["provisional_config"] = bool(
            bundle.data_dictionary.provisional
            or bundle.rules.provisional
            or bundle.feature_mapping.provisional
        )
    except FinancialConfigError as exc:
        body["config_error"] = str(exc)
        if _settings.FINANCIAL_REQUIRE_MODELS:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return body

    try:
        import joblib  # noqa: F401
        import sklearn  # noqa: F401

        body["ml_dependencies_available"] = True
    except ImportError:
        return body

    registry_root, inference_mode, _ = resolve_registry_for_settings(_settings)
    registry = ModelRegistry(registry_root)
    schema_hash = __import__(
        "app.modules.financial_validation.models.model_registry",
        fromlist=["feature_schema_hash"],
    ).feature_schema_hash(bundle.feature_mapping.feature_ids)
    body["inference_mode"] = inference_mode
    body["registry_dir"] = str(registry_root)
    try:
        body["parts_model_loaded"] = (
            registry.get_active_entry(
                "parts_cost",
                expected_schema_hash=schema_hash,
                inference_mode=inference_mode,
            )
            is not None
        )
        body["labour_model_loaded"] = (
            registry.get_active_entry(
                "labour_hours",
                expected_schema_hash=schema_hash,
                inference_mode=inference_mode,
            )
            is not None
        )
    except Exception as exc:
        body["registry_error"] = str(exc)

    if _settings.FINANCIAL_REQUIRE_MODELS and not (
        body["parts_model_loaded"] and body["labour_model_loaded"]
    ):
        raise HTTPException(status_code=503, detail="Required financial models are not available")
    return body


@router.get("/financial-validation/models")
def financial_validation_models(
    user: Annotated[CurrentUser, Depends(require_permissions("claims:read"))],
):
    registry_root, inference_mode, experimental = resolve_registry_for_settings(_settings)
    registry = ModelRegistry(registry_root)
    entries = registry.load()
    if inference_mode == "production":
        entries = [e for e in entries if e.eligible_for_inference()]
    elif experimental:
        entries = [e for e in entries if e.eligible_for_experimental_inference()]
    redacted = []
    for e in entries:
        data = e.to_dict()
        data.pop("training_data_version", None)
        redacted.append(data)
    return {
        "registry_path": str(registry.registry_path),
        "inference_mode": inference_mode,
        "entries": redacted,
        "provisional": True,
    }


@router.post("/financial-validation/predict", response_model=FinancialPredictionResponse)
def financial_predict(
    request: FinancialPredictRequest,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:assess"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> FinancialPredictionResponse:
    if not financial_validation_enabled(_settings):
        raise HTTPException(status_code=503, detail="Financial validation is disabled")

    try:
        claim = _resolve_claim_for_user(request, user, claim_service)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    service = FinancialValidationService(_settings)
    bundle = service._bundle  # noqa: SLF001 — health already uses loader
    extraction = extract_inference_features(claim, bundle.feature_mapping)
    prediction = service._predictor.predict(extraction)  # noqa: SLF001
    return FinancialPredictionResponse(
        claim_id=claim.claim_id,
        predicted_parts_cost=prediction.parts.value,
        predicted_labour_hours=prediction.labour.value,
        parts_model_version=prediction.parts.model_version,
        labour_model_version=prediction.labour.model_version,
        models_available=prediction.models_available,
        missing_critical_features=extraction.missing_critical,
        parts_model_algorithm=prediction.parts.algorithm,
        labour_model_algorithm=prediction.labour.algorithm,
        model_lifecycle=prediction.parts.lifecycle,
        experimental_prediction=prediction.experimental_enabled and prediction.models_available,
        synthetic_data_prediction=bool(prediction.parts.synthetic_data or prediction.labour.synthetic_data),
        human_review_required=True,
        limitations=prediction.limitations,
        inference_mode=prediction.inference_mode,
    )


@router.post("/financial-validation/analyze", response_model=FinancialValidationResult)
def financial_analyze(
    request: FinancialAnalyzeRequest,
    user: Annotated[CurrentUser, Depends(require_permissions("claims:assess"))],
    claim_service: Annotated[ClaimService, Depends(get_claim_service)],
) -> FinancialValidationResult:
    if not financial_validation_enabled(_settings):
        raise HTTPException(status_code=503, detail="Financial validation is disabled")
    try:
        claim = _resolve_claim_for_user(request, user, claim_service)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    service = FinancialValidationService(_settings)
    return service.validate(claim)
