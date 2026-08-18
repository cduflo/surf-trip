#!/usr/bin/env python3
"""Generate the HTML report (report.html) from data/trips.json.

Renders two blocks (pools off/on) per division — family / boys / strike, from
data['modes'] — toggled by a masthead dropdown + pools checkbox, with client-side
table filters and a pick-up-to-4 compare dialog fed by an embedded JSON blob.
Weights and gates live in the JSON; prose lives in MODE_COPY below.
"""
import html
import json
from pathlib import Path
from urllib.parse import quote

from score import composite, sensitivity_bands, tier

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
    "strikeability": ("Strike", "Forecast visibility × T-72h bookability × launch latency"),
}

CMP_CAP = 4  # max trips in the compare dialog — keep in sync with the thead tooltip and JS CMP_CAP


def gate_check(key, mode, t):
    """(ok, why) for a division's gate, ignoring the pools toggle.

    Toggle handling stays in render_mode; the compare dialog handles it in JS
    by showing "— (pools off)" for pool rows when the active view has pools off.
    """
    for d, mn in mode["gates"]:
        if t["scores"][d] < mn:
            return False, f'{DIM_LABELS[d][0].lower()} {t["scores"][d]:g} < {mn:g}'
    if t.get("pool") and key == "family" and not t.get("resort_pool"):
        return False, "pool without on-site resort"
    return True, ""


def short_name(name):
    """Primary spot name: strip parenthetical and em-dash qualifiers."""
    return name.split("(")[0].split("—")[0].strip()


def forecast_url(t):
    """Surfline search link (never a guessed deep link); empty for pools."""
    if t.get("pool"):
        return ""
    return "https://www.surfline.com/search/" + quote(short_name(t["name"]), safe="")


MODE_COPY = {
    "family": {
        "division": "mixed-ability division",
        "gate_col": "Fam",
        "gate_ok_title": "Mixed-ability verified",
        "gate_no_title": "Experts-first: true beginner under-served",
        "cards_h2": "The top ten — mixed-ability division",
        "cards_intro": """These ten pass the <strong>beginner floor</strong> ({gate_desc}): the whole
  family gets real waves, not just the strongest surfer. The pattern is unmistakable:
  <strong>access-controlled, guide-driven operations win</strong> — boat-resort models and gated point-break
  setups buy the two things money usually can't: empty lineups and daily wave certainty. Experts-first trips
  (marked ✗ below) still appear in the full table with their scores intact.""",
        "caveat": "",
        "playbook": """
    <article class="card"><h3>The full-service boat resort</h3>
      <p><strong>Namotu/Tavarua, Telos, Maldives, Las Flores.</strong> One booking buys guides, boats, kids'
      programs and the pool over the break. Highest floor, highest cost, longest flights. Book 9–12 months out —
      family weeks sell out first.</p></article>
    <article class="card"><h3>The gated point-break villa</h3>
      <p><strong>Rancho Santana, Popoyo, El Zonte, Mizata.</strong> A house or small resort inside a surf
      community, a local guide with a panga or truck. Near-resort wave access at a third of the price,
      6–7h door to door.</p></article>
    <article class="card"><h3>The easy strike</h3>
      <p><strong>Rincón, Barbados, Azores, Canaries.</strong> Nonstop flights, book two weeks out when the
      seasonal forecast firms up. Lower guarantee, minimal commitment — the repeatable school-vacation play.</p></article>""",
    },
    "boys": {
        "division": "charger division",
        "gate_col": "Crew",
        "gate_ok_title": "Charger-verified: real waves for an advanced crew",
        "gate_no_title": "Below the advanced floor: the crew outgrows it",
        "cards_h2": "The top ten — charger division",
        "cards_intro": """Same trips, same scores — reweighted for a crew of advanced surfers with no
  beginners to protect: wave count and wave ceiling first, lodging demoted to "a bed near the break," and an
  <strong>advanced floor</strong> ({gate_desc}) replacing the beginner gate. The experts-first trips the
  family division flags ✗ — Salina Cruz, Mentawai, Nihi, P-Pass — are exactly what surfaces here.""",
        "caveat": """<div class="flagbox"><strong>Boys-mode caveats (from the panel's defender).</strong>
  The family-lens gaps the defender flagged were closed in v6 — the universe now includes the boys-first rows
  (Mentawai boat charter, a North Shore Oahu base, G-Land, Zicatela-proper, Nias, Krui). Two reading notes
  remain: <strong>Nihi Sumba's</strong> rank is partly a luxury artifact (you'd be paying $$$$ for an infinity
  pool this mode says you don't need), and <strong>Taghazout's</strong> turnkey 9 encodes a learner-camp
  industry an advanced crew uses less of. Cost and min-days filter harder than the weights here: the top of
  this division skews $$$$ and 10+ days — Salina Cruz ($$) and Chicama ($) are the value line.</div>""",
        "playbook": """
    <article class="card"><h3>The boat-and-boards program</h3>
      <p><strong>Mentawai, Telos, Banyaks, Namotu.</strong> A charter or island camp where the program IS the
      trip: dawn call, boat to whichever reef is firing, repeat. Maximum waves per day money can buy; book
      6–12 months out.</p></article>
    <article class="card"><h3>The guided strike camp</h3>
      <p><strong>Salina Cruz, Las Flores, Kavieng.</strong> A guide with a truck or panga and gated access to
      sand-bottom points. Near-private lineups without charter prices.</p></article>
    <article class="card"><h3>The mileage basecamp</h3>
      <p><strong>Chicama, Popoyo, Cabo Ledo, Puerto Escondido.</strong> Cheap, consistent, uncrowded — park the
      crew for 10 days, surf three sessions a day, spend the savings on the next trip.</p></article>""",
    },
    "strike": {
        "division": "strike division",
        "gate_col": "Go",
        "gate_ok_title": "Strike-viable: forecastable, bookable at T-72h, fast to reach",
        "gate_no_title": "Not strike-viable: book-ahead trip or slow launch",
        "cards_h2": "The top ten — strike division",
        "cards_intro": """The inversion of everything above: you don't book dates and hope — you watch the
  chart and fly when it's already confirmed. Consistency collapses to near-zero weight; what matters is
  <strong>strikeability</strong> — forecast visibility, T-minus-72-hour bookability, launch latency — plus
  wave ceiling and crowd. Gate: {gate_desc}. The trips the book-ahead divisions punish hardest
  (Rincón, Scorpion Bay, the Outer Banks, Skeleton Bay) are exactly what wins here.""",
        "caveat": """<div class="flagbox"><strong>Strike-mode caveats.</strong> This division assumes a crew
  that can drop everything on five days' notice — its scores price the trip, not your calendar. Hit rates are
  priors, not guarantees: a strike that whiffs still costs the flights (cheap for Rincón, painful for
  Skeleton Bay). And strikeability decays with fame — a forecastable spot everyone can see coming (Hossegor
  in September) arrives pre-crowded, which the crowd score already prices.</div>""",
        "playbook": """
    <article class="card"><h3>The drive-or-hop strike</h3>
      <p><strong>Rincón, Outer Banks, Nova Scotia, Cocoa Beach.</strong> Watch the tropics; leave within 48
      hours by car or a sub-5h nonstop. Cheap enough to whiff and try again next swell.</p></article>
    <article class="card"><h3>The five-day window</h3>
      <p><strong>Azores, Peniche/Ericeira, Soup Bowl autumn, Zicatela.</strong> Groundswell visible ~5 days
      out, one nonstop plus a short transfer, walk-in lodging. The highest hit-rate class.</p></article>
    <article class="card"><h3>The unicorn hunt</h3>
      <p><strong>Skeleton Bay, Scorpion Bay, Pavones.</strong> Waves that break a handful of days a year.
      Standing alerts, flexible tickets, and acceptance that some years the phone never rings.</p></article>""",
    },
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
.modebar{display:flex;align-items:center;gap:12px;margin-top:28px}
.modebar label{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2);font-weight:700}
.modebar select{font:inherit;font-weight:600;color:var(--ink);background:var(--surface);
  border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:6px;
  padding:8px 14px;cursor:pointer}
