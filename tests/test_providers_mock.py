from types import SimpleNamespace as NS
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
