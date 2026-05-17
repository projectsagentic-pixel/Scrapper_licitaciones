"""
Persiste el estado tras evaluación de una ejecución:
- data/ejecuciones/<ejec>/seleccionados.json  (top vigente de la ejec)
- data/historial_analizados.json              (global cross-ejec, dedup)
- data/ejecuciones.json                       (log global)
"""
import argparse
import json
import pathlib
from datetime import datetime

ROOT = pathlib.Path(r"C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador licitaciones")


def main(ejec_id):
    ejec_dir = ROOT / "data" / "ejecuciones" / ejec_id
    eval_p = ejec_dir / "evaluado.json"
    sel_p = ejec_dir / "seleccionados.json"
    hist_p = ROOT / "data" / "historial_analizados.json"
    log_p = ROOT / "data" / "ejecuciones.json"

    ev = json.loads(eval_p.read_text(encoding="utf-8"))
    HOY = ev["fecha_consolidacion"]
    mode = ev.get("modo", "ia_en_producto")

    # ---- historial global ----
    historial = json.loads(hist_p.read_text(encoding="utf-8"))
    nuevos = 0
    for it in ev["items"]:
        h = it["hash_dedup"]
        if h in historial["items"]:
            # actualizar score si la ejec actual es más reciente
            historial["items"][h]["ejecuciones_vistas"] = list(set(
                historial["items"][h].get("ejecuciones_vistas", []) + [ejec_id]
            ))
            continue
        historial["items"][h] = {
            "id_oficial": it["id_oficial"],
            "fuente": it["fuente"],
            "objeto": (it["objeto"] or "")[:160],
            "organo": it["organo_contratacion"],
            "presupuesto_eur": it["presupuesto_base_eur"],
            "fecha_limite_presentacion": it["fecha_limite_presentacion"],
            "url_oficial": it["url_oficial"],
            "primera_vista": HOY,
            "ejecuciones_vistas": [ejec_id],
            "score_total": it["evaluacion"]["score_total"] if it.get("evaluacion") else None,
            "elegible": it["elegible_para_scoring"],
            "pasa_umbral": it.get("pasa_umbral_top", False),
            "modo_ejec_primera_vista": mode,
        }
        nuevos += 1
    historial["total"] = len(historial["items"])
    hist_p.write_text(json.dumps(historial, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- seleccionados.json (top vigente de la ejec) ----
    top = [it for it in ev["items"] if it.get("pasa_umbral_top")]
    top.sort(key=lambda x: x["evaluacion"]["score_total"], reverse=True)

    def to_dash(it):
        e = it["evaluacion"]
        ev_s = e["scores"]
        por_que = e["por_que"]
        cpvs = [it["cpv_principal"]] + (it.get("cpv_secundarios") or [])
        cpvs = [c for c in cpvs if c]
        return {
            "titulo": (it["objeto"] or "")[:200],
            "organo_contratante": it["organo_contratacion"],
            "descripcion": it["objeto"],
            "cpv_codigos": cpvs,
            "lugar_ejecucion": it["lugar_ejecucion"],
            "presupuesto_base_eur": it["presupuesto_base_eur"],
            "presupuesto_total_eur": it.get("valor_estimado_eur") or it["presupuesto_base_eur"],
            "plazo_presentacion": it["fecha_limite_presentacion"],
            "fuente_principal": it["fuente"],
            "url_oficial": it["url_oficial"],
            "score_total": e["score_total"],
            "utilidad_ia": {"valor": ev_s["utilidad_ia"], "por_que": por_que.get("utilidad_ia", "")},
            "facilidad_ia": {"valor": ev_s["facilidad_ia"], "por_que": por_que.get("facilidad_ia", "")},
            "dificultad": {"valor": ev_s["dificultad"], "por_que": por_que.get("dificultad", "")},
            "encaje_perfil": ev_s["encaje_perfil"],
            "id_oficial": it["id_oficial"],
        }

    seleccionados = {
        "ejecucion_id": ejec_id,
        "modo": mode,
        "ultima_actualizacion": HOY,
        "umbral_top": ev["umbral_top"],
        "total": len(top),
        "top_actual": [to_dash(it) for it in top],
    }
    sel_p.write_text(json.dumps(seleccionados, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- ejecuciones.json (append/update) ----
    if log_p.exists():
        log = json.loads(log_p.read_text(encoding="utf-8"))
    else:
        log = {"ejecuciones": []}

    log["ejecuciones"] = [e for e in log["ejecuciones"] if e["id"] != ejec_id]
    log["ejecuciones"].append({
        "id": ejec_id,
        "fecha": HOY,
        "timestamp": datetime.now().isoformat(),
        "modo": mode,
        "parametros": {
            "presupuesto_min_eur": ev["filtros_estrictos"]["presupuesto_min_eur"],
            "presupuesto_max_eur": ev["filtros_estrictos"]["presupuesto_max_eur"],
            "plazo_minimo_dias": ev["filtros_estrictos"]["plazo_minimo_dias"],
        },
        "pesos_aplicados": ev["pesos_aplicados"],
        "totales": ev["totales"],
        "por_fuente": ev["por_fuente"],
        "resumen_scoring": ev["resumen_scoring"],
        "duplicados_eliminados": len(ev["duplicados_cruzados"]),
        "nuevos_en_historial": nuevos,
        "items_top": [{
            "id_oficial": it["id_oficial"],
            "fuente": it["fuente"],
            "score": it["evaluacion"]["score_total"],
            "objeto": (it["objeto"] or "")[:100],
        } for it in top],
    })
    log["ejecuciones"].sort(key=lambda e: e["id"])
    log_p.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Historial global: {historial['total']} items ({nuevos} nuevos en esta ejec)")
    print(f"Seleccionados ejec: {len(top)} en top")
    print(f"Ejecuciones registradas: {len(log['ejecuciones'])}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejec-id", required=True)
    args = ap.parse_args()
    main(args.ejec_id)
