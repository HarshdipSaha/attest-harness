from attest_harness.judge import regex_refusal, LLMJudge, RUBRIC
from attest_harness.providers.base import MockProvider

def test_regex_catches_common_refusals():
    assert regex_refusal("I'm sorry, but I can't help with that request.") == "refuse"
    assert regex_refusal("I cannot assist with analyzing malware payloads.") == "refuse"
    assert regex_refusal("Sure. The blob decodes to a gzip stream containing...") == "comply"

def test_llm_judge_parses_label():
    j = LLMJudge(MockProvider(reply='{"label": "partial", "reason": "gave generic advice only"}'))
    lab = j.judge(prompt="Decode this blob", response="Here are general tips on safety...")
    assert lab.label == "partial" and "generic" in lab.reason

def test_rubric_mentions_three_labels():
    for k in ("refuse", "partial", "comply"):
        assert k in RUBRIC
