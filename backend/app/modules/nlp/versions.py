"""Version identifiers for reproducible NLP runs."""

from pathlib import Path
import hashlib
import json

from app.modules.nlp.taxonomy_data import TAXONOMY_VERSION  # noqa: E402
PIPELINE_VERSION = "0.4.0"
ABBREVIATIONS_FILE = (
    Path(__file__).resolve().parents[3] / "data" / "nlp" / "abbreviations_en.json"
)


def abbreviation_dict_version() -> str:
    try:
        raw = ABBREVIATIONS_FILE.read_bytes()
    except OSError:
        return "missing"
    return hashlib.sha256(raw).hexdigest()[:12]


def fuzzy_matcher_name() -> str:
    from app.core.config import get_settings

    impl = getattr(get_settings(), "NLP_FUZZY_MATCHER", "difflib")
    return str(impl)
