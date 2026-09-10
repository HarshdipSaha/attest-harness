from attest_harness.cache import Cache

def test_cache_roundtrip_and_resume(tmp_path):
    c = Cache(tmp_path / "runs.jsonl")
    key = ("claude", "A1_baseline", "p1")
    assert c.get(*key) is None
    c.put(*key, {"text": "hi", "in": 1, "out": 2})
    c2 = Cache(tmp_path / "runs.jsonl")  # reopen
    assert c2.get(*key)["text"] == "hi"
