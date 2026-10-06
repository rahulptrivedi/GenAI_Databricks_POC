"""Remove local test/build artifacts without deleting Databricks resources."""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = (".pytest_cache", ".ruff_cache", ".mypy_cache", "htmlcov", ".coverage")


def main() -> None:
    for relative_path in ARTIFACTS:
        path = PROJECT_ROOT / relative_path
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
    for path in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
    print("Removed local Python/test artifacts; no Databricks resources were changed.")


if __name__ == "__main__":
    main()
