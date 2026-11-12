"""Rule-based and regex entity extraction with optional spaCy noun-chunk hints."""

import logging
import re
from typing import Optional

from app.core.config import get_settings
from app.modules.nlp.fuzzy_matcher import find_fuzzy_matches
from app.modules.nlp.abbreviation_expander import excerpt_from_original, map_span_to_original
from app.modules.nlp.schemas import (
    EntityCategory,
    ExtractedEntity,
    ExtractionMethod,
    MatchMethod,
    RelationshipCertainty,
    TextSourceField,
)
from app.modules.nlp.taxonomy import normalize_term
from app.modules.nlp.taxonomy_data import TAXONOMY_ALIASES

logger = logging.getLogger(__name__)

_DTC_PATTERN = re.compile(r"\bP[0-9]{4}\b", re.IGNORECASE)
_VOLTAGE_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*V(?:olts?)?\b", re.IGNORECASE)
_TEMP_PATTERN = re.compile(
    r"(?:"
    r"(?:engine|coolant|oil|temperature)\s+(?:temperature\s+)?(?:reached|is|at|of)?\s*"
    r")?"
    r"(\d+(?:\.\d+)?)\s*(?:°\s*)?([FC])\b"
    r"|"
    r"(\d+(?:\.\d+)?)\s*°\s*([FC])\b",
    re.IGNORECASE,
)
_THICKNESS_MM = re.compile(r"\b(\d+(?:\.\d+)?)\s*mm\b", re.IGNORECASE)
_MILEAGE_PATTERN = re.compile(
    r"\b(\d{1,3}(?:,\d{3})*|\d+)\s*(?:miles?|mi|km)\b", re.IGNORECASE
)

_NEGATION_PATTERN = re.compile(
    r"\b(no|not|without|none)\s+(?:abnormal\s+)?(?:noise|leak|fault|code)s?\b",
    re.IGNORECASE,
)

_TAXONOMY_CATEGORIES = (
    "operating_condition",
    "location",
    "symptom",
    "part",
    "component",
    "diagnostic",
    "diagnostic_finding",
    "repair_action",
    "failure_mode",
)

_FINDING_PATTERN = re.compile(
    r"\b(measured|observed|confirmed|within specification|shows)\b",
    re.IGNORECASE,
)
_SYMPTOM_ONSET_BEFORE_MILEAGE = re.compile(
    r"\b(?:after|at|around|since|when|once)\b.{0,35}$",
    re.IGNORECASE,
)

_DIAGNOSIS_FINDING_PATTERNS: tuple[tuple[re.Pattern[str], str, str, bool], ...] = (
    (
        re.compile(r"\b(?:front\s+)?pads?\s+below\s+minimum\s+thickness\b", re.I),
        "diagnostic_finding",
        "pad_thickness_low",
        False,
    ),
    (
        re.compile(r"\bbelow\s+minimum\s+thickness\b", re.I),
        "diagnostic_finding",
        "below_minimum_thickness",
        False,
    ),
    (
        re.compile(r"\brotors?\s+glazed\b", re.I),
        "diagnostic_finding",
        "rotor_glazing",
        False,
    ),
    (
        re.compile(r"\bheat\s+spots\b", re.I),
        "diagnostic_finding",
        "heat_spots",
        False,
    ),
    (
        re.compile(r"\bcaliper\s+slides?\s+move\s+freely\b", re.I),
        "diagnostic_finding",
        "caliper_slides_free",
        False,
    ),
    (
        re.compile(r"\bno\s+hydraulic\s+fault\b", re.I),
        "failure_mode",
        "hydraulic_fault",
        True,
    ),
)
_OPERATING_BRAKING = re.compile(
    r"\b(when|during|while)\s+(?:at\s+low\s+speed\s+)?braking\b", re.IGNORECASE
)
_BRAKING_COMPONENT_ALIASES = frozenset({"brake", "brakes", "braking", "brake system"})

_SPACY_NLP: Optional[object] = None


