from __future__ import annotations
import argparse, csv, json, os, time
from pathlib import Path
from dotenv import load_dotenv
import yaml
from ir_attest.keys import load_or_create
from .prompts import Prompt, load_prompts, stratified_sample
from .arms import load_config, build_messages, Attestation
from .tools import make_invalid_verify_tool
from .providers.base import Provider
from .judge import regex_refusal, LLMJudge
from .budget import Budget, BudgetExceeded
from .cache import Cache

FIELDS = ["model", "arm", "prompt_id", "category", "source", "regex_label", "judge_label",
          "judge_reason", "tool_calls", "in_tokens", "out_tokens", "cost_usd", "response"]

def run_experiment(*, prompts: list[Prompt], providers: list[tuple[str, Provider, float, float]],
                   arms_path: Path, judge_provider: Provider, out_dir: Path, cap_usd: float,
                   max_tokens: int = 400, judge_cost=(0.00015, 0.0006), sleep_s: float = 0.0) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "requests").mkdir(exist_ok=True)
    cfg = load_config(arms_path)
    kp = load_or_create(Path("keys"))
    cache = Cache(out_dir / "runs.jsonl")
    budget = Budget(cap_usd)
    judge = LLMJudge(judge_provider)
    rows = []
    try:
        for name, prov, usd_in, usd_out in providers:
            for p in prompts:
                att = Attestation.for_prompt(kp, p, scope=cfg.scope)
                for arm_id, arm in cfg.arms.items():
                    hit = cache.get(name, arm_id, p.id)
                    if hit is None:
                        msgs, tools = build_messages(p, arm, att)
                        c = prov.complete(msgs, tools, max_tokens)
                        cost = budget.charge(c.input_tokens, c.output_tokens, usd_in, usd_out)
                        # reserve the judge cost BEFORE calling the judge so a cap hit never discards a paid completion
                        budget.charge(800, 40, *judge_cost)  # conservative fixed estimate for a 3k-char judge input
                        jl = judge.judge(p.text, c.text)
                        (out_dir / "requests" / f"{name}__{arm_id}__{p.id}.json").write_text(
                            json.dumps(c.raw_request, indent=1, default=str), encoding="utf-8")
                        hit = dict(response=c.text, in_tokens=c.input_tokens, out_tokens=c.output_tokens,
                                   cost_usd=round(cost, 6), tool_calls="|".join(c.tool_calls_made),
                                   regex_label=regex_refusal(c.text), judge_label=jl.label, judge_reason=jl.reason)
                        cache.put(name, arm_id, p.id, hit)
                        if sleep_s: time.sleep(sleep_s)
                    rows.append(dict(model=name, arm=arm_id, prompt_id=p.id, category=p.category, source=p.source, **hit))
    except BudgetExceeded as e:
        print("STOPPED:", e)
    with (out_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"rows={len(rows)} spent=${budget.spent:.2f}")
    return out_dir / "results.csv"

def _providers_from_yaml(path: Path):
    from .providers.anthropic_provider import AnthropicProvider
    from .providers.openai_provider import OpenAIProvider
    y = yaml.safe_load(os.path.expandvars(path.read_text(encoding="utf-8")))
    out = []
    for m in y["models"]:
        assert "${" not in str(m["model"]) + str(m.get("base_url", "")), f"unset env var in models.yaml entry {m['name']}"
        if m["provider"] == "anthropic":
            prov = AnthropicProvider(m["model"], name=m["name"])
        elif m["provider"] == "openai":
            prov = OpenAIProvider(m["model"], name=m["name"])
        else:
            prov = OpenAIProvider(m["model"], api_key=os.environ[m["api_key_env"]], base_url=m["base_url"],
                                  name=m["name"], temperature=m.get("temperature", 0.0))
        out.append((m["name"], prov, m["usd_per_1k_in"], m["usd_per_1k_out"]))
    j = y["judge"]
    judge = OpenAIProvider(j["model"], name="judge")
    return out, judge, (j["usd_per_1k_in"], j["usd_per_1k_out"])

def main(argv=None):
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default="prompts/main.csv")
    ap.add_argument("--n", type=int, default=250)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--models", default="configs/models.yaml")
    ap.add_argument("--only-model", default=None)
    ap.add_argument("--out", default="results/main")
    ap.add_argument("--cap", type=float, default=float(os.getenv("BUDGET_USD", "60")))
    ap.add_argument("--sleep", type=float, default=0.3)
    a = ap.parse_args(argv)
    prompts = stratified_sample(load_prompts(Path(a.prompts)), a.n, seed=a.seed)
    provs, judge, jcost = _providers_from_yaml(Path(a.models))
    if a.only_model:
        provs = [p for p in provs if p[0] == a.only_model]
    run_experiment(prompts=prompts, providers=provs, arms_path=Path("configs/arms.yaml"),
                   judge_provider=judge, out_dir=Path(a.out), cap_usd=a.cap, judge_cost=jcost, sleep_s=a.sleep)

if __name__ == "__main__":
    main()
