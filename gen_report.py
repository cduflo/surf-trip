#!/usr/bin/env python3
"""Generate the HTML report (report.html) from data/trips.json. Run score.py logic inline."""
import html
import json
from pathlib import Path

from score import BEGINNER_FLOOR, composite, family_ok, sensitivity_bands, tier

ROOT = Path(__file__).parent
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DIM_LABELS = {
    "consistency": ("Consistency", "Odds any given day delivers good surf in-window"),
    "crowd": ("Crowds", "Waves per person; access gating counts"),
    "quality": ("Wave quality", "Ceiling of the best wave in range"),
    "beginner": ("Beginner", "Safe, mellow, forgiving learner terrain"),
    "advanced": ("Advanced", "Genuinely exciting waves for the experts"),
    "safety": ("Family safety", "Security, medical access, kid-comfort"),
    "turnkey": ("Turnkey", "Boards, coaching & the daily call all handled — zero planning, zero Surfline"),
    "lodging": ("Lodging", "Family digs at the surf; pool-over-break bonus"),
    "travel": ("Travel ease", "Door-to-door from Boston/Providence"),
}

CSS = """
:root{
  --bg:#F6F9F8; --surface:#FFFFFF; --ink:#16262B; --ink-2:#48605F; --ink-3:#7A8A86;
  --line:#DCE5E2; --accent:#0E7C86; --accent-deep:#0A5560; --accent-soft:#CDE4E4;
  --bar-track:#E4ECEA; --sand:#8A8272; --flag:#8C4A2F; --flag-bg:#F4E9E1;
  --tier-s-bg:#0A5560; --tier-s-ink:#F2FAF9; --tier-a-bg:#0E7C86; --tier-a-ink:#F2FAF9;
  --tier-b-bg:#BFDCDD; --tier-b-ink:#123E43; --tier-c-bg:#E3E9E7; --tier-c-ink:#48605F;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0D181B; --surface:#122024; --ink:#E2EDEB; --ink-2:#9FB4B0; --ink-3:#6C807C;
    --line:#24363A; --accent:#49BEC9; --accent-deep:#7DD3DB; --accent-soft:#1B3A3F;
    --bar-track:#1C2C30; --sand:#B0A78F; --flag:#E0A184; --flag-bg:#2A1E17;
    --tier-s-bg:#49BEC9; --tier-s-ink:#062225; --tier-a-bg:#20707A; --tier-a-ink:#E7F6F5;
    --tier-b-bg:#1E3B40; --tier-b-ink:#A9D6D8; --tier-c-bg:#1C2A2D; --tier-c-ink:#9FB4B0;
  }
}
:root[data-theme="dark"]{
  --bg:#0D181B; --surface:#122024; --ink:#E2EDEB; --ink-2:#9FB4B0; --ink-3:#6C807C;
  --line:#24363A; --accent:#49BEC9; --accent-deep:#7DD3DB; --accent-soft:#1B3A3F;
  --bar-track:#1C2C30; --sand:#B0A78F; --flag:#E0A184; --flag-bg:#2A1E17;
  --tier-s-bg:#49BEC9; --tier-s-ink:#062225; --tier-a-bg:#20707A; --tier-a-ink:#E7F6F5;
  --tier-b-bg:#1E3B40; --tier-b-ink:#A9D6D8; --tier-c-bg:#1C2A2D; --tier-c-ink:#9FB4B0;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 "Avenir Next","Helvetica Neue",system-ui,sans-serif;}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px 96px}
.prose{max-width:66ch}
a{color:var(--accent-deep)}
h1,h2,h3{text-wrap:balance;line-height:1.15}
h2{font-size:1.6rem;margin:0 0 .35em;letter-spacing:-.01em}
h3{font-size:1.05rem;margin:0 0 .3em}
section{margin-top:72px}
.mono{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-variant-numeric:tabular-nums}
.eyebrow{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2);font-weight:600}

header.masthead{padding:72px 0 0}
.masthead h1{font-family:"Avenir Next Condensed","Avenir Next","Arial Narrow",sans-serif;
  font-weight:700;font-size:clamp(2.6rem,7vw,4.4rem);letter-spacing:.015em;
  text-transform:uppercase;margin:.2em 0 .15em}
.masthead h1 em{font-style:normal;color:var(--accent)}
.dek{font-size:1.12rem;color:var(--ink-2);max-width:62ch}
.statrow{display:flex;flex-wrap:wrap;gap:14px;margin-top:36px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:6px;
  padding:14px 20px;min-width:150px;flex:0 1 auto}
.stat .n{font-size:1.7rem;font-weight:700;line-height:1.2}
.stat .l{font-size:.75rem;color:var(--ink-2);letter-spacing:.06em;text-transform:uppercase}

.wtable{display:grid;grid-template-columns:auto 1fr;gap:0 18px;margin-top:20px}
.wrow{display:contents}
.wname{padding:7px 0;border-bottom:1px solid var(--line);font-weight:600;font-size:.92rem;white-space:nowrap}
.wcell{padding:7px 0;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px}
.wbar{height:10px;border-radius:0 3px 3px 0;background:var(--accent);flex:0 0 auto}
.wnum{font-weight:700;min-width:2ch}
.wdesc{color:var(--ink-2);font-size:.88rem}
.callout{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:4px;padding:16px 20px;margin-top:24px;font-size:.94rem;color:var(--ink-2)}
.callout strong{color:var(--ink)}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:18px;margin-top:28px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:20px 22px;
  display:flex;flex-direction:column;gap:10px}
.card .top{display:flex;align-items:baseline;gap:12px}
.card .rk{font-family:"Avenir Next Condensed","Arial Narrow",sans-serif;font-weight:700;
  font-size:2rem;color:var(--accent);min-width:1.6ch;line-height:1}
.card h3{flex:1}
.card .score{font-size:1.5rem;font-weight:700}
.card .meta{font-size:.8rem;color:var(--ink-2);display:flex;gap:10px;flex-wrap:wrap}
.dims{display:grid;grid-template-columns:auto 1fr auto;gap:3px 10px;font-size:.78rem}
.dims .dl{color:var(--ink-2);white-space:nowrap}
.dims .db{align-self:center;height:6px;background:var(--bar-track);border-radius:3px;overflow:hidden}
.dims .db i{display:block;height:100%;background:var(--accent);border-radius:0 3px 3px 0}
.dims .dv{text-align:right;min-width:3ch}
.card .note{font-size:.88rem;color:var(--ink-2);border-top:1px solid var(--line);padding-top:10px}

.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface);margin-top:24px}
table{border-collapse:collapse;width:100%;font-size:.85rem;min-width:1040px}
th{position:sticky;top:0;background:var(--surface);text-align:left;font-size:.68rem;
  letter-spacing:.09em;text-transform:uppercase;color:var(--ink-2);
  padding:10px 10px;border-bottom:2px solid var(--line);white-space:nowrap}
th.num,td.num{text-align:right}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:hover{background:var(--accent-soft)}
tbody tr:last-child td{border-bottom:none}
td.trip{font-weight:600;min-width:220px}
td.trip .sub{font-weight:400;font-size:.78rem;color:var(--ink-2)}
.chip{display:inline-block;font-size:.7rem;font-weight:700;padding:1px 8px;border-radius:99px;letter-spacing:.05em}
.gate-ok{color:var(--accent-deep);font-weight:700}
.gate-no{color:var(--flag);font-weight:700}
td.book{font-size:.78rem;color:var(--ink-2);min-width:150px}
.chip.S{background:var(--tier-s-bg);color:var(--tier-s-ink)}
.chip.A{background:var(--tier-a-bg);color:var(--tier-a-ink)}
.chip.B{background:var(--tier-b-bg);color:var(--tier-b-ink)}
.chip.C{background:var(--tier-c-bg);color:var(--tier-c-ink)}
.cbar{display:inline-block;vertical-align:middle;width:64px;height:7px;background:var(--bar-track);
  border-radius:3px;overflow:hidden;margin-left:8px}
.cbar i{display:block;height:100%;background:var(--accent);border-radius:0 3px 3px 0}
td .band{color:var(--ink-3);font-size:.78rem}

.seasons{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;margin-top:24px}
.season{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:20px 22px}
.season .months{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-deep);font-weight:700}
.season ol{margin:.6em 0 0;padding-left:1.3em;font-size:.9rem}
.season li{margin:.25em 0}
.season li .s{color:var(--ink-2);font-size:.8rem}
.monthstrip{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:20px}
.mcell{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:10px 12px;font-size:.8rem}
.mcell .m{font-weight:700;font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-deep)}
.mcell .p{margin-top:2px}

.flagbox{background:var(--flag-bg);border:1px solid var(--line);border-left:3px solid var(--flag);
  border-radius:4px;padding:16px 20px;margin-top:18px;font-size:.94rem}
.flagbox strong{color:var(--flag)}
ul.tight{margin:.4em 0;padding-left:1.2em}
ul.tight li{margin:.3em 0}
.arche{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-top:24px}
.arche .card p{font-size:.9rem;color:var(--ink-2);margin:.2em 0}
footer{margin-top:80px;padding-top:20px;border-top:1px solid var(--line);
  font-size:.8rem;color:var(--ink-3)}
"""


