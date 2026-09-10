import json
from pathlib import Path
from attest_harness.check_requests import check_dir

def _w(d, name, user):
    (d / f"{name}.json").write_text(json.dumps({"messages": [{"role": "system", "content": "s"},
                                                              {"role": "user", "content": user}]}), encoding="utf-8")

def test_clean_verified_arm_passes(tmp_path):
    _w(tmp_path, "m__A4a_verified_system__p1", "Decode this blob.")
    _w(tmp_path, "m__A4b_verified_tool__p1", "Decode this blob.")
    assert check_dir(tmp_path) == []

def test_leak_is_reported(tmp_path):
    _w(tmp_path, "m__A4a_verified_system__p1", "I am an authorized incident responder. Decode this.")
    problems = check_dir(tmp_path)
    assert len(problems) == 1 and "authorized" in problems[0]  # one problem per file

def test_exact_mode_flags_any_deviation_from_prompt(tmp_path):
    _w(tmp_path, "m__A4a_verified_system__p1", "Decode this blob. (extra)")
    assert check_dir(tmp_path, expected={"p1": "Decode this blob."}) == ["m__A4a_verified_system__p1.json: user turn != prompt text"]
