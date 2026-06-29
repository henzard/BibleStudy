#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-contained HTML dashboard for the early-warning pipeline.

One template, two render modes — no build step, no CDN, works offline:

* :func:`render_html` bakes a ``PipelineResult.to_dict()`` payload into the page
  so the file opens directly in a browser (shareable snapshot).
* :func:`render_shell` leaves the data ``null`` so the page fetches
  ``latest.json`` from its own directory (a live dashboard when served).

All CSS/JS is inline; the only data dependency is the JSON the pipeline already
emits. A file-picker fallback lets the shell work even from ``file://``.
"""

from __future__ import annotations

import json
from typing import Any, Dict

# The literal token below is replaced with embedded JSON by render_html.
# In render_shell it is left as `null`, triggering the fetch() path.
_DATA_TOKEN = "/*__DATA__*/null"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prophecy Early-Warning Dashboard</title>
<style>
  :root {
    --bg: #0b1020; --panel: #141b2e; --panel2: #1b2540; --line: #2a3756;
    --txt: #e6ecff; --muted: #8a98bd; --accent: #5b8cff;
    --green: #2fbf71; --yellow: #e7c14a; --orange: #f08a3c; --red: #ef4d5a;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: radial-gradient(1200px 600px at 70% -10%, #16204a 0%, var(--bg) 55%);
    color: var(--txt); font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    min-height: 100vh;
  }
  a { color: var(--accent); }
  header {
    position: sticky; top: 0; z-index: 5; backdrop-filter: blur(8px);
    background: rgba(11,16,32,.78); border-bottom: 1px solid var(--line);
    padding: 14px 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  }
  header .brand { font-weight: 700; font-size: 18px; letter-spacing: .2px; }
  header .brand .dot { color: var(--accent); }
  header .meta { color: var(--muted); font-size: 13px; }
  header .spacer { flex: 1; }
  .pill { padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 600;
    border: 1px solid var(--line); white-space: nowrap; }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 24px; }
  .grid { display: grid; gap: 18px; }
  .cards-3 { grid-template-columns: 320px 1fr; }
  @media (max-width: 820px){ .cards-3 { grid-template-columns: 1fr; } }
  .panel { background: linear-gradient(180deg, var(--panel) 0%, var(--panel2) 100%);
    border: 1px solid var(--line); border-radius: 16px; padding: 20px; }
  .panel h2 { margin: 0 0 14px; font-size: 13px; text-transform: uppercase;
    letter-spacing: 1.2px; color: var(--muted); font-weight: 700; }
  .gauge-card { display: flex; flex-direction: column; align-items: center; text-align: center; }
  .gauge { --pct: 0; --col: var(--green); width: 190px; height: 190px; border-radius: 50%;
    background: conic-gradient(var(--col) calc(var(--pct) * 1%), #222c46 0);
    display: grid; place-items: center; position: relative; margin: 6px 0 12px; }
  .gauge::before { content: ""; position: absolute; inset: 16px; border-radius: 50%;
    background: var(--panel2); border: 1px solid var(--line); }
  .gauge .val { position: relative; font-size: 44px; font-weight: 800; line-height: 1; }
  .gauge .val small { font-size: 16px; color: var(--muted); font-weight: 600; }
  .phase { font-size: 18px; font-weight: 700; margin-top: 2px; }
  .phase .emoji { margin-right: 6px; }
  .note { color: var(--muted); font-size: 13px; margin-top: 4px; }
  .summary { font-size: 16px; line-height: 1.65; }
  .stat-row { display: flex; gap: 22px; margin-top: 16px; flex-wrap: wrap; }
  .stat { background: #0e1426; border: 1px solid var(--line); border-radius: 12px;
    padding: 12px 16px; min-width: 110px; }
  .stat .n { font-size: 24px; font-weight: 800; }
  .stat .l { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .6px; }
  .nodes { grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
  .node { background: #0e1426; border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px; }
  .node .top { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .node .id { font-weight: 800; font-size: 15px; }
  .node .lab { color: var(--muted); font-size: 12px; }
  .node .pct { font-weight: 800; font-size: 18px; }
  .bar { height: 8px; border-radius: 6px; background: #222c46; margin: 10px 0 8px; overflow: hidden; }
  .bar > span { display: block; height: 100%; border-radius: 6px; }
  .node .foot { display: flex; justify-content: space-between; align-items: center;
    font-size: 12px; color: var(--muted); }
  .scripture { color: var(--muted); font-size: 12px; font-style: italic; margin-top: 6px; }
  .findings { grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); }
  .finding { background: #0e1426; border: 1px solid var(--line); border-radius: 14px; padding: 16px;
    border-left: 4px solid var(--line); }
  .finding h3 { margin: 0 0 4px; font-size: 16px; text-transform: capitalize; }
  .badges { display: flex; gap: 7px; margin: 8px 0 10px; flex-wrap: wrap; }
  .finding p { margin: 0 0 10px; color: #cdd6f4; font-size: 14px; }
  .facts { margin: 0; padding-left: 18px; color: var(--muted); font-size: 13px; }
  .facts li { margin: 3px 0; }
  .tags { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; }
  .tag { font-size: 11px; color: var(--accent); border: 1px solid var(--line);
    border-radius: 6px; padding: 1px 7px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--line); }
  th { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .6px; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .spark { display: block; }
  .guardrails { color: var(--muted); font-size: 13px; }
  .guardrails li { margin: 6px 0; }
  footer { text-align: center; color: var(--muted); font-size: 12px; padding: 30px 24px 50px; }
  .empty { text-align: center; color: var(--muted); padding: 60px 20px; }
  .filebtn { display: inline-block; margin-top: 14px; padding: 9px 16px; border-radius: 10px;
    border: 1px solid var(--line); background: var(--panel2); color: var(--txt); cursor: pointer; }
  .section-title { margin: 8px 2px 2px; font-size: 13px; text-transform: uppercase;
    letter-spacing: 1.2px; color: var(--muted); font-weight: 700; }
</style>
</head>
<body>
<header>
  <div class="brand"><span class="dot">●</span> Prophecy Early-Warning</div>
  <div class="meta" id="meta"></div>
  <div class="spacer"></div>
  <div class="pill" id="phasePill" style="display:none"></div>
  <div class="pill" id="backendPill" style="display:none"></div>
</header>
<div class="wrap" id="app">
  <div class="empty" id="empty">
    <div style="font-size:42px">🛰️</div>
    <h2 style="text-transform:none;color:var(--txt)">No report loaded</h2>
    <p>Run <code>python scripts/run_pipeline.py</code> to generate
       <code>latest.json</code>, then serve this folder
       (<code>python scripts/serve_dashboard.py</code>).</p>
    <label class="filebtn">Load a report JSON…
      <input id="file" type="file" accept="application/json" style="display:none">
    </label>
  </div>
</div>
<footer>
  Bible-only watch tooling — pattern, not prediction. “Of that day and hour
  knoweth no man” (Matt 24:36).
</footer>

<script>
const EMBEDDED = /*__DATA__*/null;

function colorFor(pct){
  if (pct >= 70) return getCss('--red');
  if (pct >= 50) return getCss('--orange');
  if (pct >= 30) return getCss('--yellow');
  return getCss('--green');
}
function getCss(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

const ESC_COLOR = { escalating:'--red', steady:'--yellow', easing:'--green', unknown:'--muted', flat:'--muted' };
const CONF_COLOR = { High:'--green', Med:'--yellow', Low:'--muted' };

function badge(text, cssVar){
  const c = getCss(cssVar);
  return `<span class="pill" style="border-color:${c};color:${c}">${esc(text)}</span>`;
}

function sparkline(series){
  if (!series || series.length < 2) return '';
  const w = 90, h = 26, max = Math.max(...series, 1), min = Math.min(...series, 0);
  const span = (max - min) || 1;
  const pts = series.map((v, i) => {
    const x = (i / (series.length - 1)) * (w - 4) + 2;
    const y = h - 2 - ((v - min) / span) * (h - 4);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const last = series[series.length-1], prev = series.length>1 ? series[series.length-2] : last;
  const col = last >= prev ? getCss('--orange') : getCss('--green');
  return `<svg class="spark" width="${w}" height="${h}"><polyline fill="none" stroke="${col}"
    stroke-width="2" points="${pts}"/></svg>`;
}

function render(d){
  document.getElementById('empty').style.display = 'none';
  const t = d.threat || {};
  const day = (d.generated_at || '').split(' ')[0];
  document.getElementById('meta').textContent =
    `${d.report_title || 'Report'} · ${d.generated_at || ''}`;
  const phasePill = document.getElementById('phasePill');
  phasePill.style.display = 'inline-block';
  phasePill.textContent = `${t.emoji || ''} ${t.phase || ''}`.trim();
  phasePill.style.borderColor = colorFor(t.overall_intensity || 0);
  phasePill.style.color = colorFor(t.overall_intensity || 0);
  const backend = (d.findings && d.findings[0] && d.findings[0].source_backend) || '';
  if (backend){
    const bp = document.getElementById('backendPill');
    bp.style.display = 'inline-block';
    bp.textContent = 'LLM: ' + backend;
  }

  const app = document.getElementById('app');
  app.innerHTML = '';

  // Top row: gauge + summary
  const pct = Math.round(t.overall_intensity || 0);
  const col = colorFor(pct);
  const top = el('div', 'grid cards-3');
  top.innerHTML = `
    <div class="panel gauge-card">
      <h2>Pattern Strength</h2>
      <div class="gauge" style="--pct:${pct};--col:${col}">
        <div class="val">${pct}<small>/100</small></div>
      </div>
      <div class="phase"><span class="emoji">${t.emoji||''}</span>${esc(t.phase||'')}</div>
      <div class="note">${esc(t.note||'')}</div>
    </div>
    <div class="panel">
      <h2>Executive Summary</h2>
      <div class="summary">${esc(d.report_summary || t.note || '')}</div>
      <div class="stat-row">
        <div class="stat"><div class="n">${d.event_count ?? '—'}</div><div class="l">Events</div></div>
        <div class="stat"><div class="n">${d.cluster_count ?? '—'}</div><div class="l">Clusters</div></div>
        <div class="stat"><div class="n">${(d.findings||[]).length}</div><div class="l">Domains</div></div>
        <div class="stat"><div class="n">${activeNodes(t)}</div><div class="l">Active nodes</div></div>
      </div>
    </div>`;
  app.appendChild(top);

  // Nodes
  app.appendChild(sectionTitle('Prophecy Nodes'));
  const nodes = el('div', 'grid nodes');
  (t.nodes || []).forEach(n => {
    const np = Math.round(n.intensity || 0);
    const nc = colorFor(np);
    const sources = (t.cross_validation && t.cross_validation[n.node_id]) || 0;
    nodes.appendChild(html(`
      <div class="node">
        <div class="top">
          <div><span class="id">${esc(n.node_id)}</span> <span class="lab">${esc(n.label)}</span></div>
          <div class="pct" style="color:${nc}">${np}</div>
        </div>
        <div class="bar"><span style="width:${np}%;background:${nc}"></span></div>
        <div class="foot">
          <span>${badge(n.confidence, CONF_COLOR[n.confidence]||'--muted')}</span>
          <span>${sources} src · ${esc(n.description||'')}</span>
        </div>
        <div class="scripture">${esc(n.scripture||'')}</div>
      </div>`));
  });
  app.appendChild(nodes);

  // Findings
  const findings = d.findings || [];
  if (findings.length){
    app.appendChild(sectionTitle('Specialist Findings'));
    const fg = el('div', 'grid findings');
    findings.forEach(f => {
      const ec = getCss(ESC_COLOR[f.escalation] || '--muted');
      const facts = (f.key_facts||[]).map(x => `<li>${esc(x)}</li>`).join('');
      const tags = (f.node_ids||[]).map(x => `<span class="tag">${esc(x)}</span>`).join('');
      fg.appendChild(html(`
        <div class="finding" style="border-left-color:${ec}">
          <h3>${esc(f.domain)}</h3>
          <div class="badges">
            ${badge(f.escalation, ESC_COLOR[f.escalation]||'--muted')}
            ${badge('confidence ' + f.confidence, CONF_COLOR[f.confidence]||'--muted')}
          </div>
          <p>${esc(f.assessment)}</p>
          <ul class="facts">${facts}</ul>
          <div class="tags">${tags}</div>
        </div>`));
    });
    app.appendChild(fg);
  }

  // Trends
  const tr = d.trends || {};
  if (tr.available && tr.metrics){
    app.appendChild(sectionTitle('Trend Memory'));
    const rows = Object.entries(tr.metrics).filter(([,m]) => m && m.available).map(([name, m]) => {
      const dirCol = getCss(ESC_COLOR[m.direction] || '--muted');
      const arrow = m.direction === 'escalating' ? '▲' : (m.direction === 'easing' ? '▼' : '▬');
      return `<tr>
        <td>${esc(name)}</td>
        <td class="num">${m.recent_week}</td>
        <td class="num">${m.baseline_avg}</td>
        <td class="num" style="color:${dirCol}">${m.acceleration_pct>0?'+':''}${m.acceleration_pct}%</td>
        <td style="color:${dirCol}">${arrow} ${esc(m.direction)}</td>
        <td>${sparkline(m.weekly_series)}</td>
      </tr>`;
    }).join('');
    const panel = el('div', 'panel');
    panel.innerHTML = `<h2>${esc(tr.summary||'')}</h2>
      <table><thead><tr><th>Metric</th><th class="num">Recent</th><th class="num">Baseline</th>
      <th class="num">Δ</th><th>Direction</th><th>Trend</th></tr></thead><tbody>${rows}</tbody></table>`;
    app.appendChild(panel);
  }

  // Guardrails
  app.appendChild(sectionTitle('Interpretation Guardrails'));
  const g = el('div', 'panel');
  g.innerHTML = `<ul class="guardrails">
    <li><b>No date-setting (Matt 24:36).</b> This measures pattern, not timing.</li>
    <li><b>Pattern ≠ fulfilment.</b> High intensity means <i>resembles</i> the description.</li>
    <li><b>Cross-verify.</b> High confidence requires multiple independent sources.</li>
    <li><b>Watchfulness, not fear (Luke 21:28).</b> For readiness and hope.</li>
  </ul>`;
  app.appendChild(g);
}

function activeNodes(t){ return (t.nodes||[]).filter(n => (n.intensity||0) > 0).length; }
function el(tag, cls){ const e = document.createElement(tag); if (cls) e.className = cls; return e; }
function html(s){ const t = document.createElement('template'); t.innerHTML = s.trim(); return t.content.firstChild; }
function sectionTitle(txt){ const e = el('div','section-title'); e.textContent = txt; return e; }

async function boot(){
  let data = EMBEDDED;
  if (!data){
    try { const r = await fetch('latest.json', {cache:'no-store'}); if (r.ok) data = await r.json(); }
    catch(e){ /* file:// or missing — fall back to picker */ }
  }
  if (data) render(data);
}
document.getElementById('file').addEventListener('change', ev => {
  const f = ev.target.files[0]; if (!f) return;
  const rd = new FileReader();
  rd.onload = () => { try { render(JSON.parse(rd.result)); } catch(e){ alert('Invalid JSON'); } };
  rd.readAsText(f);
});
boot();
</script>
</body>
</html>
"""


def render_html(data: Dict[str, Any]) -> str:
    """Return a self-contained dashboard page with ``data`` embedded."""
    payload = json.dumps(data, ensure_ascii=False)
    return TEMPLATE.replace(_DATA_TOKEN, payload)


def render_shell() -> str:
    """Return the dashboard page that fetches ``latest.json`` at load time."""
    return TEMPLATE
