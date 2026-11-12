import pytest
from pydantic import ValidationError

from app.api.schemas.claim_create import ClaimCreateRequest


def test_technician_diagnosis_required():
    with pytest.raises(ValidationError):
        ClaimCreateRequest(
            year="2024",
            make="Ford",
            model="F-150",
            category="BRAKING",
            customer_complaint="Noise",
            technician_diagnosis="   ",
            recommended_repair="Replace pads",
            parts_cost="10",
            labour_hours="1",
        )
