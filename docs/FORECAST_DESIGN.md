# Design note: Forecast layer — dovetail with SurfBot, don't rebuild it

**Status:** decision record + phased plan. **Decision: dovetail.** The Wave Index stays the
climatology/decision layer; SurfBot is the live-weather layer. Do not build a second forecast
stack in this repo.

## Why the page itself can't do forecasts

The published artifact runs under a strict CSP: no external fetches of any kind. Even without
that, Surfline's unofficial API requires HTTP/1.1 + browser-UA fingerprinting that a browser
sandbox can't spoof cross-origin. Any live layer therefore lives outside the page, and the
question is only *which* outside thing.

## Why SurfBot, not something new

SurfBot (~/surfbot, separate public repo) has already paid the costs this feature needs:

- Surfline API access with the known gotchas handled (HTTP/1.1 + browser UA for Cloudflare,
  never send accessToken, 10-day free horizon, hourly wave/rating joins).
- **Daylight-hours qualification** (a day counts only if height AND rating pass in the same
  daylight hour) — exactly the "did it actually break during surfable hours" rigor a strike
  alert needs, already debugged against a real false-alert incident.
- Spot resolution by name via Surfline search→taxonomy, two-way Telegram (`/watch <place>
  <dates>`), destination-local-time digests, watch caps, auto-expiry, fail-soft polling.
- 283 tests and a year of hardening. Rebuilding a "lighter" version of this would be lighter
  only until the first Cloudflare 403.

## Division of labor

| Layer | Answers | Horizon | Lives in |
|---|---|---|---|
| Wave Index (this repo) | *Where/when to book; which trip class* | Seasonal climatology | Static artifact |
| SurfBot | *Is it actually on; go/no-go* | Surfline 10-day free window | ~/surfbot, Telegram |

No overlap conflict: the index's consistency/strikeability scores are priors over seasons; SurfBot
is evidence over the next 10 days. The strike division's ~5-day forecast windows fit entirely
inside SurfBot's 10-day horizon — the free tier is sufficient.

## Phased plan

- **Phase 0 — SHIPPED (v10):** every non-pool trip renders a `forecast ↗` link in the table and compare
  view. Design-review amendment: links are **Surfline search URLs** (query = the trip's primary spot name),
  not hand-guessed deep links — a search cannot point at the wrong spot, and fabricated slugs rot. Curated
  spot-IDs arrive with Phase 2's SurfBot mapping. Pools never link.
- **Phase 1 (SurfBot-side):** a `/strike <place> [minft] [rating]` command — a **standing,
  threshold-driven watch** (unlike `/watch`, which is date-bounded and thresholdless): alert only
  when a qualifying daylight window appears inside the 10-day horizon, with improving/holding
  updates until go/expire. This is SurfBot's home-mode criteria logic pointed at remote spots —
  reuse, not new machinery. Lives in the surfbot repo with its own tests.
- **Phase 2 (optional bridge):** a tiny mapping file in this repo (trip name → Surfline spot id)
  so strike-division rows can be watched by exact spot rather than name search. Note some strike
  targets (Skeleton Bay) may lack useful Surfline coverage — the mapping records that honestly.

## Cautions

- Both repos are public. The mapping file carries only public spot ids — never tokens, chat ids,
  or machine paths (SurfBot public-repo hardening rules apply).
- SurfBot's watch cap (5) is a real constraint for a strike portfolio; Phase 1 should decide
  whether strike watches share that cap or get their own (suggest: own cap, 8).
- Surfline free-tier horizons are asymmetric (wave 10d / rating 11d / sunlight 17d) — strike
  alerts must key off the shortest wall, as SurfBot already does.
