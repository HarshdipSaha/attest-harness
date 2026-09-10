from __future__ import annotations
import json
from openai import OpenAI, RateLimitError
from .base import Message, ToolSpec, Completion
from .key_pool import KeyPool

class OpenAIProvider:
    """Works for OpenAI and any OpenAI-compatible endpoint (set base_url).

    Pass `api_keys` (a list of 2+ keys) instead of `api_key` to rotate through them on
    HTTP 429 rate-limit errors -- built for Groq's free tier, where a run at this volume
    can plausibly outrun a single key's per-minute quota. Only the failed request is
    retried under the next key; the tool-call loop's accumulated message state is kept.
    """
    def __init__(self, model: str, api_key: str | None = None, api_keys: list[str] | None = None,
                 base_url: str | None = None, client=None, name: str | None = None,
                 temperature: float | None = 0.0, client_factory=None, reasoning_effort: str | None = None):
        self.model = model
        self.name = name or model
        self.temperature = temperature  # None => omit (reasoning models reject the parameter)
        # Some hosted reasoning models (e.g. Groq's openai/gpt-oss-*) spend completion tokens on
        # a hidden chain-of-thought before the visible answer, and that reasoning shares the same
        # max_tokens budget as message.content. Left at the provider default ("medium" on Groq),
        # a short max_tokens (like the judge's 120) can be entirely consumed by reasoning, leaving
        # message.content empty. Set reasoning_effort="low" for such models to leave real headroom
        # for the visible answer. Omit (None) for models that don't support/need the parameter.
        self.reasoning_effort = reasoning_effort
        self._client_factory = client_factory or (lambda key: OpenAI(api_key=key, base_url=base_url))
        if client is not None:
            self.client = client
            self._pool: KeyPool | None = None
        elif api_keys:
            self._pool = KeyPool(api_keys)
            self.client = self._client_factory(self._pool.current)
        else:
            self._pool = None
            self.client = self._client_factory(api_key)

    def _rotate_client(self) -> bool:
        if self._pool is None or len(self._pool) < 2:
            return False
        self._pool.rotate()
        self.client = self._client_factory(self._pool.current)
        return True

    def _create(self, **kw):
        attempts = len(self._pool) if self._pool else 1
        for attempt in range(attempts):
            try:
                return self.client.chat.completions.create(**kw)
            except RateLimitError:
                if attempt == attempts - 1 or not self._rotate_client():
                    raise

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
            if self.reasoning_effort is not None: kw["reasoning_effort"] = self.reasoning_effort
            if oa_tools: kw["tools"] = oa_tools
            r = self._create(**kw)
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
