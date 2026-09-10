from __future__ import annotations
import json, re, time
from openai import OpenAI, RateLimitError
from .base import Message, ToolSpec, Completion
from .key_pool import KeyPool

_RETRY_AFTER_RE = re.compile(r"try again in\s+(?:(\d+)m)?([\d.]+)s", re.I)

def _seconds_until_retry(exc: RateLimitError, default: float = 30.0) -> float:
    """Best-effort wait time: the Retry-After header if present, else Groq's
    'Please try again in 3m8.784s' message text, else a default guess."""
    try:
        header = exc.response.headers.get("retry-after")
        if header:
            return float(header)
    except Exception:
        pass
    msg = ""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        msg = str(body.get("message", ""))
    if not msg:
        msg = str(exc)
    m = _RETRY_AFTER_RE.search(msg)
    if m:
        return (float(m.group(1)) if m.group(1) else 0.0) * 60 + float(m.group(2))
    return default

class OpenAIProvider:
    """Works for OpenAI and any OpenAI-compatible endpoint (set base_url).

    Pass `api_keys` (a list of 2+ keys) instead of `api_key` to rotate through them on
    HTTP 429 rate-limit errors -- built for Groq's free tier, where a run at this volume
    can plausibly outrun a single key's per-minute quota. Only the failed request is
    retried under the next key; the tool-call loop's accumulated message state is kept.

    Key rotation alone doesn't help every 429, though: verified live during the main run
    that Groq enforces some limits (e.g. tokens-per-day) per *organization*, not per key --
    if all keys belong to the same account, rotating through them just re-hits the same
    wall immediately. So after a full round of keys is exhausted, `_create` sleeps for
    Groq's own suggested wait (parsed from the error) and retries the whole cycle again,
    up to `max_wait_rounds` times, before finally raising.
    """
    def __init__(self, model: str, api_key: str | None = None, api_keys: list[str] | None = None,
                 base_url: str | None = None, client=None, name: str | None = None,
                 temperature: float | None = 0.0, client_factory=None, reasoning_effort: str | None = None,
                 max_wait_rounds: int = 10, max_wait_seconds: float = 300.0):
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
        self.max_wait_rounds = max_wait_rounds
        self.max_wait_seconds = max_wait_seconds
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
        last_exc: RateLimitError | None = None
        for round_ in range(self.max_wait_rounds):
            for attempt in range(attempts):
                try:
                    return self.client.chat.completions.create(**kw)
                except RateLimitError as e:
                    last_exc = e
                    if attempt < attempts - 1:
                        self._rotate_client()
            if round_ < self.max_wait_rounds - 1:
                time.sleep(min(_seconds_until_retry(last_exc), self.max_wait_seconds) + 1)
        raise last_exc

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
