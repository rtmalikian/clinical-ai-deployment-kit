"""SAML 2.0 assertion parsing/validation — stdlib XML.

LIMITS (documented honestly): xml.etree is not hardened against all
XML attacks the way a dedicated SAML library is. Production SAML
should use a vetted library (e.g. python3-saml / xmlsec) with X.509
certificate validation, XML Signature wrapping (XSW) defences and
defusedxml. This module implements the *validation logic* — issuer,
audience, conditions window, NameID, attributes, and a pluggable
signature-verifier interface — so the flow is testable offline. The
demo HMAC verifier exists ONLY for tests/fixtures; it is not how
real SAML signatures (RSA/ECDSA over canonicalised XML) work.
"""
from __future__ import annotations
import base64, hashlib, hmac, time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone

NS = {"saml":"urn:oasis:names:tc:SAML:2.0:assertion","samlp":"urn:oasis:names:tc:SAML:2.0:protocol"}

class SAMLError(ValueError): pass

@dataclass
class SAMLAssertion:
    issuer: str
    name_id: str
    attributes: dict = field(default_factory=dict)
    not_before: float|None = None
    not_on_or_after: float|None = None
    audience: str|None = None
    raw: str = ""

def _parse_time(s: str|None) -> float|None:
    if not s: return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()

def parse_assertion(xml_text: str) -> SAMLAssertion:
    if "<!DOCTYPE" in xml_text or "<!ENTITY" in xml_text:
        raise SAMLError("DOCTYPE/ENTITY declarations are rejected")
    try: root = ET.fromstring(xml_text)
    except ET.ParseError as e: raise SAMLError(f"invalid XML: {e}") from e
    assertion = root if root.tag.endswith("Assertion") else root.find(".//saml:Assertion", NS)
    if assertion is None: raise SAMLError("no Assertion element")
    issuer_el = assertion.find("saml:Issuer", NS)
    subject = assertion.find("saml:Subject/saml:NameID", NS)
    cond = assertion.find("saml:Conditions", NS)
    aud = assertion.find("saml:Conditions/saml:AudienceRestriction/saml:Audience", NS)
    attrs={}
    for attr in assertion.findall("saml:AttributeStatement/saml:Attribute", NS):
        vals=[v.text for v in attr.findall("saml:AttributeValue", NS)]
        attrs[attr.get("Name")] = vals[0] if len(vals)==1 else vals
    return SAMLAssertion(
        issuer=issuer_el.text if issuer_el is not None else "",
        name_id=subject.text if subject is not None else "",
        attributes=attrs,
        not_before=_parse_time(cond.get("NotBefore")) if cond is not None else None,
        not_on_or_after=_parse_time(cond.get("NotOnOrAfter")) if cond is not None else None,
        audience=aud.text if aud is not None else None,
        raw=xml_text)

def validate_assertion(a: SAMLAssertion, expected_issuer: str, expected_audience: str,
                       signature_verifier=None, now: float|None=None) -> SAMLAssertion:
    now = now or time.time()
    if a.issuer != expected_issuer: raise SAMLError("issuer mismatch")
    if expected_audience and a.audience != expected_audience: raise SAMLError("audience mismatch")
    if a.not_before is not None and now < a.not_before: raise SAMLError("assertion not yet valid")
    if a.not_on_or_after is not None and now >= a.not_on_or_after: raise SAMLError("assertion expired")
    if not a.name_id: raise SAMLError("missing NameID")
    if signature_verifier is not None and not signature_verifier(a.raw):
        raise SAMLError("signature verification failed")
    return a

def hmac_demo_verifier(shared_secret: str, expected_signature_b64: str):
    """TEST-ONLY verifier: HMAC-SHA256 over the raw assertion text."""
    def verify(raw: str) -> bool:
        digest = hmac.new(shared_secret.encode(), raw.encode(), hashlib.sha256).digest()
        return hmac.compare_digest(base64.b64encode(digest).decode(), expected_signature_b64)
    return verify

def make_sample_assertion(name_id="clinician@example.org", issuer="https://idp.example.org",
                          audience="clinical-ai-app", not_before="2020-01-01T00:00:00Z",
                          not_on_or_after="2099-01-01T00:00:00Z", role="clinician") -> str:
    return f'''<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_abc" Version="2.0" IssueInstant="2026-01-01T00:00:00Z"><saml:Issuer>{issuer}</saml:Issuer><saml:Subject><saml:NameID>{name_id}</saml:NameID></saml:Subject><saml:Conditions NotBefore="{not_before}" NotOnOrAfter="{not_on_or_after}"><saml:AudienceRestriction><saml:Audience>{audience}</saml:Audience></saml:AudienceRestriction></saml:Conditions><saml:AttributeStatement><saml:Attribute Name="role"><saml:AttributeValue>{role}</saml:AttributeValue></saml:Attribute><saml:Attribute Name="department"><saml:AttributeValue>prior-auth</saml:AttributeValue></saml:Attribute></saml:AttributeStatement></saml:Assertion>'''
