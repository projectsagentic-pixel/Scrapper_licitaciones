"""
Calcula metricas_fuentes.json para una ejecución.
"""
import argparse
import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(r"C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador licitaciones")


def main(ejec_id):
    ejec_dir = ROOT / "data" / "ejecuciones" / ejec_id
    ev = json.loads((ejec_dir / "evaluado.json").read_text(encoding="utf-8"))
    out_p = ejec_dir / "metricas_fuentes.json"

    items = ev["items"]
    duplicados = ev["duplicados_cruzados"]

    bruto_por_fuente = defaultdict(int)
    for it in items:
        bruto_por_fuente[it["fuente"]] += 1
    for d in duplicados:
        bruto_por_fuente[d["item_descartado"]["fuente"]] += 1

    unicos_por_fuente = defaultdict(int)
    corroborados_por_fuente = defaultdict(int)
    top_por_fuente = defaultdict(int)
    score_top_por_fuente = defaultdict(list)
    presup_top_por_fuente = defaultdict(list)
    for it in items:
        f = it["fuente"]
        unicos_por_fuente[f] += 1
        if it.get("solapamiento_placsp") or it.get("solapamiento_boe"):
            corroborados_por_fuente[f] += 1
        if it.get("pasa_umbral_top"):
            top_por_fuente[f] += 1
            score_top_por_fuente[f].append(it["evaluacion"]["score_total"])
            if it["presupuesto_base_eur"]:
                presup_top_por_fuente[f].append(it["presupuesto_base_eur"])

    fuentes_def = ["PLACSP", "BOE", "AUTONOMICO"]
    fuentes_metric = []
    for f in fuentes_def:
        total = bruto_por_fuente.get(f, 0)
        unicos = unicos_por_fuente.get(f, 0)
        en_top = top_por_fuente.get(f, 0)
        scores = score_top_por_fuente.get(f, [])
        presups = presup_top_por_fuente.get(f, [])
        fuentes_metric.append({
            "nombre": f,
            "n_items_total": total,
            "n_items_unicos": unicos,
            "n_items_corroborados": corroborados_por_fuente.get(f, 0),
            "n_en_top_actual": en_top,
            "ratio_top_sobre_total": (en_top / total) if total else 0,
            "score_medio_top": (sum(scores) / len(scores)) if scores else 0,
            "presupuesto_medio_top_eur": (sum(presups) / len(presups)) if presups else None,
        })

    solapamiento = defaultdict(int)
    for d in duplicados:
        a = d["item_descartado"]["fuente"]
        b = d["mantenido"]["fuente"]
        pair = tuple(sorted([a, b]))
        if a != b:
            solapamiento[f"{pair[0]}_{pair[1]}"] += 1
    for it in items:
        if it["fuente"] == "BOE" and it.get("solapamiento_placsp"):
            solapamiento["BOE_PLACSP"] += 1
        if it["fuente"] == "AUTONOMICO" and it.get("solapamiento_placsp"):
            solapamiento["AUTONOMICO_PLACSP"] += 1

    diagnostico = []
    boe = next(f for f in fuentes_metric if f["nombre"] == "BOE")
    auto = next(f for f in fuentes_metric if f["nombre"] == "AUTONOMICO")
    placsp = next(f for f in fuentes_metric if f["nombre"] == "PLACSP")

    if boe["n_items_unicos"] > 0 and boe["n_en_top_actual"] == 0:
        diagnostico.append(f"BOE: {boe['n_items_unicos']} items, 0 al top — fuente débil para este perfil <200k.")
    if auto["n_items_unicos"] > 0 and auto["n_en_top_actual"] == 0:
        diagnostico.append(f"AUTONÓMICO: {auto['n_items_unicos']} items, 0 al top — revisar accesibilidad técnica de plataformas regionales.")
    total_top = sum(f["n_en_top_actual"] for f in fuentes_metric)
    if total_top > 0 and placsp["n_en_top_actual"] == total_top:
        diagnostico.append(f"PLACSP única fuente que aporta al top ({total_top}/{total_top}). Centraliza el mercado TI <200k.")
    if solapamiento.get("BOE_PLACSP", 0) > 0:
        diagnostico.append(f"Solapamiento BOE↔PLACSP: {solapamiento['BOE_PLACSP']} items. BOE no aporta exclusividad.")

    out = {
        "ejec_id": ejec_id,
        "fecha_calculo": ev["fecha_consolidacion"],
        "modo": ev.get("modo"),
        "fuentes": fuentes_metric,
        "solapamiento": dict(solapamiento),
        "diagnostico": diagnostico,
    }
    out_p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito: {out_p}")
    for f in fuentes_metric:
        print(f"  {f['nombre']:<12} total={f['n_items_total']:>3} unicos={f['n_items_unicos']:>3} top={f['n_en_top_actual']:>2} score_medio={f['score_medio_top']:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejec-id", required=True)
    args = ap.parse_args()
    main(args.ejec_id)
