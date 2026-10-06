"""Run live Databricks tests only when explicit workspace inputs are available."""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("DATABRICKS_HOST", "DATABRICKS_WAREHOUSE_ID", "DATABRICKS_GENIE_AGENT_ID")


def main() -> int:
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        print(
            "BLOCKED: live Databricks integration tests require " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    result = subprocess.run(  # nosec B603
        [sys.executable, "-m", "pytest", "tests/integration", "-q"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
