"""Scan project text files for common committed credential patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache", "__pycache__"}
SECRET_PATTERNS = (
    re.compile(r"\bdapi[0-9a-f]{32}\b", re.IGNORECASE),
    re.compile(
        r"(?i)(?:client_secret|password|access_token)[ \t]*[:=][ \t]*['\"]?"
        r"([A-Za-z0-9._~+/=-]{20,})"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def scan_text(text: str) -> bool:
    """Return whether text contains a high-confidence credential pattern."""
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def main() -> int:
    findings: list[str] = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if scan_text(content):
            findings.append(str(path.relative_to(PROJECT_ROOT)))

    if findings:
        print("Potential credentials found in: " + ", ".join(findings), file=sys.stderr)
        return 1
    print("Secret scan passed; no high-confidence credential patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