def bar(v, w=1.0):
    return f'<span class="cbar" style="width:{int(64*w)}px"><i style="width:{v*10:.0f}%"></i></span>'


def dim_rows(scores):
    out = []
    for d, (label, _) in DIM_LABELS.items():
        v = scores[d]
        out.append(f'<span class="dl">{label}</span>'
                   f'<span class="db"><i style="width:{v*10:.0f}%"></i></span>'
                   f'<span class="dv mono">{v:g}</span>')
    return "".join(out)


def main():
    data = json.loads((ROOT / "data" / "trips.json").read_text())
    weights, trips = data["weights"], data["trips"]
    for t in trips:
        t["composite"] = round(composite(t["scores"], weights), 1)
    trips.sort(key=lambda t: -t["composite"])
    bands = sensitivity_bands(trips, weights)
    n = len(trips)
    tiers = {k: sum(1 for t in trips if tier(t["composite"]) == k) for k in "SABC"}
    ranks = {t["name"]: i + 1 for i, t in enumerate(trips)}
    top10_dev = max(max(ranks[t["name"]] - bands[t["name"]][0],
                        bands[t["name"]][1] - ranks[t["name"]]) for t in trips[:10])
    mid_dev = max(max(ranks[t["name"]] - bands[t["name"]][0],
                      bands[t["name"]][1] - ranks[t["name"]]) for t in trips[24:55])
    wk_rank = ranks["Waikiki + North Shore (Oahu)"]

    e = html.escape

    # --- weights section ---
    wrows = []
    for d, w in sorted(weights.items(), key=lambda kv: -kv[1]):
        label, desc = DIM_LABELS[d]
        wrows.append(
            f'<div class="wrow"><div class="wname">{label}</div>'
            f'<div class="wcell"><span class="wbar" style="width:{w*10}px"></span>'
            f'<span class="wnum mono">{w}</span><span class="wdesc">{desc}</span></div></div>')

    # --- top 10 cards: mixed-ability division (beginner floor applied) ---
    cards = []
    for i, t in enumerate([t for t in trips if family_ok(t)][:10], 1):
        cards.append(f"""<article class="card">
<div class="top"><span class="rk mono">{i}</span><h3>{e(t["name"])}</h3><span class="score mono">{t["composite"]}</span></div>
<div class="meta"><span>{e(t["country"])}</span><span>·</span><span>{e(t["window"])}</span><span>·</span><span>{e(t["cost_band"])}</span><span>·</span><span>min {t["min_days"]}d</span><span>·</span><span>{e(t["travel_note"])}</span></div>
<div class="dims">{dim_rows(t["scores"])}</div>
<p class="note">{e(t["note"])} <em>Booking: {e(t["booking"])}.</em></p>
</article>""")

    # --- full table ---
    dims = data["dimensions"]
    thead = ("<tr><th>#</th><th>Trip</th><th>Window</th><th>Tier</th>"
             f'<th title="Mixed-ability gate: beginner score ≥ {BEGINNER_FLOOR}">Fam</th>'
             '<th title="All-in $/person/week incl. BOS flights: $ &lt;2.5k · $$ 2.5–4k · $$$ 4–6.5k · $$$$ &gt;6.5k">Cost</th>'
             '<th class=num title="Minimum viable trip length after two-way transit and jet lag">Min d</th>'
             "<th>Booking</th><th class=num>Score</th><th class=num>Band</th>"
             + "".join(f'<th class=num title="{e(DIM_LABELS[d][1])}">{DIM_LABELS[d][0]}</th>' for d in dims)
             + "</tr>")
    rows = []
    for i, t in enumerate(trips, 1):
        lo, hi = bands[t["name"]]
        tr = tier(t["composite"])
        fam = ('<span class="gate-ok" title="Mixed-ability verified">✓</span>' if family_ok(t)
               else '<span class="gate-no" title="Experts-first: true beginner under-served">✗</span>')
        cells = "".join(f'<td class="num mono">{t["scores"][d]:g}</td>' for d in dims)
        rows.append(
            f'<tr><td class="mono">{i}</td>'
            f'<td class="trip">{e(t["name"])}<div class="sub">{e(t["country"])} — {e(t["travel_note"])}</div></td>'
            f'<td>{e(t["window"])}</td><td><span class="chip {tr}">{tr}</span></td>'
            f'<td>{fam}</td><td class="mono">{e(t["cost_band"])}</td>'
            f'<td class="num mono">{t["min_days"]}</td><td class="book">{e(t["booking"])}</td>'
            f'<td class="num mono">{t["composite"]}{bar(t["composite"]/10)}</td>'
            f'<td class="num mono band">{lo}–{hi}</td>{cells}</tr>')

    # --- month strip: #1 pick per month ---
    mcells = []
    for m in range(1, 13):
        best = next(t for t in trips if m in t["months"])
        mcells.append(f'<div class="mcell"><div class="m">{MONTHS[m-1]}</div>'
                      f'<div class="p">{e(best["name"])}</div>'
                      f'<div class="mono" style="color:var(--ink-2)">{best["composite"]}</div></div>')

    # --- season blocks ---
    def season_list(months_set, k=6, within=False):
        cond = (lambda t: set(t["months"]) <= months_set) if within else (lambda t: set(t["months"]) & months_set)
        picks = [t for t in trips if cond(t)][:k]
        return "".join(f'<li>{e(t["name"])} <span class="s mono">{t["composite"]} · {e(t["window"])}</span></li>'
                       for t in picks)

    html_doc = f"""<title>The Family Wave Index</title>
<style>{CSS}</style>
<div class="wrap">

<header class="masthead">
  <div class="eyebrow">Family surf trips from New England · scored &amp; ranked · Aug 2026</div>
  <h1>The Family <em>Wave</em> Index</h1>
  <p class="dek">{n} destination-plus-season trips scored on nine weighted dimensions, built around one brief:
  everyone in the family — first-timer to charger — gets tons of uncrowded, high-quality waves,
  with near-guaranteed swell, zero-thought logistics — boards waiting, guides booked, no forecast-checking —
  and somewhere great to stay.</p>
  <div class="statrow">
    <div class="stat"><div class="n mono">{n}</div><div class="l">Trips scored</div></div>
    <div class="stat"><div class="n mono">9</div><div class="l">Weighted dimensions</div></div>
    <div class="stat"><div class="n mono">{tiers["S"]}</div><div class="l">S-tier (80+)</div></div>
    <div class="stat"><div class="n">{e(trips[0]["name"].split("(")[0].strip())}</div><div class="l">No. 1 · {trips[0]["composite"]}</div></div>
  </div>
</header>

<section>
  <h2>How the score works</h2>
  <p class="prose">Each trip is a <strong>destination + season window</strong> — the same place can appear
  twice because consistency, crowds and conditions swing hard by month. Nine dimensions, each scored 0–10
  against written anchors, weighted to match the brief: swell certainty first, then the <strong>turnkey
  factor</strong> — the zero-thought test: boards waiting, coaching on tap, someone else making the daily
  call, never opening a forecast — then empty high-quality lineups, then family constraints ahead of
  convenience. Composite is the weighted sum on a 0–100 scale.</p>
  <div class="wtable">{"".join(wrows)}</div>
  <div class="callout"><strong>Provenance, honestly.</strong> Scores are structured expert priors from swell
  climatology and the surf-travel record as of early 2026 — an ordinal ranking tool, not measurements.
  A 3-point gap is meaningful; a 1-point gap is noise. Crowd scores decay fastest in real life; safety scores
  reflect early-2026 conditions — re-check advisories before booking. Full anchors and rationale live in
  <span class="mono">METHODOLOGY.md</span>; rerun <span class="mono">score.py</span> to regenerate everything here.
  <strong>v2 change:</strong> "guided logistics" (8 pts) became the freshly-scored turnkey factor (15 pts) —
  v1 gave no credit for boards-on-site or forecast-free surfing, letting DIY forecast-chasing trips outrank
  their real cognitive load. v1 rankings preserved in <span class="mono">rankings_v1.csv</span>.
  <strong>v3 change (seven-persona panel review):</strong> nine trips rescored on multi-seat evidence, a
  <strong>beginner floor (≥ {BEGINNER_FLOOR})</strong> now gates the headline top ten (weights unchanged —
  the panel's own vectors agreed on the top of the table, ρ = 0.88–0.99), and three unweighted decision
  columns were added: cost band, minimum viable days, and booking constraints.</div>
</section>

<section>
  <h2>The top ten — mixed-ability division</h2>
  <p class="prose">These ten pass the <strong>beginner floor</strong> (beginner ≥ {BEGINNER_FLOOR}): the whole
  family gets real waves, not just the strongest surfer. The pattern is unmistakable:
  <strong>access-controlled, guide-driven operations win</strong> — boat-resort models and gated point-break
  setups buy the two things money usually can't: empty lineups and daily wave certainty. Experts-first trips
  (marked ✗ below) still appear in the full table with their scores intact.</p>
  <div class="cards">{"".join(cards)}</div>
</section>

<section>
  <h2>All {n} trips</h2>
  <p class="prose">Band = where the trip's rank lands when any one weight is perturbed ±25% —
  a tight band means the rank is robust, a wide one means it's sensitive to how much you care about each dimension.</p>
  <div class="tablewrap"><table>
    <thead>{thead}</thead>
    <tbody>{"".join(rows)}</tbody>
  </table></div>
</section>

<section>
  <h2>When to go where</h2>
  <p class="prose">The year splits cleanly in two. <strong>April–October</strong> belongs to the Southern
  Hemisphere swell machine — Pacific Central America, Fiji, the Maldives, Indonesia. <strong>November–March</strong>
  belongs to North Atlantic and North Pacific winter — the Caribbean, Canaries, Morocco, Hawaii — with the
  Portugal/France shoulder peaking September–October.</p>
  <div class="seasons">
    <div class="season"><div class="months">Apr – Oct · southern season</div>
      <h3>The guarantee window</h3><ol>{season_list({5,6,7,8})}</ol></div>
    <div class="season"><div class="months">Nov – Mar · northern winter</div>
      <h3>School-break season</h3><ol>{season_list({12,1,2})}</ol></div>
    <div class="season"><div class="months">Sep – Oct · shoulder</div>
      <h3>The sweet overlap</h3><ol>{season_list({9,10,11}, within=True)}</ol></div>
  </div>
  <h3 style="margin-top:28px">Best-scoring trip in window, by month</h3>
  <div class="monthstrip">{"".join(mcells)}</div>
</section>

<section>
  <h2>Integrity checks</h2>
  <p class="prose">A scoring model that just likes famous places is broken, so famous-but-flawed spots serve
  as null tests — and the weights get stress-tested rather than trusted.</p>
  <ul class="tight prose">
    <li><strong>Uluwatu ranks {ranks["Uluwatu + Bingin (Bukit)"]}/{n}</strong> and
    <strong>Noosa {ranks["Noosa"]}/{n}</strong> despite world fame — crowds and (for Noosa) swell roulette
    cost them exactly as designed. Pass.</li>
    <li><strong>Sensitivity:</strong> the top 10 hold rank within ±{top10_dev} places under every single-weight
    ±25% perturbation. Mid-table (ranks 25–55) swings up to ±{mid_dev} — treat those as a tier, not an ordering.</li>
  </ul>
  <div class="flagbox"><strong>Adjudicated — Waikiki, now rank {wk_rank}.</strong> Earlier passes ranked it
  top-10 on a turnkey score of 9 — a beginner-only number smuggled in as a trip score. Waikiki is genuinely
  toothbrush-turnkey for a first-timer (boards on the sand, beach-boy pushes, an always-on wave), but wave
  acquisition in that crowd is a competition, and the bundled North Shore expert side is fully DIY
  forecast-chasing in the world's most contested lineups. Turnkey rescored to 6.5, and the panel's advanced
  seat cut the phantom-access advanced score to 6; the null check now passes on its own.</div>
  <h3 style="margin-top:28px">Seven-persona panel review (v3)</h3>
  <p class="prose">Seven personas — surf instructor, beginner, advanced surfer, family-travel expert, industry
  operator, trip CFO, and a status-quo defender — independently reviewed the weights and scores, and every
  persona's own weight vector was run against the dataset. Findings:</p>
  <ul class="tight prose">
    <li><strong>The weights survived.</strong> All seven vectors produced rank correlations of 0.88–0.99 with
    the current ranking, and six trips made the top ten under every vector (Fiji ×2, Maldives ×2, Telos,
    Las Flores). The panel's proposed reweight was rejected as redundant.</li>
    <li><strong>The structure didn't.</strong> Five of seven seats independently flagged that an additive model
    lets consistency and crowd scores buy off a failing beginner score — so "waves for everyone" now enforces a
    beginner floor instead of a weight.</li>
    <li><strong>Nine trips were rescored</strong> on converging multi-seat evidence — the largest: Mentawai
    (beginner 4.5→3, safety 7.5→5.5 for pediatric malaria prophylaxis and half-day medevac), Samoa
    (beginner 5→3.5), North Malé (beginner 6→4), Hacienda Iguana (turnkey 7.5→5 — an HOA you self-assemble,
    not a resort), and Rote upgraded for true same-session simultaneity.</li>
    <li><strong>Cost stays out of the composite</strong> (three seats converged): budget is a filter, not a
    preference — so it's a column. Note the pattern it exposes: the open-division S-tier is, with Las Flores
    as the lone exception, also the $$$$-tier.</li>
  </ul>
</section>

<section>
  <h2>Three ways to book it</h2>
  <div class="arche">
    <article class="card"><h3>The full-service boat resort</h3>
      <p><strong>Namotu/Tavarua, Telos, Maldives, Las Flores.</strong> One booking buys guides, boats, kids'
      programs and the pool over the break. Highest floor, highest cost, longest flights. Book 9–12 months out —
      family weeks sell out first.</p></article>
    <article class="card"><h3>The gated point-break villa</h3>
      <p><strong>Hacienda Iguana, Popoyo, El Zonte.</strong> Rent a house with a pool inside a surf community,
      hire a local guide with a panga or truck. Near-resort wave access at a third of the price, 6–7h door to door.</p></article>
    <article class="card"><h3>The easy strike</h3>
      <p><strong>Rincón, Barbados, Azores, Canaries.</strong> Nonstop flights, book two weeks out when the
      seasonal forecast firms up. Lower guarantee, minimal commitment — the repeatable school-vacation play.</p></article>
  </div>
</section>

<footer>The Family Wave Index · methodology, dataset and scoring script in the surf-trip repo
(<span class="mono">METHODOLOGY.md · data/trips.json · score.py</span>) · scores are early-2026 expert priors;
verify advisories, seasons and operators before booking.</footer>

</div>
"""
    out = ROOT / "report.html"
    out.write_text(html_doc)
    print(f"Wrote {out} ({len(html_doc):,} bytes)")


if __name__ == "__main__":
    main()
