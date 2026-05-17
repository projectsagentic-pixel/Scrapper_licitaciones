"""
Genera dashboards autocontenidos:
- dashboards/<ejec_id>/index.html   : por ejecución, con datos embebidos (funciona desde file://)
- dashboards/index.html             : índice global con todas las ejecuciones + top agregado dedupado

Uso:
  python scripts/build_dashboard.py --ejec-id ejec_2026-05-15_002   # actualiza esa ejec + el índice global
  python scripts/build_dashboard.py --rebuild-all                   # rehace todos los HTMLs y el índice
"""
import argparse
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador licitaciones")
EJECS_DATA_DIR = ROOT / "data" / "ejecuciones"
DASH_DIR = ROOT / "dashboards"


HTML_EJEC_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__TITLE__</title>
<style>
  :root { --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --card:#161b22; --accent:#58a6ff; --good:#3fb950; --warn:#d29922; --bad:#f85149; --border:#30363d; }
  * { box-sizing: border-box; }
  body { margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:var(--bg); color:var(--fg); line-height:1.5; }
  header { padding: 20px 24px; border-bottom: 1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
  h1 { margin:0; font-size:20px; }
  h2 { font-size: 15px; margin: 24px 24px 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .meta { color: var(--muted); font-size: 13px; }
  .mode-pill { display:inline-block; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: 600; margin-left: 8px; }
  .mode-ia_en_producto { background: rgba(88,166,255,0.18); color: var(--accent); }
  .mode-no_ia_en_producto { background: rgba(63,185,80,0.18); color: var(--good); }
  .filters { display:flex; gap:8px; padding: 12px 24px; border-bottom: 1px solid var(--border); flex-wrap:wrap; align-items:center; }
  .filters input, .filters select { background: var(--card); color: var(--fg); border: 1px solid var(--border); padding: 6px 10px; border-radius: 6px; font-size: 13px; }
  .filters label { font-size: 12px; color: var(--muted); margin-right: 4px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px 16px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: middle; }
  th { background: var(--card); font-weight: 600; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  tr.lic-row { cursor: pointer; }
  tr.lic-row:hover { background: rgba(88,166,255,0.05); }
  .pill { display:inline-block; padding: 2px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
  .good { background: rgba(63,185,80,0.18); color: var(--good); }
  .warn { background: rgba(210,153,34,0.18); color: var(--warn); }
  .bad  { background: rgba(248,81,73,0.18); color: var(--bad); }
  .badge { font-size: 11px; padding: 1px 6px; border-radius: 3px; background: var(--card); border: 1px solid var(--border); margin-right: 3px; color: var(--muted); }
  .badge-PLACSP { color: var(--accent); border-color: var(--accent); }
  .badge-BOE { color: var(--warn); border-color: var(--warn); }
  .badge-AUTONOMICO { color: var(--good); border-color: var(--good); }
  .pos { color: var(--muted); font-weight: 600; min-width: 28px; text-align: right; padding-right: 8px; }
  .titulo { font-weight: 600; color: var(--fg); }
  .organo { color: var(--muted); font-size: 12px; }
  .detail { background: var(--card); padding: 16px 24px; border-bottom: 1px solid var(--border); display:none; }
  .detail.open { display: block; }
  .detail h3 { margin: 0 0 8px; font-size: 16px; }
  .detail h4 { margin: 16px 0 6px; font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .grid3 { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
  .axis { padding: 10px 14px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; }
  .axis-name { font-size: 12px; color: var(--muted); text-transform: uppercase; }
  .axis-val { font-size: 26px; font-weight: 700; }
  .axis-why { font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.4; }
  .detail a { color: var(--accent); text-decoration: none; }
  .detail a:hover { text-decoration: underline; }
  footer { padding: 12px 24px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }
  .empty { padding: 40px 24px; text-align: center; color: var(--muted); }
  code { background: var(--card); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
  .num { font-variant-numeric: tabular-nums; }
  .nav-tabs { display:flex; gap: 4px; padding: 0 24px; border-bottom: 1px solid var(--border); background: var(--card); }
  .tab { padding: 10px 16px; cursor: pointer; color: var(--muted); border-bottom: 2px solid transparent; font-size: 13px; }
  .tab.active { color: var(--fg); border-bottom-color: var(--accent); }
  .tab-pane { display: none; }
  .tab-pane.active { display: block; }
  .stat { display: inline-block; margin-right: 24px; }
  .stat-val { font-size: 24px; font-weight: 700; color: var(--fg); }
  .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .stats-row { padding: 16px 24px; border-bottom: 1px solid var(--border); }
  .alertas { margin: 0; padding-left: 16px; font-size: 13px; }
  .alertas li { margin: 2px 0; color: var(--muted); }
</style>
</head>
<body>
<header>
  <div>
    <h1>__TITLE__ <span class="mode-pill mode-__MODE__">__MODE_LABEL__</span></h1>
    <div class="meta" id="meta">__SUBTITLE__</div>
  </div>
  <div>
    <a href="../index.html" style="color:var(--accent);text-decoration:none;font-size:13px;">← Índice global</a>
  </div>
</header>

<div class="stats-row">
  <span class="stat"><div class="stat-val" id="kpi-top">0</div><div class="stat-label">Top vigente</div></span>
  <span class="stat"><div class="stat-val" id="kpi-elegibles">0</div><div class="stat-label">Elegibles</div></span>
  <span class="stat"><div class="stat-val" id="kpi-total">0</div><div class="stat-label">Items totales</div></span>
  <span class="stat"><div class="stat-val" id="kpi-dups">0</div><div class="stat-label">Duplicados</div></span>
  <span class="stat"><div class="stat-val" id="kpi-fuentes">0</div><div class="stat-label">Fuentes</div></span>
</div>

<div class="nav-tabs">
  <div class="tab active" data-tab="top">Top (score ≥ umbral)</div>
  <div class="tab" data-tab="elegibles">Todos los elegibles</div>
  <div class="tab" data-tab="no-elegibles">Descartados (referencia)</div>
  <div class="tab" data-tab="fuentes">Comparador fuentes</div>
</div>

<div class="filters">
  <label>Buscar</label><input type="text" id="f-text" placeholder="título, órgano, CPV…" />
  <label>Fuente</label><select id="f-fuente"><option value="">todas</option></select>
  <label>Score min</label><input type="number" id="f-score" min="0" max="10" step="0.1" style="width:70px" value="0" />
</div>

<div id="tab-top" class="tab-pane active">
  <table id="t-top"><thead><tr>
    <th>#</th><th>Licitación</th><th>Fuente</th><th>Presupuesto</th><th>Plazo</th><th>Score</th>
  </tr></thead><tbody></tbody></table>
</div>

<div id="tab-elegibles" class="tab-pane">
  <table id="t-elegibles"><thead><tr>
    <th>#</th><th>Licitación</th><th>Fuente</th><th>Presupuesto</th><th>Plazo</th><th>Score</th>
  </tr></thead><tbody></tbody></table>
</div>

<div id="tab-no-elegibles" class="tab-pane">
  <table id="t-no-elegibles"><thead><tr>
    <th>#</th><th>Licitación</th><th>Fuente</th><th>Presupuesto</th><th>Plazo</th><th>Motivo descarte</th>
  </tr></thead><tbody></tbody></table>
</div>

<div id="tab-fuentes" class="tab-pane">
  <h2>Aporte por fuente</h2>
  <table id="t-fuentes"><thead><tr>
    <th>Fuente</th><th class="num">Total</th><th class="num">Únicos</th><th class="num">Corroborados</th><th class="num">En top</th><th class="num">Ratio top</th><th class="num">Score medio</th><th class="num">Presup. medio top</th>
  </tr></thead><tbody></tbody></table>
  <h2>Solapamiento entre fuentes</h2>
  <table id="t-solap"><thead><tr><th>Par</th><th class="num">Items compartidos</th></tr></thead><tbody></tbody></table>
  <h2>Diagnóstico</h2>
  <ul id="diag" class="alertas" style="padding-left: 40px; font-size: 14px;"></ul>
</div>

<footer>
  Ejecución <code>__EJEC_ID__</code> · modo <code>__MODE__</code> · datos embebidos en este HTML. Generado por <code>scripts/build_dashboard.py</code>.
</footer>

<script id="data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);

function fmtEur(n) { if (n == null) return '—'; return new Intl.NumberFormat('es-ES').format(Math.round(n)) + ' €'; }
function esc(s) { if (s == null) return ''; return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }
function scoreClass(s) { return s >= 7.5 ? 'good' : s >= 5.5 ? 'warn' : 'bad'; }
function plazoClass(d) { return d == null ? '' : d < 7 ? 'bad' : d < 14 ? 'warn' : 'good'; }

document.getElementById('kpi-top').textContent = DATA.resumen.top;
document.getElementById('kpi-elegibles').textContent = DATA.resumen.elegibles;
document.getElementById('kpi-total').textContent = DATA.resumen.total;
document.getElementById('kpi-dups').textContent = DATA.resumen.duplicados;
document.getElementById('kpi-fuentes').textContent = DATA.fuentes.length;

const allItems = [...(DATA.top||[]), ...(DATA.elegibles||[]), ...(DATA.no_elegibles||[])];
const fuentesUniq = [...new Set(allItems.map(i => i.fuente))].sort();
const fsel = document.getElementById('f-fuente');
fuentesUniq.forEach(f => { const o = document.createElement('option'); o.value = f; o.textContent = f; fsel.appendChild(o); });

function filterItems(items) {
  const ft = document.getElementById('f-text').value.toLowerCase();
  const ff = document.getElementById('f-fuente').value;
  const fmin = parseFloat(document.getElementById('f-score').value) || 0;
  return items.filter(it => {
    if (ff && it.fuente !== ff) return false;
    if ((it.score || 0) < fmin && it.score != null) return false;
    if (ft) {
      const blob = [it.titulo, it.organo, it.id_oficial, (it.cpvs||[]).join(' ')].filter(Boolean).join(' ').toLowerCase();
      if (!blob.includes(ft)) return false;
    }
    return true;
  });
}

function renderItemsTable(tbodyId, items, withScore=true) {
  const tb = document.querySelector(`#${tbodyId} tbody`);
  tb.innerHTML = '';
  if (items.length === 0) { tb.innerHTML = '<tr><td colspan="6" class="empty">Sin items que mostrar.</td></tr>'; return; }
  items.forEach((it, i) => {
    const score = it.score != null ? it.score.toFixed(2) : '—';
    const cls = it.score != null ? scoreClass(it.score) : '';
    const dias = it.dias_restantes;
    const plazoTxt = dias == null ? '—' : (dias < 0 ? 'pasado' : `${dias}d`);
    const pCls = plazoClass(dias);
    const tr = document.createElement('tr');
    tr.className = 'lic-row';
    tr.innerHTML = `
      <td class="pos">${i+1}</td>
      <td>
        <div class="titulo">${esc(it.titulo || '—')}</div>
        <div class="organo">${esc(it.organo || '—')} · ${esc(it.id_oficial || '')} · CPV ${(it.cpvs||[]).join(', ') || '—'}</div>
      </td>
      <td><span class="badge badge-${it.fuente}">${it.fuente}</span>${(it.fuentes_extra||[]).map(f => `<span class="badge badge-${f}">${f}</span>`).join('')}</td>
      <td class="num">${fmtEur(it.presupuesto)}</td>
      <td><span class="pill ${pCls}">${plazoTxt}</span></td>
      <td>${withScore ? `<span class="pill ${cls}">${score}</span>` : esc(it.motivo_descarte || '—')}</td>
    `;
    const detail = document.createElement('tr');
    detail.innerHTML = `<td colspan="6" class="detail" id="d-${tbodyId}-${i}">${renderDetail(it)}</td>`;
    tr.addEventListener('click', () => document.getElementById(`d-${tbodyId}-${i}`).classList.toggle('open'));
    tb.appendChild(tr);
    tb.appendChild(detail);
  });
}

function renderDetail(it) {
  const links = [];
  if (it.url) links.push(`<a href="${esc(it.url)}" target="_blank">${esc(it.fuente)} (oficial)</a>`);
  if (it.url_placsp && it.fuente !== 'PLACSP') links.push(`<a href="${esc(it.url_placsp)}" target="_blank">PLACSP secundaria</a>`);
  if (it.url_pliego) links.push(`<a href="${esc(it.url_pliego)}" target="_blank">Pliego técnico</a>`);

  let ejesHtml = '';
  if (it.evaluacion) {
    const e = it.evaluacion;
    const utilidadLabel = DATA.modo === 'no_ia_en_producto' ? 'Utilidad IA (peso 0)' : 'Utilidad IA';
    const ejes = [
      { k:'utilidad_ia', label:utilidadLabel, val:e.scores.utilidad_ia, why:e.por_que.utilidad_ia },
      { k:'facilidad_ia', label:'Facilidad IA (construcción)', val:e.scores.facilidad_ia, why:e.por_que.facilidad_ia },
      { k:'dificultad', label:'Dificultad', val:e.scores.dificultad, why:e.por_que.dificultad },
    ];
    ejesHtml = `<h4>Scoring</h4><div class="grid3">${ejes.map(eje => `
      <div class="axis">
        <div class="axis-name">${eje.label}</div>
        <div class="axis-val">${eje.val}<span style="font-size:12px;color:var(--muted);">/10</span></div>
        <div class="axis-why">${esc(eje.why || '—')}</div>
      </div>`).join('')}</div>
      <h4>Otros ejes</h4><div class="grid3">
        <div class="axis"><div class="axis-name">Encaje perfil</div><div class="axis-val">${e.scores.encaje_perfil}/10</div></div>
        <div class="axis"><div class="axis-name">Presup. atractivo</div><div class="axis-val">${e.scores.presupuesto_atractivo.toFixed(1)}/10</div></div>
        <div class="axis"><div class="axis-name">Plazo realista</div><div class="axis-val">${e.scores.plazo_realista.toFixed(1)}/10</div></div>
      </div>`;
  } else if (it.motivo_descarte) {
    ejesHtml = `<h4>Motivo descarte</h4><p>${esc(it.motivo_descarte)}</p>`;
  }

  let iaSection = '';
  if (DATA.modo === 'no_ia_en_producto') {
    iaSection = `
      <h4>Razón sin IA en producto</h4><p>${esc(it.razon_sin_ia || '—')}</p>
      <h4>Aceleración IA en construcción</h4><p>${esc(it.aceleracion_ia_construccion || '—')}</p>`;
  } else {
    iaSection = `<h4>Componente IA potencial (producto)</h4><p>${esc(it.ia_potencial || '—')}</p>`;
  }

  return `
    <h3>${esc(it.titulo||'—')}</h3>
    <div class="meta">${esc(it.organo||'—')} · ${esc(it.lugar||'—')} · ${esc(it.id_oficial||'')} · CPV ${(it.cpvs||[]).join(', ')||'—'}</div>
    <div style="margin:8px 0">${links.join(' · ') || '<span class="meta">sin enlaces</span>'}</div>
    <h4>Datos clave</h4>
    <div class="grid3">
      <div class="axis"><div class="axis-name">Presupuesto base</div><div class="axis-val num">${fmtEur(it.presupuesto)}</div></div>
      <div class="axis"><div class="axis-name">Fecha límite</div><div class="axis-val" style="font-size:18px;">${esc(it.fecha_limite || '—')}</div></div>
      <div class="axis"><div class="axis-name">Procedimiento</div><div class="axis-val" style="font-size:16px;">${esc(it.procedimiento||'—')}</div></div>
    </div>
    ${iaSection}
    ${ejesHtml}
    <h4>Alertas y notas</h4>
    <ul class="alertas">${(it.alertas||[]).map(a => `<li>${esc(a)}</li>`).join('') || '<li>—</li>'}</ul>
    <p class="meta" style="font-size:12px;">${esc(it.notas_verificacion||'')}</p>
  `;
}

function renderFuentes() {
  const tb = document.querySelector('#t-fuentes tbody');
  tb.innerHTML = '';
  DATA.fuentes.forEach(f => {
    tb.innerHTML += `<tr>
      <td><strong>${esc(f.nombre)}</strong></td>
      <td class="num">${f.n_items_total}</td>
      <td class="num">${f.n_items_unicos}</td>
      <td class="num">${f.n_items_corroborados}</td>
      <td class="num">${f.n_en_top_actual}</td>
      <td class="num">${(f.ratio_top_sobre_total*100).toFixed(1)}%</td>
      <td class="num">${(f.score_medio_top||0).toFixed(2)}</td>
      <td class="num">${fmtEur(f.presupuesto_medio_top_eur)}</td>
    </tr>`;
  });
  const ts = document.querySelector('#t-solap tbody');
  ts.innerHTML = '';
  const sl = DATA.solapamiento || {};
  if (Object.keys(sl).length === 0) ts.innerHTML = '<tr><td colspan="2" class="empty">Sin solapamiento.</td></tr>';
  else Object.entries(sl).forEach(([k,v]) => { ts.innerHTML += `<tr><td>${esc(k.replace('_',' ↔ '))}</td><td class="num">${v}</td></tr>`; });
  const dg = document.getElementById('diag');
  dg.innerHTML = '';
  (DATA.diagnostico || []).forEach(d => dg.innerHTML += `<li>${esc(d)}</li>`);
  if ((DATA.diagnostico||[]).length === 0) dg.innerHTML = '<li class="meta">Sin diagnóstico.</li>';
}

function rerender() {
  renderItemsTable('t-top', filterItems(DATA.top), true);
  renderItemsTable('t-elegibles', filterItems(DATA.elegibles), true);
  renderItemsTable('t-no-elegibles', filterItems(DATA.no_elegibles), false);
  renderFuentes();
}

document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById(`tab-${t.dataset.tab}`).classList.add('active');
  });
});

['f-text','f-fuente','f-score'].forEach(id => document.getElementById(id).addEventListener('input', rerender));
rerender();
</script>
</body>
</html>
"""


HTML_INDEX_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>buscador licitaciones — índice global</title>
<style>
  :root { --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --card:#161b22; --accent:#58a6ff; --good:#3fb950; --warn:#d29922; --bad:#f85149; --border:#30363d; }
  * { box-sizing: border-box; }
  body { margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:var(--bg); color:var(--fg); line-height:1.5; }
  header { padding: 24px; border-bottom: 1px solid var(--border); }
  h1 { margin:0 0 6px; font-size:22px; }
  h2 { font-size: 14px; margin: 28px 24px 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .meta { color: var(--muted); font-size: 13px; }
  table { width: calc(100% - 48px); margin: 0 24px; border-collapse: collapse; }
  th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: middle; }
  th { background: var(--card); font-weight: 600; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  td a { color: var(--accent); text-decoration: none; }
  td a:hover { text-decoration: underline; }
  .pill { display:inline-block; padding: 2px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
  .good { background: rgba(63,185,80,0.18); color: var(--good); }
  .warn { background: rgba(210,153,34,0.18); color: var(--warn); }
  .bad  { background: rgba(248,81,73,0.18); color: var(--bad); }
  .badge { font-size: 11px; padding: 1px 6px; border-radius: 3px; background: var(--card); border: 1px solid var(--border); margin-right: 3px; color: var(--muted); }
  .badge-PLACSP { color: var(--accent); border-color: var(--accent); }
  .badge-BOE { color: var(--warn); border-color: var(--warn); }
  .badge-AUTONOMICO { color: var(--good); border-color: var(--good); }
  .mode-pill { display:inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .mode-ia_en_producto { background: rgba(88,166,255,0.18); color: var(--accent); }
  .mode-no_ia_en_producto { background: rgba(63,185,80,0.18); color: var(--good); }
  .num { font-variant-numeric: tabular-nums; }
  footer { padding: 16px 24px; margin-top: 24px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }
  code { background: var(--card); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
  .stat { display: inline-block; margin-right: 32px; vertical-align: top; }
  .stat-val { font-size: 28px; font-weight: 700; color: var(--fg); }
  .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .titulo { font-weight: 600; }
  .organo { color: var(--muted); font-size: 12px; }
  .filters { display:flex; gap:8px; padding: 12px 24px; flex-wrap:wrap; align-items:center; }
  .filters input, .filters select { background: var(--card); color: var(--fg); border: 1px solid var(--border); padding: 6px 10px; border-radius: 6px; font-size: 13px; }
  .filters label { font-size: 12px; color: var(--muted); margin-right: 4px; }
</style>
</head>
<body>
<header>
  <h1>buscador licitaciones — índice global</h1>
  <div class="meta">Cada ejecución es autocontenida (carpeta <code>dashboards/&lt;ejec_id&gt;/</code>). Top global agrega top de todas las ejecuciones deduplicando por id_oficial+fuente y manteniendo el mejor score.</div>
</header>

<div style="padding: 16px 24px; border-bottom: 1px solid var(--border);">
  <span class="stat"><div class="stat-val" id="k-ejec">0</div><div class="stat-label">Ejecuciones</div></span>
  <span class="stat"><div class="stat-val" id="k-hist">0</div><div class="stat-label">Items vistos (histórico)</div></span>
  <span class="stat"><div class="stat-val" id="k-top">0</div><div class="stat-label">Top global vigente</div></span>
  <span class="stat"><div class="stat-val" id="k-fuentes">0</div><div class="stat-label">Fuentes activas</div></span>
</div>

<h2>Ejecuciones</h2>
<table id="t-ejec"><thead><tr>
  <th>Ejecución</th><th>Fecha</th><th>Modo</th><th class="num">Items</th><th class="num">Elegibles</th><th class="num">Top</th><th class="num">Score medio top</th><th>Dashboard</th>
</tr></thead><tbody></tbody></table>

<h2>Top global (todas las ejecuciones, deduplicado)</h2>
<div class="filters">
  <label>Buscar</label><input type="text" id="g-text" placeholder="título, órgano…" />
  <label>Modo</label><select id="g-mode"><option value="">todos</option><option value="ia_en_producto">ia_en_producto</option><option value="no_ia_en_producto">no_ia_en_producto</option></select>
  <label>Fuente</label><select id="g-fuente"><option value="">todas</option></select>
  <label>Score min</label><input type="number" id="g-score" min="0" max="10" step="0.1" style="width:70px" value="0" />
</div>
<table id="t-global"><thead><tr>
  <th>#</th><th>Licitación</th><th>Fuente</th><th>Modo</th><th class="num">Presupuesto</th><th>Plazo</th><th class="num">Score</th><th>Ejecución</th>
</tr></thead><tbody></tbody></table>

<footer>
  Generado por <code>scripts/build_dashboard.py</code>. Funciona desde <code>file://</code>.
</footer>

<script id="data" type="application/json">__DATA_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);

function fmtEur(n) { if (n == null) return '—'; return new Intl.NumberFormat('es-ES').format(Math.round(n)) + ' €'; }
function esc(s) { if (s == null) return ''; return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c])); }
function scoreClass(s) { return s >= 7.5 ? 'good' : s >= 5.5 ? 'warn' : 'bad'; }

document.getElementById('k-ejec').textContent = DATA.ejecuciones.length;
document.getElementById('k-hist').textContent = DATA.total_historial;
document.getElementById('k-top').textContent = DATA.top_global.length;
document.getElementById('k-fuentes').textContent = DATA.fuentes_activas;

const te = document.querySelector('#t-ejec tbody');
DATA.ejecuciones.forEach(e => {
  te.innerHTML += `<tr>
    <td><strong>${esc(e.id)}</strong></td>
    <td>${esc(e.fecha)}</td>
    <td><span class="mode-pill mode-${e.modo}">${esc(e.modo)}</span></td>
    <td class="num">${e.items_totales}</td>
    <td class="num">${e.elegibles}</td>
    <td class="num">${e.top}</td>
    <td class="num">${e.score_medio_top != null ? e.score_medio_top.toFixed(2) : '—'}</td>
    <td><a href="${esc(e.id)}/index.html">abrir →</a></td>
  </tr>`;
});

const fuentesUniq = [...new Set(DATA.top_global.map(x => x.fuente))].sort();
const gfsel = document.getElementById('g-fuente');
fuentesUniq.forEach(f => { const o = document.createElement('option'); o.value = f; o.textContent = f; gfsel.appendChild(o); });

function renderGlobal() {
  const ft = document.getElementById('g-text').value.toLowerCase();
  const fm = document.getElementById('g-mode').value;
  const ff = document.getElementById('g-fuente').value;
  const fmin = parseFloat(document.getElementById('g-score').value) || 0;
  const items = DATA.top_global.filter(it => {
    if (fm && it.modo !== fm) return false;
    if (ff && it.fuente !== ff) return false;
    if ((it.score || 0) < fmin) return false;
    if (ft) {
      const blob = [it.titulo, it.organo, it.id_oficial].filter(Boolean).join(' ').toLowerCase();
      if (!blob.includes(ft)) return false;
    }
    return true;
  });
  const tg = document.querySelector('#t-global tbody');
  tg.innerHTML = '';
  if (items.length === 0) { tg.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:40px;">Sin items.</td></tr>'; return; }
  items.forEach((it, i) => {
    tg.innerHTML += `<tr>
      <td>${i+1}</td>
      <td>
        <div class="titulo">${esc(it.titulo)}</div>
        <div class="organo">${esc(it.organo || '—')} · ${esc(it.id_oficial || '')}</div>
      </td>
      <td><span class="badge badge-${it.fuente}">${it.fuente}</span></td>
      <td><span class="mode-pill mode-${it.modo}">${esc(it.modo)}</span></td>
      <td class="num">${fmtEur(it.presupuesto)}</td>
      <td>${it.fecha_limite || '—'}</td>
      <td class="num"><span class="pill ${scoreClass(it.score)}">${it.score.toFixed(2)}</span></td>
      <td><a href="${esc(it.ejecucion_id)}/index.html">${esc(it.ejecucion_id)}</a></td>
    </tr>`;
  });
}

['g-text','g-mode','g-fuente','g-score'].forEach(id => document.getElementById(id).addEventListener('input', renderGlobal));
renderGlobal();
</script>
</body>
</html>
"""

MODE_LABELS = {
    "ia_en_producto": "IA en el producto",
    "no_ia_en_producto": "Sin IA en producto (IA solo construcción)",
}


def to_view(it, motivos=None):
    e = it.get("evaluacion")
    view = {
        "id_oficial": it["id_oficial"],
        "titulo": (it["objeto"] or "")[:200],
        "organo": it["organo_contratacion"],
        "fuente": it["fuente"],
        "fuentes_extra": (["PLACSP"] if it.get("solapamiento_placsp") and it["fuente"] != "PLACSP" else [])
                        + (["BOE"] if it.get("solapamiento_boe") and it["fuente"] != "BOE" else []),
        "presupuesto": it["presupuesto_base_eur"],
        "dias_restantes": it["dias_restantes_presentacion"],
        "fecha_limite": it["fecha_limite_presentacion"],
        "procedimiento": it.get("tipo_procedimiento"),
        "lugar": it.get("lugar_ejecucion"),
        "url": it["url_oficial"],
        "url_placsp": it.get("url_secundaria_placsp"),
        "url_pliego": it.get("url_pliego_tecnico"),
        "cpvs": [it["cpv_principal"]] + (it.get("cpv_secundarios") or []),
        "ia_potencial": it.get("componente_ia_potencial"),
        "razon_sin_ia": it.get("razon_sin_ia"),
        "aceleracion_ia_construccion": it.get("aceleracion_ia_construccion"),
        "alertas": it.get("alertas", []),
        "notas_verificacion": it.get("notas_verificacion"),
        "score": e["score_total"] if e else None,
        "evaluacion": e,
        "motivo_descarte": ", ".join(motivos) if motivos else None,
    }
    return view


def build_ejecucion_html(ejec_id):
    ejec_dir = EJECS_DATA_DIR / ejec_id
    ev = json.loads((ejec_dir / "evaluado.json").read_text(encoding="utf-8"))
    metricas = json.loads((ejec_dir / "metricas_fuentes.json").read_text(encoding="utf-8"))

    items_all = ev["items"]
    elegibles = [it for it in items_all if it["elegible_para_scoring"]]
    no_elegibles = [it for it in items_all if not it["elegible_para_scoring"]]
    top = [it for it in elegibles if it.get("pasa_umbral_top")]
    elegibles.sort(key=lambda x: (x.get("evaluacion") or {}).get("score_total", 0), reverse=True)
    top.sort(key=lambda x: x["evaluacion"]["score_total"], reverse=True)

    mode = ev.get("modo", "ia_en_producto")
    data = {
        "ejec_id": ejec_id,
        "modo": mode,
        "fecha": ev["fecha_consolidacion"],
        "resumen": {
            "total": ev["totales"]["items_tras_dedup"],
            "duplicados": ev["totales"]["duplicados_eliminados"],
            "elegibles": ev["totales"]["elegibles_para_scoring"],
            "top": ev["resumen_scoring"]["items_pasan_umbral"],
        },
        "top": [to_view(it) for it in top],
        "elegibles": [to_view(it) for it in elegibles],
        "no_elegibles": [to_view(it, motivos=it.get("motivos_no_elegible")) for it in no_elegibles],
        "fuentes": metricas["fuentes"],
        "solapamiento": metricas["solapamiento"],
        "diagnostico": metricas["diagnostico"],
    }

    data_json = json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>")
    html = (HTML_EJEC_TEMPLATE
            .replace("__TITLE__", f"Búsqueda {ejec_id}")
            .replace("__SUBTITLE__", f"{ev['fecha_consolidacion']} · {ev['totales']['items_tras_dedup']} items · {ev['resumen_scoring']['items_pasan_umbral']} en top")
            .replace("__EJEC_ID__", ejec_id)
            .replace("__MODE__", mode)
            .replace("__MODE_LABEL__", MODE_LABELS.get(mode, mode))
            .replace("__DATA_JSON__", data_json))

    out_dir = DASH_DIR / ejec_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


def build_index():
    log = json.loads((ROOT / "data" / "ejecuciones.json").read_text(encoding="utf-8"))
    historial = json.loads((ROOT / "data" / "historial_analizados.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "data" / "config.json").read_text(encoding="utf-8"))

    ejecs = []
    for e in log.get("ejecuciones", []):
        score_medio = (sum(t["score"] for t in e.get("items_top", [])) / len(e["items_top"])
                       if e.get("items_top") else None)
        ejecs.append({
            "id": e["id"],
            "fecha": e["fecha"],
            "modo": e.get("modo", "ia_en_producto"),
            "items_totales": e["totales"]["items_tras_dedup"],
            "elegibles": e["totales"]["elegibles_para_scoring"],
            "top": e.get("resumen_scoring", {}).get("items_pasan_umbral", 0),
            "score_medio_top": score_medio,
        })

    # Top global: cross-ejec dedup por (fuente,id_oficial), nos quedamos con el mejor score
    top_global_map = {}
    for e in log.get("ejecuciones", []):
        for t in e.get("items_top", []):
            key = f"{t['fuente']}:{t['id_oficial']}"
            hist_entry = None
            for hv in historial.get("items", {}).values():
                if hv.get("id_oficial") == t["id_oficial"] and hv.get("fuente") == t["fuente"]:
                    hist_entry = hv
                    break
            entry = {
                "ejecucion_id": e["id"],
                "modo": e.get("modo", "ia_en_producto"),
                "id_oficial": t["id_oficial"],
                "fuente": t["fuente"],
                "titulo": t["objeto"],
                "score": t["score"],
                "organo": hist_entry["organo"] if hist_entry else None,
                "presupuesto": hist_entry["presupuesto_eur"] if hist_entry else None,
                "fecha_limite": hist_entry["fecha_limite_presentacion"] if hist_entry else None,
            }
            if key not in top_global_map or entry["score"] > top_global_map[key]["score"]:
                top_global_map[key] = entry

    top_global = sorted(top_global_map.values(), key=lambda x: x["score"], reverse=True)
    fuentes_activas = sum(1 for f in config.get("fuentes_activas", []) if f.get("habilitada"))

    data = {
        "ejecuciones": ejecs,
        "total_historial": historial["total"],
        "top_global": top_global,
        "fuentes_activas": fuentes_activas,
    }
    data_json = json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>")
    html = HTML_INDEX_TEMPLATE.replace("__DATA_JSON__", data_json)
    out = DASH_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejec-id", help="Ejecución concreta a generar.")
    ap.add_argument("--rebuild-all", action="store_true", help="Rehacer todos los HTMLs.")
    args = ap.parse_args()

    if args.rebuild_all:
        for d in sorted(EJECS_DATA_DIR.iterdir()):
            if d.is_dir() and (d / "evaluado.json").exists():
                p = build_ejecucion_html(d.name)
                print(f"  {p}")
    elif args.ejec_id:
        p = build_ejecucion_html(args.ejec_id)
        print(f"  {p}")

    idx = build_index()
    print(f"Índice: {idx}")


if __name__ == "__main__":
    main()
