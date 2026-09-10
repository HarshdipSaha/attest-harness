import json
from pathlib import Path

class Cache:
    def __init__(self, path: Path):
        self.path = path; self._d: dict[tuple, dict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line); self._d[(r["model"], r["arm"], r["prompt_id"])] = r["data"]
    def get(self, model, arm, prompt_id):
        return self._d.get((model, arm, prompt_id))
    def put(self, model, arm, prompt_id, data: dict):
        self._d[(model, arm, prompt_id)] = data
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"model": model, "arm": arm, "prompt_id": prompt_id, "data": data}) + "\n")
