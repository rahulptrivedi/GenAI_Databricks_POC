# Architecture

## Overview

The project uses one Databricks App process running FastAPI. It serves the chat UI and typed chat, feedback, health, and readiness endpoints from the same origin. The API calls an application service through typed models. The service uses a narrow Genie client interface, forwards the authenticated caller's question to the configured Genie resource, maps the response, and formats source citations. It never runs generated SQL. Genie is configured against curated Unity Catalog gold views and uses the SQL Warehouse permitted by the workspace. Unity Catalog remains the authorization boundary. The current SDK adapter calls the Genie `space_id` API; confirm that this is the target workspace's approved Genie Agent capability before deployment.

```mermaid
flowchart LR
  U[Authorized user] --> A[Databricks App / FastAPI UI and API]
  A --> S[Chat service]
  S --> G[Genie Agent or configured Genie space]
  G --> UC[Unity Catalog curated gold views]
  G --> W[SQL Warehouse]
  UC --> B[Bronze and silver synthetic demo tables]
  S --> M[Structured logs and correlation IDs]
  S --> F[Optional feedback metadata]
  S -. optional tracing .-> ML[MLflow]
  C[Databricks Asset Bundles] --> A
  C --> UC
```

## Request sequence

```mermaid
sequenceDiagram
  actor User
  participant UI as Databricks App
  participant Service as Chat service
  participant Genie as Genie resource
  participant UC as Unity Catalog / Warehouse
  User->>UI: Ask a question
  UI->>Service: Validated question + session ID
  Service->>Service: Enforce limits, classify request, assign correlation ID
  Service->>Genie: Start or continue conversation
  Genie->>UC: Permission-checked read-only analysis
  UC-->>Genie: Result and source metadata
  Genie-->>Service: Answer, status, SQL when available, sources
  Service->>Service: Map errors, validate SQL for display, bound response
  Service-->>UI: Answer + citations + status + warnings
  UI-->>User: Safely rendered response
```

## Data model

```mermaid
erDiagram
  CUSTOMERS ||--o{ ORDERS : places
  ORDERS ||--|{ ORDER_ITEMS : contains
  PRODUCTS ||--o{ ORDER_ITEMS : referenced_by
  CUSTOMER_SUMMARY }o--|| CUSTOMERS : summarizes
  SALES_SUMMARY }o--o{ PRODUCTS : aggregates
```

All demonstration records are synthetic. Bronze stores minimally transformed source-shaped data with ingestion metadata. Silver normalizes types, removes duplicate source keys, handles invalid/null data, and documents quality checks. Gold exposes curated business views for Genie. App and monitoring schemas hold only minimal feedback/audit metadata; prompt and answer text are not persisted by default.

## Boundaries and authorization

- UI: presentation and ephemeral session controls only; no SQL construction or data access. DOM insertion uses text nodes, not HTML interpretation.
- API: same-origin chat, feedback, health, and readiness routes; Databricks App access policy protects the application.
- Service: input policy, orchestration, response mapping, error classification, citations.
- Genie adapter: platform API calls and conversation IDs; credentials come from the Databricks App identity/runtime.
- Catalog bootstrap: SQL scripts run by an explicitly authorized deployment principal, never by the chat request path.
- Caller authorization: per-user authorization/passthrough must be verified for the selected App/Genie integration. A shared application identity with broader access is not an approved default.

## Capability gates

Workspace-specific availability has not been checked. If Databricks Apps, Genie integration/resource binding, serverless SQL, or MLflow tracing is unavailable, deployment is blocked pending a documented decision. The recommended alternative must be approved and documented before implementation behavior is switched; no external database, vector store, Azure Functions, or Kubernetes is introduced by default.