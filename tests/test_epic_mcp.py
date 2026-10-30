import sys, json, asyncio
from pathlib import Path
import httpx, pytest
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from deployment_kit.epic_mcp import EpicMcpClient, PhiGuardError, screen_for_phi
from deployment_kit.fhir_validate import validate_bundle, render_report, annotate_with_epic_specs, fetch_epic_spec_references
from deployment_kit.fhir_gen import generate_bundle

TOOLS = [
    {"name": "search_documents", "description": "Search Epic documentation",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}},
    {"name": "get_document", "description": "Fetch one document by id",
     "inputSchema": {"type": "object", "properties": {"document_id": {"type": "string"}}}},
]
SEARCH_HITS = [{"id": "api:11419", "title": "Patient.Read (R4)",
                "url": "https://fhir.epic.com/api/11419", "snippet": "Read a Patient."}]

def make_transport(mode="json", session=False, seen=None):
    """Fake MCP server via httpx.MockTransport. mode: json | sse (tools/call framing)."""
    def handler(request):
        if seen is not None:
            seen.append({"method": None, "session": request.headers.get("mcp-session-id")})
        body = json.loads(request.content) if request.content else {}
        method = body.get("method")
        if seen is not None:
            seen[-1]["method"] = method
        if method == "notifications/initialized":
            return httpx.Response(202)
        headers = {"mcp-session-id": "test-session-123"} if (session and method == "initialize") else {}
        if method == "initialize":
            payload = {"jsonrpc": "2.0", "id": body.get("id"),
                       "result": {"protocolVersion": "2025-03-26",
                                  "serverInfo": {"name": "open.epic MCP", "version": "4.0.9"}}}
        elif method == "tools/list":
            payload = {"jsonrpc": "2.0", "id": body.get("id"), "result": {"tools": TOOLS}}
        elif method == "tools/call":
            name = body["params"]["name"]
            if name == "search_documents":
                result = {"content": [{"type": "text", "text": json.dumps(SEARCH_HITS)}],
                          "structuredContent": {"result": SEARCH_HITS}, "isError": False}
            else:
                result = {"content": [{"type": "text", "text": "# Patient.Read (R4)\nFull spec text."}],
                          "isError": False}
            payload = {"jsonrpc": "2.0", "id": body.get("id"), "result": result}
            if mode == "sse":
                return httpx.Response(200, headers={"content-type": "text/event-stream"},
                                      text=f"event: message\ndata: {json.dumps(payload)}\n\n")
        else:
            payload = {"jsonrpc": "2.0", "id": body.get("id"),
                       "error": {"code": -32601, "message": "method not found"}}
        return httpx.Response(200, headers=headers, json=payload)
    return httpx.MockTransport(handler)

def client(**kw):
    kw.setdefault("transport", make_transport())
    return EpicMcpClient(**kw)

def run(coro):
    return asyncio.run(coro)

# --- handshake / tools/list -------------------------------------------------

def test_initialize_and_tools_list():
    out = run(client().list_tools())
    assert out["available"] and [t["name"] for t in out["tools"]] == ["search_documents", "get_document"]
    assert out["server_info"] == {"name": "open.epic MCP", "version": "4.0.9"}

def test_session_header_echoed():
    seen = []
    c = EpicMcpClient(transport=make_transport(session=True, seen=seen))
    run(c.list_tools())
    methods = [s["method"] for s in seen]
    assert methods[0] == "initialize" and "tools/list" in methods
    # every request after initialize must echo the issued session id
    assert all(s["session"] == "test-session-123" for s in seen[1:])

# --- tools/call: JSON + SSE ---------------------------------------------------

def test_search_docs_json_response():
    out = run(client().search_docs("Patient FHIR R4"))
    assert out["available"] and out["results"] == SEARCH_HITS

def test_search_docs_sse_response():
    c = EpicMcpClient(transport=make_transport(mode="sse"))
    out = run(c.search_docs("Patient FHIR R4"))
    assert out["available"] and out["results"] == SEARCH_HITS

def test_get_document():
    out = run(client().get_document("api:11419"))
    assert out["available"] and "Full spec text." in out["content_texts"][0]

# --- no-PHI guard ---------------------------------------------------------------

def test_phi_guard_patient_reference():
    with pytest.raises(PhiGuardError):
        run(client().search_docs("show me Patient/abc-123"))

def test_phi_guard_fhir_resource_json():
    with pytest.raises(PhiGuardError):
        run(client().search_docs('{"resourceType": "Patient", "id": "x"}'))

def test_phi_guard_ssn_and_mrn():
    assert "ssn" in screen_for_phi("patient ssn 123-45-6789")
    assert screen_for_phi("MRN: 1234567")
    with pytest.raises(PhiGuardError):
        run(client().call_tool("search_documents", {"query": "MRN 1234567 record"}))

def test_phi_guard_sends_nothing():
    seen = []
    c = EpicMcpClient(transport=make_transport(seen=seen))
    with pytest.raises(PhiGuardError):
        run(c.search_docs("Patient/should-not-be-sent"))
    assert seen == []  # guard fires before any request leaves the process

def test_clean_doc_query_passes_guard():
    assert screen_for_phi("MedicationRequest FHIR R4 API specification") == []

# --- graceful degradation -------------------------------------------------------

def test_unreachable_degrades():
    def boom(request):
        raise httpx.ConnectError("connection refused", request=request)
    c = EpicMcpClient(transport=httpx.MockTransport(boom))
    listed = run(c.list_tools())
    assert listed["available"] is False and listed["tools"] == []
    searched = run(c.search_docs("Patient FHIR R4"))
    assert searched["available"] is False and searched["results"] == []

def test_disabled_degrades():
    c = EpicMcpClient(enabled=False, transport=make_transport())
    assert run(c.list_tools())["available"] is False
    assert run(c.search_docs("Patient FHIR R4"))["available"] is False

# --- FHIR validator wiring --------------------------------------------------------

def test_wiring_records_epic_spec():
    b, _ = generate_bundle(2)
    result = annotate_with_epic_specs(validate_bundle(b), client=client())
    assert result["epic_specs"]["available"]
    spec = result["epic_specs"]["specs"]["Patient"]
    assert spec["document_id"] == "api:11419" and "Patient.Read" in spec["title"]
    report = render_report(result, "test")
    assert "api:11419" in report and "Epic API spec references" in report
    assert result["total_resources"] == 10  # validation itself unchanged

def test_wiring_degrades_gracefully():
    def boom(request):
        raise httpx.ConnectError("down", request=request)
    bad = EpicMcpClient(transport=httpx.MockTransport(boom))
    refs = fetch_epic_spec_references(["Patient"], client=bad)
    assert refs["available"] is False and refs["specs"] == {}
    b, _ = generate_bundle(2)
    result = annotate_with_epic_specs(validate_bundle(b), client=bad)
    assert result["total_resources"] == 10
    assert "validation ran without Epic spec references" in render_report(result, "test")
