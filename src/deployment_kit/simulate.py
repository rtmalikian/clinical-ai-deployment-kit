"""SIMULATED 90-day prior-auth pilot dry-run — SYNTHETIC DATA ONLY.

This is NOT a real pilot. No real clinic, patients, payers or
customers are involved. It is a seeded simulation over invented
clinic workflow data that exercises the PILOT.md metric definitions
end-to-end, so the measurement code — not invented results — is
what is being demonstrated.
"""
from __future__ import annotations
import argparse, json, random, statistics
from pathlib import Path

STAMP = "SIMULATED / SYNTHETIC DATA — NOT A REAL PILOT"

def run_simulation(days: int=90, seed: int=20261028) -> dict:
    rng=random.Random(seed)
    rows=[]
    for day in range(1, days+1):
        n = rng.randint(6, 14)  # synthetic PA requests/day for a small clinic
        for _ in range(n):
            incomplete_baseline = rng.random() < 0.28   # synthetic assumption
            incomplete_with_kit = incomplete_baseline and rng.random() < 0.25  # completeness gate catches most
            assembly_baseline_min = rng.uniform(35, 95)   # coordinator assembly, synthetic
            assembly_kit_min = rng.uniform(4, 12)          # review of a gated packet, synthetic
            turnaround_baseline_d = rng.uniform(2.0, 6.0) + (3.0 if incomplete_baseline else 0.0)
            turnaround_kit_d = rng.uniform(1.5, 5.0) + (3.0 if incomplete_with_kit else 0.0)
            rows.append({
                "day": day,
                "first_pass_baseline": not incomplete_baseline,
                "first_pass_kit": not incomplete_with_kit,
                "assembly_baseline_min": round(assembly_baseline_min,2),
                "assembly_kit_min": round(assembly_kit_min,2),
                "turnaround_baseline_d": round(turnaround_baseline_d,2),
                "turnaround_kit_d": round(turnaround_kit_d,2),
            })
    total=len(rows)
    def rate(key): return round(sum(1 for r in rows if r[key])/total, 4)
    saved_min=sum(r["assembly_baseline_min"]-r["assembly_kit_min"] for r in rows)
    metrics={
        "stamp": STAMP, "days": days, "seed": seed, "requests": total,
        "first_pass_rate_baseline": rate("first_pass_baseline"),
        "first_pass_rate_with_kit": rate("first_pass_kit"),
        "mean_turnaround_days_baseline": round(statistics.mean(r["turnaround_baseline_d"] for r in rows),2),
        "mean_turnaround_days_with_kit": round(statistics.mean(r["turnaround_kit_d"] for r in rows),2),
        "mean_assembly_minutes_baseline": round(statistics.mean(r["assembly_baseline_min"] for r in rows),2),
        "mean_assembly_minutes_with_kit": round(statistics.mean(r["assembly_kit_min"] for r in rows),2),
        "coordinator_hours_saved_simulated": round(saved_min/60,1),
        "assumptions": "All inputs are synthetic assumptions chosen by the author (see module docstring). They are NOT measured results from any real clinic.",
    }
    return {"metrics": metrics, "rows": rows}

def render_dashboard(m: dict) -> str:
    return f"""# Simulated pilot dashboard — 90-day dry run

> ## {STAMP}
> No real clinic, patients, payers or customers were involved. Inputs are synthetic assumptions; outputs show the measurement pipeline working, not real-world efficacy.

| Metric (PILOT.md definition) | Simulated baseline | Simulated with kit |
|---|---|---|
| Requests over {m['days']} days | {m['requests']} | {m['requests']} |
| First-pass complete rate | {m['first_pass_rate_baseline']:.1%} | {m['first_pass_rate_with_kit']:.1%} |
| Mean payer turnaround (days) | {m['mean_turnaround_days_baseline']} | {m['mean_turnaround_days_with_kit']} |
| Mean clinic assembly time (min) | {m['mean_assembly_minutes_baseline']} | {m['mean_assembly_minutes_with_kit']} |
| Coordinator hours saved (simulated) | — | {m['coordinator_hours_saved_simulated']} |

Seed: {m['seed']} (deterministic — rerunning reproduces these numbers exactly.)
"""

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument("--days",type=int,default=90); ap.add_argument("--seed",type=int,default=20261028); ap.add_argument("--out",default="examples/simulation")
    a=ap.parse_args(argv); out=Path(a.out); out.mkdir(parents=True, exist_ok=True)
    result=run_simulation(a.days, a.seed)
    (out/"simulation_metrics.json").write_text(json.dumps(result["metrics"],indent=2))
    (out/"SIMULATED_dashboard.md").write_text(render_dashboard(result["metrics"]))
    print(render_dashboard(result["metrics"])); return 0
if __name__=="__main__": main()
