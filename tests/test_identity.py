import sys, time, base64, hashlib, hmac
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from deployment_kit.oidc import make_hs256_token, validate_oidc_token, require_permission, TokenError
from deployment_kit.saml import parse_assertion, validate_assertion, make_sample_assertion, hmac_demo_verifier, SAMLError
from deployment_kit.app import scim_create_user, scim_deprovision

SECRET="test-secret"; ISS="https://idp.example.org"; AUD="clinical-ai-app"
def tok(**over):
    claims={"sub":"user-1","iss":ISS,"aud":AUD,"exp":int(time.time())+3600,"roles":["clinician"]}
    claims.update(over); return make_hs256_token(claims, SECRET)

def test_oidc_valid(): assert validate_oidc_token(tok(), SECRET, ISS, AUD)["sub"]=="user-1"
def test_oidc_bad_signature():
    with pytest.raises(TokenError): validate_oidc_token(tok(), "wrong", ISS, AUD)
def test_oidc_expired():
    with pytest.raises(TokenError): validate_oidc_token(tok(exp=int(time.time())-7200), SECRET, ISS, AUD)
def test_oidc_wrong_issuer():
    with pytest.raises(TokenError): validate_oidc_token(tok(iss="https://evil.example"), SECRET, ISS, AUD)
def test_oidc_wrong_audience():
    with pytest.raises(TokenError): validate_oidc_token(tok(aud="other-app"), SECRET, ISS, AUD)
def test_oidc_missing_sub():
    with pytest.raises(TokenError): validate_oidc_token(tok(sub=""), SECRET, ISS, AUD)
def test_oidc_not_yet_valid():
    with pytest.raises(TokenError): validate_oidc_token(tok(nbf=int(time.time())+7200), SECRET, ISS, AUD)
def test_rbac_clinician_approve(): assert require_permission({"roles":["clinician"]}, "approve")
def test_rbac_readonly_cannot_write(): assert not require_permission({"roles":["readonly"]}, "write")
def test_rbac_auditor_audit(): assert require_permission({"roles":["auditor"]}, "view_audit")
def test_rbac_unknown_role(): assert not require_permission({"roles":["nobody"]}, "read")

def test_saml_parse():
    a=parse_assertion(make_sample_assertion()); assert a.name_id=="clinician@example.org" and a.attributes["role"]=="clinician"
def test_saml_validate_ok():
    a=parse_assertion(make_sample_assertion()); assert validate_assertion(a, ISS, AUD).name_id
def test_saml_wrong_issuer():
    a=parse_assertion(make_sample_assertion(issuer="https://evil.example"))
    with pytest.raises(SAMLError): validate_assertion(a, ISS, AUD)
def test_saml_expired():
    a=parse_assertion(make_sample_assertion(not_on_or_after="2001-01-01T00:00:00Z"))
    with pytest.raises(SAMLError): validate_assertion(a, ISS, AUD)
def test_saml_wrong_audience():
    a=parse_assertion(make_sample_assertion(audience="other"))
    with pytest.raises(SAMLError): validate_assertion(a, ISS, AUD)
def test_saml_rejects_doctype():
    with pytest.raises(SAMLError): parse_assertion("<!DOCTYPE x><Assertion/>")
def test_saml_hmac_demo_verifier():
    xml=make_sample_assertion(); secret="s3cret"
    sig=base64.b64encode(hmac.new(secret.encode(), xml.encode(), hashlib.sha256).digest()).decode()
    a=parse_assertion(xml); validate_assertion(a, ISS, AUD, signature_verifier=hmac_demo_verifier(secret, sig))
def test_saml_hmac_demo_verifier_rejects_tamper():
    xml=make_sample_assertion(); secret="s3cret"
    sig=base64.b64encode(hmac.new(secret.encode(), xml.encode(), hashlib.sha256).digest()).decode()
    a=parse_assertion(xml.replace("clinician","admin")); 
    with pytest.raises(SAMLError): validate_assertion(a, ISS, AUD, signature_verifier=hmac_demo_verifier(secret, sig))

def test_scim_create(): 
    u=scim_create_user({"userName":"jane@example.org","name":{"givenName":"Jane"}}); assert u["id"] and u["active"]
def test_scim_requires_username():
    with pytest.raises(ValueError): scim_create_user({})
def test_scim_deprovision():
    u=scim_create_user({"userName":"john@example.org"}); assert scim_deprovision(u["id"])["active"] is False
def test_scim_deprovision_missing():
    with pytest.raises(KeyError): scim_deprovision("scim-9999")
