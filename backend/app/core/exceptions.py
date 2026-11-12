class ClaimWiseError(Exception):
    """Base exception for all CLAIMWISE application errors."""


class ClaimNotFoundError(ClaimWiseError):
    """Raised when a claim cannot be found by its identifier."""

    def __init__(self, claim_id: str) -> None:
        self.claim_id = claim_id
        super().__init__(f"Claim not found: {claim_id}")


class DocumentNotFoundError(ClaimWiseError):
    """Raised when a repair document cannot be found by its identifier."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Document not found: {document_id}")


class NLPProcessingError(ClaimWiseError):
    """Raised when the NLP pipeline fails to process a claim."""


class DataLoadError(ClaimWiseError):
    """Raised when sample data files cannot be loaded or parsed."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        super().__init__(f"Failed to load data from {path}: {reason}")
