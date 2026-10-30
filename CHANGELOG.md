# Changelog

## Unreleased — 2026-10-30

- Added open.epic MCP **documentation/spec-lookup** integration
  (`src/deployment_kit/epic_mcp.py`): a dependency-light MCP client for
  Epic's remote documentation server at `https://mcp.open.epic.com`
  (Streamable HTTP; live-verified tools `search_documents` and
  `get_document`). This is documentation lookup only — **not** patient-data
  access; patient data continues to flow only through the kit's FHIR R4
  paths, never through the MCP server. Every query is screened by an
  in-code no-PHI guard that refuses anything resembling PHI/patient data,
  per Epic's warning that the server is not designated to handle PHI.
- Wired the client into the FHIR validation tooling
  (`fhir_validate.py --with-epic-specs` / `annotate_with_epic_specs()`):
  validation reports can now record which Epic API spec document (id,
  title, URL) each resource type was validated against, degrading
  gracefully when the server is disabled or unreachable.
- Added `epic-mcp.mcp.json.example` (example AI-client MCP config) and
  `EPIC_MCP.md` (what the server is/isn't, the no-PHI rule, setup, and how
  this kit uses it). Source: https://fhir.epic.com/documentation?docid=mcp
- Added mock-only tests (`tests/test_epic_mcp.py`, `MockTransport` fake
  MCP server): handshake/session echo, `tools/list`, `tools/call` over
  JSON and SSE, no-PHI guard, graceful degradation, and validator wiring.
