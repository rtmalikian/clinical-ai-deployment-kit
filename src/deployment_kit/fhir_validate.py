"""FHIR R4 validation harness (stdlib).

Checks: Bundle structure; per-resource required fields; reference
integrity; terminology formats (ICD-10-CM pattern, LOINC pattern);
data quality (missing names, implausible birth dates, future dates).
This validates format and plausibility, NOT full FHIR profile
conformance (that needs a FHIR validator / HAPI server).
Optional --with-epic-specs: record which Epic API spec document (via the
open.epic MCP documentation server, see epic_mcp.py / EPIC_MCP.md) each
resource type was validated against; lazily imported, degrades gracefully.
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path

REQUIRED = {
    "Patient": ["name","birthDate"],
    "Encounter": ["status","subject"],
    "Condition": ["code","subject"],
    "Observation": ["status","code","subject"],
    "Claim": ["status","patient","insurer"],
    "Procedure": ["status","subject"],
    "MedicationRequest": ["status","intent","subject"],
}
ICD10 = re.compile(r"^[A-TV-Z][0-9][0-9AB](?:\.[0-9A-TV-Z]{1,4})?$")
LOINC = re.compile(r"^\d{1,5}-\d$")

def _get(res, field):
    return res.get(field)

def validate_bundle(bundle: dict) -> dict:
    issues=[]; counts=Counter(); dq={"missing_fields":0,"implausible_birthdates":0,"bad_icd10":0,"bad_loinc":0,"broken_references":0,"missing_names":0}
    if bundle.get("resourceType")!="Bundle": issues.append("root is not a Bundle")
    entries=bundle.get("entry",[])
    ids=set()
    resources=[]
    for e in entries:
        res=e.get("resource",{}); resources.append(res); counts[res.get("resourceType","?")]+=1
        if res.get("id"): ids.add(f"{res.get('resourceType')}/{res['id']}")
    for res in resources:
        rt=res.get("resourceType")
        for f in REQUIRED.get(rt,[]):
            if not _get(res,f):
                dq["missing_fields"]+=1; issues.append(f"{rt}/{res.get('id')}: missing required field '{f}'")
        if rt=="Patient":
            names=res.get("name") or []
            if not names or not names[0].get("family"): dq["missing_names"]+=1; issues.append(f"Patient/{res.get('id')}: missing family name")
            bd=res.get("birthDate","")
            if bd and (bd < "1900-01-01" or bd > "2026-10-28"): dq["implausible_birthdates"]+=1; issues.append(f"Patient/{res.get('id')}: implausible birthDate {bd}")
        if rt=="Condition":
            for c in ((res.get("code") or {}).get("coding") or []):
                code=c.get("code")
                if not code:
                    dq["missing_fields"]+=1; issues.append(f"Condition/{res.get('id')}: coding missing 'code'")
                if code and "icd-10" in (c.get("system") or "") and not ICD10.match(code):
                    dq["bad_icd10"]+=1; issues.append(f"Condition/{res.get('id')}: bad ICD-10 format {code}")
        if rt=="Observation":
            for c in ((res.get("code") or {}).get("coding") or []):
                code=c.get("code")
                if code and "loinc" in (c.get("system") or "") and not LOINC.match(code):
                    dq["bad_loinc"]+=1; issues.append(f"Observation/{res.get('id')}: bad LOINC format {code}")
        # reference integrity
        def walk(o):
            if isinstance(o,dict):
                ref=o.get("reference")
                if isinstance(ref,str) and "/" in ref and not ref.startswith("http") and ref not in ids:
                    dq["broken_references"]+=1; issues.append(f"{rt}/{res.get('id')}: broken reference {ref}")
                for v in o.values(): walk(v)
            elif isinstance(o,list):
                for v in o: walk(v)
        walk(res)
    return {"total_resources": sum(counts.values()), "by_type": dict(counts),
            "data_quality": dq, "issue_count": len(issues), "issues": issues}

async def fetch_epic_spec_references_async(resource_types, client=None) -> dict:
    """Look up the Epic API spec for each FHIR resource *type* via open.epic MCP.

    The open.epic MCP server (https://mcp.open.epic.com) is a documentation /
    spec-lookup service only — it is NOT a patient-data server, and no PHI is
    ever sent to it (the client's in-code no-PHI guard screens every query;
    only resource type names such as "Patient FHIR R4" are queried here).
    Returns {"available": bool, "specs": {resource_type: {document_id, title,
    url}}, ...} and degrades gracefully (available=False) when the server is
    disabled or unreachable, so validation results never depend on it.
    """
    try:
        if client is None:
            from deployment_kit.epic_mcp import EpicMcpClient
            client = EpicMcpClient()
        specs = {}
        available = True
        for rt in sorted(set(resource_types)):
            out = await client.search_docs(f"{rt} FHIR R4")
            if not out.get("available"):
                return {"available": False,
                        "reason": out.get("reason", "open.epic MCP unavailable"),
                        "server": out.get("server"), "specs": {}}
            first = (out.get("results") or [None])[0]
            if isinstance(first, dict):
                specs[rt] = {"document_id": first.get("id") or first.get("document_id"),
                             "title": first.get("title"),
                             "url": first.get("url")}
        return {"available": available, "server": getattr(client, "base_url", None),
                "specs": specs}
    except Exception as exc:  # graceful degradation — never fail validation
        return {"available": False, "reason": str(exc), "specs": {}}

def fetch_epic_spec_references(resource_types, client=None) -> dict:
    """Sync wrapper for fetch_epic_spec_references_async (see its docstring)."""
    import asyncio
    try:
        return asyncio.run(fetch_epic_spec_references_async(resource_types, client=client))
    except Exception as exc:  # e.g. called from a running event loop
        return {"available": False, "reason": str(exc), "specs": {}}

def annotate_with_epic_specs(result: dict, client=None) -> dict:
    """Attach an "epic_specs" record to a validate_bundle() result, recording
    which Epic API spec document each validated resource type was checked
    against. Degrades gracefully: on any failure the record is
    available=False and the validation result itself is unchanged."""
    result = dict(result)
    result["epic_specs"] = fetch_epic_spec_references(result.get("by_type", {}).keys(), client=client)
    return result

def render_report(result: dict, provenance: str) -> str:
    dq=result["data_quality"]
    lines=["# FHIR R4 validation report","",f"**Data provenance:** {provenance}","",
           f"**Total resources:** {result['total_resources']}","",
           "| Resource type | Count |","|---|---|"]+[f"| {k} | {v} |" for k,v in sorted(result["by_type"].items())]
    lines+=["","## Data-quality findings","",f"- Missing required fields: {dq['missing_fields']}",
            f"- Missing patient family names: {dq['missing_names']}",
            f"- Implausible birth dates: {dq['implausible_birthdates']}",
            f"- Bad ICD-10 formats: {dq['bad_icd10']}",f"- Bad LOINC formats: {dq['bad_loinc']}",
            f"- Broken references: {dq['broken_references']}",f"- Total issues listed: {result['issue_count']}","",
            "## Issues",""]+[f"- {i}" for i in result["issues"]] or ["- none"]
    epic=result.get("epic_specs")
    if epic is not None:
        lines+=["","## Epic API spec references (open.epic MCP)","","Documentation/spec lookup only via https://mcp.open.epic.com — no patient data is sent to that server (see EPIC_MCP.md).",""]
        if epic.get("available"):
            lines+=[f"- {rt}: {s.get('title') or '(untitled)'} (`{s.get('document_id')}`){' — ' + s['url'] if s.get('url') else ''}" for rt,s in sorted(epic.get("specs",{}).items())] or ["- none returned"]
        else:
            lines+=[f"- Unavailable ({epic.get('reason','unknown')}) — validation ran without Epic spec references."]
    lines+=["","> Scope: structural, terminology-format and plausibility checks only. Not a substitute for the official HL7 FHIR validator or profile conformance testing against US Core / Da Vinci PAS."]
    return "\n".join(lines)+"\n"

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("bundle"); ap.add_argument("--md"); ap.add_argument("--provenance", default="unspecified")
    ap.add_argument("--with-epic-specs", action="store_true", help="also look up the Epic API spec for each resource type via the open.epic MCP documentation server and record it in the report (degrades gracefully when unavailable; no patient data is sent)")
    a=ap.parse_args(argv); bundle=json.loads(Path(a.bundle).read_text()); r=validate_bundle(bundle)
    if a.with_epic_specs: r=annotate_with_epic_specs(r)
    print(render_report(r, a.provenance))
    if a.md: Path(a.md).write_text(render_report(r, a.provenance))
    return 0
if __name__=="__main__": sys.exit(main())
