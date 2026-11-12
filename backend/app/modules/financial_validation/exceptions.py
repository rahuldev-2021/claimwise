"""Financial validation module errors."""


class FinancialConfigError(Exception):
    """Invalid or missing financial configuration."""


class FinancialDataError(Exception):
    """Dataset ingestion or validation failure."""


class FinancialModelError(Exception):
    """Model registry or prediction failure."""


class FinancialFeatureError(Exception):
    """Feature extraction or train/serve mismatch."""


class FinancialDependencyError(Exception):
    """Optional ML dependencies not installed."""
