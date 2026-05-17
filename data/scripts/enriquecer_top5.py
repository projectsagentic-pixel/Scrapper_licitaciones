"""
Enriquece el top 5 actual con análisis de proyecto (en qué consiste, qué problema soluciona,
funcionamiento básico, fases). Para el resto deja `analisis_proyecto = null`.

Además detecta el duplicado Marbella CPA (PLACSP SU 200/26 ↔ AUTONOMICO id sintético) y los mergea
manteniendo PLACSP como entrada principal con AUTONOMICO corroborado.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:/Users/JosebaPortasAbalde/Documents/DEV personal/buscador licitaciones")

with open(ROOT / "data" / "seleccionados.json", "r", encoding="utf-8") as f:
    SEL = json.load(f)

top = SEL.get("top_actual", [])

import unicodedata
import re as _re


def _normalize_title(s):
    """Normaliza: lower, sin diacríticos, sin puntuación extra, espacios colapsados."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # quita acentos
    s = s.lower().strip()
    s = _re.sub(r"[^a-z0-9\s]", " ", s)
    s = _re.sub(r"\s+", " ", s)
    return s


# --- 1. Detección de duplicado por (hash idéntico) | (id_oficial idéntico) | (título normalizado + presupuesto ≈ + plazo)
def es_mismo_expediente(a, b):
    # Hash idéntico
    if a.get("hash") and a.get("hash") == b.get("hash"):
        return True
    # id_oficial idéntico (mismo número de expediente en misma fuente)
    if a.get("id_oficial") and a.get("id_oficial") == b.get("id_oficial") and a.get("fuente") == b.get("fuente"):
        return True
    # Heurística cruzada por título normalizado + presupuesto ≈ + plazo
    da = a.get("datos") or {}
    db = b.get("datos") or {}
    ta = _normalize_title(da.get("titulo") or "")
    tb = _normalize_title(db.get("titulo") or "")
    if not ta or not tb:
        return False
    # Compara los primeros 80 caracteres normalizados (cabeza idéntica)
    if ta[:80] != tb[:80]:
        return False
    presup_a = da.get("presupuesto_total_eur") or 0
    presup_b = db.get("presupuesto_total_eur") or 0
    if abs(presup_a - presup_b) > 5:
        return False
    if da.get("plazo_presentacion") != db.get("plazo_presentacion"):
        return False
    return True


merged_indices = set()
for i in range(len(top)):
    if i in merged_indices:
        continue
    for j in range(i + 1, len(top)):
        if j in merged_indices:
            continue
        if es_mismo_expediente(top[i], top[j]):
            # PLACSP > AUTONOMICO > BOE en prelación
            pref = {"PLACSP": 3, "AUTONOMICO": 2, "BOE": 1}
            principal_idx = i if pref.get(top[i].get("fuente"), 0) >= pref.get(top[j].get("fuente"), 0) else j
            secundario_idx = j if principal_idx == i else i

            principal = top[principal_idx]
            secundario = top[secundario_idx]
            # Añade secundario como corroboración del principal
            fs = principal.get("fuentes_corroboradas") or [principal.get("fuente")]
            if secundario.get("fuente") not in fs:
                fs.append(secundario.get("fuente"))
            principal["fuentes_corroboradas"] = fs
            urls_corr = principal.get("urls_corroboradas") or {}
            urls_corr[secundario.get("fuente")] = secundario.get("url_oficial")
            principal["urls_corroboradas"] = urls_corr
            principal["dedup_merge_note"] = (
                f"Mergeado tras-evaluación con duplicado de fuente {secundario.get('fuente')} "
                f"(id={secundario.get('id_oficial')}, hash={secundario.get('hash')}). "
                f"El id sintético del AUTONOMICO ('{secundario.get('id_oficial')}') no permitió dedup en consolidación inicial."
            )
            merged_indices.add(secundario_idx)
            print(f"[MERGE] '{(top[principal_idx].get('datos') or {}).get('titulo','')[:60]}…' → mantengo {top[principal_idx].get('fuente')} {top[principal_idx].get('id_oficial')}, mergeado con {top[secundario_idx].get('fuente')} {top[secundario_idx].get('id_oficial')}")

