"""
Rescata items commodity estatales del Lote B ejec_001 al Lote B2 ejec_002.

Motivo: el agente B2 descartó 13 items commodity por confundir el dedup cross-ejec.
Los items SEITT, Ineco VMware y MUPRESPA UiPath son:
- Sector estatal (slice OK)
- CPV 48xxx (paquetes software)
- Presupuesto 20-200k (filtros OK)
- Plazo abierto (filtros OK)
- Sin IA en producto: el objeto contractual es licencias commodity, no funcionalidades IA.
  (UiPath puede usarse para IA, pero el pliego de MUPRESPA pide licencias puras.)
"""
import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador licitaciones")
LOTE_B1 = ROOT / "data/ejecuciones/ejec_2026-05-15_001/lotes/lote_B_placsp_adyacencias.json"
LOTE_B2 = ROOT / "data/ejecuciones/ejec_2026-05-15_002/lotes/lote_B2_placsp_paquetes_no_ia.json"

RESCATE_IDS = ["20267013-V", "20260417-00172", "PIC2026_33591"]


def main():
    b1 = json.loads(LOTE_B1.read_text(encoding="utf-8"))
    b2 = json.loads(LOTE_B2.read_text(encoding="utf-8"))

    rescatados = []
    for it in b1.get("items_seleccionados", []):
        if it["id_oficial"] in RESCATE_IDS:
            # adaptar campos al esquema modo no_ia_en_producto
            it_copy = dict(it)
            it_copy["ia_en_producto"] = False
            it_copy["razon_sin_ia"] = "Licencias commodity de software empaquetado (PKI/eIDAS, virtualización VMware, RPA UiPath) — el objeto contractual son suscripciones/licencias puras, no funcionalidades IA. Aunque el producto pueda tener capacidades IA, el alcance contratado no las requiere."
            it_copy["aceleracion_ia_construccion"] = "IA acelera oferta: análisis pliego con LLM, redacción memoria técnica, comparativa proveedores, generación matriz cumplimiento."
            it_copy["alertas"] = it.get("alertas", []) + [
                "RESCATADO_DE_EJEC_001_LOTE_B: el subagente B2 descartó por error este item como duplicado del Lote A; aquí se rescata porque CPV y slice encajan."
            ]
            rescatados.append(it_copy)

    # añadir al JSON de B2
    if "items_devueltos" not in b2:
        b2["items_devueltos"] = []
    b2["items_devueltos"].extend(rescatados)
    b2["items_rescatados_de_ejec_001"] = [it["id_oficial"] for it in rescatados]
    b2["items_extraidos_total"] = len(b2.get("items_devueltos", []))
    b2["resumen_rescate"] = f"Rescatados {len(rescatados)} items commodity estatales del Lote B ejec_001 que el agente B2 descartó incorrectamente como duplicados cross-ejec."

    LOTE_B2.write_text(json.dumps(b2, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rescatados {len(rescatados)} items: {[it['id_oficial'] for it in rescatados]}")


if __name__ == "__main__":
    main()
