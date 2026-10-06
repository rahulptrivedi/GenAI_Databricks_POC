"""Validate bundle structure locally and invoke the Databricks CLI when available."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def validate_structure() -> None:
    """Check required bundle resources and application configuration references."""
    bundle_path = PROJECT_ROOT / "databricks.yml"
    app_path = PROJECT_ROOT / "app.yaml"
    bundle: Any = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))
    app: Any = yaml.safe_load(app_path.read_text(encoding="utf-8"))

    targets = bundle.get("targets", {})
    resources = bundle.get("resources", {}).get("apps", {})
    variables = bundle.get("variables", {})
    if set(targets) != {"dev", "test", "prod"}:
        raise ValueError("databricks.yml must define exactly dev, test, and prod targets.")
    if "chatbot" not in resources:
        raise ValueError("databricks.yml is missing resources.apps.chatbot.")
    if not {"app_name", "catalog_name", "genie_agent_id", "warehouse_id"}.issubset(variables):
        raise ValueError("Bundle variables must declare app, catalog, Genie, and warehouse values.")
    if not isinstance(app.get("command"), list) or not app["command"]:
        raise ValueError("app.yaml must define a non-empty command array.")


def main() -> int:
    try:
        validate_structure()
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"Bundle structure validation failed: {error}", file=sys.stderr)
        return 1

    cli = shutil.which("databricks")
    if cli is None:
        print(
            "Bundle structure is valid. Databricks CLI not found; remote bundle validation skipped."
        )
        return 0
    if not os.environ.get("DATABRICKS_HOST"):
        print("Bundle structure is valid. Set DATABRICKS_HOST to run Databricks CLI validation.")
        return 0

    result = subprocess.run(  # noqa: S603  # nosec B603
        [cli, "bundle", "validate", "-t", os.environ.get("BUNDLE_TARGET", "dev")],
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
