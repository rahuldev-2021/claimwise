"""Financial validation orchestration (implements FinancialValidationModule)."""

from decimal import Decimal
from pathlib import Path

from app.core.config import Settings
from app.modules.financial_validation.config.loader import load_financial_config
from app.modules.financial_validation.features.consistency import assert_training_inference_consistency
from app.modules.financial_validation.features.feature_engineering import extract_inference_features
from app.modules.financial_validation.rules.financial_rules import apply_financial_rules
from app.modules.financial_validation.services.prediction_service import PredictionService
from app.schemas.claim import ClaimInput
from app.schemas.financial_validation import FinancialValidationResult


class FinancialValidationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        config_dir = Path(settings.FINANCIAL_CONFIG_DIR)
        self._bundle = load_financial_config(config_dir)
        assert_training_inference_consistency(self._bundle.feature_mapping)
        self._predictor = PredictionService(self._bundle, settings)

    def validate(self, claim: ClaimInput) -> FinancialValidationResult:
        extraction = extract_inference_features(claim, self._bundle.feature_mapping)
        prediction = self._predictor.predict(extraction)

        status, lines, parts_pct, labour_pct, triggered = apply_financial_rules(
            rules=self._bundle.rules,
            currency=claim.currency,
            parts_submitted=claim.submitted_parts_cost,
            labour_submitted=claim.submitted_labour_hours,
            parts_predicted=prediction.parts.value,
            labour_predicted=prediction.labour.value,
            missing_critical_features=extraction.missing_critical,
            models_available=prediction.models_available,
        )

        explanation = " ".join(lines)
        if prediction.limitations:
            explanation = f"{prediction.limitations} {explanation}".strip()

        return FinancialValidationResult(
            claim_id=claim.claim_id,
            submitted_parts_cost=claim.submitted_parts_cost,
            submitted_labour_hours=claim.submitted_labour_hours,
            predicted_parts_cost=prediction.parts.value,
            predicted_labour_hours=prediction.labour.value,
            parts_discrepancy_pct=parts_pct,
            labour_discrepancy_pct=labour_pct,
            financial_status=status,
            explanation=explanation,
            triggered_financial_rules=triggered,
            parts_model_version=prediction.parts.model_version,
            labour_model_version=prediction.labour.model_version,
            parts_model_algorithm=prediction.parts.algorithm,
            labour_model_algorithm=prediction.labour.algorithm,
            model_lifecycle=prediction.parts.lifecycle or prediction.labour.lifecycle,
            experimental_prediction=prediction.experimental_enabled and prediction.models_available,
            synthetic_data_prediction=bool(
                prediction.parts.synthetic_data or prediction.labour.synthetic_data
            ),
            human_review_required=True,
            limitations=prediction.limitations,
        )


def financial_validation_enabled(settings: Settings) -> bool:
    return bool(settings.FINANCIAL_ENABLED)