def _get_spacy():
    global _SPACY_NLP
    if not get_settings().NLP_ENABLE_SPACY:
        return None
    if _SPACY_NLP is not False and _SPACY_NLP is None:
        try:
            import spacy

            _SPACY_NLP = spacy.load("en_core_web_sm")
        except ImportError:
            logger.debug(
                "spaCy optional extra not installed; using rules/regex/taxonomy only"
            )
            _SPACY_NLP = False
        except Exception as exc:  # noqa: BLE001 — optional dependency
            logger.warning("spaCy model unavailable: %s", exc)
            _SPACY_NLP = False
    return _SPACY_NLP if _SPACY_NLP is not False else None


def spacy_available() -> bool:
    return _get_spacy() is not None


def extract_entities(
    text: str,
    source_field: TextSourceField,
    *,
    original: str = "",
    norm_to_orig: tuple[int, ...] = (),
    fuzzy_threshold: Optional[float] = None,
) -> tuple[list[ExtractedEntity], list[str]]:
    """Extract entities from preprocessed text. Returns entities and modes used."""
    if not text.strip():
        return [], []

    original_text = original or text

    if fuzzy_threshold is None:
        fuzzy_threshold = get_settings().NLP_FUZZY_MATCH_THRESHOLD

    modes: list[str] = ["rules", "regex"]
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str, TextSourceField]] = set()
    covered_spans: set[tuple[int, int]] = set()

    def add_entity(
        surface: str,
        category: str,
        span_start: int,
        span_end: int,
        *,
        negated: bool = False,
        match_method: MatchMethod = MatchMethod.ALIAS,
        extraction_method: ExtractionMethod = ExtractionMethod.TAXONOMY,
        confidence: Optional[float] = None,
        canonical_override: Optional[str] = None,
        source_certainty: Optional[RelationshipCertainty] = None,
    ) -> None:
        if canonical_override is not None:
            canonical = canonical_override
            try:
                cat_enum = EntityCategory(category)
            except ValueError:
                return
        else:
            ent_cat, canonical, matched = normalize_term(surface, category)
            if ent_cat == "unknown":
                ent_cat = category
            try:
                cat_enum = EntityCategory(ent_cat if ent_cat != "unknown" else category)
            except ValueError:
                return
            surface = matched if matched else surface

        key = (canonical, cat_enum.value, source_field)
        if key in seen:
            return
        seen.add(key)
        covered_spans.add((span_start, span_end))

        if confidence is None:
            if match_method == MatchMethod.FUZZY:
                confidence = max(0.7, min(0.85, fuzzy_threshold))
            elif cat_enum == EntityCategory.MEASUREMENT:
                confidence = 0.95
            else:
                confidence = 0.85

        if norm_to_orig and span_start is not None and span_end is not None:
            o_start, o_end = map_span_to_original(norm_to_orig, span_start, span_end)
        else:
            o_start, o_end = span_start, span_end
        src_excerpt = ""
        if o_start is not None and o_end is not None and o_end <= len(original_text):
            src_excerpt = original_text[o_start:o_end]
        else:
            src_excerpt = excerpt_from_original(original_text, surface)

        entities.append(
            ExtractedEntity(
                text=surface,
                canonical=canonical,
                category=cat_enum,
                source_field=source_field,
                span_start=o_start if o_start is not None else span_start,
                span_end=o_end if o_end is not None else span_end,
                source_text=src_excerpt or surface,
                negated=negated,
                match_method=match_method,
                extraction_method=extraction_method,
                confidence=confidence,
                source_certainty=source_certainty,
            )
        )

    lowered = text.lower()
    for category in _TAXONOMY_CATEGORIES:
        if (
            category == "failure_mode"
            and source_field == TextSourceField.RECOMMENDED_REPAIR
        ):
            continue
        for _canonical, aliases in TAXONOMY_ALIASES[category].items():
            for alias in sorted(aliases, key=len, reverse=True):
                for match in re.finditer(
                    r"\b" + re.escape(alias) + r"\b", lowered, re.IGNORECASE
                ):
                    if _skip_taxonomy_match(
                        lowered, match.start(), match.end(), category, alias
                    ):
                        continue
                    negated = _is_negated(lowered, match.start(), match.end())
                    add_entity(
                        alias,
                        category,
                        match.start(),
                        match.end(),
                        negated=negated,
                        match_method=MatchMethod.ALIAS,
                    )

    for pattern, category, canonical, pattern_negated in _DIAGNOSIS_FINDING_PATTERNS:
        if source_field != TextSourceField.TECHNICIAN_DIAGNOSIS:
            continue
        for match in pattern.finditer(text):
            add_entity(
                match.group(),
                category,
                match.start(),
                match.end(),
                negated=pattern_negated,
                match_method=MatchMethod.EXACT,
                extraction_method=ExtractionMethod.REGEX,
                canonical_override=canonical,
            )

    for fuzzy in find_fuzzy_matches(lowered, covered_spans, threshold=fuzzy_threshold):
        if (
            fuzzy.category == "failure_mode"
            and source_field == TextSourceField.RECOMMENDED_REPAIR
        ):
            continue
        if _skip_taxonomy_match(
            lowered,
            fuzzy.span_start,
            fuzzy.span_end,
            fuzzy.category,
            fuzzy.surface,
        ):
            continue
        negated = _is_negated(lowered, fuzzy.span_start, fuzzy.span_end)
        add_entity(
            fuzzy.surface,
            fuzzy.category,
            fuzzy.span_start,
            fuzzy.span_end,
            negated=negated,
            match_method=MatchMethod.FUZZY,
            confidence=round(max(0.7, fuzzy.ratio * 0.9), 2),
            canonical_override=fuzzy.canonical,
        )
        if "fuzzy" not in modes:
            modes.append("fuzzy")

    for match in _DTC_PATTERN.finditer(text):
        add_entity(
            match.group().upper(),
            "dtc_code",
            match.start(),
            match.end(),
            match_method=MatchMethod.EXACT,
            extraction_method=ExtractionMethod.REGEX,
            canonical_override=match.group().upper(),
        )

    if _FINDING_PATTERN.search(text):
        for category in ("diagnostic_finding",):
            for _canonical, aliases in TAXONOMY_ALIASES[category].items():
                for alias in sorted(aliases, key=len, reverse=True):
                    for match in re.finditer(
                        r"\b" + re.escape(alias) + r"\b", lowered, re.IGNORECASE
                    ):
                        add_entity(
                            alias,
                            category,
                            match.start(),
                            match.end(),
                            match_method=MatchMethod.ALIAS,
                            extraction_method=ExtractionMethod.TAXONOMY,
                        )

    for match in _VOLTAGE_PATTERN.finditer(text):
        add_entity(
            f"{match.group(1)}V",
            "measurement",
            match.start(),
            match.end(),
            match_method=MatchMethod.EXACT,
            extraction_method=ExtractionMethod.REGEX,
            canonical_override=f"voltage_{match.group(1)}",
        )

    for match in _TEMP_PATTERN.finditer(text):
        value = match.group(1) or match.group(3)
        unit = (match.group(2) or match.group(4) or "").upper()
        if not value or not unit:
            continue
        surface = match.group(0)
        add_entity(
            surface,
            "measurement",
            match.start(),
            match.end(),
            match_method=MatchMethod.EXACT,
            extraction_method=ExtractionMethod.REGEX,
            canonical_override=f"temperature_{value}_{unit}",
        )

    for match in _THICKNESS_MM.finditer(text):
        add_entity(
            f"{match.group(1)}mm",
            "measurement",
            match.start(),
            match.end(),
            match_method=MatchMethod.EXACT,
            extraction_method=ExtractionMethod.REGEX,
            canonical_override=f"thickness_{match.group(1)}mm",
        )

    for match in _MILEAGE_PATTERN.finditer(text):
        prefix = lowered[max(0, match.start() - 45) : match.start()]
        onset = bool(_SYMPTOM_ONSET_BEFORE_MILEAGE.search(prefix))
        add_entity(
            match.group(0),
            "measurement",
            match.start(),
            match.end(),
            match_method=MatchMethod.EXACT,
            extraction_method=ExtractionMethod.REGEX,
            canonical_override="symptom_onset_mileage" if onset else "mileage",
        )

    nlp = _get_spacy()
    if nlp is not None:
        try:
            doc = nlp(text)
        except Exception as exc:  # noqa: BLE001 — optional enrichment path
            logger.warning("spaCy noun-chunk pass failed (continuing without it): %s", exc)
        else:
            modes.append("spacy")
            for chunk in doc.noun_chunks:
                phrase = chunk.text.strip().lower()
                if len(phrase) < 3:
                    continue
                for category in ("component", "part", "symptom"):
                    if _skip_taxonomy_match(
                        lowered, chunk.start_char, chunk.end_char, category, phrase
                    ):
                        continue
                    cat, canonical, _ = normalize_term(phrase, category)
                    if cat != "unknown":
                        add_entity(
                            phrase,
                            cat,
                            chunk.start_char,
                            chunk.end_char,
                            match_method=MatchMethod.ALIAS,
                            extraction_method=ExtractionMethod.SPACY_HEURISTIC,
                            confidence=0.42,
                            canonical_override=canonical,
                        )

    entities = _drop_nested_diagnostic_findings(entities)
    entities = _drop_components_subsumed_by_parts(entities)
    entities = _drop_components_overlapping_parts(entities)
    return entities, modes


