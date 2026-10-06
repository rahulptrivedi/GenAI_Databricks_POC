# Local Development

## Prerequisites

- Windows PowerShell, Git, mise, uv, and Databricks CLI. Python and uv are installed through mise for reproducibility; uv is already available on the current machine, but a new terminal may be needed to refresh PATH.
- A supported Python version compatible with the selected Databricks App runtime (project default: Python 3.11; confirm with the workspace owner).
- A Databricks workspace and OAuth-based CLI profile only for live integration/deployment commands.

## Setup

```powershell
mise install
uv sync --all-groups
Copy-Item .env.example .env
```

Keep `.env` local and never add credentials to it in shared environments. Databricks CLI authentication should use the approved OAuth/device or workload-identity flow. Live credentials are optional for unit tests.

## Commands

```powershell
uv run poe format
uv run poe lint
uv run poe typecheck
uv run poe test-unit
uv run poe test-contract
uv run poe evaluate
uv run poe security
uv run poe secret-scan
uv run poe validate
uv run poe run
```

`poe validate` runs local checks and gives an explicit skip reason for workspace-dependent bundle/integration checks when no Databricks configuration is present. `poe run` starts the local FastAPI app at `http://127.0.0.1:8000`; `/health/live` works without workspace access and `/health/ready` reports an unconfigured Genie resource as not ready. The chat UI displays a safe configuration message rather than inventing answers.

## Environment reference

| Variable | Required for | Example/default |
|---|---|---|
| `ENVIRONMENT` | Runtime labels | `dev` |
| `DATABRICKS_HOST` | Live Genie / bundle operations | Unset placeholder |
| `DATABRICKS_CLIENT_ID` | OAuth where configured | Unset placeholder |
| `DATABRICKS_CLIENT_SECRET` | Only approved fallback auth | Unset; secret-store only |
| `DATABRICKS_WAREHOUSE_ID` | Live warehouse integration | Unset placeholder |
| `DATABRICKS_GENIE_AGENT_ID` | Genie calls | Unset placeholder |
| `DATABRICKS_CATALOG` | Catalog bootstrap and source allow-list | `chatbot_demo` |
| `DATABRICKS_SCHEMA` | Default schema/context | `gold` |
| `DATABRICKS_APP_NAME` | App deployment | Unset placeholder |
| `MLFLOW_EXPERIMENT_NAME` | Optional tracing/evaluation | Unset placeholder |

Configuration must be validated at startup for the selected operation. Never log secret values.

## Troubleshooting

- `uv` not found after installation: open a new terminal; verify `%LOCALAPPDATA%\Microsoft\WinGet\Links` is on PATH.
- Bundle validation asks for workspace values: authenticate using Databricks CLI OAuth and set target variables in an untracked local config or environment.
- Unit, contract, and dataset-structure evaluation tests do not need workspace access. `poe test-integration` reports `BLOCKED` unless host, warehouse, and Genie IDs are configured; with those values it calls the configured Genie resource and also requires valid Databricks SDK authentication and UC grants.
- A local app with no Genie ID is intentionally not a mock data-answering service; configure a real authorized Genie resource to ask questions.