.modebar select:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.mode{display:none}
.mode.active{display:block}
.statrow{display:flex;flex-wrap:wrap;gap:14px;margin-top:36px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:6px;
  padding:14px 20px;min-width:150px;flex:0 1 auto}
.stat .n{font-size:1.7rem;font-weight:700;line-height:1.2}
.stat .l{font-size:.75rem;color:var(--ink-2);letter-spacing:.06em;text-transform:uppercase}

.wtable{display:grid;grid-template-columns:auto 1fr 1fr 1fr;gap:0 14px;margin-top:20px}
.wrow{display:contents}
.whead{font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-2);
  font-weight:700;padding:4px 0;border-bottom:2px solid var(--line)}
.wname{padding:7px 0;border-bottom:1px solid var(--line);font-weight:600;font-size:.92rem;white-space:nowrap}
.wcell{padding:7px 0;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px}
.wbar{height:10px;border-radius:0 3px 3px 0;background:var(--accent);flex:0 0 auto}
.wcell.alt .wbar{background:var(--sand)}
.wcell.alt2 .wbar{background:var(--accent-deep)}
.wnum{font-weight:700;min-width:2ch}
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
.chip.POOL{background:var(--flag-bg);color:var(--flag);border:1px dashed var(--flag)}
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
.filterslot .filters{margin-bottom:-6px}
.filters{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;margin-top:18px;
  background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 18px}
.filters label{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);
  font-weight:700;display:flex;flex-direction:column;gap:4px}
.filters select{font:inherit;font-size:.85rem;color:var(--ink);background:var(--bg);
  border:1px solid var(--line);border-radius:5px;padding:5px 8px;cursor:pointer}
.filters select:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.filters .fchk{flex-direction:row;align-items:center;gap:6px;cursor:pointer;align-self:flex-end;padding-bottom:6px}
.filters .fcount{margin-left:auto;font-size:.8rem;color:var(--ink-2);align-self:flex-end;padding-bottom:6px}
.filters button{font:inherit;font-size:.8rem;color:var(--accent-deep);background:none;border:none;
  cursor:pointer;text-decoration:underline;align-self:flex-end;padding-bottom:6px}
.filters button.cmpbtn{font-weight:700;text-decoration:none;background:var(--accent);color:#fff;
  border-radius:6px;padding:6px 12px;align-self:flex-end}
th.cmpc,td.cmpc{width:26px;text-align:center;padding-left:6px;padding-right:2px}
td.cmpc input{cursor:pointer;width:15px;height:15px;accent-color:var(--accent)}
dialog#cmpdlg{border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--ink);
  max-width:min(1100px,94vw);padding:0;max-height:88vh}
