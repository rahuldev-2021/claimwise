from app.modules.nlp.preprocessing import preprocess_text


def test_preprocess_strips_and_collapses_whitespace():
    result = preprocess_text("  Engine   rattling   noise.  ")
    assert result.original.startswith("  Engine")
    assert result.normalized == "engine rattling noise."


def test_preprocess_empty_safe():
    result = preprocess_text("")
    assert result.original == ""
    assert result.normalized == ""


def test_preprocess_lowercase_normalized_preserves_original():
    original = "ENGINE Rattling While Accelerating - No Warning Light"
    result = preprocess_text(original)
    assert result.original == original
    assert result.normalized == "engine rattling while accelerating - no warning light"


def test_preprocess_preserves_numbers_and_codes():
    text = "Fault P0401 at 110°C, voltage 12.5V"
    result = preprocess_text(text)
    assert "p0401" in result.normalized
    assert "110°c" in result.normalized
    assert "12.5v" in result.normalized


def test_preprocess_preserves_negation():
    result = preprocess_text("No abnormal noise at idle")
    assert "no abnormal noise" in result.normalized
