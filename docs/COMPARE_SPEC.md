# Spec: Compare-N Trips

**Status:** spec only (not built). **Scope:** client-side, static-page compatible, no runtime capabilities.

## Goal

Pick 2–4 trips anywhere in the tables and see them side by side — scores, all three division
composites, and the decision-stage data — without losing the current division/filter context.

## Selection

- New first column in every table row: a checkbox (`.cmp-pick`), keyed by trip **name** (the stable
  identity across all 6 pre-rendered variants — checking a trip in one division checks it everywhere).
- Cap: **4 trips** (readability on a 1080px content column). Attempting a 5th flashes the count chip.
- A **compare chip** appears in the filter bar once ≥1 is selected: `Compare (n)` button + per-trip
  mini-chips with an `×` to deselect. Selection persists in `localStorage` (`fwi-compare`) and
  survives division switches, pool toggles, and filtering (a filtered-out row stays selected; its
  chip is the visible reminder).

## Compare view

Modal-style overlay (`position:fixed`, dismiss on `Esc`, click-outside, or `×`), containing one
column per trip and these row groups:

1. **Header** — name, country, window, cost band, min days, water temp + wetsuit, travel note,
   cluster label if any, pool badge if `pool`.
2. **Division scores** — all three composites + ranks + gate status (✓/✗ per division), with the
   *active* division's row emphasized. Showing all three is the point: "great family trip, mediocre
   strike" should be visible in one glance.
3. **Dimension bars** — all 10 dims as aligned label + bar + number rows (reuse `.dims` styles).
   Per-dimension winner gets the accent; ties get none.
4. **Booking + note** — booking constraint line and the trip note, full text.

Mobile: the overlay's inner container is `overflow-x:auto`; columns are `minmax(240px,1fr)`.

## Implementation notes

- **Data:** embed one JSON blob at build time —
  `<script type="application/json" id="tripdata">{name → {scores, composites{family,boys,strike},
  ranks, gates, cost_band, min_days, booking, water_f, wetsuit, travel_note, window, country,
  region, cluster, pool, resort_pool, note}}</script>` — ~100KB, generated in `gen_report.py`
  from the same computations that build the tables (no duplicate math in JS).
- **JS:** ~150 lines added to the existing controller IIFE: selection state, chip rendering,
  overlay build-on-demand (innerHTML from the blob), keyboard handling, `prefers-reduced-motion`
  respected (no transition if set).
- **CSS:** overlay + column grid + winner highlight; all colors via existing tokens (both themes
  free).
- Checkboxes get `aria-label="Compare {trip}"`; overlay is `role="dialog" aria-modal="true"` with
  focus trapped while open.

## Non-goals

- No URL-shareable compare state (would need query-param plumbing; possible later).
- No per-mode weight sliders inside the compare view.
- No forecast data in the compare view (see FORECAST_DESIGN.md — live data is out of scope for the
  static page).

**Estimated effort:** ~60 lines Python, ~150 lines JS, ~60 lines CSS. Page grows ~120KB (~1.03MB total).
