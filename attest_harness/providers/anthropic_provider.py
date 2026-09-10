from __future__ import annotations
from anthropic import Anthropic
from .base import Message, ToolSpec, Completion

class AnthropicProvider:
    def __init__(self, model: str, api_key: str | None = None, client=None, name: str | None = None):
        self.model = model; self.name = name or model
        self.client = client or Anthropic(api_key=api_key)

    def complete(self, messages: list[Message], tools: list[ToolSpec] | None, max_tokens: int) -> Completion:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        an_tools = [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools] if tools else None
        by_name = {t.name: t for t in tools or []}
        made, in_tok, out_tok = [], 0, 0
        first_request = {"model": self.model, "system": system, "messages": list(msgs), "tools": an_tools}
        for _ in range(3):
            kw = dict(model=self.model, system=system, messages=msgs, max_tokens=max_tokens, temperature=0)
            if an_tools: kw["tools"] = an_tools
            r = self.client.messages.create(**kw)
            in_tok += r.usage.input_tokens; out_tok += r.usage.output_tokens
            uses = [b for b in r.content if getattr(b, "type", "") == "tool_use"]
            if r.stop_reason == "tool_use" and uses:
                msgs.append({"role": "assistant", "content": [
                    {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input} for b in uses]})
                results = []
                for b in uses:
                    made.append(b.name)
                    results.append({"type": "tool_result", "tool_use_id": b.id,
                                    "content": by_name[b.name].handler(dict(b.input or {}))})
                msgs.append({"role": "user", "content": results})
                continue
            text = "".join(getattr(b, "text", "") for b in r.content if getattr(b, "type", "") == "text")
            return Completion(text, in_tok, out_tok, made, first_request)
        return Completion("", in_tok, out_tok, made, first_request)
