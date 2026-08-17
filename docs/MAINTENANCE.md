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

*(empty — add candidates here with a one-line reason and date)*

## Automation option (not enabled)

The semi-annual re-audit is a repeatable multi-agent job and could run as a scheduled cloud
routine that opens its findings as a report for approval before any dataset change. Deliberately
not enabled: audits change scores, and score changes should stay human-approved. Revisit if the
manual cadence slips.
