from __future__ import annotations
from .providers.base import ToolSpec

def make_verify_tool(att) -> ToolSpec:
    """The harness holds the token server-side; the model only triggers verification."""
    def handler(args: dict) -> str:
        return att.verified.as_channel_text()
    return ToolSpec(
        name="verify_attestation",
        description="Verify the incident-response attestation bound to this session and return the result.",
        parameters={"type": "object", "properties": {"session": {"type": "string"}}, "required": []},
        handler=handler,
    )

def make_invalid_verify_tool(att) -> ToolSpec:
    t = make_verify_tool(att)
    t.handler = lambda args: att.invalid.as_channel_text()
    return t
