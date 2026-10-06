# Architecture Decisions

## ADR-001: Isolate the Databricks project

- Status: Accepted.
- Decision: Place the project in `Databricks_LocalDevOps_POC/`.
- Context: The repository root is an existing Flutter samples repository with its own app, tooling, and CI.
- Consequence: Python dependencies, CI, docs, and deployment configuration remain project-local; root Flutter behavior is unchanged.

## ADR-002: Use one FastAPI Databricks App

- Status: Accepted, workspace capability pending.
- Decision: Package a small same-origin HTML/JavaScript chat UI and typed API in one FastAPI Databricks App process.
- Context: The project requires health/readiness endpoints, typed service boundaries, and a simple professional chat UI. One process avoids a separate UI/API service.
- Consequence: Session context is held by the browser for the active page only. Confirm FastAPI support and port configuration in the target workspace; if Databricks Apps is unavailable, pause for explicit approval of an alternative.

## ADR-003: Delegate analytical reasoning to Genie

- Status: Accepted, exact Genie Agent/space contract pending.
- Decision: Keep a typed adapter around the supported Databricks Genie API/SDK and configure it only with curated Unity Catalog gold objects and verified examples.
- Context: Genie provides the preferred native natural-language-to-data behavior and conversation support.
- Consequence: API version, resource binding, source metadata, per-user authorization, and SQL result shape must be contract-tested against the target workspace before production.

## ADR-004: Never execute generated SQL in the app

- Status: Accepted.
- Decision: The application may display validated SQL returned by Genie but never submits model-generated SQL to a warehouse.
- Context: This sharply narrows injection and destructive-operation risk; Genie performs governed analysis through its configured read-only resource.
- Consequence: SQL validation is defense-in-depth for displayed content and tests; Unity Catalog grants and Genie configuration remain the enforcement boundary.

## ADR-005: Keep conversational content ephemeral

- Status: Accepted.
- Decision: Store conversation state in the App session and do not persist raw questions/answers. Persist only explicitly approved feedback and operational metadata without content.
- Context: No data-handling or retention policy was supplied.
- Consequence: History is lost on session expiry/reset until a retention decision and privacy review approve persistence.

## ADR-006: Use uv and Poe with mise-managed runtimes

- Status: Accepted.
- Decision: Pin Python, uv, and the Databricks CLI in mise; declare Poe and Python libraries in `pyproject.toml`, lock all dependencies with `uv.lock`.
- Context: Poe is a project dependency and should resolve reproducibly with the rest of the Python environment.
- Consequence: First setup requires mise activation and `uv sync --all-groups` before invoking Poe tasks.

## ADR-007: Use synthetic layered demonstration data

- Status: Accepted.
- Decision: Provide idempotent catalog SQL and deterministic synthetic records across bronze, silver, and gold layers.
- Context: The project must be demonstrable without production data.
- Consequence: Catalog/schema names are configurable; cleanup is a separate confirmed operation.

## ADR-008: Use the Databricks Genie space SDK contract behind an adapter

- Status: Implemented for local contracts; target workspace compatibility pending.
- Decision: The adapter uses `space_id`, start/create-message, and message-polling methods exposed by the Databricks SDK.
- Context: The SDK-facing integration needs an executable, mockable contract while no workspace IDs or credentials are available.
- Consequence: `DATABRICKS_GENIE_AGENT_ID` must contain the supported Genie space ID for this adapter. Confirm that this matches the target Genie Agent resource before deployment.

## ADR-009: Keep demo grants opt-in and narrowly scoped

- Status: Accepted.
- Decision: Catalog bootstrap does not grant permissions. A separate command grants only use of the demo catalog/gold schema and select on the two curated gold views to an explicitly supplied principal.
- Context: No user/group principal or workspace authorization model was provided.
- Consequence: A workspace owner must review the principal and configure App/Genie resource permissions separately.