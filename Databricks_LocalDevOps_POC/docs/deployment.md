# Deployment

## Prerequisites

- A Databricks workspace and a principal authorized to create the required catalog/schemas, deploy Apps and Asset Bundles, and configure grants.
- Databricks CLI, mise, uv, and Poe versions from project configuration.
- A compatible Python runtime, Genie Agent/space, SQL Warehouse, and Databricks App capability in each target workspace.
- OAuth/workload identity configuration for local use and CI. Workspace host, app name, catalog, Genie ID, and warehouse ID are supplied out-of-band.

## Environment matrix

| Target | Bundle target | Data catalog | Genie resource | Warehouse | Approval |
|---|---|---|---|---|---|
| Development | `dev` | `chatbot_demo_dev` by default; override as needed | Required input | Required input | Developer authorization |
| Test | `test` | Required input | Required input | Required input | Test environment owner |
| Production | `prod` | Required input | Required input | Required input | Protected GitHub environment and data owner |

No workspace-specific IDs or hostnames are committed. Demo catalog names are defaults only and require ownership approval.

## Provision and deploy

From `Databricks_LocalDevOps_POC/`:

```powershell
mise install
uv sync --all-groups
uv run poe bundle-validate
uv run poe seed-data
uv run poe deploy-dev
```

After test approval:

```powershell
uv run poe deploy-test
```

Production requires the protected CI environment and approval:

```powershell
uv run poe deploy-prod
```

`seed-data` creates/updates only the configured synthetic demo objects; it does not delete resources. Grant access only after reviewing the principal and target:

```powershell
uv run poe catalog-grant-reader -- --principal analytics-readers@example.com
```

The explicit destructive cleanup command is separate from `poe clean` (which removes local caches only):

```powershell
uv run python scripts/deploy_catalog.py clean --confirm-catalog chatbot_demo
```

Cleanup refuses non-demo catalog names and requires exact equality with `DATABRICKS_CATALOG`. It drops the entire confirmed demo catalog and is never part of deploy/rollback.

## CI/CD and authentication

- Pull requests run lock, format, lint, type, unit, coverage, security, secret-scan, bundle-validation (when configured), and package checks.
- Dev deploys from `main`; test and production use separate manually dispatched workflows from `main`.
- Configure `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_GENIE_AGENT_ID`, and `DATABRICKS_WAREHOUSE_ID` as environment-level GitHub variables. Configure Databricks workload identity federation to trust the repository/environment and use `DATABRICKS_AUTH_TYPE=github-oidc`.
- Configure required reviewers and deployment branch restrictions on the GitHub `production` environment. Workflow YAML cannot create or enforce those repository settings.
- Never store Databricks PATs in GitHub secrets. If OIDC is unavailable, document the approved short-lived credential alternative before enabling deployment.

The bundle structure check runs offline. Remote `databricks bundle validate` and deployment were not run here because workspace host, Genie ID, warehouse ID, CLI authentication, OIDC trust, and environment approvals were not supplied.

## Rollback procedure

1. Disable or roll back the App deployment to the previously recorded bundle version.
2. Preserve Unity Catalog data. Do not use cleanup as a rollback mechanism.
3. Revert Genie instructions/resource bindings only through the reviewed bundle/config change that introduced them.
4. Verify App health/readiness, Genie connectivity, and a known synthetic query.
5. Record the deployment version, correlation IDs, impact, and follow-up action.

Bundle rollback behavior and App source/version retention must be verified in the target workspace before production. No automatic catalog/schema deletion is part of rollback.

## Operational support

Check App health and logs, correlate failures by request ID, classify whether the error originated in configuration, Genie, authorization, or query execution, and avoid copying prompts or results into tickets. Escalate authorization failures to the UC owner; API/resource failures to the Databricks platform owner; answer-quality issues to the Genie-space owner. Retention and alert thresholds are pending operations policy.