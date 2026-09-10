from __future__ import annotations
import json
from openai import OpenAI
from .base import Message, ToolSpec, Completion

class OpenAIProvider:
    """Works for OpenAI and any OpenAI-compatible endpoint (set base_url)."""
    def __init__(self, model: str, api_key: str | None = None, base_url: str | None = None, client=None,
                 name: str | None = None, temperature: float | None = 0.0):
        self.model = model
        self.name = name or model
        self.temperature = temperature  # None => omit (reasoning models reject the parameter)
        self.client = client or OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, messages: list[Message], tools: list[ToolSpec] | None, max_tokens: int) -> Completion:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        oa_tools = [{"type": "function", "function": {"name": t.name, "description": t.description,
                     "parameters": t.parameters}} for t in tools] if tools else None
        by_name = {t.name: t for t in tools or []}
        made, in_tok, out_tok = [], 0, 0
        first_request = {"model": self.model, "messages": list(msgs), "tools": oa_tools}
        for _ in range(3):  # tool loop bound
            kw = dict(model=self.model, messages=msgs, max_tokens=max_tokens)
            if self.temperature is not None: kw["temperature"] = self.temperature
            if oa_tools: kw["tools"] = oa_tools
            r = self.client.chat.completions.create(**kw)
            in_tok += r.usage.prompt_tokens; out_tok += r.usage.completion_tokens
            m = r.choices[0].message
            if getattr(m, "tool_calls", None):
                msgs.append({"role": "assistant", "content": None,
                             "tool_calls": [{"id": tc.id, "type": "function",
                                             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                                            for tc in m.tool_calls]})
                for tc in m.tool_calls:
                    made.append(tc.function.name)
                    out = by_name[tc.function.name].handler(json.loads(tc.function.arguments or "{}"))
                    msgs.append({"role": "tool", "tool_call_id": tc.id, "content": out})
                continue
            return Completion(m.content or "", in_tok, out_tok, made, first_request)
        return Completion("", in_tok, out_tok, made, first_request)
