# Security

## Trust boundaries

- The browser and all user-provided text are untrusted.
- Databricks App configuration and its runtime identity are privileged deployment inputs.
- Genie and the SQL Warehouse are trusted only within configured, permission-limited resources.
- Unity Catalog is the authoritative data-access boundary; app-side filtering is not a substitute for grants.

## Required controls

- Use Databricks OAuth/workload identity or the App's supported resource authorization. Do not use personal access tokens in CI or source files. Client secrets are allowed only when secretless auth is unavailable and must be stored in an approved secret store.
- Prefer per-user authorization. Verify that Genie runs with the caller's UC permissions. Do not ship with an overprivileged shared identity without a documented risk decision and approval.
- Grant Genie access only to the curated gold views/functions it needs and a warehouse with read-only query capability. Deployment principals and runtime principals are distinct.
- Enforce a question byte/character limit, reject empty/control-character input, bound sessions and displayed results, and apply external-call deadlines.
- Never execute application-generated/model-generated SQL. Genie configuration and UC grants must prohibit writes and DDL. Any displayed SQL must be tagged as explanatory and validated before rendering.
- Escape rendered content; do not interpret model output as HTML or Markdown with unsafe extensions. Do not expose tokens, prompts, hidden metadata, or stack traces.
- Return generic public error messages with a correlation ID. Log structured error class and timing without secrets, raw prompts, query results, or full SQL by default.
- Protect state-changing actions such as feedback submission with input validation and CSRF/session protections provided by the platform.
- CI uses least-privilege OIDC where supported; production deployment is environment-protected and restricted to approved refs.
- Pin dependencies, verify the lockfile, run Ruff/mypy/pytest and Bandit, and scan for secrets.

## Permissions matrix

| Principal | Required permissions | Explicitly excluded |
|---|---|---|
| Chat user | `CAN USE` on the Databricks App; read access to curated gold views when per-user identity is supported | Catalog/schema creation, DDL, writes, bronze/silver access by default |
| Genie execution principal | `USE CATALOG`, `USE SCHEMA` on `gold`, `SELECT` on `sales_summary` and `customer_summary`, and `CAN USE` on the configured SQL Warehouse | `MODIFY`, `CREATE`, `MANAGE`, unrelated catalogs |
| Deployment principal | Deploy the App/Bundle and create demo objects in the selected demo catalog; grant only approved readers | Production data ownership or broad workspace admin unless separately approved |
| CI validation principal | Read-only bundle validation; OIDC federation from the approved GitHub repository/environment | PATs and long-lived client secrets |

`resources/sql/grants/gold_reader.sql` is an opt-in template. `poe catalog-grant-reader -- --principal <UC-user-or-group>` grants access only to the two gold views. Review the principal and target catalog before running it. App `CAN USE` assignment and Genie/warehouse resource binding are separate workspace configuration steps.

Per-user authorization, Genie execution identity, App resource bindings, and OIDC federation are release gates. Do not deploy with a shared App identity that has broader catalog access than the caller is authorized to see.

## SQL and prompt-injection policy

Prompt instructions are not an authorization mechanism. Treat requests to reveal system prompts, secrets, hidden metadata, or restricted objects as unsupported. Limit Genie to curated objects and read-only permissions. The app does not transform user text into SQL or execute SQL. SQL returned for display is checked for a single read-only statement and omitted if it includes write/DDL/multiple-statement constructs; this display check is defense-in-depth, not a data-access control.

## Data handling and retention

- Synthetic demo data only by default.
- Do not persist prompt or response content. Keep conversation state in volatile session memory and clear it on reset/expiry.
- Audit metadata should contain correlation ID, timestamp, actor identifier only where approved, status, latency, source object names where policy allows, and error category.
- Feedback content is optional, user-submitted, and should be disabled or minimized until a privacy/retention policy is approved.
- Log retention, actor identifier policy, feedback retention, and MLflow trace sampling/redaction are pending organizational decisions.

## Security release gates

Production release is blocked until identity behavior, UC grants, Genie read-only behavior, workspace network/policy requirements, secret management, and data/log retention are verified by the Databricks administrator and security owner.