# Epic open.epic MCP — documentation/spec lookup

> **What this is:** an integration with Epic's **open.epic MCP server**, a
> *documentation and API-specification lookup* service. **It is not patient-data
> access.** Patient data in this kit flows only through the existing FHIR R4
> validation/client paths — never through this MCP server.

Source: Epic's own documentation —
https://fhir.epic.com/documentation?docid=mcp

## The server

- **URL:** `https://mcp.open.epic.com`
- **Transport:** Streamable HTTP (MCP, JSON-RPC 2.0, protocol version `2025-03-26`)
- **Server identity (verified live 2026-10-30):** `open.epic MCP`, version `4.0.9`
- **Authentication:** none documented; no credentials, no SMART/OAuth flow.

### What it returns

Documentation content only: API specifications, interface summaries, and
additional documentation (data-sharing playbooks, tutorials, and FAQs),
including Epic on FHIR content.

### Live-verified tools (discovered via `tools/list`, 2026-10-30)

Tool names are not published on Epic's page; they are discovered at runtime.
The live server exposes exactly two:

| Tool | Arguments | What it does |
|---|---|---|
| `search_documents` | `{query: string}` (≤500 chars) | Keyword/phrase search across Epic documentation; returns documents with id, url, title, and snippet. Prefer R4 APIs. Use `get_document` with a returned id for full text. |
| `get_document` | `{document_id: string}` (`api:x`, `tutorial:x`, `faq:x`, `interface:x:x`), optional `offset` | Full contents of one document; long documents paginate in 20,000-character pages via `offset` / `next_offset`. |

### What it is NOT

- It is **not** a FHIR resource server: no `Patient` / `Observation` /
  `Encounter` querying, no patient data of any kind.
- It has no SMART on FHIR / OAuth flow and takes no credentials.

## The no-PHI rule (mandatory)

Epic states the server **is not designated to handle protected health
information (PHI) or other confidential information**, and that the user is
responsible for anything transmitted to it. Use is subject to the open.epic
Terms of Use.

This kit enforces that rule **in code**, not just in this document:
`src/deployment_kit/epic_mcp.py` screens every `tools/call` argument before
anything is sent and **refuses** (raising `PhiGuardError`, logging the rule
names only — never the screened text) any query that looks like PHI or patient
data: FHIR resource JSON (`"resourceType"`), `Patient/<id>` references,
MRN/SSN-like patterns, or date-of-birth phrasing. Only documentation-style
queries — API names, resource *type* names, spec topics — are allowed.

## How this kit uses it

Module: `src/deployment_kit/epic_mcp.py` — a dependency-light client built on
`httpx` (already a project dependency; the `mcp` SDK is **not** required). It
implements `initialize` + `notifications/initialized`, captures and echoes the
`Mcp-Session-Id` header when the server issues one, handles both
`application/json` and SSE-framed (`text/event-stream`) responses, and exposes
`list_tools()`, `call_tool(name, args)`, `search_docs(query)`, and
`get_document(document_id)`.

Wiring — FHIR validation / pilot tooling (`src/deployment_kit/fhir_validate.py`):

- `annotate_with_epic_specs(result)` / `fetch_epic_spec_references(types)`
  look up the Epic API spec for each resource *type* present in a validated
  bundle (e.g. `Patient FHIR R4`) and record the spec document id, title, and
  URL in the validation result, so a report states **which Epic spec the
  validation was run against**.
- The CLI exposes this as an opt-in flag:

  ```bash
  python -m deployment_kit.fhir_validate bundle.json --with-epic-specs --md report.md
  ```

- **Graceful degradation:** with the server disabled or unreachable, the
  annotation is `available: False` with a reason, the report notes that
  validation ran without Epic spec references, and validation itself is
  completely unaffected.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `EPIC_MCP_URL` | `https://mcp.open.epic.com` | MCP server base URL |
| `EPIC_MCP_ENABLED` | `1` (enabled) | Set to `0` / `false` / `no` / `off` to disable docs lookup entirely |

Timeout is 15s; the kit works fully with the integration disabled or the
server unreachable.

## Use from an AI client (Claude Code / VS Code / Cursor)

`epic-mcp.mcp.json.example` at the repo root is an example MCP client config
to copy — it is an example, not a forced config:

```json
{
  "mcpServers": {
    "open-epic-mcp": {
      "url": "https://mcp.open.epic.com",
      "transport": "streamable-http"
    }
  }
}
```

Which filename each client reads: **Claude Code** reads `.mcp.json` at the
project root; **VS Code** (GitHub Copilot MCP support) reads
`.vscode/mcp.json` (same `mcpServers` shape, under a `servers` key in some
versions — check your version's docs); **Cursor** reads `.cursor/mcp.json`
in the project (or `~/.cursor/mcp.json` globally). Copy the example to the
filename your client expects, then ask the client to search Epic's docs —
e.g. for the `MedicationRequest` R4 API spec — while you build against the
FHIR interfaces this kit validates.

## Tests

`tests/test_epic_mcp.py` is mock-only (an `httpx` `MockTransport` fake MCP
server — no live network): initialize handshake + session-header echo,
`tools/list` parsing, `tools/call` over both JSON and SSE responses, the
no-PHI guard refusing fake patient identifiers / resource JSON, graceful
degradation when the server is unreachable or disabled, and the
FHIR-validator wiring (spec annotation present, and unchanged validation
when the lookup is unavailable).
