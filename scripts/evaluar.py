"""
Aplica la rúbrica de criterios.json a los items elegibles del consolidado.

Uso:
  python scripts/evaluar.py --ejec-id ejec_2026-05-15_001 --mode ia_en_producto
  python scripts/evaluar.py --ejec-id ejec_2026-05-15_002 --mode no_ia_en_producto

Modos:
  ia_en_producto       Rúbrica estándar v0.1.0 (premia proyectos donde la IA es central).
  no_ia_en_producto    Drop utilidad_ia (peso 0); redistribuye a facilidad_ia, encaje_perfil, presupuesto.
                       Premia proyectos software clásico viables sin IA, donde la IA solo acelera la construcción.

Los scores cualitativos (utilidad_ia, facilidad_ia, dificultad, encaje_perfil)
los lee de data/ejecuciones/<ejec>/scores_manuales.json. Debe estar relleno antes.
"""
import argparse
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador licitaciones")
CRITERIOS = ROOT / "data" / "criterios.json"


WEIGHTS_BY_MODE = {
    "ia_en_producto": {
        "utilidad_ia": 0.25,
        "facilidad_ia": 0.20,
        "dificultad": 0.15,
        "encaje_perfil": 0.20,
        "presupuesto_atractivo": 0.10,
        "plazo_realista": 0.10,
    },
    "no_ia_en_producto": {
        "utilidad_ia": 0.0,
        "facilidad_ia": 0.30,
        "dificultad": 0.20,
        "encaje_perfil": 0.25,
        "presupuesto_atractivo": 0.15,
        "plazo_realista": 0.10,
    },
}


def score_presupuesto(p):
    if p is None:
        return 0
    if 50000 <= p <= 100000:
        return 10
    if 30000 <= p < 50000:
        return 7 + 3 * (p - 30000) / 20000
    if 100000 < p <= 150000:
        return 10 - 2 * (p - 100000) / 50000
    if 20000 <= p < 30000:
        return 5 + 2 * (p - 20000) / 10000
    if 150000 < p <= 200000:
        return 8 - 4 * (p - 150000) / 50000
    return 3


def score_plazo(dias):
    if dias is None:
        return 0
    if dias >= 21:
        return 10.0
    if dias >= 14:
        return 7.0 + 3.0 * (dias - 14) / 7
    if dias >= 7:
        return (dias - 7) * 1.0
    return 0.0


def evaluate_item(it, scores_manuales, weights):
    sm = scores_manuales.get(it["id_oficial"])
    if sm is None:
        return None
    util = sm.get("utilidad_ia", 0)
    facil = sm.get("facilidad_ia", 0)
    dif = sm.get("dificultad", 0)
    encaje = sm.get("encaje_perfil", 0)
    presup_score = round(score_presupuesto(it["presupuesto_base_eur"]), 2)
    plazo_score = round(score_plazo(it["dias_restantes_presentacion"]), 2)
    dif_norm = 10 - dif
    total = (
        weights["utilidad_ia"] * util +
        weights["facilidad_ia"] * facil +
        weights["dificultad"] * dif_norm +
        weights["encaje_perfil"] * encaje +
        weights["presupuesto_atractivo"] * presup_score +
        weights["plazo_realista"] * plazo_score
    )
    return {
        "scores": {
            "utilidad_ia": util,
            "facilidad_ia": facil,
            "dificultad": dif,
            "dificultad_invertida": dif_norm,
            "encaje_perfil": encaje,
            "presupuesto_atractivo": presup_score,
            "plazo_realista": plazo_score,
        },
        "score_total": round(total, 2),
        "por_que": sm.get("por_que", {}),
    }


def main(ejec_id, mode):
    ejec_dir = ROOT / "data" / "ejecuciones" / ejec_id
    consolidado_p = ejec_dir / "consolidado.json"
    scores_p = ejec_dir / "scores_manuales.json"
    out_p = ejec_dir / "evaluado.json"

    consolidado = json.loads(consolidado_p.read_text(encoding="utf-8"))
    criterios = json.loads(CRITERIOS.read_text(encoding="utf-8"))
    weights = WEIGHTS_BY_MODE[mode]
    umbral = criterios.get("umbral_top", 6.5)

    if not scores_p.exists():
        print(f"ERROR: falta {scores_p}. Crea scores manuales por id_oficial antes de evaluar.")
        return
    scores_manuales = json.loads(scores_p.read_text(encoding="utf-8"))

    sin_score = []
    for it in consolidado["items"]:
        if it["elegible_para_scoring"]:
            ev = evaluate_item(it, scores_manuales, weights)
            if ev is None:
                sin_score.append(it["id_oficial"])
                it["evaluacion"] = None
                it["pasa_umbral_top"] = False
            else:
                it["evaluacion"] = ev
                it["pasa_umbral_top"] = ev["score_total"] >= umbral
        else:
            it["evaluacion"] = None
            it["pasa_umbral_top"] = False

    if sin_score:
        print(f"AVISO: items elegibles sin score manual ({len(sin_score)}): {sin_score[:5]}…")

    scored = [it for it in consolidado["items"] if it.get("evaluacion")]
    scored.sort(key=lambda x: x["evaluacion"]["score_total"], reverse=True)

    consolidado["modo"] = mode
    consolidado["pesos_aplicados"] = weights
    consolidado["umbral_top"] = umbral
    consolidado["resumen_scoring"] = {
        "items_evaluados": len(scored),
        "items_pasan_umbral": sum(1 for it in scored if it["pasa_umbral_top"]),
        "top_score": scored[0]["evaluacion"]["score_total"] if scored else None,
        "bottom_score": scored[-1]["evaluacion"]["score_total"] if scored else None,
    }

    out_p.write_text(json.dumps(consolidado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito: {out_p}")
    print(f"Items evaluados: {len(scored)} / Pasan umbral ({umbral}): {consolidado['resumen_scoring']['items_pasan_umbral']}")
    print()
    print("=== TOP 10 ===")
    for it in scored[:10]:
        s = it["evaluacion"]["score_total"]
        print(f"  {s:>5.2f}  [{it['fuente']}] {it['id_oficial']:<25} {(it['presupuesto_base_eur'] or 0):>9.0f}€  {(it['objeto'] or '')[:70]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejec-id", required=True)
    ap.add_argument("--mode", choices=list(WEIGHTS_BY_MODE.keys()), required=True)
    args = ap.parse_args()
    main(args.ejec_id, args.mode)
