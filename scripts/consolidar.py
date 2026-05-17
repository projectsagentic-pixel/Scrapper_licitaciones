"""
Consolida los lotes de una ejecución en un único consolidado.json.
Aplica dedup cruzado y marca elegibilidad según filtros estrictos.

Uso: python scripts/consolidar.py --ejec-id ejec_2026-05-15_002
"""
import argparse
import json
import hashlib
import pathlib
import unicodedata
from datetime import date

ROOT = pathlib.Path(r"C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador licitaciones")
HOY = date(2026, 5, 15)
PRESUP_MIN = 20000
PRESUP_MAX = 200000
PLAZO_MIN_DIAS = 14


def norm_text(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def make_hash(item):
    objeto = norm_text(item.get("objeto", ""))[:80]
    organo = norm_text(item.get("organo_contratacion", ""))[:60]
    presup = item.get("presupuesto_base_eur") or 0
    raw = f"{objeto}|{organo}|{round(presup, 2)}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


PORTAL_ROOT_PATTERNS = (
    "/inicio/", "/inici", "/portada", "/index.html", "/buscar",
    "contratacion.euskadi.eus/inicio",
    "contractaciopublica.cat/ca/inici",
    "contratosdegalicia.gal/portada",
    "juntadeandalucia.es/temas/contratacion-publica",
    "madrid.org/contratos-publicos",
)


def make_url_hash(url):
    if not url:
        return None
    if "idEvl=" in url:
        return "placsp:" + url.split("idEvl=")[1].split("&")[0]
    low = url.lower()
    if any(p in low for p in PORTAL_ROOT_PATTERNS):
        if low.count("/") <= 4 or low.endswith(("/inicio/", "/inici", "/portada.jsp?lang=es")):
            return None
    return "url:" + hashlib.sha256(url.encode()).hexdigest()[:12]


def normalize_item(raw, lote_id, fuente):
    presup = raw.get("presupuesto_base_eur")
    dias = raw.get("dias_restantes_presentacion")
    if dias is None:
        flim = raw.get("fecha_limite_presentacion")
        if flim:
            try:
                fl = date.fromisoformat(flim)
                dias = (fl - HOY).days
            except Exception:
                dias = None

    item = {
        "lote_origen": lote_id,
        "fuente": fuente,
        "id_oficial": raw.get("id_oficial"),
        "objeto": raw.get("objeto"),
        "organo_contratacion": raw.get("organo_contratacion"),
        "plataforma_autonomica": raw.get("plataforma_autonomica"),
        "url_oficial": raw.get("url_oficial"),
        "url_secundaria_placsp": raw.get("url_secundaria_placsp"),
        "solapamiento_placsp": raw.get("solapamiento_placsp"),
        "presupuesto_base_eur": presup,
        "presupuesto_incluye_iva": raw.get("presupuesto_incluye_iva"),
        "valor_estimado_eur": raw.get("valor_estimado_eur"),
        "fecha_publicacion": raw.get("fecha_publicacion") or raw.get("fecha_publicacion_boe"),
        "fecha_limite_presentacion": raw.get("fecha_limite_presentacion"),
        "dias_restantes_presentacion": dias,
        "cpv_principal": raw.get("cpv_principal"),
        "cpv_secundarios": raw.get("cpv_secundarios", []),
        "tipo_procedimiento": raw.get("tipo_procedimiento"),
        "tipo_contrato": raw.get("tipo_contrato"),
        "lugar_ejecucion": raw.get("lugar_ejecucion"),
        "tiene_pliego_tecnico_accesible": raw.get("tiene_pliego_tecnico_accesible"),
        "url_pliego_tecnico": raw.get("url_pliego_tecnico"),
        # Campos comunes
        "componente_ia_potencial": raw.get("componente_ia_potencial"),
        # Campos para modo no_ia_en_producto
        "ia_en_producto": raw.get("ia_en_producto"),
        "razon_sin_ia": raw.get("razon_sin_ia"),
        "aceleracion_ia_construccion": raw.get("aceleracion_ia_construccion"),
        "alertas": raw.get("alertas", []),
        "notas_verificacion": raw.get("notas_verificacion"),
    }
    item["hash_dedup"] = make_hash(item)
    item["url_hash"] = make_url_hash(item["url_oficial"])
    return item


def apply_filters(item):
    motivos = []
    p = item["presupuesto_base_eur"]
    d = item["dias_restantes_presentacion"]
    if p is None:
        motivos.append("presupuesto_no_visible")
    else:
        if p < PRESUP_MIN:
            motivos.append(f"presupuesto<{PRESUP_MIN}")
        if p > PRESUP_MAX:
            motivos.append(f"presupuesto>{PRESUP_MAX}")
    if d is None:
        motivos.append("plazo_no_visible")
    elif d < PLAZO_MIN_DIAS:
        motivos.append(f"plazo<{PLAZO_MIN_DIAS}d")
    item["elegible_para_scoring"] = (len(motivos) == 0)
    item["motivos_no_elegible"] = motivos
    return item


def discover_lotes(lotes_dir):
    """Devuelve [(filename, lote_id, fuente, items_key)] inspeccionando los JSON."""
    out = []
    for p in sorted(lotes_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        # detectar campo items
        items_key = None
        for k in ("items_devueltos", "items_seleccionados", "items"):
            if k in data and isinstance(data[k], list):
                items_key = k
                break
        if items_key is None:
            continue
        lote_id = data.get("lote", p.stem.split("_")[1] if "_" in p.stem else "?")
        fuente = data.get("fuente") or data.get("fuente_principal", "?")
        out.append((p.name, lote_id, fuente, items_key))
    return out


def main(ejec_id):
    ejec_dir = ROOT / "data" / "ejecuciones" / ejec_id
    lotes_dir = ejec_dir / "lotes"
    out_path = ejec_dir / "consolidado.json"

    todos = []
    metadata_lotes = discover_lotes(lotes_dir)
    print(f"Lotes detectados en {ejec_id}:")
    for fname, lote_id, fuente, ikey in metadata_lotes:
        path = lotes_dir / fname
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get(ikey, [])
        print(f"  - {fname}  lote={lote_id}  fuente={fuente}  items={len(items)}")
        todos += [normalize_item(r, lote_id, fuente) for r in items]

    print(f"Total bruto: {len(todos)}")

    seen_hash = {}
    seen_url = {}
    deduped = []
    duplicados = []
    for it in todos:
        h = it["hash_dedup"]
        uh = it["url_hash"]
        dup_match = None
        if h in seen_hash:
            dup_match = seen_hash[h]
        elif uh and uh in seen_url:
            dup_match = seen_url[uh]
        if dup_match is not None:
            duplicados.append({
                "item_descartado": {"lote": it["lote_origen"], "id_oficial": it["id_oficial"], "fuente": it["fuente"], "objeto": (it["objeto"] or "")[:80]},
                "mantenido": {"lote": dup_match["lote_origen"], "id_oficial": dup_match["id_oficial"], "fuente": dup_match["fuente"]},
                "razon": "hash_dedup_match" if h in seen_hash else "url_hash_match",
            })
            if it["fuente"] == "BOE" and dup_match["fuente"] == "PLACSP":
                dup_match["solapamiento_boe"] = True
                dup_match["url_boe"] = it["url_oficial"]
            continue
        seen_hash[h] = it
        if uh:
            seen_url[uh] = it
        deduped.append(it)

    print(f"Tras dedup: {len(deduped)} (duplicados: {len(duplicados)})")

    for it in deduped:
        apply_filters(it)

    elegibles = [it for it in deduped if it["elegible_para_scoring"]]
    no_elegibles = [it for it in deduped if not it["elegible_para_scoring"]]
    print(f"Elegibles: {len(elegibles)}  /  No elegibles: {len(no_elegibles)}")

    por_fuente = {}
    for it in deduped:
        f = it["fuente"]
        por_fuente.setdefault(f, {"total": 0, "elegibles": 0, "no_elegibles": 0})
        por_fuente[f]["total"] += 1
        if it["elegible_para_scoring"]:
            por_fuente[f]["elegibles"] += 1
        else:
            por_fuente[f]["no_elegibles"] += 1

    out = {
        "ejec_id": ejec_id,
        "fecha_consolidacion": HOY.isoformat(),
        "filtros_estrictos": {
            "presupuesto_min_eur": PRESUP_MIN,
            "presupuesto_max_eur": PRESUP_MAX,
            "plazo_minimo_dias": PLAZO_MIN_DIAS,
            "fecha_corte_plazo_min": "2026-05-29",
        },
        "totales": {
            "items_brutos": len(todos),
            "items_tras_dedup": len(deduped),
            "duplicados_eliminados": len(duplicados),
            "elegibles_para_scoring": len(elegibles),
            "no_elegibles": len(no_elegibles),
        },
        "por_fuente": por_fuente,
        "duplicados_cruzados": duplicados,
        "items": deduped,
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito: {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejec-id", required=True)
    args = ap.parse_args()
    main(args.ejec_id)
