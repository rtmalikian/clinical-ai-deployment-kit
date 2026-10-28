"""Compliance-as-code scanner.

Audits a target repository for engineering controls mapped to HIPAA
safeguards (45 CFR Part 164, Subpart C: 164.308 administrative,
164.310 physical, 164.312 technical, 164.316 policies/documentation)
and SOC 2 Trust Services Criteria (CC6/CC7/CC8 family).

This is a self-assessment aid. It does NOT certify HIPAA compliance
or SOC 2 attestation — those require organisational controls, risk
analysis, policies, training and independent audit.
Stdlib only.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".tox", "dist", "build"}
TEXT_EXT = {".py",".md",".txt",".yml",".yaml",".toml",".cfg",".ini",".json",".js",".ts",".sh",".env",".example",".html",".xml"}
MAX_BYTES = 512_000

SECRET_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("hardcoded_password", re.compile(r"(?i)\bpassword\s*=\s*['\"][^'\"]{6,}['\"]")),
    ("hardcoded_api_key", re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]")),
    ("generic_bearer", re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{30,}")),
]
PHI_LOG_PATTERNS = [
    re.compile(r"(?i)(?:log(?:ger)?\.(?:info|debug|warning|error)|print)\s*\([^)]*\b(?:ssn|social_security|patient_name|date_of_birth|medical_record_number|mrn)\b"),
]

def _iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() in TEXT_EXT or name in {"Dockerfile","requirements.txt",".gitignore","SECURITY.md"}:
                try:
                    if p.stat().st_size <= MAX_BYTES:
                        yield p
                except OSError:
                    pass

def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

@dataclass
class Finding:
    control_id: str
    title: str
    status: str  # pass | warn | fail
    hipaa: str
    soc2: str
    evidence: list = field(default_factory=list)
    remediation: str = ""

@dataclass
class ScanReport:
    target: str
    score: int
    max_score: int
    findings: list
    files_scanned: int
    secret_hits: int
    @property
    def percent(self) -> int:
        return round(100 * self.score / self.max_score) if self.max_score else 0
    def to_dict(self):
        d = asdict(self); d["percent"] = self.percent; return d

POINTS = {"pass": 10, "warn": 5, "fail": 0}

def scan(root: str | Path) -> ScanReport:
    root = Path(root).resolve()
    files = list(_iter_files(root))
    corpus = {}
    for p in files:
        corpus[str(p.relative_to(root))] = _read(p)
    blob = "\n".join(corpus.values()).lower()
    names = {n.lower() for n in corpus}
    findings: list[Finding] = []

    def has(*pats):
        return [p for p in pats if re.search(p, blob)]

    # 1 Auth
    ev = has(r"\bauthenticate\b", r"oauth2|openid|oidc|saml", r"jwt|jose|bearer token", r"login_required|requires_auth|security\s*=|Depends\(.*(?:auth|current_user|get_current)")
    findings.append(Finding("AUTH-01","Authentication present","pass" if ev else "fail",
        "164.312(d) Person or entity authentication","CC6.1", ev[:4],
        "Add authenticated access (OIDC/SAML SSO — see src/deployment_kit/oidc.py, saml.py). No unauthenticated PHI endpoints."))
    # 2 Audit logging
    ev = has(r"audit[_ ]?log|audit trail", r"logging\.(?:basic)?config|getlogger|structlog|access[_ ]log")
    findings.append(Finding("AUDIT-01","Audit logging","pass" if len(ev)>=2 else ("warn" if ev else "fail"),
        "164.312(b) Audit controls; 164.308(a)(1)(ii)(D) Information system activity review","CC7.2", ev[:4],
        "Log who accessed what, when — tamper-evident, reviewed regularly; never log PHI payloads."))
    # 3 TLS / encryption in transit
    ev = has(r"ssl|tls|https://|certbot|acme", r"hsts|strict-transport")
    findings.append(Finding("ENC-01","Encryption in transit (TLS) configured or documented",
        "pass" if ev else "fail","164.312(e)(1) Transmission security","CC6.7", ev[:4],
        "Terminate TLS everywhere, redirect HTTP->HTTPS, enable HSTS at the proxy."))
    # 4 Encryption at rest documented
    ev = has(r"encrypt(?:ion)? at rest|kms|aes-?256|encrypted volume|luks|sqlcipher")
    findings.append(Finding("ENC-02","Encryption at rest addressed","pass" if ev else "warn",
        "164.312(a)(2)(iv) Encryption and decryption (addressable)","CC6.1", ev[:4],
        "Document at-rest encryption (cloud KMS / encrypted volumes / encrypted DB) in SECURITY.md even if provided by the host."))
    # 5 Secrets in code (inverse)
    secret_hits, secret_ev = 0, []
    for rel, text in corpus.items():
        if rel.endswith((".example",)) or "test" in rel.lower():
            continue
        for label, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                secret_hits += 1; secret_ev.append(f"{rel}: {label}")
    findings.append(Finding("SEC-01","No hard-coded secrets in source",
        "pass" if secret_hits==0 else "fail",
        "164.312(a)(1) Unique user identification / access control; 164.308(a)(3) Workforce access","CC6.1",
        secret_ev[:8], "Move secrets to env/secret manager, rotate any exposed secret, add .env to .gitignore."))
    # 6 Dependency pinning
    pinned = False; pin_ev=[]
    for rel, text in corpus.items():
        if rel.endswith("requirements.txt"):
            lines=[l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
            if lines and all("==" in l for l in lines): pinned=True; pin_ev.append(rel)
        if rel in {"poetry.lock","package-lock.json","pipfile.lock","uv.lock"}: pinned=True; pin_ev.append(rel)
    findings.append(Finding("DEP-01","Dependencies pinned / lockfile present","pass" if pinned else "warn",
        "164.308(a)(8) Evaluation; 164.316(b) Documentation","CC7.1 / CC8.1", pin_ev,
        "Pin exact versions (==) or commit a lockfile so builds are reproducible and auditable."))
    # 7 SECURITY.md
    ok = any(n=="security.md" or n.endswith("/security.md") for n in names)
    findings.append(Finding("DOC-01","SECURITY.md present","pass" if ok else "fail",
        "164.316(a) Policies and procedures; 164.308(a)(6) Security incident procedures","CC7.3", ["SECURITY.md"] if ok else [],
        "Add SECURITY.md: scope, honest limits, vulnerability reporting, incident contact."))
    # 8 Backup / retention
    ev = has(r"backup|retention|restore drill|disaster recovery|contingency plan")
    findings.append(Finding("BAK-01","Backup / retention / contingency addressed","pass" if len(ev)>=2 else ("warn" if ev else "fail"),
        "164.308(a)(7) Contingency plan; 164.310(d)(2)(iv) Data backup plan","CC7.4", ev[:4],
        "Automate backups, define retention, and run a documented restore drill (see backup.py)."))
    # 9 PHI in logs (inverse)
    phi_hits=[]
    for rel, text in corpus.items():
        if "test" in rel.lower(): continue
        for pat in PHI_LOG_PATTERNS:
            if pat.search(text): phi_hits.append(rel)
    findings.append(Finding("PHI-01","No PHI-like identifiers written to logs",
        "pass" if not phi_hits else "fail",
        "164.312(b) Audit controls; 164.502(b) Minimum necessary","CC6.5", phi_hits[:6],
        "Log identifiers/hashes, never names, SSNs, DOBs or MRNs."))
    # 10 .gitignore protects env
    gi = corpus.get(".gitignore","")
    ok = ".env" in gi
    findings.append(Finding("SEC-02",".gitignore excludes .env / secrets","pass" if ok else "warn",
        "164.308(a)(3)(ii)(C) Emergency access / access establishment","CC6.1", [".gitignore:.env"] if ok else [],
        "Add .env, *.pem, *.key to .gitignore."))
    # 11 Unique IDs / RBAC
    ev = has(r"rbac|role[-_ ]based|\broles?\b.*(?:admin|clinician|auditor)|permission")
    findings.append(Finding("RBAC-01","Role-based access control addressed","pass" if ev else "warn",
        "164.312(a)(2)(i) Unique user identification; 164.308(a)(4) Information access management","CC6.3", ev[:4],
        "Define an RBAC matrix (see docs/RBAC.md), enforce least privilege."))
    # 12 Risk / incident docs
    ev = has(r"incident response|risk analysis|risk assessment|threat model")
    findings.append(Finding("IR-01","Risk analysis / incident response documented","pass" if ev else "warn",
        "164.308(a)(1)(ii)(A) Risk analysis; 164.308(a)(6) Security incident procedures","CC7.3/CC7.4", ev[:4],
        "Document a risk analysis, threat model and incident-response playbook; run a tabletop exercise."))

    score = sum(POINTS[f.status] for f in findings)
    return ScanReport(str(root), score, 10*len(findings), findings, len(files), secret_hits)

def render_markdown(r: ScanReport, label: str = "") -> str:
    lines=[f"# Compliance-as-code self-assessment — {r.target}", ""]
    if label: lines += [label, ""]
    lines += [f"**Score: {r.score}/{r.max_score} ({r.percent}%)** across {len(r.findings)} controls · Files scanned: {r.files_scanned} · Secret hits: {r.secret_hits}",
              "", "> This is an automated self-assessment of engineering artefacts in code. It is **not** HIPAA certification, **not** a SOC 2 attestation, and **not** a substitute for a formal risk analysis (45 CFR 164.308(a)(1)) or independent audit.", "",
              "| Control | Status | HIPAA (45 CFR) | SOC 2 | Matched pattern / evidence |", "|---|---|---|---|---|"]
    for f in r.findings:
        ev = "<br>".join(f.evidence) if f.evidence else "—"
        lines.append(f"| {f.control_id} {f.title} | **{f.status.upper()}** | {f.hipaa} | {f.soc2} | {ev} |")
    lines += ["", "## Remediation for non-pass controls", ""]
    for f in r.findings:
        if f.status != "pass":
            lines.append(f"- **{f.control_id} {f.title} ({f.status}):** {f.remediation}")
    return "\n".join(lines)+"\n"

def main(argv=None):
    ap=argparse.ArgumentParser(prog="deployment-kit-scan", description="HIPAA/SOC 2 compliance-as-code self-assessment scanner")
    ap.add_argument("target"); ap.add_argument("--json", dest="json_out"); ap.add_argument("--md", dest="md_out")
    a=ap.parse_args(argv)
    r=scan(a.target)
    if a.json_out: Path(a.json_out).write_text(json.dumps(r.to_dict(), indent=2))
    if a.md_out: Path(a.md_out).write_text(render_markdown(r))
    print(render_markdown(r))
    return 0

if __name__=="__main__":
    sys.exit(main())
