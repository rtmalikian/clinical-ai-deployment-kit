import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from deployment_kit.scanner import scan

def write(root, rel, text):
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)

def compliant_repo(tmp_path):
    write(tmp_path, "SECURITY.md", "# Security\nEncryption at rest via KMS AES-256. Incident response and risk analysis documented. Backup and retention policy with restore drill.")
    write(tmp_path, ".gitignore", ".env\n*.pem\n")
    write(tmp_path, "requirements.txt", "fastapi==0.115.0\nuvicorn==0.30.0\n")
    write(tmp_path, "app.py", "import logging\nlogger = logging.getLogger('audit')\n# audit log: audit_log records access\n# oauth2 oidc jwt authentication, role-based rbac admin clinician permission\n# tls https ssl termination\nuser = authenticate(token)\n")
    return tmp_path

def bad_repo(tmp_path):
    write(tmp_path, "app.py", "password = 'supersecret123'\napi_key = 'abcd1234efgh5678ijkl'\nprint(patient_name)\nimport logging\nlogger.info(ssn)\n")
    write(tmp_path, "requirements.txt", "fastapi\nuvicorn\n")
    return tmp_path

def by_id(report, cid): return next(f for f in report.findings if f.control_id == cid)

def test_compliant_scores_high(tmp_path):
    r = scan(compliant_repo(tmp_path)); assert r.percent >= 70, [(f.control_id, f.status) for f in r.findings]

def test_compliant_auth_pass(tmp_path): assert by_id(scan(compliant_repo(tmp_path)), "AUTH-01").status == "pass"
def test_compliant_security_md_pass(tmp_path): assert by_id(scan(compliant_repo(tmp_path)), "DOC-01").status == "pass"
def test_compliant_pinning_pass(tmp_path): assert by_id(scan(compliant_repo(tmp_path)), "DEP-01").status == "pass"
def test_compliant_no_secrets(tmp_path):
    r = scan(compliant_repo(tmp_path)); assert by_id(r, "SEC-01").status == "pass" and r.secret_hits == 0
def test_bad_secrets_fail(tmp_path):
    r = scan(bad_repo(tmp_path)); assert by_id(r, "SEC-01").status == "fail" and r.secret_hits >= 2
def test_bad_auth_fail(tmp_path): assert by_id(scan(bad_repo(tmp_path)), "AUTH-01").status == "fail"
def test_bad_security_md_fail(tmp_path): assert by_id(scan(bad_repo(tmp_path)), "DOC-01").status == "fail"
def test_bad_phi_logging_fail(tmp_path): assert by_id(scan(bad_repo(tmp_path)), "PHI-01").status == "fail"
def test_bad_unpinned_warn(tmp_path): assert by_id(scan(bad_repo(tmp_path)), "DEP-01").status in ("warn", "fail")
def test_scanner_skips_venv(tmp_path):
    write(tmp_path, ".venv/lib/bad.py", "password = 'supersecret123'\n")
    write(tmp_path, "app.py", "x = 1\n")
    assert scan(tmp_path).secret_hits == 0
def test_report_json_shape(tmp_path):
    d = scan(compliant_repo(tmp_path)).to_dict(); assert "percent" in d and len(d["findings"]) == 12
