from __future__ import annotations
import csv, random
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

@dataclass(frozen=True)
class Prompt:
    id: str
    source: str
    source_url: str
    category: str
    text: str
    hint: str  # likely | unlikely | unknown

def load_prompts(path: Path) -> list[Prompt]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate prompt ids in " + str(path))
    return [Prompt(r["id"], r["source"], r["source_url"], r["category"],
                   r["text"].strip(), r.get("expected_refusal_hint", "unknown")) for r in rows]

def stratified_sample(prompts: list[Prompt], n: int, by: str = "hint", seed: int = 0) -> list[Prompt]:
    rng = random.Random(seed)
    strata: dict[str, list[Prompt]] = defaultdict(list)
    for p in prompts:
        strata[getattr(p, by)].append(p)
    for s in strata.values():
        rng.shuffle(s)
    out: list[Prompt] = []
    keys = sorted(strata)
    i = 0
    while len(out) < n and any(strata.values()):
        k = keys[i % len(keys)]
        if strata[k]:
            out.append(strata[k].pop())
        i += 1
    return sorted(out, key=lambda p: p.id)
