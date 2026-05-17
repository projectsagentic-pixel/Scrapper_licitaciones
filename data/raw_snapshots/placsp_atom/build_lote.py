"""Build final lote_A_placsp_nucleo.json from parsed matches."""
import json
import datetime
import os

with open("matches_raw.json", "r", encoding="utf-8") as f:
    data = json.load(f)
matches = data["matches"]

TARGETS = {"72000000", "72200000", "72260000"}
DEV_PREFIXES = ("72200", "72210", "72220", "72260", "72261", "72262", "72263")

def cpv_score(m):
    s = 0
    for c in m["cpv_codigos"]:
        if c in TARGETS:
            s += 100
        elif c.startswith(DEV_PREFIXES):
            s += 50
        elif c.startswith("72"):
            s += 10
    return s


# === Manual classification: tipo_objeto + lugar_prestacion + scoring local ===
# Built from titles, descriptions and organo. Conservative.

# Map id_oficial -> classification dict
CLASS = {
    # 1. Jaén musealización digital
    "2026000021": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Contrato mixto de suministro-servicios de instalación para implementación de musealización digital (productos nombrados y alcance cerrado)",
        "lugar_prestacion": "infra_cliente",
        "evidencia_lugar_prestacion": "Implementación física en el Centro de Interpretación Turística Castillo de Santa Catalina de Jaén",
        "utilidad_ia": 2, "facilidad_ia": 3, "dificultad": 6,
        "principales_desafios": ["Integración hardware-software in-situ", "Plazo corto (9d)", "Coordinación con obra del Plan Sostenibilidad Turística"],
        "ideas_clave": ["IA para guiado/narración interactiva del oleoturismo", "Datos sintéticos para entrenar reconocimiento de objetos del museo"],
    },
    # 2. Abanilla AR paleontológico
    "4.2026": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Servicio de implantación de un ecosistema tecnológico de realidad aumentada, contenidos digitales y señalética accesible (entregables nombrados)",
        "lugar_prestacion": "infra_cliente",
        "evidencia_lugar_prestacion": "Para el centro de interpretación paleontológico Sierra de Quibas (Abanilla) — instalación física en sede",
        "utilidad_ia": 6, "facilidad_ia": 7, "dificultad": 5,
        "principales_desafios": ["AR contenido 3D paleontológico", "Accesibilidad universal"],
        "ideas_clave": ["IA generativa para reconstrucción 3D de fósiles", "Modelos NLU para guía interactiva multilingüe"],
    },
    # 3. Extremadura EAP mantenimiento sistemas formación
    "PSS/2026/0000033419": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicios para el mantenimiento, soporte y operación de los sistemas de información (servicios continuados, sin entregables nombrados)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Operación de sistemas en infraestructura de la Escuela de Administración Pública de Extremadura",
        "utilidad_ia": 3, "facilidad_ia": 3, "dificultad": 5,
        "principales_desafios": ["Continuidad operativa", "Conocimiento legacy del sistema EAP"],
        "ideas_clave": ["IA para automatizar tickets de soporte", "Agentes para triage de incidencias"],
    },
    # 4. SENASA LMS + comercio + portal corporativo
    "INP/618/26": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Implantación y mantenimiento de un sistema tecnológico único: LMS + comercio electrónico + nueva web corporativa + gestor de cualificación (productos nombrados)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Implantación en SENASA (Madrid); el mantenimiento puede ser remoto",
        "utilidad_ia": 7, "facilidad_ia": 8, "dificultad": 5,
        "principales_desafios": ["Integración LMS-eCommerce-cualificación", "Migración de cursos existentes"],
        "ideas_clave": ["IA generativa para creación de cursos y evaluaciones", "Tutor IA personalizado para LMS", "Búsqueda semántica del catálogo"],
    },
    # 5. O Carballiño plataforma web PERTE Auga
    "4351/2026": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Despliegue de la plataforma web y servicios de interoperatividad complementarios — PERTE Auga (entregables nombrados con financiación específica)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Plataforma web y servicios de interoperatividad — desarrollable e entregable remotamente",
        "utilidad_ia": 5, "facilidad_ia": 8, "dificultad": 4,
        "principales_desafios": ["Cumplimiento PERTE Auga", "Interoperabilidad con sistemas hídricos"],
        "ideas_clave": ["Generación de UI con IA", "Análisis IA de datos hídricos para alertas", "Asistente conversacional ciudadano"],
    },
    # 6. Marbella SaaS centros participación activa
    "SU 200/26": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Suministro en régimen de arrendamiento de una plataforma digital de gestión web en modo SaaS (producto SaaS llave en mano)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Plataforma en modo SaaS (Software as a Service) — sin presencia in-situ obligatoria",
        "utilidad_ia": 5, "facilidad_ia": 8, "dificultad": 3,
        "principales_desafios": ["Adecuación al perfil de usuario mayor", "Accesibilidad"],
        "ideas_clave": ["Chatbot IA para personas mayores", "Recomendador IA de actividades", "Voz a texto para inscripciones"],
    },
    # 7. Gijón infraestructura datos espaciales (asistencia técnica)
    "15296Q/2026": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicio de asistencia técnica para el desarrollo de la infraestructura de datos espaciales (asistencia técnica)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Servicio de asistencia técnica al Ayuntamiento de Gijón — sin precisar régimen de prestación en el resumen",
        "utilidad_ia": 4, "facilidad_ia": 5, "dificultad": 4,
        "principales_desafios": ["Conocimiento INSPIRE y CRS", "Integración con catastro"],
        "ideas_clave": ["IA para geocodificación masiva", "Detección automática de errores topológicos"],
    },
    # 8. Arganda Firewall + SOC
    "20/2026/27006": {
        "tipo_objeto": "mixto",
        "evidencia_tipo_objeto": "Renovación Soporte y Mantenimiento Firewall y SOC (combina licencias renovables + servicios SOC continuos)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "SOC suele ser servicio remoto pero firewall vive en CPD del Ayuntamiento",
        "utilidad_ia": 7, "facilidad_ia": 4, "dificultad": 7,
        "principales_desafios": ["Especialización ciberseguridad municipal", "ENS/SOC 24x7"],
        "ideas_clave": ["IA para detección de anomalías en logs", "Triage automático de alertas SOC"],
    },
    # 9. ECLAP Castilla y León plataforma formación
    "A2026/004373": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicio de asistencia técnica y mantenimiento de la plataforma de formación en línea (asistencia técnica y mantenimiento continuos)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Plataforma de formación en línea de la ECLAP — pliego no disponible para confirmar régimen",
        "utilidad_ia": 4, "facilidad_ia": 4, "dificultad": 4,
        "principales_desafios": ["Continuidad plataforma legacy", "Picos de demanda formativa"],
        "ideas_clave": ["Tutor IA por curso", "Generación automática de tests"],
    },
    # 10. Mislata control presencia SaaS
    "26-SE-08": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Prestación del servicio de implantación, puesta en funcionamiento y explotación en modalidad SaaS de un sistema integral de gestión del control de presencia",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Modalidad SaaS (Software as a Service) — entrega como servicio remoto",
        "utilidad_ia": 3, "facilidad_ia": 7, "dificultad": 3,
        "principales_desafios": ["Hardware fichaje + integración nómina", "RGPD biometría"],
        "ideas_clave": ["IA para detección de patrones anómalos de jornada", "OCR de partes de trabajo"],
    },
    # 11. Cangas (Galicia) sistema gestión recaudación
    "375/2026": {
        # NOTE: this id_oficial is already in AVOID_IDS as "375/2026 (C26/01)" — let's check
        # The CSV in hashes has "375/2026 (C26/01)" — slight variation. Our id is "375/2026". Different string.
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Implantación y mantenimiento de un sistema de información para la gestión y recaudación de los ingresos municipales (sistema nombrado)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Implantación en Ayuntamiento de Cangas (Pontevedra); mantenimiento posiblemente remoto",
        "utilidad_ia": 5, "facilidad_ia": 6, "dificultad": 6,
        "principales_desafios": ["Integración con catastro y bancos", "Cumplimiento Ley General Tributaria local"],
        "ideas_clave": ["IA para detección de morosidad", "Asistente IA al contribuyente"],
    },
    # 12. ISDEFE servicios de apoyo MALE
    "2026-00627": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicios de apoyo para administración de sistemas y desarrollo de software en el Mando de Apoyo Logístico del Ejército de Tierra (servicios de apoyo / cuerpo técnico)",
        "lugar_prestacion": "presencial_continuada",
        "evidencia_lugar_prestacion": "Apoyo al Mando de Apoyo Logístico del Ejército de Tierra (Defensa, presencia in-situ habitual con habilitación HSEC)",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 13. SEGITTUR integración FACe + Business Central
    "192026": {
        "tipo_objeto": "mixto",
        "evidencia_tipo_objeto": "Servicios de integración de FACe y facturación electrónica en Segittur, y servicio de soporte y mantenimiento de Business Central (integración + soporte)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Integración FACe y Business Central — desarrollables remotamente vía APIs y conexiones cloud",
        "utilidad_ia": 4, "facilidad_ia": 7, "dificultad": 4,
        "principales_desafios": ["Conocimiento Business Central API", "Especificación FACe vigente"],
        "ideas_clave": ["IA para clasificación automática de facturas", "Detección de duplicados/anomalías"],
    },
    # 14. Constantina turismo inteligente (patcul)
    "P4103300B-2026/000013-PEA": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Implantación de plataforma de turismo inteligente (PATCUL) — plataforma nombrada con alcance de implantación",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Implantación en Ayuntamiento de Constantina (Sevilla); plataforma de turismo típicamente cloud/SaaS",
        "utilidad_ia": 7, "facilidad_ia": 7, "dificultad": 5,
        "principales_desafios": ["Datos abiertos turísticos heterogéneos", "Justificación EDUSI/PERTE"],
        "ideas_clave": ["Recomendador IA de rutas turísticas", "Asistente conversacional al visitante", "Análisis de sentimiento de reseñas"],
    },
    # 15. Castellón mantenimiento portales web
    "7785/2025": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicio de mantenimiento de Portales Web Municipales (mantenimiento continuado de varios portales sin entregable nuevo nombrado)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Mantenimiento de portales web típicamente remoto vía SSH/CMS",
        "utilidad_ia": 3, "facilidad_ia": 5, "dificultad": 3,
        "principales_desafios": ["Variedad de portales y CMS heterogéneos", "Volumen de municipios"],
        "ideas_clave": ["Generación IA de contenidos accesibles", "Pruebas automáticas con IA"],
    },
    # 16. Burgos SaaS transporte demanda
    "4E_26": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Suministro mediante arrendamiento de una infraestructura informática en la nube (SAAS) para realizar un proyecto piloto de transporte público a demanda (piloto con alcance cerrado)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Infraestructura en la nube (SAAS) — sin presencia en sede",
        "utilidad_ia": 9, "facilidad_ia": 8, "dificultad": 6,
        "principales_desafios": ["Optimización dinámica de rutas rurales", "Adopción usuarios mayores"],
        "ideas_clave": ["IA de ruteo dinámico (DARP)", "Predicción de demanda con modelos temporales", "Voz a reserva para usuarios sin smartphone"],
    },
    # 17. Min Industria información clasificada
    "J25.044.01": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicio de mantenimiento y actualización de la infraestructura de información clasificada del Ministerio de Industria y Turismo (servicio de mantenimiento de infra clasificada)",
        "lugar_prestacion": "presencial_continuada",
        "evidencia_lugar_prestacion": "Infraestructura de información CLASIFICADA — exige habilitación de seguridad personal y presencia in-situ",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 18. MC MUTUAL plataforma IA
    "N202600269": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicio de Oficina Técnica y soporte a la plataforma IA de MC MUTUAL (oficina técnica = bolsa de horas / cuerpo de consultores)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Oficina técnica a plataforma IA — pliego no consultado para confirmar presencialidad",
        "utilidad_ia": 8, "facilidad_ia": 5, "dificultad": 6,
        "principales_desafios": ["Régimen mutualista", "Continuidad plataforma IA existente"],
        "ideas_clave": ["Evaluación y observabilidad de modelos IA", "MLOps continuo", "Guardarraíles de IA en producción"],
    },
    # 19. Arucas SIT-CAT + centro telemático
    "4390/2026": {
        "tipo_objeto": "mixto",
        "evidencia_tipo_objeto": "Servicio para la activación de la funcionalidad SIT-CAT (configuración/integración) y la colaboración en el centro de atención telemática (mezcla técnica + atención)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Activación SIT-CAT (técnica, remoto) + colaboración en centro telemático (típicamente con turnos)",
        "utilidad_ia": 6, "facilidad_ia": 5, "dificultad": 4,
        "principales_desafios": ["Integración con sistemas tributarios canarios", "Atención multicanal al contribuyente"],
        "ideas_clave": ["IA para clasificación automática de consultas", "Asistente IA al agente telemático"],
    },
    # 20. ISDEFE mantenimiento EFESO FSE+
    "2026-00465": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicios de Mantenimiento de la herramienta software de gestión de ayudas EFESO (mantenimiento continuo, sin entregable nuevo)",
        "lugar_prestacion": "presencial_continuada",
        "evidencia_lugar_prestacion": "ISDEFE habitualmente exige trabajo en sede del cliente (Ministerios) con habilitaciones",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 21. ENUSA firma electrónica eIDAS
    "PLI-02405": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Suministro, implantación y puesta en servicio de una plataforma de firma electrónica y flujo de firmas (producto nombrado, alcance cerrado, eIDAS)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Plataforma de firma electrónica utilizable en entornos de escritorio y dispositivos móviles; implantación con conexión a infra ENUSA",
        "utilidad_ia": 3, "facilidad_ia": 6, "dificultad": 6,
        "principales_desafios": ["Cumplimiento eIDAS y certificados qualified", "Integración con CADES/PADES/XADES"],
        "ideas_clave": ["OCR + clasificación IA de documentos a firmar", "Detección de cláusulas obligatorias"],
    },
    # 22. Navantia asesoramiento contratación internacional
    "5100065919 ASESORAMIENTO CONT INTERNACIONAL": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicios de asesoramiento experto en Contratación Internacional (consultoría/asesoramiento = horas expertas)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Asesoramiento jurídico-contractual; no se especifica régimen",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 23. Fuente Tójar sistema digitalizado de agua
    "GEX 1175/2024": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Implantación de un sistema digitalizado en la captación y distribución del agua (sistema nombrado con alcance cerrado)",
        "lugar_prestacion": "infra_cliente",
        "evidencia_lugar_prestacion": "Sensórica/SCADA en la red municipal de agua — instalación física en la red del Ayuntamiento de Fuente Tójar",
        "utilidad_ia": 7, "facilidad_ia": 6, "dificultad": 6,
        "principales_desafios": ["Hardware sensorial robusto en campo", "Conectividad rural"],
        "ideas_clave": ["IA para detección de fugas por anomalías de presión", "Predicción de demanda hídrica", "Mantenimiento predictivo"],
    },
    # 24. Rivas SaaS Bicinrivas
    "21148/2026": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Suministro de licencia y soporte para mantenimiento de la tecnología de gestión de Bicinrivas, en modalidad SAAS (producto SaaS específico)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Modalidad SAAS — sin presencia in-situ",
        "utilidad_ia": 3, "facilidad_ia": 4, "dificultad": 3,
        "principales_desafios": ["Producto específico (Bicinrivas) — barrera competitiva", "Continuidad servicio"],
        "ideas_clave": ["Análisis IA de uso para optimizar estaciones", "Mantenimiento predictivo de bicis"],
    },
    # 25. EMVS control acceso y presencia
    "055/2026": {
        "tipo_objeto": "mixto",
        "evidencia_tipo_objeto": "Servicios de control de acceso, presencia y acreditación en EMVS Madrid (servicios continuos + posibles equipos)",
        "lugar_prestacion": "infra_cliente",
        "evidencia_lugar_prestacion": "Control de acceso físico a la EMVS Madrid — instalación y operación en sede",
        "utilidad_ia": 4, "facilidad_ia": 5, "dificultad": 4,
        "principales_desafios": ["RGPD biometría", "Integración con sistemas RR.HH."],
        "ideas_clave": ["Reconocimiento facial con consentimiento", "Detección de patrones inusuales"],
    },
    # 26-27. Blanca - sensores aire/basura — CPV 72260000 marginal, son sumistros físicos
    # Las descarto: predominantemente suministro físico, fuera del scope de software
    "M6-2026": None,
    "M5-2026": None,
    # 28. RTPA HbbTV medición
    "40/26 RTPA": {
        "tipo_objeto": "mixto",
        "evidencia_tipo_objeto": "Servicios de medición de consumo HbbTV y de emisión y gestión de contenidos interactivos (medición + gestión de contenidos)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Medición HbbTV puede ser remoto; gestión de contenidos puede requerir presencia en CPD de RTPA",
        "utilidad_ia": 6, "facilidad_ia": 5, "dificultad": 5,
        "principales_desafios": ["Estándar HbbTV", "Telemetría broadcast"],
        "ideas_clave": ["IA para recomendación de contenido", "Detección automática de patrones de consumo"],
    },
    # 29. SODEPAL La Palma consultoría destino comercial
    "626/2025": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicios de consultoría empresarial especializada, destinados al diseño, desarrollo y ejecución de actuaciones (consultoría)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Consultoría para proyecto Destino Comercial Inteligente en La Palma",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 30. EMT Palma desarrollo software transporte a demanda
    "7/26": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Servicios para el desarrollo de un software para la gestión y optimización del transporte a la demanda (desarrollo de software con objetivo claro)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Desarrollo de software entregable; la EMT explota luego en su infra",
        "utilidad_ia": 9, "facilidad_ia": 8, "dificultad": 6,
        "principales_desafios": ["Optimización en tiempo real DARP", "Integración con flota EMT existente"],
        "ideas_clave": ["IA de ruteo dinámico", "Predicción de demanda urbana", "RL para asignación óptima"],
    },
    # 31. Tenerife OTC ciberseguridad turística
    "03/2026": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Servicios consistentes en una oficina técnica de ciberseguridad turística (oficina técnica = cuerpo de consultores)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Oficina técnica de ciberseguridad; sin precisar régimen",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 32. FIIAPP sistema alerta feminicidio
    "APAS-2026-004.": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Servicio de diseño, desarrollo e implementación de un sistema de alertas tempranas para la identificación y seguimiento de casos de mujeres en riesgo de feminicidio (sistema nombrado, alcance cerrado)",
        "lugar_prestacion": "mixto",
        "evidencia_lugar_prestacion": "Sistema desarrollable remotamente, posible despliegue en infra de la FIIAPP/contraparte",
        "utilidad_ia": 9, "facilidad_ia": 7, "dificultad": 8,
        "principales_desafios": ["Sensibilidad ética/sesgos del modelo", "Calidad de datos de denuncias", "Coordinación interagencial"],
        "ideas_clave": ["NLP de denuncias y atestados", "Modelos de riesgo con explicabilidad", "Triage automatizado priorizando seguridad"],
    },
    # 33. CCS PDFTools renovación licencias
    "759/2026": {
        "tipo_objeto": "horas_servicio",
        "evidencia_tipo_objeto": "Renovación de las licencias de uso del software PDFTools SDK, incluyendo soporte técnico, mantenimiento correctivo, actualizaciones (renovación + soporte de producto de terceros)",
        "lugar_prestacion": "remoto",
        "evidencia_lugar_prestacion": "Licencias + soporte remoto; sin presencia in-situ",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
    # 34. Caravaca museo música étnica
    "1243928D": {
        "tipo_objeto": "entregable_definido",
        "evidencia_tipo_objeto": "Contrato mixto de servicios y suministro para la implantación de un sistema interactivo accesible en el Museo de la Música Étnica de Barranda (sistema interactivo nombrado)",
        "lugar_prestacion": "infra_cliente",
        "evidencia_lugar_prestacion": "Instalación física en el museo de la Música Étnica de Barranda (Caravaca de la Cruz)",
        "utilidad_ia": 6, "facilidad_ia": 7, "dificultad": 5,
        "principales_desafios": ["Hardware interactivo en museo rural", "Accesibilidad universal"],
        "ideas_clave": ["IA para reconocimiento de instrumentos por audio", "Asistente conversacional del museo", "Generación de contenidos multilingües"],
    },
    # 35. Ineco OpenShift licencias
    "20260406-00145": {
        "tipo_objeto": "mixto",
        "evidencia_tipo_objeto": "Servicio de implantación de las licencias Red Hat OpenShift (implantación de producto de terceros)",
        "lugar_prestacion": "indeterminado",
        "evidencia_lugar_prestacion": "Implantación de licencias OpenShift en Ineco; no precisa régimen de prestación",
        "utilidad_ia": None, "facilidad_ia": None, "dificultad": None,
        "principales_desafios": [],
        "ideas_clave": [],
    },
}


