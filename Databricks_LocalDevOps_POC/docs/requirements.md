# Requirements

## Purpose

Provide an authorized, read-only chatbot for natural-language analysis of curated Databricks Unity Catalog data. This project is a self-contained subproject so the existing Flutter sample repository remains unchanged.

## Functional requirements

- Accept natural-language questions and preserve Genie conversation context for follow-ups.
- Ground answers in a configured Genie space/agent backed only by approved Unity Catalog objects.
- Return an answer, execution status, safe SQL when available, source object names, warnings, and a correlation ID.
- Ask for clarification when the request is ambiguous and state when data, configuration, or permission is missing.
- Return a clear no-data result rather than infer unsupported facts.
- Keep the chatbot read-only. The application must not execute model-generated SQL.
- Validate question length, bound result display, safely render text, and support explicit session reset and feedback.
- Create configurable synthetic demonstration data for customers, products, orders, order items, sales summary, and customer summary.
- Define bronze, silver, gold, app, and monitoring schemas and document object ownership, relationships, quality expectations, business terms, and example questions/queries.
- Provide idempotent provisioning and seed scripts. Destructive demo cleanup requires a separate explicit command and confirmation.

## Quality and operational requirements

- Keep UI, application services, platform clients, configuration, security, and telemetry concerns separate.
- Use typed configuration and API models, structured logs, correlation IDs, bounded external calls, and classified public errors.
- Never commit credentials, workspace identifiers, warehouse IDs, Genie IDs, or populated `.env` files.
- Prefer Databricks Apps, Genie, Unity Catalog, SQL Warehouses, Asset Bundles, and MLflow. Record capability gaps instead of silently substituting services.
- Support dev, test, and prod bundle targets with environment-specific variables and production environment protection.
- Include unit, optional Databricks integration, contract, and evaluation tests. External tests must report a blocked/skipped state when credentials or workspace configuration are absent.
- Provide repeatable mise, uv, and Poe workflows, lockfile checks, CI validation, deployment, rollback, and support documentation.

## Acceptance criteria

- Local setup installs from committed `uv.lock`; `poe validate` runs local quality/security gates and skips only workspace-dependent checks with a useful explanation.
- Unit tests cover settings, contracts, error handling, SQL safety, source citations, and service behavior without a live workspace.
- Integration tests cover Genie, warehouse, and Unity Catalog access when explicitly configured; otherwise they are clearly skipped, never reported as passed.
- Synthetic catalog SQL and seed data are repeatable and non-destructive by default.
- Every answer cites configured Unity Catalog sources and exposes no generated SQL execution route.
- Bundle validation and deployments use explicit target configuration and never fabricate workspace-specific values.

## Explicit pending decisions

- Whether the target workspace supports Databricks Apps, the required Genie Agent/space API and resource binding, serverless SQL, and MLflow tracing.
- Whether the App can preserve per-user Unity Catalog authorization for Genie execution; this is a release gate, not an assumption.
- Workspace host, OAuth client configuration, warehouse ID, Genie ID, catalog ownership/grants, supported runtime, data retention policy, and production approval owners.
- Whether conversation history may be persisted. Default: no server-side persistence of question or answer content.