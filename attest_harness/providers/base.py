from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Protocol, Callable

Role = Literal["system", "user", "assistant", "tool"]

@dataclass
class Message:
    role: Role
    content: str
    tool_call_id: str | None = None   # for role == "tool"
    name: str | None = None

@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict  # JSON schema
    handler: Callable[[dict], str]

@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    tool_calls_made: list[str] = field(default_factory=list)
    raw_request: dict = field(default_factory=dict)  # dumped for check_requests

class Provider(Protocol):
    name: str
    def complete(self, messages: list[Message], tools: list[ToolSpec] | None,
                 max_tokens: int) -> Completion: ...

class MockProvider:
    """Returns canned text; records requests; auto-calls the first tool once if present."""
    name = "mock"
    def __init__(self, reply: str = "Sure. Here is the analysis."):
        self.reply = reply; self.requests: list[dict] = []
    def complete(self, messages, tools=None, max_tokens=400):
        calls = []
        if tools:
            out = tools[0].handler({"token": "__from_messages__"})
            calls.append(tools[0].name)
            messages = messages + [Message("tool", out, tool_call_id="t1", name=tools[0].name)]
        req = {"messages": [m.__dict__ for m in messages], "tools": [t.name for t in tools or []]}
        self.requests.append(req)
        return Completion(self.reply, 100, 50, calls, req)
