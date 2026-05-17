"""
Genera dashboards/dashboard.html — autocontenido, vanilla JS, vanilla CSS.

Implementa todo lo descrito en .claude/skills/lic-dashboard/SKILL.md:
- Score destacado por item + desglose por factor
- Sección "Memoria de empresa" (taglines + prompts)
- Filtros (score, tipo_objeto, lugar_prestacion, fuente, presupuesto, plazo, feedback, texto libre)
- Tabla rankeada con like/dislike/⭐ inline
- Ficha expandible: detalle + email previo + carta inicial + comentarios
- localStorage para feedback con export/import JSON
- Plantillas de prompts (copiar)
"""
import json
import os
import html
from pathlib import Path
from datetime import datetime

ROOT = Path(r"C:/Users/JosebaPortasAbalde/Documents/DEV personal/buscador licitaciones")
EJEC_ID = "ejec_2026-05-16_001"

with open(ROOT / "data" / "seleccionados.json", "r", encoding="utf-8") as f:
    SEL = json.load(f)
with open(ROOT / "data" / "criterios.json", "r", encoding="utf-8") as f:
    CRIT = json.load(f)
with open(ROOT / "data" / "config.json", "r", encoding="utf-8") as f:
    CFG = json.load(f)
with open(ROOT / "data" / "perfil_empresa.json", "r", encoding="utf-8") as f:
    PERFIL = json.load(f)
with open(ROOT / "data" / "historial_analizados.json", "r", encoding="utf-8") as f:
    HIST = json.load(f)


def safe_text(v, default=""):
    if v is None:
        return default
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v).encode("latin-1", errors="ignore").decode("latin-1", errors="ignore")


# Datos serializados al JS
data_para_js = {
    "ejecucion_id": EJEC_ID,
    "fecha_generacion": datetime.now().isoformat(timespec="seconds"),
    "version_criterios": CRIT["version"],
    "modo_busqueda": CFG.get("modo_busqueda", "mixto"),
    "umbral_top": CRIT["umbral_top"],
    "factores": CRIT["factores"],
    "total_analizados": HIST.get("total", 0),
    "top": SEL.get("top_actual", []),
    "fuera_del_top": SEL.get("fuera_del_top", []),
    "descartados": SEL.get("descartados", []),
    "perfil_empresa": PERFIL,
}

DATA_JSON = json.dumps(data_para_js, ensure_ascii=False, indent=2)

