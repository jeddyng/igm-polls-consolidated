#!/usr/bin/env python3
"""
Build the static HTML site from polls_data.json.
Outputs to docs/index.html for GitHub Pages.
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, 'polls_data.json')
OUT_DIR = os.path.join(SCRIPT_DIR, 'docs')


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)

    # Clean for embedding
    for s in data:
        for q in s['questions']:
            if 'votes' in q:
                del q['votes']
        if not s.get('topic'):
            s.pop('topic', None)
        if not s.get('panel'):
            s['panel'] = 'US'

    data_json = json.dumps(data, separators=(',', ':'))

    html = build_html(data_json)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'index.html')
    with open(out_path, 'w') as f:
        f.write(html)
    print(f'Built {out_path} ({len(html)} bytes, {len(data)} surveys)')


def build_html(data_json):
    return (
        r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IGM Expert Polls — Economist Consensus Database</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600;8..60,700&family=DM+Sans:wght@400;500;600;700&display=swap');

:root {
  --bg: #f5f0eb; --card: #ffffff; --text: #1a1a1a; --text2: #555;
  --border: #e0d8cf; --accent: #b8860b;
  --sa: #1a5c2e; --a: #2d7d46; --u: #d4a017; --d: #c0392b; --sd: #8b1a1a; --no: #bbb;
}
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }

.nav-tabs {
  position:sticky; top:0; z-index:100; background:#1a1a1a;
  display:flex; justify-content:center; gap:0; border-bottom:2px solid #333;
}
.nav-tab {
  padding:0.75rem 2rem; color:#999; font-size:0.85rem; font-weight:600;
  text-transform:uppercase; letter-spacing:0.06em; cursor:pointer;
  border-bottom:3px solid transparent; transition:all 0.2s;
}
.nav-tab:hover { color:#ddd; }
.nav-tab.active { color:var(--accent); border-bottom-color:var(--accent); }

.page { display:none; }
.page.active { display:block; }

.hero {
  background:#1a1a1a; color:#f5f0eb;
  padding:2.5rem 2rem 2rem; text-align:center;
}
.hero h1 { font-family:'Source Serif 4',serif; font-size:2.2rem; font-weight:700; letter-spacing:-0.02em; margin-bottom:0.3rem; }
.hero p { font-size:0.9rem; opacity:0.7; max-width:600px; margin:0 auto; }
.hero .stats { display:flex; gap:2rem; justify-content:center; margin-top:1.2rem; flex-wrap:wrap; }
.hero .stat .num { font-family:'Source Serif 4',serif; font-size:1.8rem; font-weight:700; color:var(--accent); }
.hero .stat .lbl { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; opacity:0.6; }

.controls {
  max-width:1100px; margin:0 auto; padding:1.5rem 1.5rem 0;
  display:flex; gap:0.75rem; flex-wrap:wrap; align-items:center;
}
.search-box { flex:1; min-width:200px; position:relative; }
.search-box input {
  width:100%; padding:0.7rem 1rem 0.7rem 2.5rem;
  border:2px solid var(--border); border-radius:8px;
  font-size:0.95rem; font-family:'DM Sans',sans-serif;
  background:var(--card); transition:border-color 0.2s;
}
.search-box input:focus { outline:none; border-color:var(--accent); }
.search-box::before { content:'\1F50D'; position:absolute; left:0.8rem; top:50%; transform:translateY(-50%); font-size:1rem; opacity:0.4; }

.filter-btn {
  padding:0.5rem 0.85rem; border:2px solid var(--border); border-radius:8px;
  background:var(--card); font-family:'DM Sans',sans-serif;
  font-size:0.8rem; font-weight:500; cursor:pointer;
  transition:all 0.15s; color:var(--text2);
}
.filter-btn:hover { border-color:var(--accent); color:var(--text); }
.filter-btn.active { background:var(--text); color:var(--bg); border-color:var(--text); }

select.ctrl-select {
  padding:0.5rem 0.7rem; border:2px solid var(--border); border-radius:8px;
  background:var(--card); font-family:'DM Sans',sans-serif;
  font-size:0.8rem; color:var(--text2); cursor:pointer; appearance:auto;
}
select.ctrl-select:focus { outline:none; border-color:var(--accent); }

.per-page-wrap {
  display:flex; align-items:center; gap:0.4rem; font-size:0.8rem; color:var(--text2);
}
.per-page-wrap select {
  padding:0.4rem 0.5rem; border:2px solid var(--border); border-radius:6px;
  background:var(--card); font-family:'DM Sans',sans-serif;
  font-size:0.8rem; color:var(--text2); cursor:pointer;
}

.result-count { width:100%; padding:0.5rem 0 0; font-size:0.8rem; color:var(--text2); }

.grid {
  max-width:1100px; margin:1rem auto 1rem; padding:0 1.5rem;
  display:flex; flex-direction:column; gap:1rem;
}
.card {
  background:var(--card); border-radius:10px; border:1px solid var(--border);
  padding:1.5rem; transition:box-shadow 0.2s;
}
.card:hover { box-shadow:0 4px 20px rgba(0,0,0,0.08); }
.card-header { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:0.5rem; }
.card-title { font-family:'Source Serif 4',serif; font-size:1.2rem; font-weight:600; line-height:1.3; }
.card-title a { color:inherit; text-decoration:none; }
.card-title a:hover { color:var(--accent); }
.card-meta { display:flex; gap:0.5rem; flex-shrink:0; align-items:center; flex-wrap:wrap; }
.badge { padding:0.2rem 0.6rem; border-radius:4px; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; }
.badge-us { background:#e8f0fe; color:#1a56db; }
.badge-europe { background:#fef3c7; color:#92400e; }
.badge-finance { background:#ecfdf5; color:#065f46; }
.badge-date { font-size:0.75rem; color:var(--text2); white-space:nowrap; }

.archive-links { font-size:0.7rem; margin-bottom:0.75rem; }
.archive-links a { color:var(--text2); text-decoration:none; margin-right:0.75rem; }
.archive-links a:hover { color:var(--accent); text-decoration:underline; }

.question-block { margin-top:1rem; padding-top:1rem; border-top:1px solid #f0ece6; }
.question-block:first-child { margin-top:0; border-top:none; padding-top:0; }
.q-label { font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--accent); margin-bottom:0.25rem; }
.q-text { font-size:0.88rem; color:var(--text); margin-bottom:0.75rem; line-height:1.5; }

.bar-row { display:flex; height:26px; border-radius:6px; overflow:hidden; margin-bottom:0.4rem; }
.bar-seg {
  display:flex; align-items:center; justify-content:center;
  font-size:0.63rem; font-weight:700; color:white;
  min-width:0; white-space:nowrap; overflow:hidden;
}
.bar-seg.sa { background:var(--sa); } .bar-seg.a { background:var(--a); }
.bar-seg.u { background:var(--u); } .bar-seg.d { background:var(--d); }
.bar-seg.sd { background:var(--sd); } .bar-seg.no { background:var(--no); }

.bar-legend { display:flex; gap:0.6rem; flex-wrap:wrap; font-size:0.68rem; color:var(--text2); }
.bar-legend span::before { content:''; display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:3px; vertical-align:middle; }
.bar-legend .l-sa::before { background:var(--sa); } .bar-legend .l-a::before { background:var(--a); }
.bar-legend .l-u::before { background:var(--u); } .bar-legend .l-d::before { background:var(--d); }
.bar-legend .l-sd::before { background:var(--sd); } .bar-legend .l-no::before { background:var(--no); }

.consensus-tag {
  display:inline-block; padding:0.15rem 0.5rem; border-radius:4px;
  font-size:0.7rem; font-weight:700; margin-left:0.5rem; vertical-align:middle;
}
.consensus-agree { background:#d4edda; color:#2d7d46; }
.consensus-disagree { background:#f8d7da; color:#c0392b; }
.consensus-uncertain { background:#fff3cd; color:#856404; }
.consensus-mixed { background:#e2e8f0; color:#475569; }

.respondents { font-size:0.7rem; color:var(--text2); margin-top:0.3rem; }

.load-more {
  display:block; margin:1rem auto 3rem; padding:0.8rem 2.5rem;
  background:var(--text); color:var(--bg); border:none; border-radius:8px;
  font-family:'DM Sans',sans-serif; font-size:0.9rem; font-weight:600;
  cursor:pointer; transition:opacity 0.2s;
}
.load-more:hover { opacity:0.85; }

.section-load-more {
  display:block; margin:0.75rem auto 2rem; padding:0.6rem 2rem;
  background:transparent; color:var(--accent); border:2px solid var(--accent); border-radius:8px;
  font-family:'DM Sans',sans-serif; font-size:0.82rem; font-weight:600;
  cursor:pointer; transition:all 0.2s;
}
.section-load-more:hover { background:var(--accent); color:white; }

/* INSIGHTS */
.insights-wrap { max-width:1100px; margin:0 auto; padding:1.5rem; }
.insights-wrap h2 {
  font-family:'Source Serif 4',serif; font-size:1.6rem; font-weight:700;
  margin:2rem 0 0.5rem; border-bottom:2px solid var(--border); padding-bottom:0.5rem;
}
.insights-wrap h2:first-child { margin-top:0; }

.insight-card {
  background:var(--card); border-radius:10px; border:1px solid var(--border);
  padding:1rem 1.25rem; margin-bottom:0.75rem;
}
.insight-card .ic-title { font-size:0.88rem; font-weight:500; margin-bottom:0.3rem; line-height:1.4; }
.insight-card .ic-title a { color:inherit; text-decoration:none; }
.insight-card .ic-title a:hover { color:var(--accent); }
.insight-card .ic-meta { font-size:0.72rem; color:var(--text2); margin-bottom:0.4rem; }
.insight-card .ic-bar { display:flex; height:20px; border-radius:5px; overflow:hidden; margin-bottom:0.3rem; }
.insight-card .ic-pct { font-size:0.78rem; font-weight:700; margin-bottom:0.25rem; }
.insight-card .ic-pct.green { color:var(--a); }
.insight-card .ic-pct.red { color:var(--d); }
.insight-card .ic-archive { font-size:0.65rem; margin-top:0.3rem; }
.insight-card .ic-archive a { color:var(--text2); text-decoration:none; margin-right:0.6rem; }
.insight-card .ic-archive a:hover { color:var(--accent); text-decoration:underline; }

.summary-bars { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin:1rem 0; }
.summary-bar-card {
  background:var(--card); border-radius:10px; border:1px solid var(--border);
  padding:1.25rem; text-align:center;
}
.summary-bar-card .sb-num { font-family:'Source Serif 4',serif; font-size:2.2rem; font-weight:700; }
.summary-bar-card .sb-label { font-size:0.75rem; color:var(--text2); text-transform:uppercase; letter-spacing:0.06em; }

@media (max-width:600px) {
  .hero h1 { font-size:1.5rem; }
  .controls { padding:1rem; }
  .grid { padding:0 1rem; }
  .card { padding:1rem; }
  .card-header { flex-direction:column; gap:0.5rem; }
  .nav-tab { padding:0.6rem 1rem; font-size:0.75rem; }
  .insights-wrap { padding:1rem; }
}
</style>
</head>
<body>

<div class="nav-tabs">
  <div class="nav-tab active" data-page="polls">All Polls</div>
  <div class="nav-tab" data-page="insights">Consensus Insights</div>
</div>

<div class="page active" id="page-polls">
  <div class="hero">
    <h1>Economist Expert Consensus</h1>
    <p>Every IGM / Clark Center poll — what top economists actually think about policy</p>
    <div class="stats">
      <div class="stat"><div class="num" id="s-surveys">0</div><div class="lbl">Surveys</div></div>
      <div class="stat"><div class="num" id="s-questions">0</div><div class="lbl">Questions</div></div>
      <div class="stat"><div class="num" id="s-years">0</div><div class="lbl">Years Span</div></div>
    </div>
  </div>
  <div class="controls">
    <div class="search-box"><input type="text" id="search" placeholder="Search polls... (e.g. minimum wage, tariffs, climate)"></div>
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="US">US</button>
    <button class="filter-btn" data-filter="Europe">Europe</button>
    <button class="filter-btn" data-filter="Finance">Finance</button>
    <button class="filter-btn" data-filter="agree">✓ Agree</button>
    <button class="filter-btn" data-filter="disagree">✗ Disagree</button>
    <button class="filter-btn" data-filter="mixed">◎ Mixed</button>
    <select class="ctrl-select" id="sort-select">
      <option value="newest">Newest First</option>
      <option value="oldest">Oldest First</option>
      <option value="random">🎲 Random</option>
    </select>
    <div class="per-page-wrap">
      Show
      <select id="per-page">
        <option value="10">10</option>
        <option value="30" selected>30</option>
        <option value="50">50</option>
        <option value="100">100</option>
        <option value="9999">All</option>
      </select>
    </div>
    <div class="result-count" id="result-count"></div>
  </div>
  <div class="grid" id="grid"></div>
  <button class="load-more" id="load-more" style="display:none">Load More</button>
</div>

<div class="page" id="page-insights">
  <div class="hero" style="padding-bottom:1.5rem">
    <h1>Consensus Insights</h1>
    <p>Where economists agree most, disagree most, and remain divided</p>
  </div>
  <div class="insights-wrap" id="insights-content"></div>
</div>

<script>
const DATA = '''
        + data_json
        + r''';

function parseDate(s) {
  if (!s) return new Date(2000,0,1);
  try { return new Date(s); } catch { return new Date(2000,0,1); }
}
DATA.sort((a,b) => parseDate(b.date) - parseDate(a.date));

const totalQ = DATA.reduce((s,d)=>s+d.questions.length,0);
document.getElementById('s-surveys').textContent = DATA.length;
document.getElementById('s-questions').textContent = totalQ;
const yrs = DATA.filter(d=>d.date).map(d=>parseDate(d.date).getFullYear()).filter(y=>y>2000);
document.getElementById('s-years').textContent = yrs.length?(Math.max(...yrs)-Math.min(...yrs)+1):'?';

// NAV
document.querySelectorAll('.nav-tab').forEach(tab=>{
  tab.addEventListener('click',()=>{
    document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('page-'+tab.dataset.page).classList.add('active');
    if (tab.dataset.page==='insights'&&!insightsBuilt) buildInsights();
  });
});

// HELPERS
function archiveLinks(url) {
  const wa='https://web.archive.org/web/'+encodeURIComponent(url);
  const ai='https://archive.is/newest/'+encodeURIComponent(url);
  return `<div class="archive-links"><a href="${url}" target="_blank">Original</a><a href="${wa}" target="_blank">Web Archive</a><a href="${ai}" target="_blank">Archive.is</a></div>`;
}
function archiveLinksInline(url) {
  const wa='https://web.archive.org/web/'+encodeURIComponent(url);
  const ai='https://archive.is/newest/'+encodeURIComponent(url);
  return `<div class="ic-archive"><a href="${url}" target="_blank">Original</a><a href="${wa}" target="_blank">Web Archive</a><a href="${ai}" target="_blank">Archive.is</a></div>`;
}
function consensusTag(maj) {
  const cls={Agree:'agree',Disagree:'disagree',Uncertain:'uncertain',Mixed:'mixed'}[maj]||'mixed';
  const icon={Agree:'✓',Disagree:'✗',Uncertain:'?',Mixed:'◎'}[maj]||'?';
  return `<span class="consensus-tag consensus-${cls}">${icon} ${maj}</span>`;
}
function badgeClass(p){return{US:'badge-us',Europe:'badge-europe',Finance:'badge-finance'}[p]||'badge-us';}

function renderBar(c) {
  if(!c)return'';
  const segs=[
    {k:'sa',p:c.p_sa,l:'Str. Agree'},{k:'a',p:c.p_a,l:'Agree'},
    {k:'u',p:c.p_u,l:'Uncertain'},{k:'d',p:c.p_d,l:'Disagree'},
    {k:'sd',p:c.p_sd,l:'Str. Disagree'},{k:'no',p:c.p_no,l:'No Opinion'},
  ].filter(s=>s.p>0);
  const bar=segs.map(s=>`<div class="bar-seg ${s.k}" style="flex:${s.p}" title="${s.l}: ${s.p}%">${s.p>=8?s.p+'%':''}</div>`).join('');
  const legend=segs.map(s=>`<span class="l-${s.k}">${s.l} ${s.p}%</span>`).join('');
  return `<div class="bar-row">${bar}</div><div class="bar-legend">${legend}</div>`;
}

function shuffle(arr){const a=[...arr];for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}

// STATE
let currentFilter='all', searchTerm='', sortMode='newest', perPage=30, showCount=30;
let displayOrder=[...Array(DATA.length).keys()];

function applySort(){
  if(sortMode==='newest') displayOrder.sort((a,b)=>parseDate(DATA[b].date)-parseDate(DATA[a].date));
  else if(sortMode==='oldest') displayOrder.sort((a,b)=>parseDate(DATA[a].date)-parseDate(DATA[b].date));
  else if(sortMode==='random') displayOrder=shuffle(displayOrder);
}
applySort();

function filtered(){
  return displayOrder.map(i=>DATA[i]).filter(d=>{
    if(searchTerm){const s=searchTerm.toLowerCase();const h=(d.title+' '+d.questions.map(q=>q.text).join(' ')).toLowerCase();if(!h.includes(s))return false;}
    if(currentFilter==='all')return true;
    if(['US','Europe','Finance'].includes(currentFilter))return d.panel===currentFilter;
    if(currentFilter==='agree')return d.questions.some(q=>q.consensus&&q.consensus.maj==='Agree');
    if(currentFilter==='disagree')return d.questions.some(q=>q.consensus&&q.consensus.maj==='Disagree');
    if(currentFilter==='mixed')return d.questions.some(q=>q.consensus&&(q.consensus.maj==='Mixed'||q.consensus.maj==='Uncertain'));
    return true;
  });
}

function render(){
  const items=filtered();
  const showing=items.slice(0,showCount);
  document.getElementById('result-count').textContent=`Showing ${Math.min(showCount,items.length)} of ${items.length} polls`;
  document.getElementById('grid').innerHTML=showing.map(d=>{
    const qs=d.questions.map(q=>{
      const label=q.label?`<div class="q-label">${q.label} ${q.consensus?consensusTag(q.consensus.maj):''}</div>`:
                          (q.consensus?`<div class="q-label">${consensusTag(q.consensus.maj)}</div>`:'');
      return `<div class="question-block">${label}
        <div class="q-text">${q.text||'<em>Question text not available</em>'}</div>
        ${q.consensus?renderBar(q.consensus):''}
        ${q.consensus?`<div class="respondents">${q.consensus.total} respondents</div>`:''}
      </div>`;
    }).join('');
    return `<div class="card">
      <div class="card-header">
        <div class="card-title"><a href="${d.url}" target="_blank">${d.title}</a></div>
        <div class="card-meta"><span class="badge ${badgeClass(d.panel)}">${d.panel}</span><span class="badge-date">${d.date||''}</span></div>
      </div>
      ${archiveLinks(d.url)}
      ${qs}
    </div>`;
  }).join('');
  document.getElementById('load-more').style.display=showCount<items.length?'block':'none';
}

document.getElementById('search').addEventListener('input',e=>{searchTerm=e.target.value;showCount=perPage;render();});
document.querySelectorAll('.filter-btn').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');currentFilter=btn.dataset.filter;showCount=perPage;render();
  });
});
document.getElementById('sort-select').addEventListener('change',e=>{sortMode=e.target.value;applySort();showCount=perPage;render();});
document.getElementById('per-page').addEventListener('change',e=>{perPage=parseInt(e.target.value);showCount=perPage;render();});
document.getElementById('load-more').addEventListener('click',()=>{showCount+=perPage;render();});
render();

// ==================== INSIGHTS PAGE ====================
let insightsBuilt=false;

function buildInsights(){
  insightsBuilt=true;

  // Flatten all questions
  const allQ=[];
  DATA.forEach(d=>{
    d.questions.forEach(q=>{
      if(!q.consensus)return;
      const c=q.consensus;
      allQ.push({
        title:d.title, url:d.url, date:d.date, panel:d.panel,
        label:q.label, text:q.text, consensus:c,
        agPct:(c.p_sa||0)+(c.p_a||0),
        dgPct:(c.p_sd||0)+(c.p_d||0),
        uPct:c.p_u||0,
      });
    });
  });

  const majCounts={Agree:0,Disagree:0,Uncertain:0,Mixed:0,'N/A':0};
  allQ.forEach(q=>{majCounts[q.consensus.maj]=(majCounts[q.consensus.maj]||0)+1;});
  const panelCounts={};
  DATA.forEach(d=>{panelCounts[d.panel]=(panelCounts[d.panel]||0)+1;});

  // Sort into categories
  const topAgree=[...allQ].sort((a,b)=>b.agPct-a.agPct);
  const topDisagree=[...allQ].sort((a,b)=>b.dgPct-a.dgPct);
  const topUncertain=[...allQ].sort((a,b)=>b.uPct-a.uPct);
  const topPolarized=[...allQ].filter(q=>q.agPct>15&&q.dgPct>15)
    .sort((a,b)=>Math.abs(a.agPct-a.dgPct)-Math.abs(b.agPct-b.dgPct));

  // Per-section show counts
  const sectionState = { agree:10, disagree:10, polarized:10, uncertain:10 };

  function insightCard(q,pctText,pctClass){
    const c=q.consensus;
    const segs=[{k:'sa',p:c.p_sa},{k:'a',p:c.p_a},{k:'u',p:c.p_u},{k:'d',p:c.p_d},{k:'sd',p:c.p_sd},{k:'no',p:c.p_no}].filter(s=>s.p>0);
    const bar=segs.map(s=>`<div class="bar-seg ${s.k}" style="flex:${s.p};height:20px">${s.p>=10?s.p+'%':''}</div>`).join('');
    return `<div class="insight-card">
      <div class="ic-pct ${pctClass}">${pctText}</div>
      <div class="ic-title"><a href="${q.url}" target="_blank">${q.title}</a>${q.label?' — '+q.label:''}</div>
      <div class="ic-meta">${q.panel} · ${q.date||'Unknown date'}</div>
      <div class="q-text" style="font-size:0.82rem;margin-bottom:0.5rem">${q.text||''}</div>
      <div class="ic-bar">${bar}</div>
      ${archiveLinksInline(q.url)}
    </div>`;
  }

  function renderSection(id, items, labelFn, pctClassFn) {
    const el = document.getElementById('section-'+id);
    const btnEl = document.getElementById('btn-'+id);
    const count = sectionState[id];
    const showing = items.slice(0, count);
    el.innerHTML = showing.map(q => insightCard(q, labelFn(q), pctClassFn(q))).join('');
    if (count < items.length) {
      btnEl.style.display = 'block';
      btnEl.textContent = `Load More (${Math.min(count, items.length)} of ${items.length})`;
    } else {
      btnEl.style.display = 'none';
    }
  }

  // Build skeleton
  document.getElementById('insights-content').innerHTML = `
    <div class="summary-bars">
      <div class="summary-bar-card"><div class="sb-num" style="color:var(--a)">${majCounts.Agree}</div><div class="sb-label">Consensus Agree</div></div>
      <div class="summary-bar-card"><div class="sb-num" style="color:var(--d)">${majCounts.Disagree}</div><div class="sb-label">Consensus Disagree</div></div>
      <div class="summary-bar-card"><div class="sb-num" style="color:var(--u)">${majCounts.Uncertain}</div><div class="sb-label">Uncertain</div></div>
      <div class="summary-bar-card"><div class="sb-num" style="color:#7f8c8d">${majCounts.Mixed}</div><div class="sb-label">Mixed / Divided</div></div>
    </div>
    <div class="summary-bars">
      <div class="summary-bar-card"><div class="sb-num">${panelCounts['US']||0}</div><div class="sb-label">US Polls</div></div>
      <div class="summary-bar-card"><div class="sb-num">${panelCounts['Europe']||0}</div><div class="sb-label">Europe Polls</div></div>
      <div class="summary-bar-card"><div class="sb-num">${panelCounts['Finance']||0}</div><div class="sb-label">Finance Polls</div></div>
      <div class="summary-bar-card"><div class="sb-num">${allQ.length}</div><div class="sb-label">Total Questions</div></div>
    </div>

    <h2>🟢 Strongest Agreement</h2>
    <p style="color:var(--text2);font-size:0.85rem;margin-bottom:1rem">Questions where economists most overwhelmingly agree</p>
    <div id="section-agree"></div>
    <button class="section-load-more" id="btn-agree">Load More</button>

    <h2>🔴 Strongest Disagreement</h2>
    <p style="color:var(--text2);font-size:0.85rem;margin-bottom:1rem">Questions where economists most overwhelmingly disagree</p>
    <div id="section-disagree"></div>
    <button class="section-load-more" id="btn-disagree">Load More</button>

    <h2>⚖️ Most Polarized</h2>
    <p style="color:var(--text2);font-size:0.85rem;margin-bottom:1rem">Questions with the most even split between agreement and disagreement</p>
    <div id="section-polarized"></div>
    <button class="section-load-more" id="btn-polarized">Load More</button>

    <h2>❓ Most Uncertain</h2>
    <p style="color:var(--text2);font-size:0.85rem;margin-bottom:1rem">The hardest questions — where economists themselves don't know</p>
    <div id="section-uncertain"></div>
    <button class="section-load-more" id="btn-uncertain">Load More</button>
  `;

  // Initial render
  renderSection('agree', topAgree, q=>Math.round(q.agPct)+'% agree', ()=>'green');
  renderSection('disagree', topDisagree, q=>Math.round(q.dgPct)+'% disagree', ()=>'red');
  renderSection('polarized', topPolarized, q=>Math.round(q.agPct)+'% agree / '+Math.round(q.dgPct)+'% disagree', ()=>'');
  renderSection('uncertain', topUncertain, q=>Math.round(q.uPct)+'% uncertain', ()=>'');

  // Load more handlers
  document.getElementById('btn-agree').addEventListener('click',()=>{
    sectionState.agree+=10;
    renderSection('agree', topAgree, q=>Math.round(q.agPct)+'% agree', ()=>'green');
  });
  document.getElementById('btn-disagree').addEventListener('click',()=>{
    sectionState.disagree+=10;
    renderSection('disagree', topDisagree, q=>Math.round(q.dgPct)+'% disagree', ()=>'red');
  });
  document.getElementById('btn-polarized').addEventListener('click',()=>{
    sectionState.polarized+=10;
    renderSection('polarized', topPolarized, q=>Math.round(q.agPct)+'% agree / '+Math.round(q.dgPct)+'% disagree', ()=>'');
  });
  document.getElementById('btn-uncertain').addEventListener('click',()=>{
    sectionState.uncertain+=10;
    renderSection('uncertain', topUncertain, q=>Math.round(q.uPct)+'% uncertain', ()=>'');
  });
}
</script>
</body>
</html>'''
    )


if __name__ == '__main__':
    main()