.cmpinner{padding:20px 22px}
dialog#cmpdlg::backdrop{background:rgba(8,18,20,.55)}
.cmphead{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.cmphead h2{margin:0;font-size:1.3rem}
#cmp-close{font:inherit;font-size:1.4rem;line-height:1;background:none;border:none;color:var(--ink-2);
  cursor:pointer;padding:2px 8px}
#cmp-close:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
#cmpbanner .flagbox{margin:0 0 12px}
.cmpcols{display:flex;gap:14px;overflow-x:auto;padding-bottom:6px}
.cmpcol{flex:1;min-width:240px;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.cmpcol h3{font-size:1rem;margin:0}
.cmpverdict{display:flex;align-items:baseline;gap:8px;margin:6px 0 2px;flex-wrap:wrap}
.cmpverdict .cv{font-size:1.7rem;font-weight:700}
.cmpverdict .cr{font-size:.78rem;color:var(--ink-2)}
.cmpfacts{font-size:.78rem;color:var(--ink-2);margin:6px 0;line-height:1.55}
.cmpdivs{font-size:.78rem;margin:8px 0 0;border-top:1px solid var(--line);padding-top:8px;color:var(--ink-2)}
.cmpdivs div{display:flex;justify-content:space-between;gap:8px;padding:2px 0}
.cmpdivs .act{font-weight:700;color:var(--ink)}
.cdims{margin-top:8px;border-top:1px solid var(--line);padding-top:8px}
.cdims .dims .db i.win{background:var(--accent-deep)}
.cdims .dims .dl.win{color:var(--accent-deep);font-weight:700}
.cmpnote{font-size:.78rem;color:var(--ink-2);border-top:1px solid var(--line);padding-top:8px;margin-top:8px}
"""

JS = """
<script>
(function(){
  var sel = document.getElementById('modesel');
  var chk = document.getElementById('poolchk');
  if (!sel || !chk) return;
  var F = ['f-cost', 'f-travel', 'f-days', 'f-water', 'f-month', 'f-region', 'f-gate']
    .map(function(id){ return document.getElementById(id); });
  function applyFilters(){
    var cost = +F[0].value, trav = +F[1].value, days = +F[2].value, water = +F[3].value;
    var month = F[4].value, region = F[5].value, gateOnly = F[6].checked;
    document.querySelectorAll('.mode tbody tr').forEach(function(row){
      var d = row.dataset, ok = true;
      if (cost && +d.cost > cost) ok = false;
      if (trav && +d.travel < trav) ok = false;
      if (days && +d.days > days) ok = false;
      if (water && +d.waterlo < water) ok = false;
      if (month && d.months.indexOf(',' + month + ',') < 0) ok = false;
      if (region && d.region !== region) ok = false;
      if (gateOnly && d.gate !== '1') ok = false;
      row.style.display = ok ? '' : 'none';
    });
    var act = document.querySelector('.mode.active'), n = 0, tot = 0;
    if (act) act.querySelectorAll('tbody tr').forEach(function(r){
      tot++; if (r.style.display !== 'none') n++;
    });
    document.getElementById('f-count').textContent = n + ' of ' + tot + ' trips shown';
  }
  function apply(m, p){
    var ps = p ? 'on' : 'off';
    document.querySelectorAll('.mode').forEach(function(el){
      el.classList.toggle('active',
        el.getAttribute('data-mode') === m && el.getAttribute('data-pools') === ps);
    });
    sel.value = m; chk.checked = p;
    var slot = document.querySelector('.mode.active .filterslot');
    if (slot) slot.appendChild(document.getElementById('fbar'));
    try { localStorage.setItem('fwi-mode', m); localStorage.setItem('fwi-pools', ps); } catch (e) {}
    applyFilters();
  }
  sel.addEventListener('change', function(){ apply(sel.value, chk.checked); });
  chk.addEventListener('change', function(){ apply(sel.value, chk.checked); });
  F.forEach(function(el){ el.addEventListener('change', applyFilters); });
  document.getElementById('f-reset').addEventListener('click', function(){
    F.forEach(function(el){ if (el.type === 'checkbox') el.checked = false; else el.value = el.options[0].value; });
    applyFilters();
  });
  // ---- compare ----
  var TD = {trips: {}};
  try { TD = JSON.parse(document.getElementById('tripdata').textContent); } catch (e) {}
  var CMP_CAP = 4;      // keep in sync with Python CMP_CAP / thead tooltip
  var WIN_GAP = 1.0;    // methodology noise floor — see COMPARE_SPEC.md amendment 2
  var picks = [];
  try {
    picks = (JSON.parse(localStorage.getItem('fwi-compare') || '[]') || [])
      .filter(function(n, i, a){ return TD.trips && TD.trips[n] && a.indexOf(n) === i; })
      .slice(0, CMP_CAP);
  } catch (e) {}
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
    return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function savePicks(){ try { localStorage.setItem('fwi-compare', JSON.stringify(picks)); } catch (e) {} }
  function paintPicks(){
    document.querySelectorAll('.cmp-pick').forEach(function(cb){
      cb.checked = picks.indexOf(cb.dataset.name) >= 0;
    });
    document.getElementById('cmp-n').textContent = picks.length;
    document.getElementById('cmp-open').style.display = picks.length >= 2 ? '' : 'none';
    document.getElementById('cmp-clear').style.display = picks.length ? '' : 'none';
  }
  document.addEventListener('change', function(ev){
    var cb = ev.target && ev.target.classList && ev.target.classList.contains('cmp-pick') ? ev.target : null;
    if (!cb) return;
    var name = cb.dataset.name, i = picks.indexOf(name);
    if (cb.checked && i < 0) {
      if (picks.length >= CMP_CAP) { cb.checked = false; return; }
      picks.push(name);
    } else if (!cb.checked && i >= 0) picks.splice(i, 1);
    savePicks(); paintPicks();
  });
  document.getElementById('cmp-clear').addEventListener('click', function(){
    picks = []; savePicks(); paintPicks();
  });
  var dlg = document.getElementById('cmpdlg');
  function monthsUntil(months){
    var now = new Date().getMonth() + 1, best = 12;
    months.forEach(function(mm){ var d = (mm - now + 12) % 12; if (d < best) best = d; });
    return best;
  }
  function buildCompare(){
    var act = document.querySelector('.mode.active');
    var akey = act ? act.getAttribute('data-mode') : 'family';
    var dimsSorted = TD.dims.slice().sort(function(a, b){
      return (TD.weights[akey][b] || 0) - (TD.weights[akey][a] || 0); });
    var win = {};
    dimsSorted.forEach(function(d){
      var vals = picks.map(function(n){ return TD.trips[n].scores[d]; })
        .sort(function(a, b){ return b - a; });
      if (vals.length > 1 && vals[0] - vals[1] >= WIN_GAP) win[d] = vals[0];
    });
    var poolsOff = act && act.getAttribute('data-pools') === 'off';
    function gateMark(t, d){
      // mirror the visible table: pool rows show no gate verdict while pools are off
      if (poolsOff && t.pool) return '\u2014 <span title="Toggle wave pools on to rank this row">(pools off)</span>';
      return d.ok ? '\u2713' : '<span title="' + esc(d.why) + '">\u2717</span>';
    }
    var cols = picks.map(function(n){
      var t = TD.trips[n], a = t.divs[akey];
      var mu = monthsUntil(t.months);
      var facts = esc(t.country) + ' \u00b7 ' + esc(t.window) +
        (mu ? ' (opens in ~' + mu + 'mo)' : ' (in window now)') + '<br>' +
        esc(t.cost_band) + ' \u00b7 min ' + t.min_days + 'd \u00b7 ' +
        t.water_f[0] + '\u2013' + t.water_f[1] + '\u00b0F \u00b7 ' + esc(t.wetsuit) +
        '<br>' + esc(t.travel_note) +
        (t.cluster ? '<br><em>cluster: ' + esc(t.cluster) + '</em>' : '') +
        (t.pool ? '<br><em>wave pool</em>'
                : '<br><a href="' + t.forecast + '" target="_blank" rel="noopener">forecast \u2197</a>');
      var divrows = Object.keys(t.divs).map(function(k){
        var d = t.divs[k];
        return '<div class="' + (k === akey ? 'act' : '') + '"><span>' + esc(TD.modelabels[k]) + '</span>' +
          '<span class="mono">' + d.comp + ' \u00b7 #' + d.rank + ' (' + d.band[0] + '\u2013' + d.band[1] + ') ' +
          gateMark(t, d) + '</span></div>';
      }).join('');
      var bars = dimsSorted.map(function(d){
        var v = t.scores[d], w = win[d] !== undefined && v === win[d];
        return '<span class="dl' + (w ? ' win' : '') + '">' + esc(TD.labels[d]) + '</span>' +
          '<span class="db"><i' + (w ? ' class="win"' : '') + ' style="width:' + (v * 10) + '%"></i></span>' +
          '<span class="dv mono">' + v + '</span>';
      }).join('');
      return '<div class="cmpcol"><h3>' + esc(n) + '</h3>' +
        '<div class="cmpverdict"><span class="cv mono">' + a.comp + '</span>' +
        '<span class="cr">#' + a.rank + ' in ' + esc(TD.modelabels[akey]) +
        ' \u00b7 band ' + a.band[0] + '\u2013' + a.band[1] +
        ' \u00b7 gate ' + (poolsOff && t.pool ? '\u2014 (pools off)'
                             : (a.ok ? '\u2713' : '\u2717 ' + esc(a.why))) + '</span></div>' +
        '<div class="cmpfacts">' + facts + '</div>' +
        '<div class="cmpdivs">' + divrows + '</div>' +
        '<div class="cdims"><div class="dims">' + bars + '</div></div>' +
        '<div class="cmpnote"><strong>Booking:</strong> ' + esc(t.booking) + ' ' + esc(t.note) + '</div></div>';
    }).join('');
    var counts = {};
    picks.forEach(function(n){ var c = TD.trips[n].cluster; if (c) counts[c] = (counts[c] || 0) + 1; });
    var dups = Object.keys(counts).filter(function(c){ return counts[c] > 1; });
    document.getElementById('cmpbanner').innerHTML = dups.length
      ? '<div class="flagbox"><strong>Same-trip warning (' + esc(dups.join(', ')) + '):</strong> ' +
        'these rows are day-trip-range siblings \u2014 you are largely comparing one trip with itself.</div>'
      : '';
    document.getElementById('cmpbody').innerHTML = cols;
  }
  document.getElementById('cmp-open').addEventListener('click', function(){
    if (picks.length < 2) return;
    buildCompare();
    dlg.showModal();
  });
  document.getElementById('cmp-close').addEventListener('click', function(){ dlg.close(); });
  dlg.addEventListener('click', function(ev){ if (ev.target === dlg) dlg.close(); });

  var m = null, p = null;
  try { m = localStorage.getItem('fwi-mode'); p = localStorage.getItem('fwi-pools'); } catch (e) {}
  if (!document.querySelector('.mode[data-mode="' + m + '"]')) m = 'family';
  apply(m, p === 'on');
  paintPicks();
})();
</script>
"""

e = html.escape


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


def render_mode(key, mode, trips, dims, pools_on):
    """One full division block: stats, top-10 cards, table, calendar, playbook."""
    weights = mode["weights"]
    gates = mode["gates"]
    copy = MODE_COPY[key]

    def gate(t):
        if not gate_check(key, mode, t)[0]:
            return False
        return pools_on or not t.get("pool")

    gate_desc = " and ".join(f'{DIM_LABELS[d][0].lower()} score ≥ {m:g}' for d, m in gates)
    if key == "family":
        gate_desc += " (pools: on-site resort required)"

    ranked = sorted(trips, key=lambda t: -composite(t["scores"], weights))
    comp = {t["name"]: round(composite(t["scores"], weights), 1) for t in trips}
    bands = sensitivity_bands(trips, weights)
    eligible = [t for t in ranked if gate(t)]
    n = len(ranked)
    s_count = sum(1 for t in ranked if tier(comp[t["name"]]) == "S"
                  and (pools_on or not t.get("pool")))
    top = eligible[0]

    stats = f"""<div class="statrow">
    <div class="stat"><div class="n mono">{n}</div><div class="l">Trips scored</div></div>
    <div class="stat"><div class="n mono">{len(eligible)}</div><div class="l">Pass {copy["gate_col"].lower()} gate</div></div>
    <div class="stat"><div class="n mono">{s_count}</div><div class="l">S-tier (80+)</div></div>
    <div class="stat"><div class="n">{e(short_name(top["name"]))}</div><div class="l">No. 1 · {comp[top["name"]]}</div></div>
  </div>"""

    cards = []
    for i, t in enumerate(eligible[:10], 1):
        cards.append(f"""<article class="card">
<div class="top"><span class="rk mono">{i}</span><h3>{e(t["name"])}</h3><span class="score mono">{comp[t["name"]]}</span></div>
<div class="meta"><span>{e(t["country"])}</span><span>·</span><span>{e(t["window"])}</span><span>·</span><span>{e(t["cost_band"])}</span><span>·</span><span>min {t["min_days"]}d</span><span>·</span><span>{t["water_f"][0]}–{t["water_f"][1]}°F · {e(t["wetsuit"])}</span><span>·</span><span>{e(t["travel_note"])}</span></div>
<div class="dims">{dim_rows(t["scores"])}</div>
<p class="note">{e(t["note"])} <em>Booking: {e(t["booking"])}.</em></p>
</article>""")

    thead = ('<tr><th class="cmpc" title="Select up to 4 trips to compare"></th>'
             "<th>#</th><th>Trip</th><th>Window</th><th>Tier</th>"
             f'<th title="{e(copy["gate_ok_title"])} ({gate_desc})">{copy["gate_col"]}</th>'
             '<th title="All-in $/person/week incl. BOS flights: $ &lt;2.5k · $$ 2.5–4k · $$$ 4–6.5k · $$$$ &gt;6.5k">Cost</th>'
             '<th class=num title="Minimum viable trip length after two-way transit and jet lag">Min d</th>'
             "<th>Booking</th>"
             '<th title="In-window sea temperature and the wetsuit it demands">Water</th>'
             "<th class=num>Score</th><th class=num>Band</th>"
             + "".join(f'<th class=num title="{e(DIM_LABELS[d][1])}">{DIM_LABELS[d][0]}</th>' for d in dims)
             + "</tr>")
    rows = []
    for i, t in enumerate(ranked, 1):
        c = comp[t["name"]]
        lo, hi = bands[t["name"]]
        if t.get("pool") and not pools_on:
            tr, g = "POOL", '<span title="Toggle wave pools on to rank this row">—</span>'
        else:
            tr = tier(c)
            g = (f'<span class="gate-ok" title="{e(copy["gate_ok_title"])}">✓</span>' if gate(t)
                 else f'<span class="gate-no" title="{e(copy["gate_no_title"])}">✗</span>')
        cells = "".join(f'<td class="num mono">{t["scores"][d]:g}</td>' for d in dims)
        rows.append(
            f'<tr data-cost="{len(t["cost_band"])}" data-days="{t["min_days"]}" '
            f'data-travel="{t["scores"]["travel"]:g}" data-waterlo="{t["water_f"][0]}" '
            f'data-region="{e(t["region"])}" data-months=",{",".join(map(str, t["months"]))}," '
            f'data-gate="{1 if gate(t) else 0}">'
            f'<td class="cmpc"><input type="checkbox" class="cmp-pick" data-name="{e(t["name"])}" '
            f'aria-label="Compare {e(t["name"])}"></td>'
            f'<td class="mono">{i}</td>'
            f'<td class="trip">{e(t["name"])}<div class="sub">{e(t["country"])} — {e(t["travel_note"])}'
            + (f' · <em>{e(t["cluster"])}</em>' if t.get("cluster") else '')
            + (f' · <a href="{forecast_url(t)}" target="_blank" rel="noopener">forecast ↗</a>'
               if forecast_url(t) else '') + '</div></td>'
            f'<td>{e(t["window"])}</td><td><span class="chip {tr}">{tr}</span></td>'
            f'<td>{g}</td><td class="mono">{e(t["cost_band"])}</td>'
            f'<td class="num mono">{t["min_days"]}</td><td class="book">{e(t["booking"])}</td>'
            f'<td class="book"><span class="mono">{t["water_f"][0]}–{t["water_f"][1]}°F</span> · {e(t["wetsuit"])}</td>'
            f'<td class="num mono">{c}{bar(c/10)}</td>'
            f'<td class="num mono band">{lo}–{hi}</td>{cells}</tr>')

    mcells = []
    for m in range(1, 13):
        best = next(t for t in ranked if m in t["months"] and not t.get("pool") and gate(t))
        mcells.append(f'<div class="mcell"><div class="m">{MONTHS[m-1]}</div>'
                      f'<div class="p">{e(best["name"])}</div>'
                      f'<div class="mono" style="color:var(--ink-2)">{comp[best["name"]]}</div></div>')

    def season_list(months_set, k=6, within=False):
        cond = (lambda t: set(t["months"]) <= months_set) if within else (lambda t: set(t["months"]) & months_set)
        picks = [t for t in ranked if cond(t) and not t.get("pool") and gate(t)][:k]
        return "".join(f'<li>{e(t["name"])} <span class="s mono">{comp[t["name"]]} · {e(t["window"])}</span></li>'
                       for t in picks)

    return f"""<div class="mode" data-mode="{key}" data-pools="{'on' if pools_on else 'off'}">
  {stats}

<section>
  <h2>{copy["cards_h2"]}</h2>
  <p class="prose">{copy["cards_intro"].format(gate_desc=gate_desc)}</p>
  <div class="cards">{"".join(cards)}</div>
  {copy["caveat"]}
</section>

<section>
  <h2>All {n} trips — {mode["label"].lower()} weighting</h2>
  <p class="prose">Band = where the trip's rank lands when any one weight is perturbed ±25% —
  a tight band means the rank is robust. {copy["gate_col"]} = this division's gate ({gate_desc}).
  Filters below apply to <strong>this table only</strong> — the top-ten cards and calendar always show the
  model's unfiltered opinion. Rank numbers keep their gaps so you can see what a filter costs you.</p>
  <div class="filterslot"></div>
  <div class="tablewrap"><table>
    <thead>{thead}</thead>
    <tbody>{"".join(rows)}</tbody>
  </table></div>
</section>

<section>
  <h2>When to go where</h2>
  <p class="prose">The year splits cleanly in two: <strong>April–October</strong> belongs to the Southern
  Hemisphere swell machine, <strong>November–March</strong> to North Atlantic and North Pacific winter, with
  the Portugal/France shoulder peaking September–October. Gate-passing trips only.</p>
  <div class="seasons">
    <div class="season"><div class="months">Apr – Oct · southern season</div>
      <h3>The guarantee window</h3><ol>{season_list({5,6,7,8})}</ol></div>
    <div class="season"><div class="months">Nov – Mar · northern winter</div>
      <h3>Winter season</h3><ol>{season_list({12,1,2})}</ol></div>
    <div class="season"><div class="months">Sep – Oct · shoulder</div>
      <h3>The sweet overlap</h3><ol>{season_list({9,10,11}, within=True)}</ol></div>
  </div>
  <h3 style="margin-top:28px">Best gate-passing trip in window, by month</h3>
  <div class="monthstrip">{"".join(mcells)}</div>
</section>

<section>
  <h2>Three ways to book it</h2>
  <div class="arche">{copy["playbook"]}
  </div>
</section>
</div>"""


def main():
    data = json.loads((ROOT / "data" / "trips.json").read_text())
    trips, dims, modes = data["trips"], data["dimensions"], data["modes"]
    fam_w = modes["family"]["weights"]

    # Family-mode figures for the shared integrity section (the audit record)
    ranked = sorted(trips, key=lambda t: -composite(t["scores"], fam_w))
    comp = {t["name"]: round(composite(t["scores"], fam_w), 1) for t in trips}
    bands = sensitivity_bands(trips, fam_w)
    ranks = {t["name"]: i + 1 for i, t in enumerate(ranked)}
    n = len(trips)
    top10_dev = max(max(ranks[t["name"]] - bands[t["name"]][0],
                        bands[t["name"]][1] - ranks[t["name"]]) for t in ranked[:10])
    mid_dev = max(max(ranks[t["name"]] - bands[t["name"]][0],
                      bands[t["name"]][1] - ranks[t["name"]]) for t in ranked[24:55])
    wk_rank = ranks["Waikiki (Oahu) — winter"]
    waco = max(comp[t["name"]] for t in trips if t.get("pool"))

    # Compare blob: per-trip record + per-division stats, same math as the tables
    mode_stats = {}
    for k, m in modes.items():
        w = m["weights"]
        order = sorted(trips, key=lambda t: -composite(t["scores"], w))
        mode_stats[k] = ({t["name"]: round(composite(t["scores"], w), 1) for t in trips},
                         {t["name"]: i + 1 for i, t in enumerate(order)},
                         sensitivity_bands(trips, w), m)

    cmp_trips = {}
    for t in trips:
        divs = {}
        for k, (mc, mr, mb, m) in mode_stats.items():
            gok, why = gate_check(k, m, t)
            divs[k] = {"comp": mc[t["name"]], "rank": mr[t["name"]],
                       "band": mb[t["name"]], "ok": gok, "why": why}
        cmp_trips[t["name"]] = {
            "scores": t["scores"], "divs": divs, "country": t["country"],
            "window": t["window"], "months": t["months"], "cost_band": t["cost_band"],
            "min_days": t["min_days"], "booking": t["booking"], "water_f": t["water_f"],
            "wetsuit": t["wetsuit"], "travel_note": t["travel_note"],
            "cluster": t.get("cluster", ""), "pool": bool(t.get("pool")),
            "forecast": forecast_url(t), "note": t["note"]}
    blob_json = json.dumps(
        {"weights": {k: m["weights"] for k, m in modes.items()},
         "labels": {d: DIM_LABELS[d][0] for d in dims},
         "modelabels": {k: m["label"] for k, m in modes.items()},
         "dims": dims, "trips": cmp_trips},
        ensure_ascii=False).replace("</", "<\\/") \
        .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")  # prevent </script> breakout
    cmp_dialog = """<dialog id="cmpdlg" aria-label="Trip comparison">
 <div class="cmpinner">
  <div class="cmphead"><h2>Compare</h2>
    <button id="cmp-close" type="button" aria-label="Close comparison">×</button></div>
  <div id="cmpbanner"></div>
  <div class="cmpcols" id="cmpbody"></div>
 </div>
</dialog>"""

    # Triple-column weights grid (family / boys / strike)
    boys_w, strike_w = modes["boys"]["weights"], modes["strike"]["weights"]
    wrows = ['<div class="wrow"><div class="whead">Dimension</div><div class="whead">Family</div>'
             '<div class="whead">Solo / boys</div><div class="whead">Strike</div></div>']
    all_dims = sorted(set(fam_w) | set(strike_w), key=lambda d: -(fam_w.get(d, 0)))
    for d in all_dims:
        label, desc = DIM_LABELS[d]
        fw, bw, sw = fam_w.get(d, 0), boys_w.get(d, 0), strike_w.get(d, 0)
        wrows.append(
            f'<div class="wrow"><div class="wname" title="{e(desc)}">{label}</div>'
            f'<div class="wcell"><span class="wbar" style="width:{fw*7}px"></span><span class="wnum mono">{fw:g}</span></div>'
            f'<div class="wcell alt"><span class="wbar" style="width:{bw*7}px"></span><span class="wnum mono">{bw:g}</span></div>'
            f'<div class="wcell alt2"><span class="wbar" style="width:{sw*7}px"></span><span class="wnum mono">{sw:g}</span></div></div>')

    mode_opts = "".join(f'<option value="{k}">{e(m["label"])}</option>' for k, m in modes.items())
    month_opts = "".join(f'<option value="{i}">{MONTHS[i-1]}</option>' for i in range(1, 13))
    region_opts = "".join(f'<option value="{e(r)}">{e(r)}</option>'
                          for r in sorted({t["region"] for t in trips}))
    mode_blocks = "\n".join(render_mode(k, m, trips, dims, pools_on)
                            for k, m in modes.items() for pools_on in (False, True))

    html_doc = f"""<title>The Family Wave Index</title>
<style>{CSS}</style>
<div class="wrap">

<header class="masthead">
  <div class="eyebrow">Surf trips from New England · scored &amp; ranked · Aug 2026</div>
  <h1>The Family <em>Wave</em> Index</h1>
  <p class="dek">{n} destination-plus-season trips scored on ten dimensions, ranked three ways:
  a <strong>family division</strong> (everyone scores, beginner floor), a <strong>solo/boys division</strong>
  (advanced crews, wave count first), and a <strong>strike division</strong> (don't book dates — watch the
  chart and fly when it's confirmed). Same trips, same scores; only the weights and the gate change. Wave
  pools are a toggle: off, they appear untiered as calibration rows; on, they compete — and in the family
  division a pool only counts when it's part of a resort.</p>
  <div class="modebar">
    <label for="modesel">Optimize for</label>
    <select id="modesel">{mode_opts}</select>
    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;text-transform:none;letter-spacing:0">
      <input type="checkbox" id="poolchk"> include wave pools</label>
  </div>
</header>

<section>
  <h2>How the score works</h2>
  <p class="prose">Each trip is a <strong>destination + season window</strong>, scored 0–10 on nine dimensions
  against written anchors; a division's composite is its weighted sum on a 0–100 scale. The family weighting
  puts swell certainty and the turnkey factor first and gates on a beginner floor; the solo/boys weighting —
  derived from a charger + charter-captain + defender persona panel — promotes crowds, quality, and advanced,
  demotes lodging and beginner, and gates on an advanced floor instead.</p>
  <div class="wtable">{"".join(wrows)}</div>
  <div class="callout"><strong>Provenance, honestly.</strong> Scores are structured expert priors from swell
  climatology and the surf-travel record as of early 2026 — an ordinal ranking tool, not measurements.
  A 3-point gap is meaningful; a 1-point gap is noise. Crowd scores decay fastest in real life; safety scores
  reflect early-2026 conditions — re-check advisories before booking. Full anchors and the v1→v7 changelog
  (incl. rejected proposals) live in <span class="mono">METHODOLOGY.md</span>; rerun
  <span class="mono">score.py</span> + <span class="mono">gen_report.py</span> to regenerate everything here.</div>
</section>

<div id="filterhome" hidden>
  <div class="filters" id="fbar">
    <label>Budget<select id="f-cost"><option value="0">Any</option><option value="1">$ only</option>
      <option value="2">Up to $$</option><option value="3">Up to $$$</option></select></label>
    <label>Travel<select id="f-travel"><option value="0">Any</option>
      <option value="7.5">Short haul / nonstop</option><option value="5.5">≤ 1 easy connection</option>
      <option value="3">No expeditions (under ~20h)</option></select></label>
    <label>Max days I have<select id="f-days"><option value="0">Any</option><option value="4">≤ 4</option>
      <option value="6">≤ 6</option><option value="8">≤ 8</option><option value="10">≤ 10</option></select></label>
    <label>Rubber<select id="f-water"><option value="0">Any</option>
      <option value="75">Trunks only (≥75°F)</option><option value="66">Springsuit or warmer (≥66°F)</option></select></label>
    <label>Month<select id="f-month"><option value="">Any</option>{month_opts}</select></label>
    <label>Region<select id="f-region"><option value="">Any</option>{region_opts}</select></label>
    <label class="fchk"><input type="checkbox" id="f-gate"> passes this division's gate</label>
    <button id="cmp-open" type="button" class="cmpbtn" style="display:none">Compare (<span id="cmp-n">0</span>)</button>
    <button id="cmp-clear" type="button" style="display:none">clear picks</button>
    <button id="f-reset" type="button">reset</button>
    <span class="fcount" id="f-count"></span>
  </div>
</div>

{mode_blocks}

<section>
  <h2>Integrity checks</h2>
  <p class="prose">Checks run on the family weighting (the boys division reuses the same scores). A scoring
  model that just likes famous places is broken, so famous-but-flawed spots serve as null tests — and the
  weights get stress-tested rather than trusted.</p>
  <ul class="tight prose">
    <li><strong>Uluwatu ranks {ranks["Uluwatu + Bingin (Bukit)"]}/{n}</strong> and
    <strong>Noosa {ranks["Noosa"]}/{n}</strong> despite world fame — crowds and (for Noosa) swell roulette
    cost them exactly as designed. Pass.</li>
    <li><strong>Sensitivity:</strong> the top 10 hold rank within ±{top10_dev} places under every single-weight
    ±25% perturbation. Mid-table swings up to ±{mid_dev} — treat those as a tier, not an ordering.</li>
  </ul>
  <div class="flagbox"><strong>Adjudicated — Waikiki winter, rank {wk_rank}.</strong> Earlier passes ranked it
  top-10 on a turnkey score of 9 — a beginner-only number smuggled in as a trip score — and on North Shore
  quality a mixed group can't ride (the base-pairing error caught in the v4 audit). Rescored as Waikiki-only;
  the null check now passes on its own.</div>
  <h3 style="margin-top:28px">Seven-persona panel review (v3)</h3>
  <ul class="tight prose">
    <li><strong>The family weights survived:</strong> all seven persona vectors correlated 0.88–0.99 with the
    ranking, and six trips topped every vector — so the proposed reweight was rejected as redundant.</li>
    <li><strong>The structure didn't:</strong> five of seven seats flagged that an additive model lets
    consistency and crowd buy off a failing beginner score — hence the beginner floor instead of a weight.</li>
    <li><strong>Nine trips rescored</strong> on converging multi-seat evidence (Mentawai, Samoa, North Malé,
    Hacienda Iguana, Rote, others); <strong>cost stays out of the composite</strong> — budget is a filter,
    so it's a column. The family S-tier is, Las Flores excepted, also the $$$$-tier.</li>
  </ul>
  <h3 style="margin-top:28px">Adversarial coverage audit (v4)</h3>
  <ul class="tight prose">
    <li><strong>The blind spot was property-level products</strong> — the list scored coastlines and missed
    resorts on validated corridors (Nihi Sumba, Rancho Santana, Mizata). 17 rows added; original 69 judged
    ~80–85% comprehensive.</li>
    <li><strong>The wave pools tell on the model:</strong> the best pool scores {waco:g} under family
    weights — above every ocean trip — because "guaranteed, safe, zero-thought waves" literally describes a
    pool. With the toggle off they sit untiered as calibration rows; toggled on they compete, and in the
    family division only resort pools (Waco, Surf Ranch, The Wave Bristol) pass the gate.</li>
    <li><strong>Exclusions held:</strong> dozens of plausible destinations (Japan, Taiwan, Eleuthera, Tobago,
    Australia's points, Réunion) confirmed to fail the brief — recorded so they aren't relitigated.</li>
  </ul>
</section>

<footer>The Family Wave Index · methodology, dataset and scoring script in the surf-trip repo
(<span class="mono">METHODOLOGY.md · data/trips.json · score.py</span>) · scores are early-2026 expert priors;
verify advisories, seasons and operators before booking.</footer>

{cmp_dialog}
</div>
<script type="application/json" id="tripdata">{blob_json}</script>
{JS}"""
    out = ROOT / "report.html"
    out.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {out} ({len(html_doc):,} bytes)")


if __name__ == "__main__":
    main()
