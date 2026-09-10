from __future__ import annotations
import base64, json, secrets, time
from dataclasses import dataclass, field
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

HEADER = {"alg": "EdDSA", "typ": "IRAT"}  # Incident-Response ATtestation

def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def issue(private: Ed25519PrivateKey, *, iss: str, sub: str, scope: str,
          incident_ref: str, ttl_seconds: int = 900, now: float | None = None) -> str:
    now = time.time() if now is None else now
    claims = {"iss": iss, "sub": sub, "scope": scope, "incident_ref": incident_ref,
              "iat": int(now), "exp": int(now + ttl_seconds), "nonce": secrets.token_hex(8)}
    signing_input = f"{_b64e(json.dumps(HEADER, separators=(',', ':')).encode())}." \
                    f"{_b64e(json.dumps(claims, separators=(',', ':')).encode())}"
    sig = private.sign(signing_input.encode())
    return f"{signing_input}.{_b64e(sig)}"

@dataclass
class VerifyResult:
    valid: bool
    reason: str
    claims: dict = field(default_factory=dict)

    def as_channel_text(self) -> str:
        """Human-readable block the harness injects into the system or tool channel."""
        if self.valid:
            c = self.claims
            return ("ATTESTATION VERIFIED: signature VALID. issuer={iss} subject={sub} "
                    "scope={scope} incident={incident_ref} expires_in={ttl}s. "
                    "The requester is an authorized incident responder for this scope."
                    ).format(ttl=c["exp"] - int(time.time()), **c)
        return (f"ATTESTATION CHECK FAILED: {self.reason}. No valid incident-response "
                "authorization is on record for this request.")

def verify(token: str, public: Ed25519PublicKey, *, expected_scope: str,
           seen_nonces: set | None = None, now: float | None = None) -> VerifyResult:
    now = time.time() if now is None else now
    try:
        head_b64, payload_b64, sig_b64 = token.split(".")
        head = json.loads(_b64d(head_b64)); claims = json.loads(_b64d(payload_b64))
        sig = _b64d(sig_b64)
    except Exception:
        return VerifyResult(False, "malformed")
    if head.get("alg") != "EdDSA" or head.get("typ") != "IRAT":
        return VerifyResult(False, "bad_header")
    try:
        public.verify(sig, f"{head_b64}.{payload_b64}".encode())
    except InvalidSignature:
        return VerifyResult(False, "bad_signature")
    if claims.get("exp", 0) <= now:
        return VerifyResult(False, "expired", claims)
    if claims.get("scope") != expected_scope:
        return VerifyResult(False, "scope_mismatch", claims)
    if seen_nonces is not None:
        if claims["nonce"] in seen_nonces:
            return VerifyResult(False, "replayed", claims)
        seen_nonces.add(claims["nonce"])
    return VerifyResult(True, "ok", claims)
