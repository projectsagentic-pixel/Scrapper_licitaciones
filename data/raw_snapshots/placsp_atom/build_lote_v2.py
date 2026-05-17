"""Build final lote_A_placsp_nucleo.json — applying v0.2.0 auto-discards (horas_servicio + presencial_continuada)."""
import sys
sys.path.insert(0, '.')
import build_lote as bl
import json
import datetime
import os

matches = bl.matches
CLASS = bl.CLASS
data = bl.data
cpv_score = bl.cpv_score

# Build final lote with v0.2.0 auto-discards applied
ms = sorted(matches, key=cpv_score, reverse=True)

items_descartados_fuera_scope = 0
items_descartados_tipo_horas_y_presencial = 0
items_descartados_solo_horas = 0  # Note: horas_servicio alone is an auto-discard per criterios.json
items_descartados_solo_presencial = 0

selected = []  # list of (m, cls)

for m in ms:
    cls = CLASS.get(m["id_oficial"])
    if cls is None:
        # Marked as out-of-scope or not in CLASS — already handled M5/M6
        continue
    tipo = cls.get("tipo_objeto")
    lugar = cls.get("lugar_prestacion")

    # Per criterios.json v0.2.0 descartes_automaticos:
    # - tipo_objeto = 'horas_servicio' explícito → descarte
    # - lugar_prestacion = 'presencial_continuada' obligatorio → descarte
    if tipo == "horas_servicio" and lugar == "presencial_continuada":
        items_descartados_tipo_horas_y_presencial += 1
        continue
    if tipo == "horas_servicio":
        # Strict per rúbrica v0.2.0
        items_descartados_solo_horas += 1
        continue
    if lugar == "presencial_continuada":
        items_descartados_solo_presencial += 1
        continue
    selected.append((m, cls))

# M5-2026, M6-2026 out of scope
for mid in ("M5-2026", "M6-2026"):
    if mid in CLASS and CLASS[mid] is None:
        items_descartados_fuera_scope += 1

total_descartados_auto = (items_descartados_fuera_scope
                         + items_descartados_tipo_horas_y_presencial
                         + items_descartados_solo_horas
                         + items_descartados_solo_presencial)

print(f"Seleccionados (post auto-descartes): {len(selected)}")
print(f"  descartados horas+presencial: {items_descartados_tipo_horas_y_presencial}")
print(f"  descartados solo horas: {items_descartados_solo_horas}")
print(f"  descartados solo presencial: {items_descartados_solo_presencial}")
print(f"  descartados fuera scope (sensórica): {items_descartados_fuera_scope}")

# Limit to 20
NOW_ISO = datetime.datetime(2026, 5, 16, 21, 0, 0).isoformat() + "+02:00"
entries = []
for m, cls in selected:
    if len(entries) >= 20:
        break
    entry = {
        "hash": m["hash"],
        "id_oficial": m["id_oficial"],
        "url_oficial": m["url_oficial"],
        "fuente": "PLACSP",
        "fecha_visto": NOW_ISO,
        "datos": {
            "titulo": m["titulo"],
            "descripcion": m["descripcion"] if m["descripcion"] else m["summary_atom"],
            "organo_contratante": m["organo_contratante"],
            "presupuesto_base_eur": m["presupuesto_base_eur"],
            "presupuesto_total_eur": m["presupuesto_total_eur"],
            "plazo_presentacion": m["plazo_presentacion"],
            "cpv_codigos": m["cpv_codigos"],
            "lugar_ejecucion": m["lugar_ejecucion"],
            "url_pliego_pcap": m["url_pliego_pcap"],
            "url_pliego_ppt": m["url_pliego_ppt"],
            "tipo_objeto": cls["tipo_objeto"],
            "evidencia_tipo_objeto": cls["evidencia_tipo_objeto"],
            "lugar_prestacion": cls["lugar_prestacion"],
            "evidencia_lugar_prestacion": cls["evidencia_lugar_prestacion"],
            "dificultad": cls["dificultad"],
            "facilidad_ia": cls["facilidad_ia"],
            "utilidad_ia": cls["utilidad_ia"],
            "principales_desafios": cls["principales_desafios"],
            "ideas_clave": cls["ideas_clave"],
        },
        "fuentes_corroboradas": ["PLACSP"],
        "scoring_local": {
            "utilidad_ia": cls["utilidad_ia"],
            "facilidad_ia": cls["facilidad_ia"],
            "dificultad": cls["dificultad"],
        },
    }
    entries.append(entry)

print(f"Items observados (cap 20): {len(entries)}")

lote = {
    "lote_id": "lote_A_placsp_nucleo",
    "ejecucion_id": "ejec_2026-05-16_001",
    "fuente": "PLACSP",
    "fecha": "2026-05-16",
    "metodo": "feed_atom",
    "queries_usadas": [
        "feed_atom_PLACSP_mensual:licitacionesPerfilesContratanteCompleto3_202605.zip",
        "filtro_cpv:72000000|72200000|72260000|prefijos 722* 7226*",
        "filtro_presupuesto:20000-200000_EUR_TaxExclusiveAmount",
        "filtro_estado:PUB",
        "filtro_plazo_minimo_dias:7",
    ],
    "items_extraidos_total": data["total_raw"],
    "items_descartados_por_fetch_fallido": 0,
    "items_descartados_por_descarte_automatico": total_descartados_auto,
    "desglose_descartes_automaticos": {
        "fuera_scope_software_it": items_descartados_fuera_scope,
        "tipo_horas_servicio_y_presencial_continuada": items_descartados_tipo_horas_y_presencial,
        "tipo_horas_servicio": items_descartados_solo_horas,
        "lugar_presencial_continuada": items_descartados_solo_presencial,
    },
    "items_descartados_por_dedup": data["descartes_dedup"],
    "items_observados": entries,
    "limitaciones": (
        "Datos extraídos del feed ATOM mensual oficial de PLACSP (mecanismo de sindicación de la DG Patrimonio - "
        "licitacionesPerfilesContratanteCompleto3_202605.zip). Las URLs apuntan al expediente individual "
        "(deeplink:detalle_licitacion) tal como las publica PLACSP en cada <entry>. "
        "El feed ATOM trae summary, cbc:Name, presupuesto, plazo, CPV, órgano y URLs de pliegos pero NO el texto completo del pliego; "
        "la clasificación tipo_objeto / lugar_prestacion se ha realizado a partir del título y nombre del proyecto. "
        "Cuando el texto no era concluyente se ha usado 'indeterminado' o 'mixto' para que lic-evaluador desempate consultando los pliegos individuales. "
        "Aplicados los descartes automáticos v0.2.0: tipo_objeto='horas_servicio' (asistencia técnica / cuerpo de consultores / oficina técnica / mantenimiento puro) "
        "y lugar_prestacion='presencial_continuada' (Defensa con habilitación HSEC, información clasificada). "
        "Se descartaron también 2 items con CPV 72260000 marginal (M5/M6-2026, sensores físicos en Blanca) por estar fuera del scope software/IT. "
        "Hashes calculados con sha256(id_oficial)[:16]; 5 IDs descartados por estar en hashes_a_evitar. "
        "El acceso a los expedientes individuales vía web requiere certificado en muchos casos; el feed ATOM es la vía estable y autorizada."
    ),
}

out_path = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "ejecuciones", "ejec_2026-05-16_001", "lotes", "lote_A_placsp_nucleo.json"
))
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(lote, f, indent=2, ensure_ascii=False)
print(f"Lote saved: {out_path}")
print(f"Items in lote: {len(entries)}")
