# Maintenance & Refresh Policy

The dataset is a set of expert priors with known decay rates. This is the process that keeps it
honest. Adopted v11 (2026-08-17) after Puro Surf — a flagship property missed by the coastline
row — proved the v4 blind spot recurs on its own schedule.

## What decays, and how fast

| Field class | Decay | Refresh trigger |
|---|---|---|
| **Universe membership** (new resorts/camps/pools, closures) | New property-level entrants appear ~yearly per region; this is the proven blind spot (Rancho Santana, Mizata, Nihi, Puro Surf were all missed by coastline rows) | Semi-annual re-audit |
| **Crowd scores** | Fastest-decaying number in the file (a spot can blow up in 2 years) | Annual pass |
| **Safety scores** | Advisory-driven; can step-change (El Salvador did) | Quarterly advisory check on rows with safety ≤ 7 |
| **Booking / cost_band / min-lead** | Operator churn, price drift, schedule changes | Annual pass; verify before any actual booking regardless |
| Wave quality / consistency / beginner terrain | Geology and climatology — effectively static (exception: uplift/sand events, e.g. Nias 2005) | Event-driven only |

## The cadence

1. **Semi-annual (Feb + Aug): coverage re-audit.** Re-run the v4 adversarial pattern — 3 regional
   gap-hunters + 1 construction skeptic, prompts recorded in METHODOLOGY v4 — with an explicit
   brief to hunt **property-level entrants** (new resorts/academies/pools) and closures, not just
   coastlines. Score survivors, add rows, record confirmed-correct exclusions in the changelog so
   they aren't relitigated.
2. **Annual (Aug): decay pass.** Re-verify crowd, cost_band, booking, and safety for the top ~40
   rows of each division (web-verified, like the v4 Africa audit). Changes go through the normal
   pipeline with per-row provenance notes.
3. **Quarterly: advisory check.** State Dept / FCDO advisories against every row with safety ≤ 7.
   Score changes only on advisory-level changes; log "checked, no change" in the changelog.
4. **Event-driven intake.** Candidate spots noticed between audits get a line in the Candidates
   list below — they are scored at the next semi-annual audit, not ad hoc, unless the user asks.

Every refresh: edit `data/trips.json` → `python3 score.py && python3 gen_report.py &&
python3 gen_radar.py` → verify null checks still pass → commit with a dated METHODOLOGY
changelog entry → republish the artifact → copy `strike_radar.json` to SurfBot if the strike
roster changed.

## Candidates (intake list — score at next audit)

- 2026-08-17: Atlantic Park / Wavegarden Cove (Virginia Beach, VA) — 46-module wave pool + on-site hotel, opened Aug 2025, strongest strike-division fit found this cycle (domestic, no passport) [https://wavegarden.com/north-americas-first-wavegarden-cove-opens-at-atlantic-park-in-virginia-beach/]
- 2026-08-17: Cabo Real Surf Club (Los Cabos, Mexico) — gated residential community anchored by North America's first Endless Surf basin, opening 2026 [https://www.surfer.com/news/inside-cabo-real-surf-club-mexicos-first-luxury-wave-pool-community]
- 2026-08-17: DSRT Surf (Palm Desert, CA) — 52-module Wavegarden Cove + 139-room hotel, opening summer 2026, same archetype as Palm Springs Surf Club [https://wavegarden.com/6-new-wavegarden-world-class-surf-destinations-on-the-horizon/]
- 2026-08-17: Surfers Cove (Óbidos, Portugal) — Portugal's first Wavegarden Cove, between Ericeira and Nazaré, bookings opened July 2026 [https://www.idealista.pt/en/news/lifestyle-in-portugal/2026/07/17/76622-portugal-s-first-wave-pool-now-open-for-bookings]
- 2026-08-17: NIHI Rote (Rote Island, Indonesia) — sister property to NIHI Sumba, opens May 2026, same blind-spot pattern that produced the v11 Puro Surf/NIHI Sumba adds [https://www.surfer.com/culture/nihi-rote-indonesia-surf-resort-opening]
- 2026-08-17: The Point Surf Park (Fellsmere, FL) — Endless Surf pool with concurrent beginner/advanced basin, targeting 2026 [https://endlesssurf.com/2025/05/14/the-point-surf-park-breaks-ground-in-florida-powered-by-the-usas-first-endless-surf-lagoon/]
- 2026-08-17: Hotel Fermata (Santa Teresa, Costa Rica) — 35-room beachfront hotel on La Lora break, opened Dec 2025, lower-confidence source, verify before scoring [hospitality trade coverage — verify directly]
- 2026-08-17: Lamangata Luxury Surf Resort (Dominical, Costa Rica) — all-inclusive boutique resort on an already-scored coastline [https://www.surfer.com/culture/lamangata-luxury-surf-resort-costa-rica]

## Automation (enabled 2026-08-17 — findings only)

A monthly cloud routine ("Wave Index monthly discovery scan", 1st of each month 08:00 UTC) runs
the discovery half automatically: hunts new property-level entrants/wave pools, checks operator
closures for the top ~40 rows, and re-checks advisories for safety ≤ 7 rows — then reports and
appends candidates to the list above on a `maint/scan-YYYY-MM` branch (never main). The line that
stays human: **the routine never touches scores or trips.json** — candidates are scored at the
semi-annual audit after review. Manage the routine at claude.ai/code/routines.
