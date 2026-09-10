import time
import pytest
from ir_attest.keys import generate_keypair
from ir_attest.token import issue, verify

@pytest.fixture
def kp():
    return generate_keypair()

def base_claims():
    return dict(iss="hf-security", sub="responder-42", scope="ir:forensics",
                incident_ref="HF-2026-07", ttl_seconds=600)

def test_valid_token_verifies(kp):
    tok = issue(kp.private, **base_claims())
    res = verify(tok, kp.public, expected_scope="ir:forensics")
    assert res.valid is True
    assert res.claims["iss"] == "hf-security"
    assert res.reason == "ok"

def test_expired_token_invalid(kp):
    tok = issue(kp.private, **{**base_claims(), "ttl_seconds": -1})
    res = verify(tok, kp.public, expected_scope="ir:forensics")
    assert res.valid is False and res.reason == "expired"

def test_bad_signature_invalid(kp):
    other = generate_keypair()
    tok = issue(other.private, **base_claims())
    res = verify(tok, kp.public, expected_scope="ir:forensics")
    assert res.valid is False and res.reason == "bad_signature"

def test_wrong_scope_invalid(kp):
    tok = issue(kp.private, **base_claims())
    res = verify(tok, kp.public, expected_scope="ir:offense")
    assert res.valid is False and res.reason == "scope_mismatch"

def test_replayed_nonce_invalid(kp):
    tok = issue(kp.private, **base_claims())
    seen = set()
    assert verify(tok, kp.public, expected_scope="ir:forensics", seen_nonces=seen).valid
    assert verify(tok, kp.public, expected_scope="ir:forensics", seen_nonces=seen).reason == "replayed"

def test_tampered_payload_invalid(kp):
    tok = issue(kp.private, **base_claims())
    head, payload, sig = tok.split(".")
    tampered = ".".join([head, payload[:-2] + "AA", sig])
    assert verify(tampered, kp.public, expected_scope="ir:forensics").valid is False

def test_garbage_invalid(kp):
    assert verify("not.a.token", kp.public, expected_scope="x").reason in ("malformed", "bad_signature")