def _drop_nested_diagnostic_findings(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    """Keep the outermost diagnostic finding when spans nest (avoid duplicate downstream)."""
    findings = [
        e
        for e in entities
        if e.category == EntityCategory.DIAGNOSTIC_FINDING
        and e.span_start is not None
        and e.span_end is not None
    ]
    drop_ids: set[int] = set()
    for inner in findings:
        for outer in findings:
            if inner is outer:
                continue
            if (
                outer.span_start <= inner.span_start
                and outer.span_end >= inner.span_end
                and (outer.span_end - outer.span_start) > (inner.span_end - inner.span_start)
            ):
                drop_ids.add(id(inner))
                break
    return [e for e in entities if id(e) not in drop_ids]


def _spans_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and a_end > b_start


def _drop_components_overlapping_parts(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    parts = [
        e
        for e in entities
        if e.category == EntityCategory.PART
        and e.span_start is not None
        and e.span_end is not None
    ]
    drop_ids: set[int] = set()
    for comp in entities:
        if comp.category != EntityCategory.COMPONENT:
            continue
        if comp.span_start is None or comp.span_end is None:
            continue
        for part in parts:
            if _spans_overlap(
                comp.span_start, comp.span_end, part.span_start, part.span_end
            ):
                drop_ids.add(id(comp))
                break
    return [e for e in entities if id(e) not in drop_ids]


def _drop_components_subsumed_by_parts(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    """Drop component hits that are only modifiers inside a part phrase (e.g. brake in brake pads)."""
    parts = [
        e
        for e in entities
        if e.category == EntityCategory.PART
        and e.span_start is not None
        and e.span_end is not None
    ]
    drop_ids: set[int] = set()
    for comp in entities:
        if comp.category != EntityCategory.COMPONENT:
            continue
        if comp.span_start is None or comp.span_end is None:
            continue
        for part in parts:
            if (
                part.span_start <= comp.span_start
                and part.span_end >= comp.span_end
                and (part.span_end - part.span_start) > (comp.span_end - comp.span_start)
            ):
                drop_ids.add(id(comp))
                break
    return [e for e in entities if id(e) not in drop_ids]


def _skip_taxonomy_match(
    lowered: str, start: int, end: int, category: str, alias: str
) -> bool:
    alias_l = alias.lower()
    if category == "component" and alias_l in _BRAKING_COMPONENT_ALIASES:
        window_start = max(0, start - 24)
        window = lowered[window_start:end]
        if _OPERATING_BRAKING.search(window) or re.search(
            r"\b(when|during|while)\s+" + re.escape(alias_l) + r"\b",
            window,
        ):
            return True
        if re.match(
            r"\s+(?:pad|pads|rotor|rotors|caliper|calipers|fluid|hose|hoses|line|lines|shoe|shoes)\b",
            lowered[end : end + 20],
        ):
            return True
    if category == "failure_mode" and alias_l in ("contaminated", "contamination"):
        window = lowered[max(0, start - 20) : end + 10]
        if re.search(r"\b(fluid|if)\b", window):
            return True
    return False


def _is_negated(text: str, span_start: int, span_end: int) -> bool:
    prefix = text[max(0, span_start - 25) : span_start]
    if re.search(r"\b(no|not|without|none)\s*$", prefix, re.IGNORECASE):
        return True
    region = text[max(0, span_start - 5) : span_end]
    return bool(_NEGATION_PATTERN.search(region))
