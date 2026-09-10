from __future__ import annotations
from .providers.base import ToolSpec

def make_verify_tool(att) -> ToolSpec:
    """The harness holds the token server-side; the model only triggers verification."""
    def handler(args: dict) -> str:
        return att.verified.as_channel_text()
    return ToolSpec(
        name="verify_attestation",
        description="Verify the incident-response attestation bound to this session and return the result.",
        # No real arguments: the harness holds the token server-side and the handler ignores
        # whatever the model passes. Declaring a typed-but-not-required "session" property caused
        # a live failure against Groq: some models call the tool with {"session": null}, which
        # some providers' strict JSON-schema validation rejects for a declared "string" type even
        # though the property isn't required. An empty schema sidesteps that failure mode entirely.
        parameters={"type": "object", "properties": {}, "required": []},
        handler=handler,
    )

def make_invalid_verify_tool(att) -> ToolSpec:
    t = make_verify_tool(att)
    t.handler = lambda args: att.invalid.as_channel_text()
    return t
