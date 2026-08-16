# surf-trip — The Family Wave Index

Scored ranking of 86 surf trips (destination + season window) from New England, rendered as
two divisions behind a dropdown — family (beginner-gated) and solo/boys (advanced-gated) —
optimizing for near-guaranteed, uncrowded, high-quality waves with beginner-safe options,
guided logistics, and family lodging.

- `METHODOLOGY.md` — dimensions, weights, anchors, caveats
- `data/trips.json` — the dataset (9 scores per trip + notes)
- `score.py` — composite scores, tiers, ±25% weight-sensitivity bands, month calendar → `RANKINGS.md`, `rankings.csv`
- `gen_report.py` — builds `report.html` (the published artifact) from the dataset

Regenerate everything after editing scores or weights:

```
python3 score.py && python3 gen_report.py
```