# Construye HTML monolítico
HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buscador Licitaciones — Top vigente — v__VERSION_CRIT__</title>
<style>
* { box-sizing: border-box; }
:root {
  --bg: #0d1117;
  --bg-elev: #161b22;
  --bg-row: #1c2128;
  --bg-row-hover: #262d36;
  --fg: #e6edf3;
  --fg-muted: #8b949e;
  --border: #30363d;
  --accent: #58a6ff;
  --green: #3fb950;
  --yellow: #d29922;
  --orange: #db8a4a;
  --red: #f85149;
  --like: #3fb950;
  --dislike: #f85149;
  --star: #f0c419;
}
body {
  margin: 0; padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--fg);
  font-size: 14px; line-height: 1.5;
}
.container { max-width: 1600px; margin: 0 auto; padding: 16px 24px; }
header { border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 16px; }
header h1 { margin: 0 0 4px 0; font-size: 22px; }
.meta { color: var(--fg-muted); font-size: 13px; display: flex; gap: 16px; flex-wrap: wrap; }
.meta span.pill {
  background: var(--bg-elev); border: 1px solid var(--border);
  padding: 2px 10px; border-radius: 12px; color: var(--fg);
}
.banner-fb {
  background: rgba(88,166,255,0.08); border: 1px solid rgba(88,166,255,0.3);
  padding: 10px 14px; border-radius: 6px; margin: 12px 0;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.banner-fb .info { font-size: 13px; color: var(--fg-muted); }
button {
  background: var(--bg-elev); color: var(--fg); border: 1px solid var(--border);
  padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px;
  transition: background 0.15s, border-color 0.15s;
}
button:hover { background: var(--bg-row-hover); border-color: var(--accent); }
button.primary { background: var(--accent); color: white; border-color: var(--accent); }
button.primary:hover { background: #4493f8; }
details {
  background: var(--bg-elev); border: 1px solid var(--border); border-radius: 8px;
  margin-bottom: 16px; padding: 0;
}
details > summary {
  padding: 14px 18px; cursor: pointer; font-weight: 600;
  list-style: none; display: flex; justify-content: space-between; align-items: center;
}
details > summary::-webkit-details-marker { display: none; }
details > summary::after { content: "▼"; font-size: 11px; color: var(--fg-muted); transition: transform 0.2s; }
details[open] > summary::after { transform: rotate(180deg); }
.detail-body { padding: 0 18px 16px 18px; }
.taglines { list-style: none; padding: 0; margin: 8px 0; }
.taglines li {
  background: var(--bg-row); padding: 8px 12px; border-radius: 4px; margin-bottom: 6px;
  border-left: 3px solid var(--accent);
}
.prompt-block {
  background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
  padding: 10px 12px; font-family: 'Consolas', 'Monaco', monospace; font-size: 12px;
  white-space: pre-wrap; margin: 8px 0; max-height: 360px; overflow-y: auto;
}
.filtros {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px; margin-bottom: 16px;
}
.filtros input, .filtros select {
  background: var(--bg-elev); border: 1px solid var(--border); color: var(--fg);
  padding: 7px 10px; border-radius: 6px; font-size: 13px; width: 100%;
}
.filtros input::placeholder { color: var(--fg-muted); }
.tabla {
  width: 100%; border-collapse: collapse; background: var(--bg-elev);
  border-radius: 8px; overflow: hidden; margin-bottom: 16px;
}
.tabla th, .tabla td {
  padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border);
  font-size: 13px; vertical-align: middle;
}
.tabla th { background: var(--bg); color: var(--fg-muted); font-weight: 600; cursor: pointer; user-select: none; }
.tabla th:hover { color: var(--fg); }
.tabla tr.row-item { cursor: pointer; transition: background 0.1s; }
.tabla tr.row-item:hover { background: var(--bg-row-hover); }
.tabla tr.row-favorito { background: rgba(240,196,25,0.05); }
.tabla tr.row-like { background: rgba(63,185,80,0.04); }
.tabla tr.row-dislike { opacity: 0.5; }
.score-badge {
  display: inline-block; min-width: 44px; padding: 4px 8px; border-radius: 6px;
  font-weight: 700; text-align: center; font-size: 14px;
}
.score-low { background: rgba(248,81,73,0.2); color: #ff8a85; border: 1px solid rgba(248,81,73,0.4); }
.score-mid { background: rgba(210,153,34,0.2); color: #f1c454; border: 1px solid rgba(210,153,34,0.4); }
.score-high { background: rgba(63,185,80,0.2); color: #56d364; border: 1px solid rgba(63,185,80,0.4); }
.score-top { background: linear-gradient(135deg, #3fb950, #58a6ff); color: white; }
.fb-buttons { display: flex; gap: 4px; }
.fb-buttons button {
  padding: 3px 8px; font-size: 14px; line-height: 1;
  background: var(--bg-row); border: 1px solid var(--border);
}
.fb-buttons button.active.like { background: rgba(63,185,80,0.3); border-color: var(--like); }
.fb-buttons button.active.dislike { background: rgba(248,81,73,0.3); border-color: var(--dislike); }
.fb-buttons button.active.fav { background: rgba(240,196,25,0.3); border-color: var(--star); }
.title-cell { max-width: 380px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.title-cell .descripcion-mini { color: var(--fg-muted); font-size: 11px; }
.chip {
  display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px;
  background: var(--bg-row); border: 1px solid var(--border); margin-right: 3px;
}
.chip-entregable { background: rgba(63,185,80,0.15); color: #56d364; border-color: rgba(63,185,80,0.4); }
.chip-mixto { background: rgba(210,153,34,0.15); color: #f1c454; border-color: rgba(210,153,34,0.4); }
.chip-indeterminado { background: rgba(139,148,158,0.15); color: var(--fg-muted); }
.chip-horas { background: rgba(248,81,73,0.15); color: #ff8a85; border-color: rgba(248,81,73,0.4); }
.chip-remoto { background: rgba(63,185,80,0.15); color: #56d364; border-color: rgba(63,185,80,0.4); }
.chip-presencial { background: rgba(248,81,73,0.15); color: #ff8a85; border-color: rgba(248,81,73,0.4); }
.chip-infra-cliente { background: rgba(219,138,74,0.15); color: #f0a875; border-color: rgba(219,138,74,0.4); }
.chip-legacy { background: rgba(139,148,158,0.2); color: var(--fg-muted); }

/* Ficha expandible */
.ficha-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 1000;
  display: none; justify-content: center; align-items: flex-start; padding: 40px 20px; overflow-y: auto;
}
.ficha-overlay.open { display: flex; }
.ficha {
  background: var(--bg-elev); border: 1px solid var(--border); border-radius: 12px;
  max-width: 1100px; width: 100%; padding: 28px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.ficha header { border-bottom: 1px solid var(--border); padding-bottom: 14px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.ficha h2 { margin: 0; font-size: 18px; line-height: 1.3; }
.ficha .close-btn { background: transparent; border: none; color: var(--fg-muted); font-size: 24px; cursor: pointer; padding: 0 6px; }
.ficha .close-btn:hover { color: var(--fg); }
.ficha-section { margin: 18px 0; }
.ficha-section h3 { font-size: 14px; margin: 0 0 8px 0; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
.factor-table { width: 100%; border-collapse: collapse; }
.factor-table td, .factor-table th { padding: 8px 10px; border-bottom: 1px solid var(--border); font-size: 12.5px; }
.factor-table th { background: var(--bg); color: var(--fg-muted); }
.factor-bar { background: var(--bg); height: 8px; border-radius: 4px; overflow: hidden; min-width: 60px; }
.factor-bar-fill { background: var(--accent); height: 100%; }
.kv { display: grid; grid-template-columns: 160px 1fr; gap: 8px 16px; font-size: 13px; }
.kv dt { color: var(--fg-muted); }
.kv dd { margin: 0; word-break: break-word; }
.tabs { display: flex; border-bottom: 1px solid var(--border); margin-bottom: 12px; }
.tabs button { background: transparent; border: none; border-bottom: 2px solid transparent; padding: 8px 16px; color: var(--fg-muted); cursor: pointer; }
.tabs button.active { color: var(--accent); border-bottom-color: var(--accent); }
textarea {
  width: 100%; min-height: 110px; background: var(--bg); color: var(--fg);
  border: 1px solid var(--border); border-radius: 6px; padding: 10px;
  font-family: inherit; font-size: 13px; resize: vertical;
}
.comentario-item { background: var(--bg-row); padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 13px; }
.comentario-item .ts { color: var(--fg-muted); font-size: 11px; }
footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--fg-muted); font-size: 12px; }
.pesos-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; margin-top: 8px; }
.peso-item { background: var(--bg-row); padding: 6px 10px; border-radius: 4px; font-size: 12px; }
.peso-bar { background: var(--bg); height: 4px; border-radius: 2px; margin-top: 4px; }
.peso-bar-fill { background: var(--accent); height: 100%; border-radius: 2px; }
.toast {
  position: fixed; bottom: 20px; right: 20px; background: var(--green); color: white;
  padding: 12px 18px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  z-index: 2000; opacity: 0; transition: opacity 0.2s, transform 0.2s; transform: translateY(20px);
}
.toast.show { opacity: 1; transform: translateY(0); }
.no-results { text-align: center; padding: 40px; color: var(--fg-muted); }
.small { font-size: 11px; color: var(--fg-muted); }
.tag-pendiente { background: rgba(210,153,34,0.15); color: #f1c454; padding: 1px 6px; border-radius: 4px; font-size: 10px; }
/* Señales v0.3.0 */
.senal-chip {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 1px 7px; border-radius: 10px; font-size: 10.5px;
  border: 1px solid var(--border); background: var(--bg-row); margin: 0 2px 2px 0;
  vertical-align: middle;
}
.senal-positiva { background: rgba(63,185,80,0.12); border-color: rgba(63,185,80,0.4); color: #56d364; }
.senal-negativa { background: rgba(248,81,73,0.12); border-color: rgba(248,81,73,0.4); color: #ff8a85; }
.senal-pliego-detallado { background: rgba(88,166,255,0.12); border-color: rgba(88,166,255,0.4); color: #79b8ff; }
.senal-pliego-vago { background: rgba(210,153,34,0.12); border-color: rgba(210,153,34,0.4); color: #f1c454; }
.senal-conf-baja { opacity: 0.6; }
.senal-conf-media { opacity: 0.85; }
.senal-conf-alta { opacity: 1; font-weight: 600; }
.senales-cell { white-space: normal; max-width: 200px; line-height: 1.6; }
.senales-tabla { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.senales-tabla th, .senales-tabla td { padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; }
.senales-tabla th { background: var(--bg); color: var(--fg-muted); font-weight: 600; }
.profundizar-btn { background: linear-gradient(135deg, #58a6ff, #79b8ff); color: white; border: none; padding: 8px 16px; font-weight: 600; }
.profundizar-btn:hover { background: linear-gradient(135deg, #4493f8, #58a6ff); }
.profundizar-done { color: var(--green); font-weight: 600; }
.analisis-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.analisis-bloque { background: var(--bg-row); padding: 12px 16px; border-radius: 8px; border-left: 3px solid var(--accent); }
.analisis-bloque h4 { margin: 0 0 8px 0; font-size: 13px; color: var(--accent); }
.analisis-bloque p { margin: 0; font-size: 13px; line-height: 1.6; }
.lista-funcionamiento { margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.7; }
.lista-funcionamiento li { margin-bottom: 4px; }
.fases-list { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.fase-card { display: flex; gap: 12px; background: var(--bg); padding: 10px 14px; border-radius: 6px; border: 1px solid var(--border); }
.fase-num { background: var(--accent); color: white; min-width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; flex-shrink: 0; margin-top: 2px; }
.fase-body { flex: 1; }
.fase-titulo { font-size: 13px; margin-bottom: 4px; }
.fase-desc { font-size: 12.5px; color: var(--fg); line-height: 1.5; }
.fase-entregable { font-size: 11.5px; color: var(--fg-muted); margin-top: 6px; padding-top: 6px; border-top: 1px dashed var(--border); }
@media (max-width: 800px) { .analisis-grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="container">

<header>
  <h1>🎯 Buscador de Licitaciones — Top vigente</h1>
  <div class="meta">
    <span class="pill">Ejecución <strong>__EJEC_ID__</strong></span>
    <span class="pill">Generado <strong>__FECHA__</strong></span>
    <span class="pill">Rúbrica <strong>v__VERSION_CRIT__</strong></span>
    <span class="pill">Modo <strong>__MODO__</strong></span>
    <span class="pill">Top: <strong id="contador-top">__N_TOP__</strong></span>
    <span class="pill">Analizados (histórico): <strong>__N_ANALIZADOS__</strong></span>
  </div>
</header>

<div class="banner-fb">
  <div class="info">
    <div id="estado-servidor">⏳ Verificando servidor…</div>
    <div style="font-size:11px; opacity:0.8; margin-top:4px">Si el servidor está activo, cada like/dislike/⭐/comentario se persiste automáticamente en <code>data/feedback_dashboard.json</code>. Si abres el HTML directamente sin servidor, cae a localStorage y necesitarás el botón de exportar.</div>
  </div>
  <div>
    <button onclick="exportarFeedback()" title="Solo necesario si no estás usando el servidor">📥 Exportar feedback</button>
    <button onclick="document.getElementById('import-input').click()" title="Cargar feedback de otra sesión">📤 Importar feedback</button>
    <input id="import-input" type="file" accept="application/json" style="display:none" onchange="importarFeedback(event)"/>
  </div>
</div>

<!-- Sección Memoria de empresa -->
<details>
  <summary>📝 Memoria de empresa (taglines + prompts) — boceto inicial</summary>
  <div class="detail-body">
    <p class="small">Estado actual: <strong>__ESTADO_PERFIL__</strong>. Pendientes del usuario: __PENDIENTES__. Edita <code>data/perfil_empresa.json</code> en la próxima sesión con Claude para personalizarlo.</p>
    <h3>Taglines de posicionamiento</h3>
    <ul class="taglines" id="taglines-list"></ul>
    <h3>Qué NO hacemos (filtro explícito)</h3>
    <ul class="taglines" id="que-no-hacemos-list"></ul>
    <h3>📋 Prompt para generar memoria técnica completa por licitación</h3>
    <p class="small">Cópialo y úsalo con Claude / ChatGPT para producir la memoria técnica de cualquier licitación del top.</p>
    <div class="prompt-block" id="prompt-memoria-completa"></div>
    <button onclick="copiarTexto(document.getElementById('prompt-memoria-completa').textContent, '✓ Prompt memoria técnica copiado')">📋 Copiar prompt</button>
  </div>
</details>

<!-- Filtros -->
<div class="filtros">
  <input type="text" id="f-texto" placeholder="🔍 Buscar título / órgano..." oninput="renderTabla()">
  <select id="f-tipo" onchange="renderTabla()">
    <option value="">Tipo objeto (todos)</option>
    <option value="entregable_definido">Entregable definido</option>
    <option value="mixto">Mixto</option>
    <option value="indeterminado">Indeterminado</option>
  </select>
  <select id="f-lugar" onchange="renderTabla()">
    <option value="">Lugar prestación (todos)</option>
    <option value="remoto">Remoto</option>
    <option value="mixto">Mixto</option>
    <option value="infra_cliente">Infra cliente</option>
    <option value="indeterminado">Indeterminado</option>
  </select>
  <select id="f-fuente" onchange="renderTabla()">
    <option value="">Fuente (todas)</option>
    <option value="PLACSP">PLACSP</option>
    <option value="BOE">BOE</option>
    <option value="AUTONOMICO">Autonómico</option>
  </select>
  <select id="f-score" onchange="renderTabla()">
    <option value="">Score (todos)</option>
    <option value="top">Solo top (≥ umbral)</option>
    <option value="fuera">Fuera del top</option>
    <option value="all">Top + fuera</option>
  </select>
  <select id="f-feedback" onchange="renderTabla()">
    <option value="">Feedback (todos)</option>
    <option value="like">👍 Like</option>
    <option value="dislike">👎 Dislike</option>
    <option value="favorito">⭐ Favorito</option>
    <option value="sin">Sin tocar</option>
  </select>
  <select id="f-senal" onchange="renderTabla()">
    <option value="">Señales (todas)</option>
    <option value="moat_fuerte">🎯 Moat fuerte (≥2 positivas altas)</option>
    <option value="killer">⚠️ Killer (≥1 negativa alta)</option>
    <option value="spec_friendly">📋 Pliego detallado</option>
    <option value="profundizado">🧠 Profundizado</option>
  </select>
</div>

<table class="tabla">
  <thead>
    <tr>
      <th onclick="sortBy('rank')">#</th>
      <th onclick="sortBy('score_total')">Score ▼</th>
      <th>👍👎⭐</th>
      <th onclick="sortBy('titulo')">Título · Señales</th>
      <th onclick="sortBy('organo')">Órgano</th>
      <th onclick="sortBy('presupuesto')">€</th>
      <th onclick="sortBy('plazo')">Plazo</th>
      <th>Tipo objeto</th>
      <th>Lugar</th>
      <th>Fuente</th>
      <th>Pliego</th>
    </tr>
  </thead>
  <tbody id="tbody-tabla"></tbody>
</table>
<div class="no-results" id="no-results" style="display:none">No hay resultados con estos filtros.</div>

<!-- Ficha overlay -->
<div class="ficha-overlay" id="ficha-overlay" onclick="if(event.target===this){cerrarFicha()}">
  <div class="ficha" id="ficha-content"></div>
</div>

<footer>
  <details>
    <summary>⚖️ Rúbrica vigente (v__VERSION_CRIT__) — pesos y descartes</summary>
    <div class="detail-body">
      <div class="pesos-grid" id="pesos-grid"></div>
      <p class="small" style="margin-top:14px">Umbral top: <strong>__UMBRAL__</strong>. Descartes automáticos: <span id="descartes-list"></span></p>
    </div>
  </details>
  <p class="small">Para regenerar este dashboard: <code>/lic-dashboard</code> · Nueva búsqueda: <code>/lic-buscar</code> · Ajustar criterios: <code>/lic-criterios</code></p>
</footer>

</div>

<div class="toast" id="toast"></div>

<script>
const DATA = __DATA_JSON__;

// Storage keys (localStorage fallback)
const SK = {
  fb: 'lic.feedback.v1.likes',
  fav: 'lic.feedback.v1.favoritos',
  com: 'lic.feedback.v1.comentarios',
  msg: 'lic.feedback.v1.mensajes'
};

let SERVER_OK = false; // se actualiza en init()

const getFB = () => JSON.parse(localStorage.getItem(SK.fb) || '{}');
const getFav = () => JSON.parse(localStorage.getItem(SK.fav) || '[]');
const getCom = () => JSON.parse(localStorage.getItem(SK.com) || '{}');
const getMsg = () => JSON.parse(localStorage.getItem(SK.msg) || '{}');
const setItem = (k, v) => localStorage.setItem(k, JSON.stringify(v));

// --- Persistencia vía servidor local (con fallback automático a localStorage) ---
async function pingServer() {
  try {
    const r = await fetch('/api/ping', {method: 'GET', cache: 'no-store'});
    if (!r.ok) return false;
    const j = await r.json();
    return !!j.ok;
  } catch (e) { return false; }
}

async function postEvento(evt) {
  if (!SERVER_OK) return false;
  try {
    const r = await fetch('/api/feedback', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(evt)
    });
    return r.ok;
  } catch (e) { return false; }
}

async function hidratarDesdeServidor() {
  if (!SERVER_OK) return;
  try {
    const r = await fetch('/api/feedback', {cache: 'no-store'});
    if (!r.ok) return;
    const fb = await r.json();
    if (fb.likes_dislikes) setItem(SK.fb, fb.likes_dislikes);
    if (fb.favoritos) setItem(SK.fav, fb.favoritos);
    if (fb.comentarios) setItem(SK.com, fb.comentarios);
    if (fb.mensajes_generados) setItem(SK.msg, fb.mensajes_generados);
  } catch (e) { /* silencioso */ }
}

let sortKey = 'score_total';
let sortDir = -1;
let allItems = [];

async function init() {
  // Construye allItems: top + fuera del top
  allItems = DATA.top.concat(DATA.fuera_del_top || []).map((it, idx) => ({
    ...it,
    _rank: idx + 1,
    _en_top: idx < DATA.top.length,
    _id_key: it.id_oficial || it.hash || ('idx_' + idx)
  }));
  // Ping servidor + hidratación
  SERVER_OK = await pingServer();
  if (SERVER_OK) {
    await hidratarDesdeServidor();
    document.getElementById('estado-servidor').innerHTML = '🟢 Servidor activo — feedback se persiste automáticamente';
  } else {
    document.getElementById('estado-servidor').innerHTML = '🟡 Sin servidor — feedback en localStorage (usa el botón Exportar para Claude)';
  }
  renderHeader();
  renderTagsMemoria();
  renderPesos();
  renderTabla();
}

function renderHeader() {
  document.getElementById('contador-top').textContent = DATA.top.length;
}

function renderTagsMemoria() {
  const p = DATA.perfil_empresa || {};
  const ul1 = document.getElementById('taglines-list');
  const ul2 = document.getElementById('que-no-hacemos-list');
  (p.taglines || []).forEach(t => {
    const li = document.createElement('li'); li.textContent = t; ul1.appendChild(li);
  });
  (p.que_no_hacemos || []).forEach(t => {
    const li = document.createElement('li'); li.textContent = '🚫 ' + t; ul2.appendChild(li);
  });

  const tagsText = (p.taglines || []).map(t => '- ' + t).join('\\n');
  const prompt = `Escribe la memoria técnica completa para esta licitación pública. Tono: formal y técnico. Longitud: la que pida el pliego (típicamente 20-40 páginas).

DATOS DEL EXPEDIENTE:
[Pega aquí los datos del item desde el dashboard]

QUIÉNES SOMOS (taglines de posicionamiento):
${tagsText}

QUÉ NO HACEMOS:
${(p.que_no_hacemos || []).map(t => '- ' + t).join('\\n')}

ESTRUCTURA RECOMENDADA (adáptala al pliego si exige otra):
1. Presentación del licitador y equipo.
2. Comprensión del objeto del contrato.
3. Enfoque metodológico (con énfasis en entrega cerrada + infraestructura propia + uso de IA como acelerador).
4. Plan de trabajo y cronograma.
5. Arquitectura técnica propuesta.
6. Equipo asignado y roles.
7. Plan de calidad y aceptación.
8. Garantía y soporte post-entrega.
9. Riesgos y plan de mitigación.
10. Mejoras opcionales sobre el pliego.

REGLAS DE ESTILO:
- Sé específico: cita el pliego, propon decisiones técnicas concretas, evita generalidades de consultora.
- Evita clichés ("alta calidad", "excelencia", "compromiso firme").
- Demuestra comprensión del problema antes de proponer solución.
- Cada decisión técnica debe estar justificada con criterio operativo o económico.`;
  document.getElementById('prompt-memoria-completa').textContent = prompt;
}

function renderPesos() {
  const grid = document.getElementById('pesos-grid');
  DATA.factores.forEach(f => {
    const div = document.createElement('div');
    div.className = 'peso-item';
    div.innerHTML = `<strong>${f.nombre}</strong> — ${(f.peso*100).toFixed(0)}%
      <div class="peso-bar"><div class="peso-bar-fill" style="width:${f.peso*100}%"></div></div>`;
    grid.appendChild(div);
  });
  document.getElementById('descartes-list').textContent = ['presupuesto fuera de 20k-200k', 'plazo < 7d / vencido', 'fuera de scope TI', 'duplicado', 'tipo_objeto=horas_servicio', 'lugar_prestacion=presencial_continuada'].join(' · ');
}

function chip(text, kind) {
  return `<span class="chip chip-${kind}">${text || '—'}</span>`;
}

function chipTipo(t) {
  if (!t) return chip('—', 'indeterminado');
  return chip(t.replace('_',' '), t === 'entregable_definido' ? 'entregable' : t);
}

const SENAL_EMOJI = {
  stack_mainstream: '🧱', crud_masivo: '🔁', integraciones_estandar: '🔌',
  logica_mecanica: '✅', boilerplate_alto: '📦', testeable: '🧪',
  pliego_detallado: '📋', pliego_vago: '❓',
  hardware_raro: '🔧', legacy_mal_doc: '📜', ux_experimental: '🎨', investigacion: '🔬'
};
const SENALES_POSITIVAS = new Set(['stack_mainstream','crud_masivo','integraciones_estandar','logica_mecanica','boilerplate_alto','testeable']);
const SENALES_NEGATIVAS = new Set(['hardware_raro','legacy_mal_doc','ux_experimental','investigacion']);

function senalChip(s, compact=false) {
  if (!s) return '';
  const emoji = SENAL_EMOJI[s.nombre] || '•';
  let cls = 'senal-chip senal-conf-' + (s.confianza || 'media');
  if (s.nombre === 'pliego_detallado') cls += ' senal-pliego-detallado';
  else if (s.nombre === 'pliego_vago') cls += ' senal-pliego-vago';
  else if (SENALES_POSITIVAS.has(s.nombre)) cls += ' senal-positiva';
  else if (SENALES_NEGATIVAS.has(s.nombre)) cls += ' senal-negativa';
  const lbl = compact ? emoji : `${emoji} ${s.nombre.replace(/_/g,' ')}`;
  const titulo = `${s.nombre} (${s.confianza}${s.origen ? ', '+s.origen : ''})\\n— ${(s.evidencia || '').slice(0, 200)}`;
  return `<span class="${cls}" title="${escapeHtml(titulo)}">${lbl}</span>`;
}

function senalRank(s) {
  // Ordena señales por fuerza absoluta (para mostrar las 3 más fuertes)
  const r = {alta: 3, media: 2, baja: 1};
  return r[s.confianza] || 0;
}

function senalesCompactas(item) {
  const sen = (item.datos || {}).senales || [];
  if (sen.length === 0) return '<span class="small" style="opacity:0.5">—</span>';
  // Ordena por rank descendente; máx 3
  const ordenadas = [...sen].sort((a, b) => senalRank(b) - senalRank(a)).slice(0, 3);
  return ordenadas.map(s => senalChip(s, true)).join(' ');
}

function tieneMoatFuerte(item) {
  const sen = (item.datos || {}).senales || [];
  const altasPos = sen.filter(s => SENALES_POSITIVAS.has(s.nombre) && s.confianza === 'alta').length;
  return altasPos >= 2;
}
function tieneKiller(item) {
  const sen = (item.datos || {}).senales || [];
  return sen.some(s => SENALES_NEGATIVAS.has(s.nombre) && s.confianza === 'alta');
}
function tienePliegoDetallado(item) {
  const sen = (item.datos || {}).senales || [];
  return sen.some(s => s.nombre === 'pliego_detallado' && (s.confianza === 'alta' || s.confianza === 'media'));
}
function chipLugar(l) {
  if (!l) return chip('—', 'indeterminado');
  const cls = l === 'remoto' ? 'remoto' : l === 'presencial_continuada' ? 'presencial' : l === 'infra_cliente' ? 'infra-cliente' : l;
  return chip(l.replace('_',' '), cls);
}

function scoreClass(s) {
  if (s >= 8) return 'score-top';
  if (s >= 6.5) return 'score-high';
  if (s >= 5) return 'score-mid';
  return 'score-low';
}

function renderTabla() {
  const ft = document.getElementById('f-texto').value.toLowerCase();
  const ftipo = document.getElementById('f-tipo').value;
  const flugar = document.getElementById('f-lugar').value;
  const ffuente = document.getElementById('f-fuente').value;
  const fscore = document.getElementById('f-score').value;
  const ffb = document.getElementById('f-feedback').value;
  const fbs = getFB();
  const favs = getFav();

  let items = allItems.slice();

  // Filtro score
  if (fscore === 'top') items = items.filter(i => i._en_top);
  else if (fscore === 'fuera') items = items.filter(i => !i._en_top);
  else if (fscore === '') items = items.filter(i => i._en_top);

  if (ft) items = items.filter(i =>
    ((i.datos || {}).titulo || '').toLowerCase().includes(ft) ||
    ((i.datos || {}).organo_contratante || '').toLowerCase().includes(ft)
  );
  if (ftipo) items = items.filter(i => ((i.datos || {}).tipo_objeto || 'indeterminado') === ftipo);
  if (flugar) items = items.filter(i => ((i.datos || {}).lugar_prestacion || 'indeterminado') === flugar);
  if (ffuente) items = items.filter(i => i.fuente === ffuente);
  if (ffb === 'like') items = items.filter(i => fbs[i._id_key] === 'like');
  else if (ffb === 'dislike') items = items.filter(i => fbs[i._id_key] === 'dislike');
  else if (ffb === 'favorito') items = items.filter(i => favs.includes(i._id_key));
  else if (ffb === 'sin') items = items.filter(i => !fbs[i._id_key] && !favs.includes(i._id_key));

  const fsenal = document.getElementById('f-senal').value;
  if (fsenal === 'moat_fuerte') items = items.filter(tieneMoatFuerte);
  else if (fsenal === 'killer') items = items.filter(tieneKiller);
  else if (fsenal === 'spec_friendly') items = items.filter(tienePliegoDetallado);
  else if (fsenal === 'profundizado') items = items.filter(i => i.profundizado_at || i.analisis_pliego);

  // Sort
  items.sort((a, b) => {
    let av, bv;
    switch(sortKey) {
      case 'rank': av = a._rank; bv = b._rank; break;
      case 'score_total': av = a.score_total || 0; bv = b.score_total || 0; break;
      case 'titulo': av = ((a.datos || {}).titulo || '').toLowerCase(); bv = ((b.datos || {}).titulo || '').toLowerCase(); break;
      case 'organo': av = ((a.datos || {}).organo_contratante || '').toLowerCase(); bv = ((b.datos || {}).organo_contratante || '').toLowerCase(); break;
      case 'presupuesto': av = (a.datos || {}).presupuesto_total_eur || (a.datos || {}).presupuesto_base_eur || 0; bv = (b.datos || {}).presupuesto_total_eur || (b.datos || {}).presupuesto_base_eur || 0; break;
      case 'plazo': av = (a.datos || {}).plazo_presentacion || ''; bv = (b.datos || {}).plazo_presentacion || ''; break;
      default: av = a.score_total || 0; bv = b.score_total || 0;
    }
    return (av < bv ? -1 : av > bv ? 1 : 0) * sortDir;
  });

  // Re-rank
  items.forEach((it, idx) => it._rank_filtrado = idx + 1);

  const tbody = document.getElementById('tbody-tabla');
  tbody.innerHTML = '';
  document.getElementById('no-results').style.display = items.length === 0 ? 'block' : 'none';

  items.forEach(it => {
    const tr = document.createElement('tr');
    tr.className = 'row-item';
    const fbState = fbs[it._id_key];
    const isFav = favs.includes(it._id_key);
    if (isFav) tr.classList.add('row-favorito');
    else if (fbState === 'like') tr.classList.add('row-like');
    else if (fbState === 'dislike') tr.classList.add('row-dislike');

    const d = it.datos || {};
    const score = it.score_total || 0;
    const presup = d.presupuesto_total_eur || d.presupuesto_base_eur || 0;
    const desglose = (it.scoring || {});
    const tooltip = Object.entries(desglose).map(([k,v]) => `${k}: ${v.valor}`).join(' / ');

    tr.innerHTML = `
      <td>${it._rank_filtrado}</td>
      <td><span class="score-badge ${scoreClass(score)}" title="${escapeHtml(tooltip)}">${score.toFixed(2)}</span></td>
      <td>
        <div class="fb-buttons" onclick="event.stopPropagation()">
          <button class="${fbState === 'like' ? 'active like' : ''}" onclick="toggleFB('${it._id_key}', 'like', this)">👍</button>
          <button class="${fbState === 'dislike' ? 'active dislike' : ''}" onclick="toggleFB('${it._id_key}', 'dislike', this)">👎</button>
          <button class="${isFav ? 'active fav' : ''}" onclick="toggleFav('${it._id_key}', this)">⭐</button>
        </div>
      </td>
      <td class="title-cell senales-cell">
        <div><strong>${escapeHtml((d.titulo || '').slice(0, 80))}${(d.titulo || '').length > 80 ? '…' : ''}</strong>
        ${it.es_legacy ? '<span class="chip chip-legacy" title="Item legacy">legacy</span>' : ''}
        ${(d.tipo_objeto === 'indeterminado' && !it.es_legacy) ? '<span class="tag-pendiente">verificar pliego</span>' : ''}
        ${it.profundizado_at ? '<span class="chip" style="background:rgba(63,185,80,0.15);color:#56d364;border-color:rgba(63,185,80,0.4)" title="Pliego profundizado">🧠</span>' : ''}</div>
        <div style="margin-top:3px">${senalesCompactas(it)}</div>
      </td>
      <td>${escapeHtml(((d.organo_contratante || '').slice(0, 50)))}</td>
      <td>${presup ? presup.toLocaleString('es-ES', {maximumFractionDigits: 0}) + ' €' : '—'}</td>
      <td>${d.plazo_presentacion || '—'}</td>
      <td>${chipTipo(d.tipo_objeto)}</td>
      <td>${chipLugar(d.lugar_prestacion)}</td>
      <td>${chip(it.fuente || '—', 'indeterminado')}</td>
      <td>${it.url_oficial ? `<a href="${it.url_oficial}" target="_blank" onclick="event.stopPropagation()" title="${escapeHtml(it.url_oficial)}">🔗</a>` : '—'}</td>
    `;
    tr.addEventListener('click', () => abrirFicha(it));
    tbody.appendChild(tr);
  });
}

function sortBy(key) {
  if (sortKey === key) sortDir = -sortDir;
  else { sortKey = key; sortDir = (key === 'score_total' || key === 'presupuesto') ? -1 : 1; }
  renderTabla();
}

async function toggleFB(idKey, val, btn) {
  const fb = getFB();
  let nuevoValor;
  if (fb[idKey] === val) { delete fb[idKey]; nuevoValor = null; }
  else { fb[idKey] = val; nuevoValor = val; }
  setItem(SK.fb, fb);
  renderTabla();
  toast(nuevoValor ? (val === 'like' ? '👍 Like' : '👎 Dislike') + ' guardado' : '↺ Retirado');
  // Persiste en servidor
  await postEvento({type: val, id_key: idKey, value: nuevoValor});
}
async function toggleFav(idKey, btn) {
  let favs = getFav();
  const yaEstaba = favs.includes(idKey);
  if (yaEstaba) favs = favs.filter(x => x !== idKey);
  else favs.push(idKey);
  setItem(SK.fav, favs);
  renderTabla();
  toast(!yaEstaba ? '⭐ Añadido a favoritos' : '↺ Quitado de favoritos');
  await postEvento({type: 'favorito', id_key: idKey, value: !yaEstaba});
}

function renderSenalesProfundizar(it) {
  const sen = (it.datos || {}).senales || [];
  const isProf = !!it.profundizado_at;
  const btnHtml = isProf
    ? `<div class="profundizar-done">🧠 Profundizado el ${it.profundizado_at.replace('T',' ').slice(0,16)}. <button onclick="encolarProfundizar(${JSON.stringify(it).replace(/"/g,'&quot;')})" style="margin-left:8px">🔄 Re-profundizar</button></div>`
    : `<button class="profundizar-btn" onclick="encolarProfundizar(${JSON.stringify(it).replace(/"/g,'&quot;')})">🔬 Profundizar pliego (descarga PCAP/PPT y refina señales)</button>`;
  if (sen.length === 0) {
    return `<p class="small">Sin señales detectadas por heurística. ${btnHtml}</p>`;
  }
  const filas = sen.map(s => {
    let cls = '';
    if (s.nombre === 'pliego_detallado') cls = 'senal-pliego-detallado';
    else if (s.nombre === 'pliego_vago') cls = 'senal-pliego-vago';
    else if (SENALES_POSITIVAS.has(s.nombre)) cls = 'senal-positiva';
    else if (SENALES_NEGATIVAS.has(s.nombre)) cls = 'senal-negativa';
    return `<tr>
      <td><span class="senal-chip ${cls}">${SENAL_EMOJI[s.nombre] || '•'} ${s.nombre.replace(/_/g,' ')}</span></td>
      <td>${s.confianza}</td>
      <td><em>${s.origen || 'heuristica'}</em></td>
      <td class="small">${escapeHtml((s.evidencia || '').slice(0, 200))}</td>
    </tr>`;
  }).join('');
  return `
    <table class="senales-tabla">
      <thead><tr><th>Señal</th><th>Confianza</th><th>Origen</th><th>Evidencia</th></tr></thead>
      <tbody>${filas}</tbody>
    </table>
    <div style="margin-top:10px">${btnHtml}</div>
  `;
}

function renderAnalisisPliego(ap) {
  if (!ap) return '';
  const crit = ap.criterios_adjudicacion || {};
  const sol = ap.solvencia_tecnica || {};
  const vol = ap.volumen_estimado || {};
  return `
    <dl class="kv">
      ${crit.tecnico_pct != null ? `<dt>Criterios adjudicación</dt><dd>${crit.tecnico_pct}% técnico · ${crit.economico_pct || 0}% económico</dd>` : ''}
      ${crit.subcriterios_tecnicos ? `<dt>Subcriterios técnicos</dt><dd>${(crit.subcriterios_tecnicos || []).map(s => `<span class="chip">${escapeHtml(s)}</span>`).join(' ')}</dd>` : ''}
      ${sol.certificaciones ? `<dt>Certificaciones requeridas</dt><dd>${(sol.certificaciones || []).map(s => `<span class="chip">${escapeHtml(s)}</span>`).join(' ')}</dd>` : ''}
      ${sol.experiencia_previa ? `<dt>Experiencia previa</dt><dd>${escapeHtml(sol.experiencia_previa)}</dd>` : ''}
      ${ap.stack_obligatorio_o_recomendado ? `<dt>Stack pliego</dt><dd>${(ap.stack_obligatorio_o_recomendado || []).map(s => `<span class="chip">${escapeHtml(s)}</span>`).join(' ')}</dd>` : ''}
      ${vol.usuarios ? `<dt>Volumen estimado</dt><dd>${vol.usuarios} usuarios · ${vol.transacciones_dia || '—'} tx/día</dd>` : ''}
      ${ap.riesgos_detectados ? `<dt>⚠️ Riesgos</dt><dd><ul>${(ap.riesgos_detectados || []).map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul></dd>` : ''}
      ${ap.puntos_diferenciales_para_oferta ? `<dt>💡 Puntos para oferta</dt><dd><ul>${(ap.puntos_diferenciales_para_oferta || []).map(s => `<li>${escapeHtml(s)}</li>`).join('')}</ul></dd>` : ''}
      ${ap.limitaciones ? `<dt>📌 Limitaciones</dt><dd class="small">${escapeHtml(ap.limitaciones)}</dd>` : ''}
    </dl>
  `;
}

async function encolarProfundizar(it) {
  if (!SERVER_OK) {
    toast('❌ Servidor no activo — no se puede encolar profundización');
    return;
  }
  const d = it.datos || {};
  try {
    const r = await fetch('/api/profundizar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        hash: it.hash,
        id_oficial: it.id_oficial,
        url_oficial: it.url_oficial,
        url_pliego_pcap: d.url_pliego_pcap,
        url_pliego_ppt: d.url_pliego_ppt,
        titulo: d.titulo
      })
    });
    const j = await r.json();
    if (j.ok) toast(`🔬 Encolado para profundizar (${j.pendientes} pendiente${j.pendientes!==1?'s':''})`);
    else toast('❌ Error encolando');
  } catch(e) {
    toast('❌ Error encolando: ' + e.message);
  }
}

function renderAnalisisProyecto(it) {
  const a = it.analisis_proyecto;
  if (!a) {
    return `<p class="small" style="font-style:italic; padding:14px; background:var(--bg-row); border-radius:6px; border-left:3px solid var(--yellow)">
      📝 <strong>Análisis pendiente.</strong> Solo el top 5 tiene análisis completo (en qué consiste, problema, funcionamiento, fases). Pídeselo a Claude para este item cuando quieras: <code>"genera análisis del proyecto para ${(it.id_oficial || it.hash || '').replace(/'/g, "")}"</code>
    </p>`;
  }
  const fases = (a.fases_principales || []).map((f, i) => `
    <div class="fase-card">
      <div class="fase-num">${i + 1}</div>
      <div class="fase-body">
        <div class="fase-titulo"><strong>${escapeHtml(f.nombre)}</strong></div>
        <div class="fase-desc">${escapeHtml(f.descripcion)}</div>
        ${f.entregable ? `<div class="fase-entregable">📦 <strong>Entregable:</strong> ${escapeHtml(f.entregable)}</div>` : ''}
      </div>
    </div>
  `).join('');
  const funcionamiento = (a.funcionamiento_basico || []).map(f => `<li>${escapeHtml(f)}</li>`).join('');
  return `
    <div class="analisis-grid">
      <div class="analisis-bloque">
        <h4>📌 En qué consiste</h4>
        <p>${escapeHtml(a.en_que_consiste || '')}</p>
      </div>
      <div class="analisis-bloque">
        <h4>🎯 Qué problema soluciona</h4>
        <p>${escapeHtml(a.que_problema_soluciona || '')}</p>
      </div>
    </div>
    <div class="analisis-bloque" style="margin-top:14px">
      <h4>⚙️ Funcionamiento básico del software</h4>
      <ul class="lista-funcionamiento">${funcionamiento}</ul>
    </div>
    <div class="analisis-bloque" style="margin-top:14px">
      <h4>🛣️ Fases / hitos del desarrollo (${(a.fases_principales || []).length})</h4>
      <div class="fases-list">${fases}</div>
    </div>
    <p class="small" style="margin-top:10px; opacity:0.7">Análisis generado: ${a.generado_at || '—'} · ${a.generado_por || ''}</p>
  `;
}

function abrirFicha(it) {
  const d = it.datos || {};
  const scoring = it.scoring || {};
  const score = it.score_total || 0;
  const factores = DATA.factores;
  const presup = d.presupuesto_total_eur || d.presupuesto_base_eur || 0;
  const filas = factores.map(f => {
    const s = scoring[f.nombre] || {};
    const valor = s.valor != null ? s.valor : '—';
    const aporte = (f.nombre === 'dificultad' && s.valor != null) ? ((10 - s.valor) * f.peso) : ((s.valor || 0) * f.peso);
    const pctValor = s.valor != null ? (s.valor / 10 * 100) : 0;
    return `<tr>
      <td><strong>${f.nombre}</strong><div class="small">${escapeHtml(f.descripcion.slice(0, 90))}…</div></td>
      <td style="text-align:center"><strong>${valor}</strong>/10</td>
      <td><div class="factor-bar"><div class="factor-bar-fill" style="width:${pctValor}%"></div></div></td>
      <td>${(f.peso*100).toFixed(0)}%</td>
      <td><strong>${aporte.toFixed(2)}</strong></td>
      <td class="small">${escapeHtml((s.por_que || '').slice(0, 200))}</td>
    </tr>`;
  }).join('');

  const com = getCom();
  const msg = getMsg();
  const fbs = getFB();
  const favs = getFav();
  const itemCom = com[it._id_key] || [];
  const itemMsg = msg[it._id_key] || {email_previo: '', carta_inicial: ''};

  // Plantillas
  const tagsText = (DATA.perfil_empresa.taglines || []).slice(0,5).map(t => '- ' + t).join('\\n');
  const promptEmail = `Necesito un email corto al órgano de contratación de esta licitación. Tono: profesional pero cercano, sin lenguaje pomposo. Objetivo: presentarnos como equipo de 2 personas que aporta IA real al desarrollo, mostrar interés en el expediente, pedir aclaración técnica si procede. Máx 180 palabras.

DATOS DE LA LICITACIÓN:
- Órgano: ${d.organo_contratante || '—'}
- Expediente: ${it.id_oficial || '—'}
- Objeto: ${d.titulo || '—'}
- Presupuesto: ${presup ? presup.toLocaleString('es-ES') + ' €' : '—'}
- Plazo: ${d.plazo_presentacion || '—'}
- URL: ${it.url_oficial || '—'}

QUIÉNES SOMOS:
${tagsText}

ESTRUCTURA:
1. Saludo + presentación breve (2 frases).
2. Mención del expediente y por qué nos encaja.
3. Pregunta técnica relevante (si hay duda razonable).
4. Cierre con disponibilidad para reunión breve.

Firma: ${DATA.perfil_empresa.firma_usuario || '[PENDIENTE: nombre + cargo + email + teléfono]'}`;

  const promptCarta = `Escribe la primera página formal de la memoria técnica que abrirá nuestra oferta para esta licitación pública. Tono: formal sin pomposidad, denso en valor, breve (máx 1 página A4 ≈ 450 palabras).

DATOS DEL EXPEDIENTE:
- Órgano: ${d.organo_contratante || '—'}
- Expediente: ${it.id_oficial || '—'}
- Objeto: ${d.titulo || '—'}
- Descripción: ${(d.descripcion || '').slice(0, 500)}
- Presupuesto: ${presup ? presup.toLocaleString('es-ES') + ' €' : '—'}
- Plazo: ${d.plazo_presentacion || '—'}

QUIÉNES SOMOS:
${tagsText}

ESTRUCTURA OBLIGATORIA:
1. **Presentación del licitador** (2 párrafos): equipo de 2 personas con IA como apalancamiento doble (acelerador de desarrollo y funcionalidad de producto).
2. **Comprensión del objeto del contrato** (1 párrafo): reformula con tus palabras lo que el órgano necesita.
3. **Enfoque propuesto** (1-2 párrafos): cómo abordaríamos el proyecto. Mencionar explícitamente que entregamos solución completa (no horas) desde nuestra infraestructura.
4. **Resumen de valor diferencial** (1 párrafo): por qué nosotros y no otro.

EVITA: clichés ("alta calidad", "excelencia", "compromiso firme"). Sé concreto, cita el expediente, demuestra comprensión.`;

  const ficha = document.getElementById('ficha-content');
  ficha.innerHTML = `
    <header>
      <div style="flex:1">
        <h2>${escapeHtml(d.titulo || 'Sin título')}</h2>
        <div class="small">${escapeHtml(d.organo_contratante || '')} · ${it.fuente} · ${it.id_oficial || ''}</div>
      </div>
      <div style="display:flex; align-items:center; gap:12px">
        <span class="score-badge ${scoreClass(score)}" style="font-size:18px; padding:8px 14px">${score.toFixed(2)}</span>
        <div class="fb-buttons">
          <button class="${fbs[it._id_key] === 'like' ? 'active like' : ''}" onclick="toggleFB('${it._id_key}', 'like'); abrirFicha(${JSON.stringify(it).replace(/"/g, '&quot;')})">👍</button>
          <button class="${fbs[it._id_key] === 'dislike' ? 'active dislike' : ''}" onclick="toggleFB('${it._id_key}', 'dislike'); abrirFicha(${JSON.stringify(it).replace(/"/g, '&quot;')})">👎</button>
          <button class="${favs.includes(it._id_key) ? 'active fav' : ''}" onclick="toggleFav('${it._id_key}'); abrirFicha(${JSON.stringify(it).replace(/"/g, '&quot;')})">⭐</button>
        </div>
        <button class="close-btn" onclick="cerrarFicha()">×</button>
      </div>
    </header>

    <div class="ficha-section">
      <h3>📊 Desglose de score (rúbrica v${DATA.version_criterios})</h3>
      <table class="factor-table">
        <thead><tr><th>Factor</th><th>Valor</th><th>Visual</th><th>Peso</th><th>Aporte</th><th>Justificación</th></tr></thead>
        <tbody>${filas}</tbody>
      </table>
    </div>

    <div class="ficha-section">
      <h3>📋 Datos del expediente</h3>
      <dl class="kv">
        <dt>Descripción</dt><dd>${escapeHtml((d.descripcion || '').slice(0, 600))}</dd>
        <dt>Presupuesto base</dt><dd>${d.presupuesto_base_eur ? d.presupuesto_base_eur.toLocaleString('es-ES') + ' €' : '—'}</dd>
        <dt>Presupuesto total</dt><dd>${d.presupuesto_total_eur ? d.presupuesto_total_eur.toLocaleString('es-ES') + ' €' : '—'}</dd>
        <dt>Plazo presentación</dt><dd>${d.plazo_presentacion || '—'}</dd>
        <dt>CPV</dt><dd>${(d.cpv_codigos || []).join(', ') || '—'}</dd>
        <dt>Lugar ejecución</dt><dd>${escapeHtml(d.lugar_ejecucion || '—')}</dd>
        <dt>Tipo objeto</dt><dd>${chipTipo(d.tipo_objeto)} <span class="small">— ${escapeHtml((d.evidencia_tipo_objeto || '').slice(0, 200))}</span></dd>
        <dt>Lugar prestación</dt><dd>${chipLugar(d.lugar_prestacion)} <span class="small">— ${escapeHtml((d.evidencia_lugar_prestacion || '').slice(0, 200))}</span></dd>
        <dt>URL oficial</dt><dd>${it.url_oficial ? `<a href="${it.url_oficial}" target="_blank">${escapeHtml(it.url_oficial)}</a>` : '—'}</dd>
        <dt>PCAP</dt><dd>${d.url_pliego_pcap ? `<a href="${d.url_pliego_pcap}" target="_blank">descargar</a>` : '—'}</dd>
        <dt>PPT</dt><dd>${d.url_pliego_ppt ? `<a href="${d.url_pliego_ppt}" target="_blank">descargar</a>` : '—'}</dd>
        <dt>Fuentes corroboradas</dt><dd>${(it.fuentes_corroboradas || []).join(', ')}</dd>
      </dl>
    </div>

    <div class="ficha-section">
      <h3>🎯 Señales detectadas (v0.3.0)</h3>
      ${renderSenalesProfundizar(it)}
    </div>

    ${it.analisis_pliego ? `<div class="ficha-section">
      <h3>🧠 Análisis del pliego (profundizado)</h3>
      ${renderAnalisisPliego(it.analisis_pliego)}
    </div>` : ''}

    <div class="ficha-section">
      <h3>🔎 Análisis del proyecto</h3>
      ${renderAnalisisProyecto(it)}
    </div>

    <div class="ficha-section">
      <h3>✉️ Plantillas de presentación</h3>
      <div class="tabs">
        <button class="active" onclick="switchTab(event, 'tab-email')">Email previo al órgano</button>
        <button onclick="switchTab(event, 'tab-carta')">Carta inicial de la oferta</button>
      </div>
      <div id="tab-email">
        <p class="small">📋 Copia el prompt, pégalo en Claude / ChatGPT, y guarda el resultado en el textarea de abajo.</p>
        <details><summary>Ver prompt</summary>
          <div class="prompt-block">${escapeHtml(promptEmail)}</div>
          <button onclick="copiarTexto(${JSON.stringify(promptEmail).replace(/"/g, '&quot;')}, '✓ Prompt email copiado')">📋 Copiar prompt</button>
        </details>
        <textarea id="ta-email" placeholder="Pega aquí el email generado para guardarlo en este dashboard...">${escapeHtml(itemMsg.email_previo || '')}</textarea>
        <button onclick="guardarMsg('${it._id_key}', 'email_previo', document.getElementById('ta-email').value)">💾 Guardar email</button>
      </div>
      <div id="tab-carta" style="display:none">
        <p class="small">📋 Copia el prompt, pégalo en Claude / ChatGPT, y guarda el resultado en el textarea de abajo.</p>
        <details><summary>Ver prompt</summary>
          <div class="prompt-block">${escapeHtml(promptCarta)}</div>
          <button onclick="copiarTexto(${JSON.stringify(promptCarta).replace(/"/g, '&quot;')}, '✓ Prompt carta copiado')">📋 Copiar prompt</button>
        </details>
        <textarea id="ta-carta" style="min-height:200px" placeholder="Pega aquí la carta inicial generada para guardarla en este dashboard...">${escapeHtml(itemMsg.carta_inicial || '')}</textarea>
        <button onclick="guardarMsg('${it._id_key}', 'carta_inicial', document.getElementById('ta-carta').value)">💾 Guardar carta</button>
      </div>
    </div>

    <div class="ficha-section">
      <h3>💬 Comentarios</h3>
      <div id="comentarios-list">
        ${itemCom.map(c => `<div class="comentario-item"><div class="ts">${c.ts}</div>${escapeHtml(c.texto)}</div>`).join('') || '<p class="small">Sin comentarios aún.</p>'}
      </div>
      <textarea id="ta-comentario" placeholder="Anota lo que quieras sobre este item — útil para reajustar el modelo (qué te gustó, qué falla, qué cambiar de la rúbrica...)"></textarea>
      <button onclick="addComentario('${it._id_key}')">➕ Añadir comentario</button>
    </div>
  `;
  document.getElementById('ficha-overlay').classList.add('open');
}

function cerrarFicha() {
  document.getElementById('ficha-overlay').classList.remove('open');
}

function switchTab(ev, tabId) {
  ev.target.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('active'));
  ev.target.classList.add('active');
  document.getElementById('tab-email').style.display = tabId === 'tab-email' ? '' : 'none';
  document.getElementById('tab-carta').style.display = tabId === 'tab-carta' ? '' : 'none';
}

async function guardarMsg(idKey, campo, valor) {
  const msg = getMsg();
  msg[idKey] = msg[idKey] || {};
  msg[idKey][campo] = valor;
  setItem(SK.msg, msg);
  toast('💾 Guardado');
  await postEvento({type: 'mensaje', id_key: idKey, campo: campo, value: valor});
}

async function addComentario(idKey) {
  const ta = document.getElementById('ta-comentario');
  const texto = ta.value.trim();
  if (!texto) return;
  const com = getCom();
  com[idKey] = com[idKey] || [];
  com[idKey].push({ts: new Date().toISOString().slice(0, 16).replace('T', ' '), texto});
  setItem(SK.com, com);
  ta.value = '';
  toast('💬 Comentario añadido');
  await postEvento({type: 'comentario_add', id_key: idKey, value: texto});
  // Reload ficha
  const it = allItems.find(x => x._id_key === idKey);
  if (it) abrirFicha(it);
}

function exportarFeedback() {
  const blob = {
    _exported_at: new Date().toISOString(),
    ejecucion_origen: DATA.ejecucion_id,
    version_criterios: DATA.version_criterios,
    likes_dislikes: getFB(),
    favoritos: getFav(),
    comentarios: getCom(),
    mensajes_generados: getMsg()
  };
  const txt = JSON.stringify(blob, null, 2);
  const a = document.createElement('a');
  a.href = 'data:application/json;charset=utf-8,' + encodeURIComponent(txt);
  a.download = `feedback_dashboard_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  toast('📥 Feedback exportado');
}

async function importarFeedback(ev) {
  const file = ev.target.files[0];
  if (!file) return;
  const fr = new FileReader();
  fr.onload = async () => {
    try {
      const blob = JSON.parse(fr.result);
      if (blob.likes_dislikes) setItem(SK.fb, blob.likes_dislikes);
      if (blob.favoritos) setItem(SK.fav, blob.favoritos);
      if (blob.comentarios) setItem(SK.com, blob.comentarios);
      if (blob.mensajes_generados) setItem(SK.msg, blob.mensajes_generados);
      renderTabla();
      toast('📤 Feedback importado');
      // Replica al servidor también
      await postEvento({type: 'bulk_import', id_key: '_bulk', value: blob});
    } catch(e) {
      toast('❌ JSON inválido');
    }
  };
  fr.readAsText(file);
  ev.target.value = '';
}

function copiarTexto(t, msg) {
  navigator.clipboard.writeText(t).then(() => toast(msg || '✓ Copiado'));
}

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
}

// Keyboard shortcuts en ficha
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') cerrarFicha();
});

init();
</script>
</body>
</html>
"""

REPLACES = {
    "__EJEC_ID__": EJEC_ID,
    "__FECHA__": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "__VERSION_CRIT__": CRIT["version"],
    "__MODO__": CFG.get("modo_busqueda", "mixto"),
    "__N_TOP__": str(len(SEL.get("top_actual", []))),
    "__N_ANALIZADOS__": str(HIST.get("total", 0)),
    "__UMBRAL__": str(CRIT["umbral_top"]),
    "__ESTADO_PERFIL__": PERFIL.get("estado", "—"),
    "__PENDIENTES__": ", ".join(PERFIL.get("campos_pendientes_de_usuario", []) or ["—"]),
}

# El JSON va al final para evitar problemas de replace con caracteres especiales en otros placeholders
out = HTML
for k, v in REPLACES.items():
    out = out.replace(k, v)
# Reemplazo del JSON solo al final (sustitución única exacta)
out = out.replace("__DATA_JSON__", DATA_JSON)

dashboards_dir = ROOT / "dashboards"
dashboards_dir.mkdir(exist_ok=True)
with open(dashboards_dir / "dashboard.html", "w", encoding="utf-8") as f:
    f.write(out)

# Tamaño
size_kb = (dashboards_dir / "dashboard.html").stat().st_size / 1024
print(f"[OK] dashboards/dashboard.html generado ({size_kb:.1f} KB)")
print(f"     Top: {len(SEL.get('top_actual', []))} items, fuera del top: {len(SEL.get('fuera_del_top', []))}, descartados: {len(SEL.get('descartados', []))}")
