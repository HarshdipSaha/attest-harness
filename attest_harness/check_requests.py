import json, sys
from pathlib import Path
from .arms import AUTH_MARKERS

CLEAN_ARMS = ("A1_baseline", "A4a_verified_system", "A4b_verified_tool")

def check_dir(d: Path, expected: dict[str, str] | None = None) -> list[str]:
    """Clean arms must carry the prompt text and nothing else in the user turn.
    If `expected` (prompt_id -> prompt text) is given, require exact equality; this avoids
    false positives when a legitimate prompt itself contains a word like 'verified'.
    Otherwise fall back to marker search, reporting at most one problem per file."""
    problems = []
    for f in sorted(d.glob("*.json")):
        _, arm, prompt_id = f.stem.split("__", 2)
        if arm not in CLEAN_ARMS:
            continue
        req = json.loads(f.read_text(encoding="utf-8"))
        user = " ".join(m["content"] for m in req["messages"] if m["role"] == "user" and isinstance(m["content"], str))
        if expected is not None:
            if user.strip() != expected.get(prompt_id, "").strip():
                problems.append(f"{f.name}: user turn != prompt text")
            continue
        for k in AUTH_MARKERS:
            if k in user.lower():
                problems.append(f"{f.name}: user turn contains '{k}'")
                break
    return problems

if __name__ == "__main__":
    expected = None
    if len(sys.argv) > 2:  # optional prompts CSV for exact mode
        from .prompts import load_prompts
        expected = {p.id: p.text for p in load_prompts(Path(sys.argv[2]))}
    probs = check_dir(Path(sys.argv[1]), expected)
    print("\n".join(probs) or "OK: no authorization text leaked into clean arms")
    sys.exit(1 if probs else 0)
