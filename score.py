#!/usr/bin/env python3
"""Score family surf trips: composite, tiers, weight-sensitivity bands, month calendar.

Usage: python3 score.py   (writes RANKINGS.md and rankings.csv)
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PERTURB = 0.25  # +/- fraction applied to one weight at a time


def composite(scores, weights):
    total_w = sum(weights.values())
    return sum(weights[d] * scores[d] for d in weights) / total_w * 10.0


def rank_map(trips, weights):
    ordered = sorted(trips, key=lambda t: -composite(t["scores"], weights))
    return {t["name"]: i + 1 for i, t in enumerate(ordered)}


def sensitivity_bands(trips, weights):
    """Min/max rank per trip across one-at-a-time +/-25% weight perturbations."""
    bands = {t["name"]: [rank_map(trips, weights)[t["name"]]] * 2 for t in trips}
    for dim in weights:
        for sign in (1 + PERTURB, 1 - PERTURB):
            w = dict(weights)
            w[dim] = weights[dim] * sign
            rm = rank_map(trips, w)
            for name, r in rm.items():
                lo, hi = bands[name]
                bands[name] = [min(lo, r), max(hi, r)]
    return bands


def tier(score):
    if score >= 80:
        return "S"
    if score >= 75:
        return "A"
    if score >= 70:
        return "B"
    return "C"


BEGINNER_FLOOR = 6  # panel-adopted gate: below this, the trip is "experts-first"


def family_ok(trip):
    """Mixed-ability gate: does the true beginner get real waves here?"""
    return trip["scores"]["beginner"] >= BEGINNER_FLOOR


def main():
    data = json.loads((ROOT / "data" / "trips.json").read_text())
    weights, trips = data["weights"], data["trips"]
    assert abs(sum(weights.values()) - 100) < 1e-9, "weights must sum to 100"
    for t in trips:
        missing = set(weights) - set(t["scores"])
        assert not missing, f"{t['name']} missing {missing}"

    for t in trips:
        t["composite"] = round(composite(t["scores"], weights), 1)
    trips.sort(key=lambda t: -t["composite"])
    bands = sensitivity_bands(trips, weights)

    # CSV
    dims = data["dimensions"]
    with open(ROOT / "rankings.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "trip", "country", "region", "window", "composite", "tier",
                    "family_ok", "cost_band", "min_days", "booking",
                    "rank_lo", "rank_hi"] + dims + ["travel_note", "note"])
        for i, t in enumerate(trips, 1):
            lo, hi = bands[t["name"]]
            w.writerow([i, t["name"], t["country"], t["region"], t["window"],
                        t["composite"], tier(t["composite"]),
                        "yes" if family_ok(t) else "no",
                        t["cost_band"], t["min_days"], t["booking"], lo, hi]
                       + [t["scores"][d] for d in dims] + [t["travel_note"], t["note"]])

    # Markdown
    lines = ["# Family Surf Trip Rankings", "",
             f"{len(trips)} trips scored. Composite 0–100; see METHODOLOGY.md for weights and anchors.",
             "Rank band = min–max rank when any one weight is perturbed ±25% (tight band = robust).",
             f"Fam = mixed-ability gate (beginner ≥ {BEGINNER_FLOOR}); ✗ marks experts-first trips.",
             "Cost = all-in $/person/week incl. BOS flights ($ <2.5k · $$ 2.5–4k · $$$ 4–6.5k · $$$$ >6.5k).", "",
             "| # | Trip | Where | Window | Score | Tier | Fam | Cost | Min days | Booking | Rank band |",
             "|---|------|-------|--------|-------|------|-----|------|----------|---------|-----------|"]
    for i, t in enumerate(trips, 1):
        lo, hi = bands[t["name"]]
        lines.append(f"| {i} | {t['name']} | {t['country']} | {t['window']} | "
                     f"{t['composite']} | {tier(t['composite'])} | "
                     f"{'✓' if family_ok(t) else '✗'} | {t['cost_band']} | {t['min_days']} | "
                     f"{t['booking']} | {lo}–{hi} |")

    gated = [t for t in trips if family_ok(t)]
    lines += ["", f"## Mixed-ability division (beginner ≥ {BEGINNER_FLOOR}) — top 12", ""]
    for i, t in enumerate(gated[:12], 1):
        lines.append(f"{i}. {t['name']} — {t['composite']} ({t['cost_band']}, {t['window']})")
    excluded = [t["name"] for t in trips if not family_ok(t)]
    lines.append(f"\nExperts-first (gated out): {len(excluded)} trips — {', '.join(excluded)}")

    # Month calendar: top 5 per month
    lines += ["", "## Best trips by month (top 5 in-window)", ""]
    for m in range(1, 13):
        in_month = [t for t in trips if m in t["months"]][:5]
        picks = "; ".join(f"{t['name']} ({t['composite']})" for t in in_month)
        lines.append(f"- **{MONTHS[m-1]}**: {picks}")

    # Null check: famous crowded spots must not top the table
    lines += ["", "## Null check", ""]
    fame_traps = ["Uluwatu + Bingin (Bukit)", "Noosa", "Waikiki + North Shore (Oahu)"]
    ranks = {t["name"]: i + 1 for i, t in enumerate(trips)}
    for name in fame_traps:
        lines.append(f"- {name}: rank {ranks[name]} of {len(trips)} "
                     f"({'PASS — fame did not buy rank' if ranks[name] > 10 else 'REVIEW'})")

    (ROOT / "RANKINGS.md").write_text("\n".join(lines) + "\n")
    print(f"Scored {len(trips)} trips -> RANKINGS.md, rankings.csv")
    for i, t in enumerate(trips[:15], 1):
        lo, hi = bands[t["name"]]
        print(f"{i:>2}. {t['composite']:>5}  [{lo}-{hi}]  {t['name']} — {t['window']}")


if __name__ == "__main__":
    main()