top_limpio = [it for i, it in enumerate(top) if i not in merged_indices]
print(f"[DEDUP] {len(top)} → {len(top_limpio)} items tras merge")

# --- 2. Análisis de proyecto para el top 5 ---

# Indexa por id_oficial para asignar análisis a los items correctos
analisis_por_id = {
    # #1 Burgos - Piloto transporte a demanda rural (DARP)
    "4E_26": {
        "en_que_consiste": (
            "Plataforma SaaS para pilotar transporte público a demanda en municipios rurales de la provincia de Burgos. "
            "Los ciudadanos solicitan trayectos (origen, destino, ventana horaria) y un motor de optimización dinámica "
            "(DARP — Dial-a-Ride Problem) asigna vehículos compartidos de una flota reducida, agrupando peticiones para "
            "maximizar ocupación y minimizar kilómetros vacíos. Incluye predicción de demanda y un canal de voz para "
            "usuarios sin smartphone."
        ),
        "que_problema_soluciona": (
            "La España vaciada no tiene masa crítica para líneas regulares de autobús: los pueblos pequeños quedan "
            "aislados y los mayores dependen de taxis caros o de un familiar. Las líneas fijas circulan medio vacías y "
            "queman presupuesto público. Este sistema sustituye la rigidez del horario fijo por un servicio bajo demanda "
            "que solo mueve vehículos cuando hay peticiones reales, reduciendo coste por viajero y aumentando cobertura."
        ),
        "funcionamiento_basico": [
            "El ciudadano solicita viaje desde app móvil, web o llamada de voz (IVR + ASR) indicando origen, destino y franja horaria deseada.",
            "El motor DARP recibe peticiones en tiempo real, las agrupa por proximidad geográfica y temporal, y asigna cada cluster al vehículo óptimo.",
            "Un modelo predictivo (series temporales sobre histórico de viajes) preposiciona vehículos en zonas/horas calientes antes de que lleguen las peticiones.",
            "El conductor recibe la ruta dinámica en una app móvil con navegación y lista ordenada de paradas; cada parada confirma recogida.",
            "El usuario recibe notificación push/SMS con hora estimada y seguimiento del vehículo en mapa.",
            "El gestor de flota tiene un dashboard con KPIs en vivo: ocupación, tiempos de espera, km recorridos, peticiones rechazadas.",
        ],
        "fases_principales": [
            {"nombre": "Fase 1 — Análisis y diseño funcional", "descripcion": "Mapeo de municipios piloto, modelado de demanda inicial con datos históricos del CRTM, definición de zonas y políticas de servicio.", "entregable": "Documento funcional + modelo de zonas + plan de pilotaje"},
            {"nombre": "Fase 2 — Backend de optimización", "descripcion": "Motor DARP, capa de persistencia, autenticación, API REST.", "entregable": "Backend desplegado en cloud + suite de tests"},
            {"nombre": "Fase 3 — Predicción de demanda", "descripcion": "Modelos de series temporales para anticipar carga por zona/hora; integración con motor DARP para preposicionamiento.", "entregable": "Modelos entrenados + pipeline de inferencia"},
            {"nombre": "Fase 4 — App ciudadana y canal de voz", "descripcion": "App móvil iOS/Android + web responsive + IVR con reconocimiento de voz para usuarios mayores.", "entregable": "Apps publicadas + número de teléfono operativo"},
            {"nombre": "Fase 5 — Panel de gestión", "descripcion": "Dashboard de operación para Diputación + app para conductores.", "entregable": "Dashboard web + app conductores"},
            {"nombre": "Fase 6 — Piloto controlado", "descripcion": "Despliegue en 2-3 municipios durante 8 semanas con recogida de telemetría y feedback.", "entregable": "Informe de piloto + ajustes técnicos"},
            {"nombre": "Fase 7 — Entrega y traspaso", "descripcion": "Documentación, formación al equipo de la Diputación, traspaso operativo.", "entregable": "Sistema operativo + manuales + plan de soporte"},
        ],
    },
    # #2 EMT Palma - DRT urbano
    "7/26": {
        "en_que_consiste": (
            "Software de gestión y optimización del transporte a la demanda (DRT) para la EMT de Palma. "
            "Complementa la red de líneas regulares con un servicio bajo demanda en zonas y franjas de baja densidad "
            "(barrios periféricos, noche, fin de semana). Integra el motor de optimización en tiempo real con la flota "
            "de autobuses existente de la EMT, sus sistemas de telemática y su app ciudadana."
        ),
        "que_problema_soluciona": (
            "Las líneas regulares de autobús urbano son ineficientes en zonas de baja demanda: vehículos vacíos circulando "
            "para cumplir horario, costes operativos altos y emisiones por viajero elevadas. La EMT necesita un mecanismo "
            "para asignar dinámicamente autobuses a peticiones reales en lugar de mantener frecuencias fijas en rutas que "
            "no las necesitan. Mejor cobertura para el usuario, menor coste para la EMT, menos emisiones."
        ),
        "funcionamiento_basico": [
            "El usuario solicita viaje desde la app o web de la EMT (origen, destino, hora) — el sistema responde si es viable y en qué franja.",
            "Un motor DARP en tiempo real agrupa peticiones compatibles y las asigna a uno de los autobuses de la zona, calculando ruta óptima.",
            "Un modelo de predicción de demanda urbana (ML sobre histórico, eventos, meteorología) anticipa puntos calientes.",
            "Un módulo de Reinforcement Learning ajusta las políticas de asignación con la experiencia operativa real (recompensa = ocupación, tiempo de espera, km).",
            "El sistema se integra con la telemática de los autobuses EMT para conocer posición/estado en tiempo real.",
            "El conductor ve la ruta dinámica en pantalla a bordo y confirma cada recogida.",
            "Supervisión operativa: dashboard de KPIs por zona y tramo horario, alertas de saturación.",
        ],
        "fases_principales": [
            {"nombre": "Fase 1 — Análisis con EMT", "descripcion": "Definición de zonas DRT, modelos de servicio (carrier vs feeder), integraciones con sistemas EMT existentes (telemática, app, SAE).", "entregable": "Documento funcional + plan de integraciones"},
            {"nombre": "Fase 2 — Motor DARP", "descripcion": "Backend de optimización en tiempo real, API REST, persistencia.", "entregable": "Motor + tests de carga"},
            {"nombre": "Fase 3 — Modelos predictivos + RL", "descripcion": "Modelos de predicción de demanda y módulo de RL para optimizar políticas.", "entregable": "Pipeline ML + modelos entrenados + simulador"},
            {"nombre": "Fase 4 — Integración con sistemas EMT", "descripcion": "Conectores con telemática vehicular, app ciudadana, SAE y back-office EMT.", "entregable": "Conectores + tests de integración E2E"},
            {"nombre": "Fase 5 — App ciudadana + panel conductor", "descripcion": "Extensión de la app de la EMT con solicitud DRT + nueva app conductor.", "entregable": "App ciudadana actualizada + app conductor desplegada"},
            {"nombre": "Fase 6 — Pilotaje en zona acotada", "descripcion": "Despliegue real en una zona piloto durante 12 semanas, métricas y ajustes.", "entregable": "Informe piloto + ajuste de modelos"},
            {"nombre": "Fase 7 — Despliegue total y formación", "descripcion": "Roll-out a todas las zonas DRT acordadas + formación operativa.", "entregable": "Sistema operativo + manuales + soporte"},
        ],
    },
    # #3 O Carballiño PERTE Auga
    "4351/2026": {
        "en_que_consiste": (
            "Plataforma web y servicios de interoperabilidad para el Ayuntamiento de O Carballiño dentro del PERTE de "
            "Aguas (digitalización integral del ciclo del agua, fondos NextGenerationEU). Incluye portal ciudadano de "
            "consumo y reporte de incidencias, backoffice técnico municipal, APIs estándar de interoperabilidad con "
            "sistemas autonómicos y nacionales (Augas de Galicia, MITECO), y un asistente conversacional para el ciudadano."
        ),
        "que_problema_soluciona": (
            "Los municipios pequeños tienen datos del ciclo del agua dispersos (consumo, calidad, sensórica IoT, "
            "facturación) sin un punto único de acceso ni APIs estandarizadas. Esto bloquea reporte al MITECO, dificulta "
            "detectar fugas, y el ciudadano no tiene forma de consultar consumo o reportar incidencias salvo presencialmente. "
            "El PERTE Auga exige digitalización con criterios de interoperabilidad — sin esta plataforma, el municipio "
            "no puede acceder a los fondos."
        ),
        "funcionamiento_basico": [
            "Portal web ciudadano: consulta de consumo histórico, gráficas comparativas, alertas de consumo anómalo, gestión de domiciliaciones.",
            "Formulario y app para reporte de incidencias (fugas, calidad, presión baja) con geolocalización y fotos.",
            "APIs REST estándar (esquemas INSPIRE/MITECO) para exponer datos a Xunta, gestores de cuenca y plataformas estatales.",
            "Backoffice técnico: visualización de la red sobre mapa, alertas automáticas de los sensores IoT, gestión de órdenes de trabajo.",
            "Asistente conversacional IA: el ciudadano pregunta '¿cuál es mi consumo este mes?' o '¿hay cortes programados?' y obtiene respuesta natural.",
            "Cumplimiento ENS Medio y normativa PERTE Auga, trazabilidad y auditoría para reporting NextGen.",
        ],
        "fases_principales": [
            {"nombre": "Fase 1 — Análisis funcional y alineación PERTE", "descripcion": "Sesiones con técnicos del Ayuntamiento + revisión de requisitos PERTE Auga + catalogación de fuentes de datos existentes.", "entregable": "Documento funcional + mapa de datos + checklist PERTE"},
            {"nombre": "Fase 2 — Modelo de datos y APIs", "descripcion": "Diseño del modelo de datos común + APIs REST con esquemas INSPIRE/MITECO + autenticación OAuth2.", "entregable": "APIs publicadas + documentación OpenAPI"},
            {"nombre": "Fase 3 — Portal ciudadano", "descripcion": "Frontend web responsive con consulta de consumo, reporte de incidencias, autenticación con Cl@ve.", "entregable": "Portal web en producción"},
            {"nombre": "Fase 4 — Backoffice técnico", "descripcion": "Panel para técnicos: mapa de red, alertas, gestión de incidencias, órdenes de trabajo.", "entregable": "Backoffice desplegado + formación"},
            {"nombre": "Fase 5 — Asistente conversacional", "descripcion": "Integración de LLM con base de conocimiento del ayuntamiento + canal web y telegrama.", "entregable": "Asistente activo + métricas de uso"},
            {"nombre": "Fase 6 — Integraciones y reporting PERTE", "descripcion": "Conectores con sistemas existentes (facturación, sensórica) + módulo de reporting al MITECO.", "entregable": "Integraciones + primer reporte PERTE generado"},
            {"nombre": "Fase 7 — Validación y entrega", "descripcion": "Pruebas de aceptación con el Ayuntamiento, ENS, formación, traspaso.", "entregable": "Sistema certificado + manuales + plan de soporte"},
        ],
    },
    # #4 Marbella CPA
    "SU 200/26": {
        "en_que_consiste": (
            "Plataforma SaaS de gestión integral de los Centros de Participación Activa (CPA) para personas mayores del "
            "Ayuntamiento de Marbella. Reemplaza la gestión manual (Excel, papel, presencial) por un sistema digital "
            "diseñado específicamente para usuarios de tercera edad: alta de socios, programación de actividades y "
            "talleres, inscripciones online, listas de espera, comunicaciones, todo accesible desde web/app con UX "
            "adaptada y un asistente conversacional con entrada de voz."
        ),
        "que_problema_soluciona": (
            "Los CPA gestionan cientos de actividades semanales para mayores: talleres, charlas, actividades físicas. "
            "Con Excel y papel hay errores constantes en aforos y listas de espera, los socios deben acudir en persona "
            "para inscribirse, y avisar de cambios (cancelaciones, traslados de sala) es costoso. Además los mayores "
            "que sí usan smartphone se quedan fuera porque no hay canal digital accesible. El personal del CPA pierde "
            "horas en tareas administrativas que podrían dedicar al servicio real."
        ),
        "funcionamiento_basico": [
            "Backoffice para personal del CPA: alta de socios, programación de actividades, gestión de aforos y listas de espera, comunicaciones masivas.",
            "Portal web y app móvil para socios mayores con UX adaptada: tipografía grande, contraste alto, navegación simplificada, etiquetas verbales.",
            "Inscripciones online con validación de empadronamiento contra el padrón municipal y de socio activo.",
            "Asistente IA conversacional con entrada por voz: el socio pregunta '¿qué hay hoy a las 6?' y recibe respuestas naturales.",
            "Notificaciones push/SMS automáticas de confirmación, recordatorio, cambios y cancelaciones.",
            "Cumplimiento accesibilidad UNE 139803 / WCAG 2.1 AA y RGPD.",
        ],
        "fases_principales": [
            {"nombre": "Fase 1 — Análisis UX con usuarios reales", "descripcion": "Sesiones con personal CPA y grupos focales de socios mayores para validar arquitectura de información, lenguaje y patrones de interacción.", "entregable": "Documento UX + prototipos validados"},
            {"nombre": "Fase 2 — Modelo de datos y reglas", "descripcion": "Diseño del modelo (socios, actividades, aforos, listas espera) y reglas de negocio (prioridades, antigüedad, exclusiones).", "entregable": "Modelo de datos + motor de reglas"},
            {"nombre": "Fase 3 — Backoffice", "descripcion": "Panel de gestión para personal CPA con todas las operaciones administrativas.", "entregable": "Backoffice en producción"},
            {"nombre": "Fase 4 — Portal/app accesible", "descripcion": "Frontend para socios con UX adaptada, certificación accesibilidad UNE 139803.", "entregable": "Portal web + app móvil + informe accesibilidad"},
            {"nombre": "Fase 5 — Asistente IA por voz", "descripcion": "LLM + ASR/TTS para conversación natural; base de conocimiento del CPA.", "entregable": "Asistente activo + métricas de uso"},
            {"nombre": "Fase 6 — Integraciones", "descripcion": "Padrón municipal para validación, sistema de notificaciones SMS, pasarela de comunicación.", "entregable": "Integraciones + tests"},
            {"nombre": "Fase 7 — Piloto en 1 CPA", "descripcion": "Despliegue en un centro durante 6 semanas con observación directa y ajustes.", "entregable": "Informe piloto + ajustes"},
            {"nombre": "Fase 8 — Despliegue total y formación", "descripcion": "Roll-out a todos los CPA + formación a personal + canal de soporte.", "entregable": "Sistema operativo + manuales + 4 años SaaS"},
        ],
    },
    # #5 Mislata Control presencia (después del merge de Marbella, sube de #6 a #5)
    "26-SE-08": {
        "en_que_consiste": (
            "Plataforma SaaS de control de presencia y registro de jornada del personal del Ayuntamiento de Mislata. "
            "Combina hardware de fichaje en sedes municipales (lectores existentes o nuevos), app móvil con "
            "geolocalización para personal en exteriores (educadores, técnicos en obra, policía local), backoffice de "
            "RR.HH. con reglas configurables y conexión al software de nómina existente."
        ),
        "que_problema_soluciona": (
            "El Real Decreto-Ley 8/2019 obliga al registro diario de jornada de TODO el personal. Los ayuntamientos "
            "medianos suelen tener fichaje manual o sistemas obsoletos: errores constantes, conflicto con sindicatos, "
            "imposibilidad de auditar, y trabajo administrativo enorme cada mes para conciliar fichajes con nómina. "
            "Necesitan un sistema fiable, accesible para personal de campo, auditable y que cumpla RGPD si se usa biometría."
        ),
        "funcionamiento_basico": [
            "Puntos físicos de fichaje (lectores RFID, biométricos o teclado) instalados en sedes municipales, conectados a la plataforma cloud.",
            "App móvil para personal en exteriores con fichaje por geolocalización y, opcionalmente, foto.",
            "Backoffice de RR.HH.: control de vacaciones, permisos, horas extra, ausencias, calendarios laborales.",
            "Reglas configurables por colectivo (turnos, jornadas reducidas, festivos locales, convenios específicos).",
            "Detección IA de patrones anómalos: fichajes atípicos, duplicados, posibles errores u olvidos.",
            "Módulo OCR para partes de trabajo en papel (cuando el campo no permite app digital).",
            "Exportación al software de nómina existente (CIVITAS, SICALWIN o equivalente) con formato y periodicidad acordados.",
            "Cumplimiento RGPD reforzado para tratamiento de datos biométricos (cifrado, finalidad limitada, derecho de oposición).",
        ],
        "fases_principales": [
            {"nombre": "Fase 1 — Análisis funcional", "descripcion": "Mapeo de colectivos (administrativos, policía, servicios sociales, brigadas), reglas de jornada por convenio, integraciones requeridas.", "entregable": "Documento funcional + matriz de colectivos"},
            {"nombre": "Fase 2 — Infraestructura cloud + integración hardware", "descripcion": "Despliegue del backend SaaS, integración con lectores existentes y aprovisionamiento de nuevos puntos si procede.", "entregable": "Backend + lectores integrados"},
            {"nombre": "Fase 3 — App móvil de fichaje", "descripcion": "App iOS/Android con fichaje geolocalizado, foto opcional, modo offline.", "entregable": "Apps publicadas en stores"},
            {"nombre": "Fase 4 — Backoffice RR.HH.", "descripcion": "Panel con calendarios, gestión de permisos, horas extra, reportes a Intervención.", "entregable": "Backoffice en producción"},
            {"nombre": "Fase 5 — IA detección anomalías + OCR partes", "descripcion": "Modelo de detección de patrones anómalos y OCR de partes manuales.", "entregable": "Modelos en producción + métricas"},
            {"nombre": "Fase 6 — Integración con nómina", "descripcion": "Conector con el software de nómina del Ayuntamiento + cuadre mensual automático.", "entregable": "Integración nómina + primer cierre conciliado"},
            {"nombre": "Fase 7 — Piloto", "descripcion": "Despliegue en 1-2 colectivos durante 4 semanas + ajustes.", "entregable": "Informe piloto + cambios aplicados"},
            {"nombre": "Fase 8 — Despliegue total + formación", "descripcion": "Roll-out a toda la plantilla + formación al personal + canal de soporte.", "entregable": "Sistema operativo + 4 años SaaS"},
        ],
    },
}

