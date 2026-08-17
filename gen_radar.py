#!/usr/bin/env python3
"""Export data/strike_radar.json — the strike-eligible portfolio for SurfBot's
strike-radar monitor (docs/FORECAST_DESIGN.md, Phase 1.5).

Eligibility: passes the strike gate (advanced >= 7 AND strikeability >= 7),
not a pool, deduped by cluster (highest strike composite wins). Each entry
carries the season window, a Surfline search query, and min_lead_days — the
alert horizon floor derived from launch latency: alerting on a swell that
arrives sooner than you can is noise.

Usage: python3 gen_radar.py
"""
import json
from pathlib import Path

from score import composite

ROOT = Path(__file__).parent


def min_lead_days(t):
    """Days of forecast lead needed to launch, from the travel-ease score."""
    tr = t["scores"]["travel"]
    if tr >= 8:
        return 2   # drive or short nonstop
    if tr >= 5.5:
        return 3   # one easy connection
    if tr >= 3:
        return 4   # long haul
    return 5       # expedition


def main():
    data = json.loads((ROOT / "data" / "trips.json").read_text())
    strike = data["modes"]["strike"]
    gates = strike["gates"]

    eligible = [t for t in data["trips"]
                if not t.get("pool")
                and all(t["scores"][d] >= mn for d, mn in gates)]

    # Cluster dedupe: siblings share a coastline; monitor the strongest row only
    best = {}
    for t in eligible:
        key = t.get("cluster") or t["name"]
        c = composite(t["scores"], strike["weights"])
        if key not in best or c > best[key][0]:
            best[key] = (c, t)

    spots = []
    for c, t in sorted(best.values(), key=lambda x: -x[0]):
        spots.append({
            "trip": t["name"],
            "query": t["name"].split("(")[0].split("—")[0].strip(),
            "months": t["months"],
            "strike_composite": round(c, 1),
            "min_lead_days": min_lead_days(t),
            "min_rating": "GOOD",   # strike bar: worth a flight, not a drive
            "min_height_ft": 4,     # default size floor; override per spot in SurfBot
            "cluster": t.get("cluster", ""),
            "notes": t["booking"],
        })

    out = ROOT / "data" / "strike_radar.json"
    out.write_text(json.dumps(
        {"_doc": "Strike-radar portfolio for SurfBot. Regenerate with gen_radar.py; "
                 "do not hand-edit. Spot-id resolution and per-spot threshold overrides "
                 "live on the SurfBot side.",
         "gate": {d: mn for d, mn in gates},
         "spots": spots}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {out}: {len(spots)} radar spots (from {len(eligible)} eligible rows)")
    for s in spots:
        m = s["months"]
        print(f"  {s['strike_composite']:>5}  lead≥{s['min_lead_days']}d  "
              f"months {min(m)}–{max(m)}  {s['trip']}")


if __name__ == "__main__":
    main()
