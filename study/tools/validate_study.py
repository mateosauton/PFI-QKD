from __future__ import annotations

import argparse
import re
from pathlib import Path

MARKER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER)\b", re.IGNORECASE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def unfinished_markers(root: Path) -> list[str]:
    violations: list[str] = []
    for path in markdown_files(root):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if MARKER_RE.search(line):
                violations.append(f"{path}:{line_number}:{line.strip()}")
    return violations


def broken_links(root: Path) -> list[str]:
    violations: list[str] = []
    for path in markdown_files(root):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            for raw_target in LINK_RE.findall(line):
                target = raw_target.split("#", 1)[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                if not (path.parent / target).resolve().exists():
                    violations.append(f"{path}:{line_number}:{raw_target}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate QKD study Markdown files")
    parser.add_argument("root", nargs="?", default="study", type=Path)
    args = parser.parse_args()
    violations = unfinished_markers(args.root) + broken_links(args.root)
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