# --- 3. Asignación: top 5 con análisis, resto con null ---
ya_asignados = 0
for it in top_limpio:
    idof = it.get("id_oficial")
    if idof in analisis_por_id and ya_asignados < 5:
        it["analisis_proyecto"] = analisis_por_id[idof]
        it["analisis_proyecto"]["generado_at"] = datetime.now().isoformat(timespec="seconds")
        it["analisis_proyecto"]["generado_por"] = "claude (sesión 2026-05-16)"
        ya_asignados += 1
    else:
        it["analisis_proyecto"] = None

# Re-rank después del merge
todos = top_limpio + [
    it for it in (SEL.get("fuera_del_top") or [])
]
todos = [t for t in todos if not t.get("descartado_automaticamente")]
todos.sort(key=lambda x: x.get("score_total", 0), reverse=True)

# Aplica también analisis_proyecto=null a items fuera del top
for it in todos:
    if "analisis_proyecto" not in it:
        it["analisis_proyecto"] = None

# Reconstruir top_actual + fuera_del_top con el orden re-rankeado
umbral = SEL.get("umbral_top", 6.5)
new_top = [t for t in todos if t.get("score_total", 0) >= umbral]
new_fuera = [t for t in todos if t.get("score_total", 0) < umbral]

SEL["top_actual"] = new_top
SEL["fuera_del_top"] = new_fuera
SEL["total_top"] = len(new_top)
SEL["fecha_enriquecimiento_top5"] = datetime.now().isoformat(timespec="seconds")

with open(ROOT / "data" / "seleccionados.json", "w", encoding="utf-8") as f:
    json.dump(SEL, f, indent=2, ensure_ascii=False)

print(f"[OK] Top {len(new_top)} (5 con análisis completo, resto null)")
print(f"     Items con análisis asignado: {ya_asignados}")
print()
print("Top 5 actual con análisis:")
for i, it in enumerate(new_top[:5], 1):
    d = it.get("datos") or {}
    print(f"  {i}. {it['score_total']:.2f} | {it.get('fuente'):10s} | {it.get('id_oficial'):24s} | {(d.get('titulo','')[:65])}")
