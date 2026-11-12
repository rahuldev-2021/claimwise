"""Typed rule registry metadata (detection rules; aggregation is separate)."""

from dataclasses import dataclass

from app.modules.technical_validation.validation_rules import _rules
from app.modules.technical_validation.versions import TV_RULES_VERSION


@dataclass(frozen=True)
class RuleRecord:
    rule_id: str
    version: str
    description: str
    enabled: bool = True


def list_rule_records() -> list[RuleRecord]:
    return [
        RuleRecord(rule_id=r.rule_id, version=TV_RULES_VERSION, description=r.message, enabled=True)
        for r in _rules()
    ]


def rules_version() -> str:
    return TV_RULES_VERSION
