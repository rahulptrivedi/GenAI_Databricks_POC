# Implementation Plan

## Components

- FastAPI app with health/readiness endpoints and a same-origin UI with session reset, source/status display, and feedback controls.
- Typed core settings and API/result contracts.
- Chat orchestration service, SQL display-safety validator, citation formatter, and classified errors.
- Databricks Genie adapter with an injectable interface for unit and contract tests.
- Structured logging, correlation IDs, health/readiness functions, and optional redacted MLflow tracing.
- Databricks Asset Bundle with dev/test/prod targets, App configuration, synthetic catalog SQL, and explicit seed/grant/cleanup commands.
- pytest unit/integration/contract/evaluation suites, Poe tasks, mise config, GitHub CI workflows, and operational docs.

## Dependencies

- Runtime: FastAPI, Uvicorn, Pydantic, Databricks SDK. Add SQL connector only if required by approved bootstrap/integration behavior.
- Development: Poe, Ruff, mypy, pytest, pytest-cov, Bandit, secret scanning.
- Platform: Databricks Apps, Genie API/resource, Unity Catalog, SQL Warehouse, Asset Bundles; MLflow tracing optional pending workspace support.
- No Azure Functions, Kubernetes, Redis, or external vector database.

## Sequence and validation

1. Specifications and this plan (complete before implementation).
2. Python package, settings/contracts/security helpers, and focused unit tests; run `uv lock`, `uv run poe test-unit`, Ruff, and mypy.
3. Genie adapter and FastAPI same-origin UI with configuration-safe behavior; implemented and covered by contract tests.
4. Synthetic bronze/silver/gold SQL, guarded seed/cleanup, and least-privilege gold grants; implemented with SQL parsing/safety tests.
5. Bundle targets, CI/deployment workflows, Poe/mise workflows, and docs; implemented. Offline bundle structure validation passes; Databricks CLI validation remains pending.
6. Run workspace integration and answer-quality evaluation only after IDs, grants, auth mode, and capabilities are supplied. Integration tests are implemented but blocked without those inputs.

## Current validation record

- API and Genie contract tests: 5 passed in the last focused run.
- Catalog seed/grant safety tests: 6 passed in the last focused run.
- Evaluation dataset schema test: 1 passed.
- Secret scanner tests: 2 passed.
- Strict mypy: no issues in 19 source files.
- Full project validation, coverage threshold, GitHub workflows, and remote Databricks bundle validation still require final execution/configuration.

## Assumptions

- The root Flutter repository is out of scope and remains unchanged.
- The new project lives under `Databricks_LocalDevOps_POC/`.
- Python 3.11 is the initial project target pending runtime confirmation.
- Synthetic data uses a configurable demo catalog; it is never treated as production data.
- No raw conversation persistence; app session state is ephemeral.
- Genie performs governed analysis; the app never executes generated SQL.

## Pending decisions

- Databricks Apps and Genie Agent/space availability and exact supported integration contract. The current adapter uses the SDK's `space_id` contract.
- Per-user identity propagation and read-only permission model.
- Workspace host, OAuth client, warehouse and Genie IDs, catalog owner, app names, and CI identity.
- Serverless SQL and MLflow tracing availability.
- Organizational log, feedback, trace, and conversation retention policy.
- Owners/approvers for dev, test, production, rollback, and incident response.