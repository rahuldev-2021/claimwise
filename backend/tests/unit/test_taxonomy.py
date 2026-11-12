from app.modules.nlp.taxonomy import lookup_aliases, normalize_term


def test_brake_lining_maps_to_brake_pad():
    cat, canonical, _ = normalize_term("brake lining", "part")
    assert cat == "part"
    assert canonical == "brake_pad"


def test_engine_running_hot_maps_to_overheating_symptom():
    _, canonical, _ = normalize_term("engine overheating", "symptom")
    assert canonical == "engine_overheating"


def test_unknown_term_slugified():
    _, canonical, _ = normalize_term("widget failure", "symptom")
    assert canonical == "widget_failure"


def test_lookup_aliases_returns_list():
    aliases = lookup_aliases("part", "brake_pad")
    assert "brake pad" in aliases
