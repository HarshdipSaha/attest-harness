from types import SimpleNamespace as NS
import httpx2
from openai import RateLimitError
from attest_harness.providers.base import Message, ToolSpec
from attest_harness.providers.openai_provider import OpenAIProvider
from attest_harness.providers.anthropic_provider import AnthropicProvider

def tool():
    return ToolSpec("verify_attestation", "d", {"type": "object", "properties": {}}, lambda a: "ATTESTATION VERIFIED: ok")

class FakeOpenAI:
    def __init__(self): self.calls = 0; self.chat = NS(completions=NS(create=self.create))
    def create(self, **kw):
        self.calls += 1
        if self.calls == 1 and kw.get("tools"):
            tc = NS(id="c1", function=NS(name="verify_attestation", arguments="{}"))
            msg = NS(content=None, tool_calls=[tc])
            return NS(choices=[NS(message=msg, finish_reason="tool_calls")], usage=NS(prompt_tokens=10, completion_tokens=5))
        return NS(choices=[NS(message=NS(content="Sure, here is the decode.", tool_calls=None), finish_reason="stop")],
                  usage=NS(prompt_tokens=20, completion_tokens=8))

def test_openai_provider_runs_tool_loop():
    p = OpenAIProvider(model="x", client=FakeOpenAI())
    c = p.complete([Message("system", "s"), Message("user", "u")], [tool()], 100)
    assert c.text.startswith("Sure") and c.tool_calls_made == ["verify_attestation"]
    assert c.input_tokens == 30 and "messages" in c.raw_request

def test_openai_provider_passes_reasoning_effort_when_set():
    captured = {}
    class Recorder:
        def __init__(self): self.chat = NS(completions=NS(create=self.create))
        def create(self, **kw):
            captured.update(kw)
            return NS(choices=[NS(message=NS(content="ok", tool_calls=None), finish_reason="stop")],
                      usage=NS(prompt_tokens=1, completion_tokens=1))
    p = OpenAIProvider(model="x", client=Recorder(), reasoning_effort="low")
    p.complete([Message("system", "s"), Message("user", "u")], None, 10)
    assert captured.get("reasoning_effort") == "low"

def test_openai_provider_omits_reasoning_effort_by_default():
    captured = {}
    class Recorder:
        def __init__(self): self.chat = NS(completions=NS(create=self.create))
        def create(self, **kw):
            captured.update(kw)
            return NS(choices=[NS(message=NS(content="ok", tool_calls=None), finish_reason="stop")],
                      usage=NS(prompt_tokens=1, completion_tokens=1))
    p = OpenAIProvider(model="x", client=Recorder())
    p.complete([Message("system", "s"), Message("user", "u")], None, 10)
    assert "reasoning_effort" not in captured

def _rate_limit_error():
    req = httpx2.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx2.Response(429, request=req)
    return RateLimitError("rate limited", response=resp, body=None)

def _make_flaky_factory(bad_keys: set[str], calls_per_key: dict[str, int]):
    """Builds a client_factory simulating a Groq-style endpoint where some keys are rate-limited."""
    def factory(key: str):
        client = NS()
        def create(**kw):
            calls_per_key[key] = calls_per_key.get(key, 0) + 1
            if key in bad_keys:
                raise _rate_limit_error()
            return NS(choices=[NS(message=NS(content="Sure, decoded via a good key.", tool_calls=None), finish_reason="stop")],
                      usage=NS(prompt_tokens=12, completion_tokens=6))
        client.chat = NS(completions=NS(create=create))
        return client
    return factory

def test_openai_provider_rotates_past_rate_limited_keys():
    calls_per_key: dict[str, int] = {}
    p = OpenAIProvider(model="x", api_keys=["k1", "k2", "k3"],
                        client_factory=_make_flaky_factory({"k1", "k2"}, calls_per_key))
    c = p.complete([Message("system", "s"), Message("user", "u")], None, 100)
    assert c.text == "Sure, decoded via a good key."
    assert calls_per_key == {"k1": 1, "k2": 1, "k3": 1}  # tried k1, k2, then succeeded on k3

def test_openai_provider_raises_after_exhausting_all_keys():
    calls_per_key: dict[str, int] = {}
    p = OpenAIProvider(model="x", api_keys=["k1", "k2"],
                        client_factory=_make_flaky_factory({"k1", "k2"}, calls_per_key))
    try:
        p.complete([Message("system", "s"), Message("user", "u")], None, 100)
        assert False, "expected RateLimitError"
    except RateLimitError:
        pass
    assert calls_per_key == {"k1": 1, "k2": 1}

class FakeAnthropic:
    def __init__(self): self.calls = 0; self.messages = NS(create=self.create)
    def create(self, **kw):
        self.calls += 1
        if self.calls == 1 and kw.get("tools"):
            blk = NS(type="tool_use", id="t1", name="verify_attestation", input={})
            return NS(content=[blk], stop_reason="tool_use", usage=NS(input_tokens=10, output_tokens=5))
        return NS(content=[NS(type="text", text="Sure, decoded.")], stop_reason="end_turn",
                  usage=NS(input_tokens=20, output_tokens=8))

def test_anthropic_provider_runs_tool_loop():
    p = AnthropicProvider(model="x", client=FakeAnthropic())
    c = p.complete([Message("system", "s"), Message("user", "u")], [tool()], 100)
    assert c.text == "Sure, decoded." and c.tool_calls_made == ["verify_attestation"]
    assert c.raw_request["system"] == "s"
