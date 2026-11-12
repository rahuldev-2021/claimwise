from app.modules.rag.document_cleaner import clean_text, is_blank


def test_is_blank_detects_empty():
    assert is_blank("   ")
    assert not is_blank("Brake inspection")


def test_clean_text_normalizes_whitespace():
    assert "a b" in clean_text("a   b")