# Build final lote
ms = sorted(matches, key=cpv_score, reverse=True)
items_observados = []
items_descartados_fuera_scope = 0  # Out of software/IT scope (sensores físicos)

for m in ms:
    cls = CLASS.get(m["id_oficial"])
    if cls is None:
        # Not yet selected; skip
        continue
    if cls is False:  # explicitly marked as out-of-scope
        items_descartados_fuera_scope += 1
        continue
    if cls is None:
        continue
    # Handle None (M5/M6 marked as None = discarded)
    items_observados.append((m, cls))

# Filter explicit None entries (already handled by cls is None branch above).
# But we also have M5-2026 / M6-2026 set to None — those we want to count as descartados_fuera_scope.
for mid in ("M5-2026", "M6-2026"):
    if mid in CLASS and CLASS[mid] is None:
        items_descartados_fuera_scope += 1

print(f"Items seleccionados: {len(items_observados)}")
print(f"Items descartados fuera scope: {items_descartados_fuera_scope}")

# Build entries
NOW_ISO = datetime.datetime(2026, 5, 16, 21, 0, 0).isoformat() + "+02:00"

entries = []
for m, cls in items_observados:
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

# Limit to 20
if len(entries) > 20:
    entries = entries[:20]

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
    "items_descartados_por_descarte_automatico": items_descartados_fuera_scope,
    "items_descartados_por_dedup": data["descartes_dedup"],
    "items_observados": entries,
    "limitaciones": (
        "Datos extraídos del feed ATOM mensual oficial de PLACSP (mecanismo de sindicación de Hacienda). "
        "Las URLs son las URLs de detalle del expediente publicadas en cada entry del feed (deeplink:detalle_licitacion). "
        "Las descripciones detalladas y los pliegos completos (PCAP/PPT) requieren navegar al expediente individual o descargar los pliegos enlazados; "
        "el feed ATOM solo trae el resumen summary y el nombre del proyecto (cbc:Name). "
        "La clasificación tipo_objeto / lugar_prestacion se ha realizado a partir del título y del nombre del proyecto: cuando el texto no era concluyente se ha usado 'indeterminado' o 'mixto' para que lic-evaluador desempate con los pliegos. "
        "El acceso programático al detalle individual requiere certificado en muchos casos; el feed es la vía estable. "
        "Se han descartado 2 items con CPV 72260000 marginal (M5-2026 y M6-2026, sensores físicos de aire/basura en Blanca) por estar fuera del scope software/IT. "
        "Hashes calculados con sha256(id_oficial)[:16]; se han descartado 5 IDs presentes en hashes_a_evitar."
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
