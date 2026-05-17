"""
Consolidación + evaluación v0.2.0 — ejec_2026-05-16_001.

Pasos:
 1. Carga los 5 lotes
 2. Dedup cruzado: hash + id_oficial + referencia_placsp (BOE)
 3. Evalúa cada item NUEVO con rúbrica v0.2.0
 4. Aplica descartes automáticos (incl. tipo_objeto=horas_servicio y lugar_prestacion=presencial_continuada)
 5. Re-evalúa historial previo con rúbrica v0.2.0 (items legacy: modelo_entrega y autonomia_infra = 5 neutro por falta de evidencia)
 6. Persiste consolidado.json, evaluado.json, seleccionados.json, historial_analizados.json
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:/Users/JosebaPortasAbalde/Documents/DEV personal/buscador licitaciones")
EJEC_ID = "ejec_2026-05-16_001"
EJEC_DIR = ROOT / "data" / "ejecuciones" / EJEC_ID
LOTES = [
    "lote_A_placsp_nucleo",
    "lote_B_placsp_adyacencias",
    "lote_C_placsp_id_sistemas",
    "lote_D_boe",
    "lote_E_autonomico",
]

with open(ROOT / "data" / "criterios.json", "r", encoding="utf-8") as f:
    CRITERIOS = json.load(f)

VERSION_CRITERIOS = CRITERIOS["version"]
PESOS = {f["nombre"]: f["peso"] for f in CRITERIOS["factores"]}
UMBRAL_TOP = CRITERIOS["umbral_top"]

# ---------------------------------------------------------------------------
# 1. Carga lotes y consolidación con dedup
# ---------------------------------------------------------------------------

items_por_hash = {}
items_descartados_dedup = 0
desglose_por_fuente = {}

for nombre_lote in LOTES:
    path = EJEC_DIR / "lotes" / f"{nombre_lote}.json"
    if not path.exists():
        print(f"[WARN] {nombre_lote}: no existe")
        continue
    with open(path, "r", encoding="utf-8") as f:
        lote = json.load(f)
    fuente = lote.get("fuente", "?")
    desglose_por_fuente.setdefault(fuente, {"recibidos": 0, "consolidados": 0, "dedup_cruzados": 0})
    items = lote.get("items_observados") or lote.get("items") or []
    for it in items:
        desglose_por_fuente[fuente]["recibidos"] += 1
        h = it.get("hash")
        idof = it.get("id_oficial")
        ref_placsp = (it.get("datos") or {}).get("referencia_placsp")

        # Dedup por hash
        if h and h in items_por_hash:
            existing = items_por_hash[h]
            if fuente not in existing.get("fuentes_corroboradas", []):
                existing.setdefault("fuentes_corroboradas", []).append(fuente)
            existing.setdefault("urls_corroboradas", {})[fuente] = it.get("url_oficial")
            desglose_por_fuente[fuente]["dedup_cruzados"] += 1
            items_descartados_dedup += 1
            continue

        # Dedup cruzado por id_oficial
        cross_match = None
        for h_existing, existing in items_por_hash.items():
            if existing.get("id_oficial") == idof and idof:
                cross_match = existing
                break
            # Match BOE → PLACSP via referencia_placsp
            existing_ref = (existing.get("datos") or {}).get("referencia_placsp")
            if ref_placsp and (existing.get("id_oficial") == ref_placsp or existing_ref == idof):
                cross_match = existing
                break
        if cross_match:
            if fuente not in cross_match.get("fuentes_corroboradas", []):
                cross_match.setdefault("fuentes_corroboradas", []).append(fuente)
            cross_match.setdefault("urls_corroboradas", {})[fuente] = it.get("url_oficial")
            desglose_por_fuente[fuente]["dedup_cruzados"] += 1
            items_descartados_dedup += 1
            continue

        # Nuevo item
        if not h:
            continue
        items_por_hash[h] = it
        items_por_hash[h].setdefault("urls_corroboradas", {})[fuente] = it.get("url_oficial")
        desglose_por_fuente[fuente]["consolidados"] += 1

consolidado_items = list(items_por_hash.values())
print(f"[CONSOLIDACIÓN] {len(consolidado_items)} items únicos consolidados, {items_descartados_dedup} dedup cruzados")
print(f"[POR FUENTE] {json.dumps(desglose_por_fuente, indent=2)}")

# ---------------------------------------------------------------------------
# 2. Evaluación con rúbrica v0.2.0
# ---------------------------------------------------------------------------

# Heurística textual para inferir tipo_objeto/lugar_prestacion cuando falta o es indeterminado
RE_HORAS = re.compile(
    r"(servicios?\s+de\s+apoyo|asistencia\s+t[eé]cnica|bolsa\s+de\s+horas|cuerpo\s+(de\s+)?(t[eé]cnico|consultores)|"
    r"perfiles?\s+a\s+demanda|jornadas\s+t[eé]cnicas|horas\s+estimadas|soporte\s+funcional|"
    r"apoyo\s+a\s+usuarios|consultor[ií]a\s+a\s+demanda|gesti[oó]n\s+y\s+tramitaci[oó]n|"
    r"coordinaci[oó]n\s+de\s+(las\s+)?tareas|trabajos\s+de\s+modelado|servicio\s+de\s+apoyo|"
    r"asistencia\s+(t[eé]cnica\s+)?especializada)",
    re.IGNORECASE,
)
RE_PRESENCIAL = re.compile(
    r"(presencia\s+f[ií]sica\s+continuada|habilitaci[oó]n\s+(de\s+)?seguridad\s+personal|"
    r"dependencias\s+del\s+[oó]rgano|in\s+situ\s+(en|de)?|trabajos\s+en\s+las\s+instalaciones|"
    r"sede\s+del\s+(cliente|[oó]rgano)|red\s+SARA|defensa\s+clasificado|HSEC\s+obligatori)",
    re.IGNORECASE,
)
RE_ENTREGABLE = re.compile(
    r"(desarrollo\s+e\s+implantaci[oó]n|implantaci[oó]n\s+de\s+(la\s+)?(plataforma|sistema|aplicaci[oó]n)|"
    r"migraci[oó]n\s+tecnol[oó]gica|construcci[oó]n\s+del\s+sistema|implementaci[oó]n\s+de|"
    r"creaci[oó]n\s+de\s+(la\s+)?(web|portal|aplicaci[oó]n)|dise[ñn]o\s+(,\s+producci[oó]n\s+)?e\s+implantaci[oó]n|"
    r"plataforma\s+web|portal\s+(institucional|corporativo)|sistema\s+de\s+gesti[oó]n|"
    r"app(licaci[oó]n)?\s+(m[oó]vil|web)|software\s+a\s+medida|integraci[oó]n\s+con\s+\w+)",
    re.IGNORECASE,
)


def inferir_tipo_objeto(texto):
    """Heurística textual → (tipo_objeto, evidencia_inferida, confianza)"""
    if not texto:
        return ("indeterminado", "Sin texto disponible para inferir", "baja")
    t = texto[:1500]
    m_horas = RE_HORAS.search(t)
    m_entreg = RE_ENTREGABLE.search(t)
    if m_horas and not m_entreg:
        return ("horas_servicio", f"Patrón texto: '{m_horas.group(0)}'", "media")
    if m_entreg and not m_horas:
        return ("entregable_definido", f"Patrón texto: '{m_entreg.group(0)}'", "media")
    if m_entreg and m_horas:
        return ("mixto", f"Coexisten patrones entregable='{m_entreg.group(0)}' y horas='{m_horas.group(0)}'", "media")
    return ("indeterminado", "Sin patrones claros en el texto", "baja")


def inferir_lugar_prestacion(texto):
    if not texto:
        return ("indeterminado", "Sin texto disponible para inferir", "baja")
    t = texto[:1500]
    m = RE_PRESENCIAL.search(t)
    if m:
        return ("presencial_continuada", f"Patrón texto: '{m.group(0)}'", "media")
    return ("indeterminado", "Sin patrones de presencialidad continuada", "baja")


def puntuar_modelo_entrega(tipo_objeto, evidencia):
    tabla = {
        "entregable_definido": (9, "Pliego identifica entregables/productos con alcance cerrado"),
        "mixto": (5, "Combinación de entregable y horas/soporte"),
        "horas_servicio": (0, "Bolsa de horas / asistencia técnica / cuerpo de consultores"),
        "indeterminado": (5, "Sin evidencia clara — nota neutra hasta verificar pliego"),
    }
    valor, why_base = tabla.get(tipo_objeto, (5, "Sin clasificar"))
    why = f"{why_base}. Evidencia: «{(evidencia or '—')[:160]}»"
    return {"valor": valor, "por_que": why, "evidencia": (evidencia or "")[:200]}


def puntuar_autonomia_infra(lugar_prestacion, evidencia):
    tabla = {
        "remoto": (10, "Entrega de artefacto o SaaS sin presencia física"),
        "mixto": (6, "Combina trabajo remoto con coordinación puntual presencial"),
        "infra_cliente": (6, "Desarrollo remoto, despliegue obligatorio en infra cliente"),
        "presencial_continuada": (0, "Presencia física continuada en sede del cliente o habilitación de seguridad"),
        "indeterminado": (5, "Sin evidencia clara — nota neutra hasta verificar pliego"),
    }
    valor, why_base = tabla.get(lugar_prestacion, (5, "Sin clasificar"))
    why = f"{why_base}. Evidencia: «{(evidencia or '—')[:160]}»"
    return {"valor": valor, "por_que": why, "evidencia": (evidencia or "")[:200]}


def _coerce_num(v):
    """Algunos lotes guardan {'valor': X, 'por_que': ...}; otros guardan un int directo."""
    if v is None:
        return None
    if isinstance(v, dict):
        return v.get("valor")
    return v


# ============================================================================
# DETECCIÓN HEURÍSTICA DE SEÑALES v0.3.0
# ============================================================================
# Catálogo de 12 señales operativas. Cada señal busca patrones textuales en
# título+descripción. Devuelve confianza ('alta'|'media'|'baja') o None.

import re as _re_senales

SENALES_PATRONES = {
    # POSITIVAS (suman a spec_driven_fit)
    "stack_mainstream": [
        (r"\b(react|angular|vue|next\.?js|nuxt|svelte|astro|node|nodejs)\b", "alta"),
        (r"\b(django|rails|laravel|fastapi|spring|express|flask|symfony|\.net|asp\.?net)\b", "alta"),
        (r"\b(postgres|mysql|mariadb|mongodb|redis|elasticsearch)\b", "media"),
        (r"\b(docker|kubernetes|k8s|terraform|ansible)\b", "media"),
        (r"\b(api\s+rest|rest\s*ful|microservicios?|microservices?|openapi|swagger|graphql)\b", "alta"),
        (r"\b(cms|wordpress|drupal|liferay|sharepoint)\b", "media"),
        (r"\b(aws|amazon\s+web|azure|gcp|google\s+cloud|cloud)\b", "media"),
        (r"\b(java|python|javascript|typescript|php)\b", "baja"),
    ],
    "crud_masivo": [
        (r"\b(sistema\s+de\s+gesti[oó]n|gestor\s+integral|backoffice|back-?office|administraci[oó]n\s+integral)\b", "alta"),
        (r"\b(multi[\s-]?(rol|tenant|usuario|sede|m[oó]dulo))\b", "alta"),
        (r"\b(crud|abm|alta\s+baja\s+modificaci[oó]n|altas?\s+y\s+bajas)\b", "alta"),
        (r"\b(panel\s+de\s+(control|gesti[oó]n|administraci[oó]n))\b", "media"),
        (r"\b(formulario|registro\s+de|fichas?\s+de|expedientes?)\b", "baja"),
    ],
    "integraciones_estandar": [
        (r"\b(face|cl@?ve|eidas|aeat\s*sii|sii\s*aeat|ens|@firma|autenticaci[oó]n\s+integrada|oauth|oidc|saml)\b", "alta"),
        (r"\b(rest|openapi|swagger|odata)\b", "alta"),
        (r"\b(integraci[oó]n\s+con|conector|api\s+(p[uú]blica|abierta|est[aá]ndar))\b", "media"),
        (r"\b(interoperabilidad|sni|notific@?|sara)\b", "media"),
        (r"\b(factura\s+(electr[oó]nica|e))\b", "media"),
    ],
    "logica_mecanica": [
        (r"\b(workflow|flujo\s+de\s+trabajo|tramitaci[oó]n\s+autom[aá]tica|expediente\s+electr[oó]nico|firma\s+electr[oó]nica)\b", "alta"),
        (r"\b(validaciones?|reglas\s+de\s+negocio|c[aá]lculos?|liquidaci[oó]n|motor\s+de\s+(c[aá]lculo|reglas))\b", "alta"),
        (r"\b(automatizaci[oó]n|automatizar|procedimiento\s+automatizado)\b", "media"),
        (r"\b(notificaciones?|alertas?|reportes?\s+autom[aá]ticos?)\b", "baja"),
    ],
    "boilerplate_alto": [
        (r"\b(multi[\s-]?(idioma|lenguaje|i18n)|internacionalizaci[oó]n)\b", "media"),
        (r"\b(multi[\s-]?tenant|multi[\s-]?inquilino)\b", "alta"),
        (r"\b(accesibilidad|wcag|une\s*139803|une\s*en\s*301549)\b", "media"),
        (r"\b(rgpd|gdpr|esquema\s+nacional\s+de\s+seguridad)\b", "baja"),
        (r"\b(monitorizaci[oó]n|observabilidad|logging|auditor[ií]a)\b", "baja"),
    ],
    "testeable": [
        (r"\b(api|rest|integraci[oó]n|c[aá]lculo|workflow|validaci[oó]n)\b", "media"),  # cosas con I/O deterministas
        (r"\b(tests?\s+(automatizados?|unitarios?|integraci[oó]n)|pruebas\s+autom[aá]ticas)\b", "alta"),
    ],
    # PLIEGO (positiva y negativa)
    "pliego_detallado": [
        (r"\b(entregables?\s+(definidos?|nombrados?|listados?))\b", "alta"),
        (r"\b(criterios?\s+de\s+(aceptaci[oó]n|adjudicaci[oó]n|valoraci[oó]n))\b", "alta"),
        (r"\b(arquitectura\s+propuesta|arquitectura\s+t[eé]cnica|cl[aá]usulas?\s+t[eé]cnicas?)\b", "media"),
        (r"\b(fases?\s+del\s+proyecto|cronograma|hitos?\s+nombrados?|plan\s+de\s+trabajo)\b", "media"),
        (r"\b(implantaci[oó]n|despliegue|formaci[oó]n)\b.*\b(soporte|mantenimiento|garant[ií]a)\b", "media"),
    ],
    "pliego_vago": [
        (r"\b(modernizaci[oó]n\s+general|transformaci[oó]n\s+digital|estrategia\s+digital)\b", "alta"),
        (r"\b(consultor[ií]a|asesoramiento)\b(?!.*\bentregable)", "media"),
        (r"\b(seg[uú]n\s+(necesidades|requerimientos)\s+(del\s+)?(adjudicatario|cliente|[oó]rgano))\b", "alta"),
    ],
    # NEGATIVAS (restan a spec_driven_fit)
    "hardware_raro": [
        (r"\b(driver|dispositivo|sensor\s+espec[ií]fico|iot\s+propietario|fpga|asic|microcontrolador)\b", "alta"),
        (r"\b(instalaci[oó]n\s+f[ií]sica|cableado|hardware\s+a\s+medida)\b", "media"),
        (r"\b(equipamiento\s+electromec[aá]nico|maquinaria|robot\s+industrial)\b", "alta"),
    ],
    "legacy_mal_doc": [
        (r"\b(cobol|as\s*400|as\/400|mainframe|delphi\s+[0-9]|visual\s+basic\s+6|powerbuilder)\b", "alta"),
        (r"\b(sistema\s+heredado|sistema\s+legacy|migraci[oó]n\s+desde\s+sistema\s+antiguo)\b", "media"),
        (r"\b(adaptaci[oó]n\s+sobre|extensi[oó]n\s+de\s+aplicaci[oó]n\s+existente)\b", "baja"),
    ],
    "ux_experimental": [
        (r"\b(realidad\s+(virtual|aumentada|mixta|extendida)|vr|ar|metaverso|3d\s+interactivo)\b", "alta"),
        (r"\b(experiencia\s+inmersiva|gamificaci[oó]n\s+profunda|interfaz\s+novedosa|ux\s+innovador)\b", "media"),
        (r"\b(co[\s-]?dise[ñn]o\s+con\s+usuarios|iteraci[oó]n\s+con\s+usuarios|design\s+thinking\s+intensivo)\b", "media"),
    ],
    "investigacion": [
        (r"\b(i\+d|i\+d\+i|investigaci[oó]n|prueba\s+de\s+concepto|poc\s+experimental)\b", "alta"),
        (r"\b(algoritmo\s+propio|modelo\s+propio|optimizaci[oó]n\s+espec[ií]fica\s+no\s+est[aá]ndar)\b", "media"),
        (r"\b(reinforcement\s+learning|aprendizaje\s+por\s+refuerzo)\b", "baja"),  # baja porque LLMs ayudan algo aunque sea R&D
    ],
}


def detectar_senales(datos):
    """Heurística textual sobre título+descripción+desafíos+ideas → lista de señales detectadas."""
    titulo = (datos.get("titulo") or "")
    desc = (datos.get("descripcion") or "")
    desafios = " ".join(datos.get("principales_desafios") or [])
    ideas = " ".join(datos.get("ideas_clave") or [])
    texto = f"{titulo} {desc} {desafios} {ideas}".lower()
    if not texto.strip():
        return []
    detectadas = []
    for nombre_senal, patrones in SENALES_PATRONES.items():
        mejor_conf = None
        mejor_match = None
        # Buscar el patrón con mayor confianza que matchea
        rank_conf = {"alta": 3, "media": 2, "baja": 1}
        for patron, conf in patrones:
            m = _re_senales.search(patron, texto, _re_senales.IGNORECASE)
            if m and (mejor_conf is None or rank_conf[conf] > rank_conf[mejor_conf]):
                mejor_conf = conf
                mejor_match = m.group(0)
        if mejor_conf:
            # Recortar evidencia con un poco de contexto
            pos = texto.find(mejor_match)
            evidencia = texto[max(0, pos - 40):min(len(texto), pos + len(mejor_match) + 60)].strip()
            detectadas.append({
                "nombre": nombre_senal,
                "confianza": mejor_conf,
                "evidencia": evidencia[:200],
                "origen": "heuristica",
            })
    return detectadas


_PESO_SENAL_POSITIVA = {"alta": 1.2, "media": 0.6, "baja": 0.3}
_PESO_SENAL_NEGATIVA = {"alta": -2.0, "media": -1.0, "baja": -0.5}
_SENALES_POSITIVAS = {"stack_mainstream", "crud_masivo", "integraciones_estandar", "logica_mecanica", "boilerplate_alto", "testeable"}
_SENALES_NEGATIVAS = {"hardware_raro", "legacy_mal_doc", "ux_experimental", "investigacion"}


def puntuar_spec_driven_fit(datos):
    """Aplica la fórmula explícita: clamp(5 + sum(positivas) - sum(negativas), 0, 10)."""
    senales = datos.get("senales") or []
    base = 5.0
    sumas_pos = []
    sumas_neg = []
    detalle = []
    for s in senales:
        nombre = s.get("nombre")
        conf = s.get("confianza")
        if nombre in _SENALES_POSITIVAS:
            delta = _PESO_SENAL_POSITIVA.get(conf, 0)
            sumas_pos.append((nombre, conf, delta))
            base += delta
            detalle.append(f"+{nombre}({conf})={delta:+.1f}")
        elif nombre in _SENALES_NEGATIVAS:
            delta = _PESO_SENAL_NEGATIVA.get(conf, 0)
            sumas_neg.append((nombre, conf, delta))
            base += delta
            detalle.append(f"-{nombre}({conf})={delta:+.1f}")
    valor = max(0, min(10, base))
    why = f"5.0 base " + ("".join(detalle) if detalle else "(sin señales detectadas — neutro)") + f" → {valor:.2f}"
    return {"valor": round(valor, 1), "por_que": why[:400]}


def puntuar_claridad_pliego(datos):
    senales = datos.get("senales") or []
    base = 5.0
    bonus_map = {"alta": 3, "media": 1.5, "baja": 0.5}
    pen_map = {"alta": -3, "media": -1.5, "baja": -0.5}
    detalle = []
    for s in senales:
        if s.get("nombre") == "pliego_detallado":
            delta = bonus_map.get(s.get("confianza"), 0)
            base += delta
            detalle.append(f"+pliego_detallado({s.get('confianza')})={delta:+.1f}")
        elif s.get("nombre") == "pliego_vago":
            delta = pen_map.get(s.get("confianza"), 0)
            base += delta
            detalle.append(f"-pliego_vago({s.get('confianza')})={delta:+.1f}")
    valor = max(0, min(10, base))
    why = f"5.0 base " + ("".join(detalle) if detalle else "(sin señal de claridad — neutro)") + f" → {valor:.2f}"
    return {"valor": round(valor, 1), "por_que": why[:400]}


def puntuar_utilidad_ia(scoring_local, datos, modo_busqueda="mixto"):
    if modo_busqueda == "sin_ia_en_producto":
        return {"valor": 0, "por_que": "N/A en modo sin_ia_en_producto"}
    valor = _coerce_num(scoring_local.get("utilidad_ia") if scoring_local else None)
    if valor is None:
        valor = _coerce_num(datos.get("utilidad_ia"))
    if valor is None:
        valor = 3  # default bajo (v0.3.0: utilidad_ia importa poco)
        why = "Sin propuesta del subagente, default 3 (utilidad_ia en v0.3.0 es factor marginal)"
    else:
        why = f"Subagente: utilidad_ia={valor} (v0.3.0: factor marginal, 0.05 peso)"
    return {"valor": int(valor), "por_que": why[:300]}


# Mantenemos referencia retrocompatible para items legacy con campo facilidad_ia
def puntuar_facilidad_ia(scoring_local, datos):
    """LEGACY v0.2.0 — alias a spec_driven_fit. Kept for retrocompat de items históricos."""
    return puntuar_spec_driven_fit(datos)


def puntuar_dificultad(scoring_local, datos):
    valor = _coerce_num(scoring_local.get("dificultad") if scoring_local else None)
    if valor is None:
        valor = _coerce_num(datos.get("dificultad"))
    if valor is None:
        valor = 5
        why = "Sin propuesta del subagente, default 5 (dificultad media)"
    else:
        desafios = datos.get("principales_desafios") or []
        why = f"Subagente: dificultad={valor}. " + ("; ".join(desafios[:2]) if desafios else "ver pliego")
    return {"valor": int(valor), "por_que": why[:300]}


def puntuar_encaje_perfil(datos):
    """Heurística simple: stack moderno + cliente conocido + sector blando = 8, hardware/legacy/clasificado = 3"""
    titulo = (datos.get("titulo") or "").lower()
    desc = (datos.get("descripcion") or "").lower()
    texto = titulo + " " + desc
    score = 6
    why = []
    # Boost por palabras positivas
    for kw in ["web", "app", "portal", "api", "cms", "workflow", "saas", "crud", "plataforma"]:
        if kw in texto:
            score = min(10, score + 1)
            why.append(f"+{kw}")
            break
    # Penalty por palabras negativas
    for kw_neg in ["hardware", "instalación física", "legacy", "mainframe", "obra", "suministro físico"]:
        if kw_neg in texto:
            score = max(1, score - 2)
            why.append(f"-{kw_neg}")
    return {"valor": score, "por_que": f"Heurística texto: {' '.join(why) if why else 'neutro'}"}


def puntuar_presupuesto(datos):
    p = datos.get("presupuesto_total_eur") or datos.get("presupuesto_base_eur") or 0
    # Sweet spot 40-120k
    if 40000 <= p <= 120000:
        return {"valor": 9, "por_que": f"Sweet spot 40-120k: {p:.0f}€"}
    elif 25000 <= p < 40000 or 120000 < p <= 180000:
        return {"valor": 7, "por_que": f"Banda razonable: {p:.0f}€"}
    elif p > 0:
        return {"valor": 5, "por_que": f"Banda subóptima: {p:.0f}€"}
    return {"valor": 3, "por_que": "Sin presupuesto"}


def puntuar_plazo(datos, hoy=datetime(2026, 5, 16)):
    plazo = datos.get("plazo_presentacion")
    if not plazo:
        return {"valor": 5, "por_que": "Sin fecha de plazo"}
    try:
        fecha = datetime.strptime(plazo, "%Y-%m-%d")
    except Exception:
        return {"valor": 5, "por_que": f"Fecha no parseable: {plazo}"}
    dias = (fecha - hoy).days
    if dias >= 14:
        return {"valor": 10, "por_que": f"{dias} días — holgado"}
    elif dias >= 7:
        return {"valor": int(5 + (dias - 7) * 5 / 7), "por_que": f"{dias} días — ajustado"}
    elif dias >= 0:
        return {"valor": 0, "por_que": f"{dias} días — riesgo descarte"}
    return {"valor": 0, "por_que": "Plazo vencido"}


def aplicar_descartes_automaticos(item, datos):
    p = datos.get("presupuesto_total_eur") or datos.get("presupuesto_base_eur") or 0
    if p > 0 and p < 20000:
        return f"presupuesto < 20k ({p}€)"
    if p > 200000:
        return f"presupuesto > 200k ({p}€)"
    plazo = datos.get("plazo_presentacion")
    if plazo:
        try:
            fecha = datetime.strptime(plazo, "%Y-%m-%d")
            if fecha < datetime(2026, 5, 16):
                return f"plazo vencido ({plazo})"
            dias = (fecha - datetime(2026, 5, 16)).days
            if dias < 7:
                return f"plazo < 7 días ({dias}d)"
        except Exception:
            pass
    tipo = datos.get("tipo_objeto") or "indeterminado"
    if tipo == "horas_servicio":
        return f"tipo_objeto=horas_servicio (bolsa de horas/asistencia técnica): «{(datos.get('evidencia_tipo_objeto') or '')[:120]}»"
    lugar = datos.get("lugar_prestacion") or "indeterminado"
    if lugar == "presencial_continuada":
        return f"lugar_prestacion=presencial_continuada: «{(datos.get('evidencia_lugar_prestacion') or '')[:120]}»"
    return None


def calcular_score(scoring):
    total = 0.0
    for nombre, factor_data in scoring.items():
        peso = PESOS.get(nombre, 0)
        valor = factor_data["valor"]
        if nombre == "dificultad":
            total += (10 - valor) * peso
        else:
            total += valor * peso
    return round(total, 2)


def evaluar_item(item, modo_busqueda="mixto"):
    datos = item.get("datos") or {}
    razon_descarte = aplicar_descartes_automaticos(item, datos)
    if razon_descarte:
        return {
            "descartado_automaticamente": True,
            "razon_descarte": razon_descarte,
            "score_total": 0,
            "scoring": {},
            "version_criterios_aplicada": VERSION_CRITERIOS,
            "evaluacion_insuficiente": False,
        }
    scoring_local = item.get("scoring_local") or {}
    # v0.3.0: detecta señales y las persiste en datos.senales[] (si no estaban ya)
    senales_pre_existentes = datos.get("senales") or []
    # Si ya hay señales profundizadas, las preservamos; si no, detectamos heurísticas
    if not senales_pre_existentes:
        datos["senales"] = detectar_senales(datos)
    elif not any(s.get("origen") == "heuristica" for s in senales_pre_existentes):
        # Sólo profundizadas presentes: añadimos heurística como complemento
        heur = detectar_senales(datos)
        nombres_existentes = {s.get("nombre") for s in senales_pre_existentes}
        datos["senales"] = senales_pre_existentes + [s for s in heur if s["nombre"] not in nombres_existentes]
    scoring = {
        "modelo_entrega": puntuar_modelo_entrega(datos.get("tipo_objeto"), datos.get("evidencia_tipo_objeto")),
        "autonomia_infra": puntuar_autonomia_infra(datos.get("lugar_prestacion"), datos.get("evidencia_lugar_prestacion")),
        "spec_driven_fit": puntuar_spec_driven_fit(datos),
        "claridad_pliego": puntuar_claridad_pliego(datos),
        "utilidad_ia": puntuar_utilidad_ia(scoring_local, datos, modo_busqueda),
        "encaje_perfil": puntuar_encaje_perfil(datos),
        "dificultad": puntuar_dificultad(scoring_local, datos),
        "presupuesto_atractivo": puntuar_presupuesto(datos),
        "plazo_realista": puntuar_plazo(datos),
    }
    score_total = calcular_score(scoring)
    return {
        "descartado_automaticamente": False,
        "razon_descarte": None,
        "score_total": score_total,
        "scoring": scoring,
        "version_criterios_aplicada": VERSION_CRITERIOS,
        "evaluacion_insuficiente": False,
    }


# Evalúa items nuevos
evaluados = []
for it in consolidado_items:
    evaluacion = evaluar_item(it, modo_busqueda="mixto")
    it_evaluado = dict(it)
    it_evaluado.update(evaluacion)
    evaluados.append(it_evaluado)

# Estadísticas
descartados = sum(1 for e in evaluados if e["descartado_automaticamente"])
n_arriba_umbral = sum(1 for e in evaluados if e["score_total"] >= UMBRAL_TOP)
print(f"[EVAL NUEVOS] {len(evaluados)} evaluados, {descartados} descartados auto, {n_arriba_umbral} >= umbral {UMBRAL_TOP}")

# ---------------------------------------------------------------------------
# 3. Re-evaluación del historial previo con v0.2.0
# ---------------------------------------------------------------------------

with open(ROOT / "data" / "historial_analizados.json", "r", encoding="utf-8") as f:
    historial = json.load(f)

# Carga seleccionados previos para tener acceso a scoring antiguo detallado (top_actual)
historico_seleccionados = []
for ejec_id in ["ejec_2026-05-15_001", "ejec_2026-05-15_002"]:
    p = ROOT / "data" / "ejecuciones" / ejec_id / "seleccionados.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            historico_seleccionados.extend(json.load(f).get("top_actual", []))

# Indexar por id_oficial
idx_historico = {(s.get("id_oficial") or s.get("titulo", "")[:40]): s for s in historico_seleccionados}

items_historial_reevaluados = []
items_historial_indexados_por_hash = historial.get("items", {})

for h_hash, h_entry in items_historial_indexados_por_hash.items():
    idof = h_entry.get("id_oficial", "")
    objeto = h_entry.get("objeto", "")
    organo = h_entry.get("organo", "")
    p = h_entry.get("presupuesto_eur", 0) or 0
    plazo = h_entry.get("fecha_limite_presentacion")

    # Inferencia heurística textual
    texto_para_inferir = f"{objeto} {organo}"
    tipo_objeto, ev_tipo, conf_tipo = inferir_tipo_objeto(texto_para_inferir)
    lugar, ev_lugar, conf_lugar = inferir_lugar_prestacion(texto_para_inferir)

    # Si tenemos el scoring antiguo en histórico_seleccionados, recuperar facilidad_ia/utilidad_ia/dificultad
    legado = idx_historico.get(idof)
    if legado:
        fac_legacy = legado.get("facilidad_ia", {}).get("valor") if isinstance(legado.get("facilidad_ia"), dict) else legado.get("facilidad_ia")
        util_legacy = legado.get("utilidad_ia", {}).get("valor") if isinstance(legado.get("utilidad_ia"), dict) else legado.get("utilidad_ia")
        dif_legacy = legado.get("dificultad", {}).get("valor") if isinstance(legado.get("dificultad"), dict) else legado.get("dificultad")
        encaje_legacy = legado.get("encaje_perfil", 5)
    else:
        fac_legacy = util_legacy = dif_legacy = None
        encaje_legacy = 5

    # Construye item sintético
    item_synth = {
        "hash": h_hash,
        "id_oficial": idof,
        "url_oficial": h_entry.get("url_oficial"),
        "fuente": h_entry.get("fuente"),
        "datos": {
            "titulo": objeto,
            "descripcion": objeto,
            "organo_contratante": organo,
            "presupuesto_base_eur": p,
            "presupuesto_total_eur": p,
            "plazo_presentacion": plazo,
            "tipo_objeto": tipo_objeto,
            "evidencia_tipo_objeto": f"[inferido legacy v0.2.0 conf={conf_tipo}] {ev_tipo}",
            "lugar_prestacion": lugar,
            "evidencia_lugar_prestacion": f"[inferido legacy v0.2.0 conf={conf_lugar}] {ev_lugar}",
            "facilidad_ia": fac_legacy,
            "utilidad_ia": util_legacy,
            "dificultad": dif_legacy,
            "cpv_codigos": [],
            "lugar_ejecucion": "",
        },
        "scoring_local": {
            "facilidad_ia": fac_legacy,
            "utilidad_ia": util_legacy,
            "dificultad": dif_legacy,
        },
        "es_legacy": True,
    }
    if legado:
        item_synth["datos"]["encaje_perfil_legacy"] = encaje_legacy

    evaluacion = evaluar_item(item_synth, modo_busqueda="mixto")
    item_synth.update(evaluacion)
    items_historial_reevaluados.append(item_synth)

print(f"[EVAL HISTORIAL LEGACY] {len(items_historial_reevaluados)} items re-evaluados con v0.2.0")
desc_legacy = sum(1 for e in items_historial_reevaluados if e["descartado_automaticamente"])
top_legacy = sum(1 for e in items_historial_reevaluados if e["score_total"] >= UMBRAL_TOP)
print(f"   Descartados legacy: {desc_legacy}, sobre umbral: {top_legacy}")

# ---------------------------------------------------------------------------
# 4. Persistencia
# ---------------------------------------------------------------------------

# consolidado.json
consolidado_out = {
    "ejecucion_id": EJEC_ID,
    "fecha_consolidacion": datetime.now().isoformat(timespec="seconds"),
    "items_consolidados": len(consolidado_items),
    "items_descartados_dedup_cruzado": items_descartados_dedup,
    "desglose_por_fuente": desglose_por_fuente,
    "items": consolidado_items,
}
with open(EJEC_DIR / "consolidado.json", "w", encoding="utf-8") as f:
    json.dump(consolidado_out, f, indent=2, ensure_ascii=False)

# evaluado.json
evaluado_out = {
    "ejecucion_id": EJEC_ID,
    "fecha_evaluacion": datetime.now().isoformat(timespec="seconds"),
    "version_criterios": VERSION_CRITERIOS,
    "modo_busqueda": "mixto",
    "total_evaluados_nuevos": len(evaluados),
    "total_evaluados_legacy": len(items_historial_reevaluados),
    "descartados_auto_nuevos": descartados,
    "descartados_auto_legacy": desc_legacy,
    "items_nuevos": evaluados,
    "items_legacy_reevaluados": items_historial_reevaluados,
}
with open(EJEC_DIR / "evaluado.json", "w", encoding="utf-8") as f:
    json.dump(evaluado_out, f, indent=2, ensure_ascii=False)

# seleccionados.json — top global = nuevos elegibles + legacy elegibles, ordenados por score
todos_elegibles = [
    e for e in (evaluados + items_historial_reevaluados)
    if not e["descartado_automaticamente"]
    and not e.get("evaluacion_insuficiente")
    and e["score_total"] >= UMBRAL_TOP
]
todos_elegibles.sort(key=lambda x: x["score_total"], reverse=True)

# También guardamos los descartados sobre umbral PERO descartados, para mostrarlos en filtros (no en top)
seleccionados_out = {
    "ejecucion_id": EJEC_ID,
    "fecha": datetime.now().isoformat(timespec="seconds"),
    "version_criterios": VERSION_CRITERIOS,
    "modo_busqueda": "mixto",
    "umbral_top": UMBRAL_TOP,
    "total_top": len(todos_elegibles),
    "total_evaluados": len(evaluados) + len(items_historial_reevaluados),
    "top_actual": todos_elegibles,
    # Items no descartados pero por debajo del umbral, para que el dashboard los muestre como "fuera del top"
    "fuera_del_top": [
        e for e in (evaluados + items_historial_reevaluados)
        if not e["descartado_automaticamente"] and e["score_total"] < UMBRAL_TOP
    ],
    "descartados": [
        e for e in (evaluados + items_historial_reevaluados) if e["descartado_automaticamente"]
    ],
}
with open(ROOT / "data" / "seleccionados.json", "w", encoding="utf-8") as f:
    json.dump(seleccionados_out, f, indent=2, ensure_ascii=False)

# También guardamos en la carpeta de ejecución
with open(EJEC_DIR / "seleccionados.json", "w", encoding="utf-8") as f:
    json.dump(seleccionados_out, f, indent=2, ensure_ascii=False)

# Actualiza historial_analizados.json con items nuevos
nuevos_hashes = 0
for ev in evaluados:
    h = ev.get("hash")
    if not h or h in items_historial_indexados_por_hash:
        continue
    datos = ev.get("datos") or {}
    items_historial_indexados_por_hash[h] = {
        "id_oficial": ev.get("id_oficial"),
        "fuente": ev.get("fuente"),
        "objeto": (datos.get("titulo") or "")[:200],
        "organo": datos.get("organo_contratante"),
        "presupuesto_eur": datos.get("presupuesto_total_eur") or datos.get("presupuesto_base_eur"),
        "fecha_limite_presentacion": datos.get("plazo_presentacion"),
        "url_oficial": ev.get("url_oficial"),
        "primera_vista": "2026-05-16",
        "ejecuciones_vistas": [EJEC_ID],
        "score_total": ev["score_total"],
        "elegible": not ev["descartado_automaticamente"],
        "pasa_umbral": ev["score_total"] >= UMBRAL_TOP,
        "modo_ejec_primera_vista": "mixto_v0.2.0",
        "tipo_objeto": datos.get("tipo_objeto"),
        "lugar_prestacion": datos.get("lugar_prestacion"),
        "version_criterios_aplicada": VERSION_CRITERIOS,
    }
    nuevos_hashes += 1

# También actualiza items legacy con nuevo scoring v0.2.0
for ev in items_historial_reevaluados:
    h = ev.get("hash")
    if h in items_historial_indexados_por_hash:
        items_historial_indexados_por_hash[h].update({
            "score_total_v0_2_0": ev["score_total"],
            "pasa_umbral_v0_2_0": ev["score_total"] >= UMBRAL_TOP,
            "descartado_v0_2_0": ev["descartado_automaticamente"],
            "razon_descarte_v0_2_0": ev.get("razon_descarte"),
            "tipo_objeto_inferido_v0_2_0": ev["datos"].get("tipo_objeto"),
            "lugar_prestacion_inferido_v0_2_0": ev["datos"].get("lugar_prestacion"),
        })

historial["total"] = len(items_historial_indexados_por_hash)
historial["items"] = items_historial_indexados_por_hash
historial["ultima_actualizacion"] = datetime.now().isoformat(timespec="seconds")
with open(ROOT / "data" / "historial_analizados.json", "w", encoding="utf-8") as f:
    json.dump(historial, f, indent=2, ensure_ascii=False)

print(f"[HISTORIAL] añadidos {nuevos_hashes} nuevos, total ahora: {historial['total']}")
print(f"[TOP FINAL] {len(todos_elegibles)} items sobre umbral {UMBRAL_TOP}")

# Actualiza ejecuciones.json
ejec_path = ROOT / "data" / "ejecuciones.json"
if ejec_path.exists():
    with open(ejec_path, "r", encoding="utf-8") as f:
        ejecuciones = json.load(f)
else:
    ejecuciones = {"ejecuciones": []}
ejecuciones["ejecuciones"].append({
    "id": EJEC_ID,
    "fecha": "2026-05-16",
    "modo_busqueda": "mixto",
    "version_criterios": VERSION_CRITERIOS,
    "objetivo_total": 100,
    "items_consolidados": len(consolidado_items),
    "items_descartados_auto": descartados,
    "items_top": len(todos_elegibles),
    "fuentes": list(desglose_por_fuente.keys()),
})
with open(ejec_path, "w", encoding="utf-8") as f:
    json.dump(ejecuciones, f, indent=2, ensure_ascii=False)

print("[OK] Consolidación + evaluación completada.")
