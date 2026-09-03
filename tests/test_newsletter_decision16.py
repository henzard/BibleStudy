"""The newsletter delivers the text and asks the question. It does not interpret (Decision 16)."""
import scripts.generate_newsletter as gn


def test_reflection_block_is_text_plus_questions_only():
    block = gn.reflection_block()
    assert "Matthew 24:7-8" in block
    assert "beginning of sorrows" in block
    for q in ("Observation", "Interpretation", "Application"):
        assert q in block
    # No generated commentary: none of the phrases the old template produced.
    for banned in ("confirms", "we observe", "this week's data", "sobriety", "knowing 'the end is not yet'"):
        assert banned.lower() not in block.lower()


def test_enhance_with_openai_no_longer_returns_a_reflection(monkeypatch):
    monkeypatch.setattr(gn, "HAS_OPENAI", False)
    out = gn.enhance_with_openai({"overall_intensity": 0, "wars_intensity": 0}, {"total": 0}, {}, {})
    assert "scripture_reflection" not in out
