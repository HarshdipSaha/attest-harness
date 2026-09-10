# IRAT Token Spec (v0.1)

1. **Purpose**: out-of-band incident-response authorization; a channel signal, not a text claim.

2. **Format**: `base64url(header).base64url(claims).base64url(sig)`; header `{"alg":"EdDSA","typ":"IRAT"}`;
   claims `iss, sub, scope, incident_ref, iat, exp, nonce`; Ed25519 over `header.claims`.

3. **Issuer = accountability object**: the deployer's own security team signs; the signing event is
   logged (who, sub, scope, incident_ref, iat, exp) and retained per incident-record obligations.
   Issuer and relying party are the same organization, so there is no certificate-authority question
   in v0.1.

4. **Verification**: signature, expiry, scope match, nonce not replayed; result is a structured
   boolean plus reason, delivered to the model through the system or tool channel, never via user
   text.

5. **Scope vocabulary**: `ir:forensics`, `ir:detection`, `ir:triage`; default TTL 15 min; max 1 h.

6. **Non-goals (v0.1)**: PKI, revocation lists, multi-issuer trust, provider-side enforcement.

7. **Threats acknowledged**: token theft within TTL, issuer compromise, deployer omitting
   verification (the Aurora case).
