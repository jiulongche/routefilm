from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "build-route-map-video"


def test_canonical_skill_and_portable_agent_entry_points():
    assert (SKILL / "SKILL.md").is_file()
    for vendor in (".agents", ".claude"):
        entry = ROOT / vendor / "skills" / "build-route-map-video" / "SKILL.md"
        assert entry.is_file()
        assert not entry.is_symlink()
        body = entry.read_text(encoding="utf-8")
        assert "../../../skills/build-route-map-video/SKILL.md" in body
        assert "canonical workflow" in body


def test_openai_interface_metadata():
    metadata = yaml.safe_load((SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert metadata["interface"]["display_name"]
    assert "$build-route-map-video" in metadata["interface"]["default_prompt"]
    entry_metadata = yaml.safe_load(
        (
            ROOT
            / ".agents"
            / "skills"
            / "build-route-map-video"
            / "agents"
            / "openai.yaml"
        ).read_text(encoding="utf-8")
    )
    assert entry_metadata == metadata


def test_skill_asks_one_adaptive_choice_question_at_a_time():
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "Ask exactly one question at a time" in body
    assert "request_user_input" in body
    assert "AskUserQuestion" in body
    assert "generation_enabled" in body
    assert "do not offer generation" in body
    assert "blocking setup state" in body
    assert "Do not create an ad hoc empty file" in body
    assert "Do not render a poster, sample, silent master" in body
    assert "片名怎么设置？" in body
    assert "recommendation itself must be visible" in body
    assert "video.title" in body
