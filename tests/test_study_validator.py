from pathlib import Path

from study.tools.validate_study import broken_links, unfinished_markers


def test_clean_markdown_has_no_violations(tmp_path: Path) -> None:
    (tmp_path / "target.md").write_text("# Target\n", encoding="utf-8")
    source = tmp_path / "source.md"
    source.write_text("# Source\n\n[Target](target.md)\n", encoding="utf-8")

    assert unfinished_markers(tmp_path) == []
    assert broken_links(tmp_path) == []


def test_reports_unfinished_markers(tmp_path: Path) -> None:
    path = tmp_path / "lesson.md"
    path.write_text("# Lesson\n\nTODO: explain this.\n", encoding="utf-8")

    assert unfinished_markers(tmp_path) == [f"{path}:3:TODO: explain this."]


def test_reports_broken_relative_links(tmp_path: Path) -> None:
    path = tmp_path / "lesson.md"
    path.write_text("# Lesson\n\n[Missing](missing.md)\n", encoding="utf-8")

    assert broken_links(tmp_path) == [f"{path}:3:missing.md"]
