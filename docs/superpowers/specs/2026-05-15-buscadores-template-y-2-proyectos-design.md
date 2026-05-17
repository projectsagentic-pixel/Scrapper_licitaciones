# Spec — `buscador-lic` + `buscador negocios` + `buscador licitaciones`

**Fecha:** 2026-05-15
**Autor:** Joseba (oficinaestrategica.blab@businessmind.es)
**Estado:** Aprobado para implementación
**Origen:** brainstorming session 2026-05-15 sobre adaptación del patrón `buscador_coches` a dos nuevos dominios, extrayendo previamente una plantilla reutilizable.

---

## 1. Contexto y motivación

Existe `C:\Users\JosebaPortasAbalde\Documents\DEV personal\buscador_coches`, un sistema agéntico modular sobre Claude Code (skills + slash commands + subagentes) que rastrea milanuncios/wallapop/autoscout, mantiene historial deduplicado en JSON, evalúa con una rúbrica auto-mejorable y genera dashboard HTML autocontenido. Funciona y no se toca.

El usuario quiere replicar ese patrón en dos dominios nuevos:

1. **Negocios locales** como leads B2B para una agencia de IA: descubrir, enriquecer (Maps + web + redes + directorios), puntuar la web (5 ejes 1-10), y generar mensaje personalizado con 1-2 acciones IA.
2. **Licitaciones públicas españolas de software**: agregar de varias fuentes (PLACSP, BOE, autonómicas, agregadores), puntuar viabilidad-IA (dificultad, facilidad-IA, utilidad-IA), comparar fuentes entre sí.

Para evitar copiar-pegar `buscador_coches` dos veces, antes se construye una **plantilla reutilizable** (`buscador-lic`) que sirva tanto para estos dos como para futuros dominios.

---

## 2. Decisiones tomadas en brainstorming

| Pregunta | Decisión |
|---|---|
| Fuentes para negocios | Scraping libre tipo agente con Chrome (mcp chrome-devtools): Google Maps/Business + web propia + redes + directorios oportunistas. Iterativo, ajustado con feedback humano. |
| Definición de target | Sistema hace 3-4 preguntas guiadas pre-búsqueda (sector, zona, tamaño, señales-de-necesidad). Si hay brief en `config.json`, las salta. |
| Fuentes para licitaciones | Mixtas en paralelo: PLACSP + BOE + autonómicas configurables + agregadores libres. Comparador interno mide qué fuente aporta valor. |
| Organización skills | Crear `buscador-lic/` como tercera carpeta hermana, base reutilizable. Cada proyecto se clona a partir de ahí y diverge. `buscador_coches` no migra (sigue funcionando independiente). |

---

## 3. Filosofía heredada

Regla absoluta para los 3 proyectos:

> **Cada dato del informe debe coincidir exactamente con la fuente origen, y cada enlace debe llevar exactamente al recurso que la tarjeta promete. Si no se puede verificar, no se afirma.**

Aplicado a negocios → no inventar teléfonos ni emails: o se extraen del scraping con URL fuente, o se omiten. Aplicado a licitaciones → cada licitación debe tener URL oficial verificable y datos contrastables con el origen.

---

## 4. Arquitectura común — patrón canónico

Todas las carpetas siguen la estructura de `buscador_coches`:

```
<proyecto>/
├── .claude/
│   ├── commands/        # slash commands del proyecto
│   ├── agents/          # subagentes (uno o más investigadores)
│   └── skills/          # skills aisladas
├── data/
│   ├── config.json              # parámetros de búsqueda actuales
│   ├── criterios.json           # rúbrica de scoring + pesos (auto-mejorable, con trazabilidad)
│   ├── historial_analizados.json # todos los items vistos (dedup por hash)
│   ├── seleccionados.json       # top global vigente + histórico
│   ├── feedback.json            # log de feedback humano
│   ├── ejecuciones.json         # log de ejecuciones (lotes, fechas, métricas)
│   ├── propuestas_mejora.json   # propuestas de auto-mejora aplicadas y rechazadas
│   └── lotes/                   # lote_NNN.json crudo de cada subagente
├── dashboards/
│   ├── dashboard.html           # informe final autocontenido
│   └── control.html             # remote control móvil (opcional)
├── scripts/                     # helpers Python si hace falta parsear/consolidar offline
├── README.md
└── serve.py                     # servidor local para abrir dashboards
```

---

## 5. `buscador-lic/`

Carpeta hermana **no ejecutable directamente**, sirve de plantilla.

### 5.1 Skills (8, prefijo `lic-`)

| Skill | Función |
|---|---|
| `lic-orquestador` | Coordina ejecución completa, lee `config.json`, despacha N subagentes, consolida resultados, dispara dashboard y auto-mejora |
| `lic-recolector` | Calcula slices disjuntos para repartir entre subagentes sin solape |
| `lic-evaluador` | Aplica rúbrica de `criterios.json` a cada item, devuelve score + justificación factor-a-factor |
| `lic-historial` | Hashing, dedup entre lotes y ejecuciones, persistencia |
| `lic-criterios` | Gestiona `criterios.json` (añadir/quitar factores, ajustar pesos, registrar cambios). Cada cambio pasa por confirmación humana |
| `lic-feedback` | Captura feedback humano sobre items o sobre criterios, lo registra y traduce en propuestas de cambio |
| `lic-dashboard` | Genera el HTML final autocontenido desde el estado actual |
| `lic-automejora` | Tras cada ejecución, analiza patrones (qué falló, qué dudas surgieron, qué se podría mejorar) y propone cambios concretos a criterios/slices/prompts/config — siempre con explicación y confirmación |

### 5.2 Slash commands (6 base)

| Comando | Función |
|---|---|
| `/lic-buscar` | Maestro: confirma parámetros, lanza N lotes paralelos, consolida, abre dashboard |
| `/lic-status` | Estado: total analizados, último lote, top vigente, fechas |
| `/lic-feedback` | Captura feedback del usuario sobre items o criterios → propone ajustes |
| `/lic-criterios` | Ver/editar criterios y pesos directamente |
| `/lic-dashboard` | Regenera dashboard desde estado actual |
| `/lic-reset` | Limpia historial (con confirmación explícita) |

### 5.3 Subagente plantilla

`lic-lote-investigador`: recibe slice + criterios + hashes a evitar, devuelve hasta N candidatos verificados con datos crudos y URL fuente. Stub adaptable por dominio.

### 5.4 README + bootstrap

- `README.md` documenta el patrón y cómo personalizar.
- `bootstrap.ps1` opcional: copia la plantilla a una nueva ruta y reemplaza el prefijo `lic-` por el del dominio nuevo. Uso: `pwsh bootstrap.ps1 -Target "..\buscador-X" -Prefix "x"`.

### 5.5 JSONs base

Cada uno con un schema mínimo y comentarios de ejemplo, listos para personalizar.

---

## 6. `buscador negocios/`

### 6.1 Personalización del template

- Skills renombradas con prefijo `neg-` (8 base) **+ 2 extras de dominio**:
  - `neg-prospector-web` — analiza la web propia del negocio en 5 ejes 1-10: **diseño**, **copywriting**, **SEO básico**, **mobile/UX**, **conversión**. Cada eje con `por_que` razonado.
  - `neg-mensajero` — genera mensaje personalizado de outreach con 1-2 acciones IA recomendadas (web nueva, agente de reservas, automatización X, etc.) basado en las necesidades detectadas.

### 6.2 Comandos

`/neg-buscar`, `/neg-status`, `/neg-feedback`, `/neg-criterios`, `/neg-dashboard`, `/neg-reset`, **+** `/neg-mensaje <id>` (genera/regenera el outreach de un lead concreto).

### 6.3 Subagente

`neg-lote-investigador`: usa herramientas `mcp__chrome-devtools__*` para scraping libre tipo agente. Flujo por lead:

1. Buscar negocios en Google Maps por consulta `<sector> en <ubicacion>`
2. Para cada resultado: extraer ficha (nombre, rating, nº reviews, teléfono, dirección, web, horario)
3. Si tiene web: navegar y extraer copy + capturar screenshot opcional para el scoring web
4. Buscar redes sociales: LinkedIn (api oficial vía web), Instagram (perfil público)
5. Si datos insuficientes → buscar en directorios (Páginas Amarillas, Axesor) oportunísticamente
6. Cada dato se guarda con `fuente_url` para verificación

### 6.4 Pre-búsqueda guiada

`neg-orquestador` ANTES de ejecutar:

- Si `config.json` tiene brief completo → usa esos parámetros y confirma.
- Si NO → hace 3-4 preguntas ABC al usuario sobre: sector(es), zona(s), filtros opcionales (rating, presencia web, tamaño), prioridad de señales-de-necesidad. Guarda la respuesta en `config.json` para futura referencia.

### 6.5 Schema por lead (`seleccionados.json`)

```jsonc
{
  "id": "neg_<hash>",
  "nombre": "...",
  "sector": "...",
  "ubicacion": { "ciudad": "...", "provincia": "...", "direccion": "..." },
  "contacto": { "telefono": "...", "email": "...", "fuentes": ["..."] },
  "google_maps": { "url": "...", "rating": 4.6, "n_reviews": 312 },
  "resumen_negocio": "...",
  "publico_objetivo": "...",
  "necesidades_detectadas": ["...", "..."],
  "web": {
    "url": "...",
    "score": {
      "diseno":      { "valor": 6, "por_que": "..." },
      "copywriting": { "valor": 4, "por_que": "..." },
      "seo_basico":  { "valor": 5, "por_que": "..." },
      "mobile_ux":   { "valor": 7, "por_que": "..." },
      "conversion":  { "valor": 3, "por_que": "..." }
    },
    "score_total": 5.0
  },
  "redes": { "linkedin": "...", "instagram": "...", "otras": [] },
  "oportunidad_ia_total": 8.2,
  "acciones_recomendadas": [
    { "titulo": "Web nueva con reservas online", "racional": "..." },
    { "titulo": "Agente IA de WhatsApp para preguntas frecuentes", "racional": "..." }
  ],
  "mensaje_personalizado": "...",
  "fuentes": ["url_maps", "url_web", "url_directorio", "..."],
  "hash": "...",
  "ultima_actualizacion": "2026-05-15T..."
}
```

### 6.6 Dashboard

- Tabla rankeada por `oportunidad_ia_total`.
- Filtros: sector, zona, score web, rating Google.
- Ficha expandible con todo el JSON anterior + botón **"copiar mensaje"** + enlaces directos a Maps/web/redes.
- Indicador visual de cada eje del scoring web (barras 1-10).

### 6.7 Auto-mejora específica

`neg-automejora` propone, con confirmación:

- Nuevos sectores/queries que han dado mejores leads.
- Nuevos ejes de scoring web si detecta patrones (ej. "presencia de blog", "schema.org", "velocidad").
- Nuevos directorios a scrapear si los actuales saturan.
- Nuevos formatos de mensaje según feedback de respuesta del usuario.

---

## 7. `buscador licitaciones/`

### 7.1 Personalización del template

- Skills renombradas con prefijo `lic-` (8 base) **+ 1 extra de dominio**:
  - `lic-comparador-fuentes` — mide qué fuente aporta más/mejores licitaciones. Alimenta auto-mejora ("baja peso a X", "sube prioridad de Y").

### 7.2 Comandos

`/lic-buscar`, `/lic-status`, `/lic-feedback`, `/lic-criterios`, `/lic-dashboard`, `/lic-reset`, **+** `/lic-fuentes` (panel comparativo entre fuentes).

### 7.3 Subagentes (uno por fuente — paralelo y comparable)

| Subagente | Fuente |
|---|---|
| `lic-placsp-investigador` | Plataforma de Contratación del Sector Público (estatal, oficial). Permite filtros por CPV, presupuesto, plazo, órgano. |
| `lic-boe-investigador` | BOE, sección de anuncios de licitación. Para licitaciones publicadas solo en BOE o que validan PLACSP. |
| `lic-autonomico-investigador` | Plataformas autonómicas (Euskadi/Catalunya/Madrid/Andalucía/Galicia... configurable en `config.json`). |
| `lic-agregador-investigador` | Agregadores libres (contratosdelsector, etc.) opcional. |

Cada subagente emite su `lote_<fuente>_NNN.json` con campos comunes + campo `fuente`. Luego el orquestador hace dedup cruzado (la misma licitación puede aparecer en varias fuentes — se guarda con `fuentes_corroboradas: [...]`).

### 7.4 Schema por licitación (`seleccionados.json`)

```jsonc
{
  "id": "lic_<hash>",
  "titulo": "...",
  "descripcion": "...",
  "organo_contratante": "...",
  "fuente_principal": "PLACSP",
  "fuentes_corroboradas": ["PLACSP", "BOE"],
  "url_oficial": "...",
  "urls_corroboradas": { "PLACSP": "...", "BOE": "..." },
  "presupuesto_base_eur": 120000,
  "presupuesto_total_eur": 145200,
  "plazo_presentacion": "2026-06-30",
  "cpv_codigos": ["72000000", "..."],
  "lugar_ejecucion": "...",

  "dificultad":   { "valor": 6, "por_que": "..." },
  "facilidad_ia": { "valor": 8, "por_que": "..." },
  "utilidad_ia":  { "valor": 9, "por_que": "..." },
  "score_total": 7.8,

  "principales_desafios": ["...", "..."],
  "ideas_clave": ["...", "..."],

  "hash": "...",
  "ultima_actualizacion": "2026-05-15T..."
}
```

### 7.5 Dashboard principal

- Tabla rankeada por `score_total`.
- Filtros: fuente, CPV, rango presupuesto, plazo restante, dificultad.
- Ficha expandible con racionales + sección **"ideas clave para propuesta"**.
- Badge multifuente cuando una licitación está corroborada en >1 fuente.

### 7.6 Dashboard secundario `dashboards/fuentes.html`

Comparativa entre fuentes:
- nº licitaciones encontradas por fuente
- ratio score >= 7 por fuente
- presupuesto medio por fuente
- solapamiento (cuántas únicas vs corroboradas)
- evolución temporal (últimos N lotes)

### 7.7 Auto-mejora específica

`lic-automejora` + `lic-comparador-fuentes` proponen:

- Bajar/subir peso a fuentes según ratio de calidad.
- Nuevos códigos CPV relevantes detectados en licitaciones bien puntuadas.
- Ajustar pesos de los 3 ejes de scoring si el feedback humano muestra divergencia sistemática.

---

## 8. Auto-mejora recursiva — patrón común a los 3

Cada proyecto tiene su `*-automejora`. Tras cada ejecución analiza:

- patrones en lo que el evaluador descartó vs lo que pasó
- patrones en feedback humano del último ciclo
- métricas de calidad del lote (cobertura, dedup ratio, tiempo, % de items con datos faltantes)
- en negocios: ratio de leads con web vs sin web, score medio por sector
- en licitaciones: aporte por fuente

**Propone cambios concretos** (criterios, slices, prompts del subagente, fuentes, queries) **con explicación y confirmación humana antes de aplicar**.

Las propuestas se loguean en `data/propuestas_mejora.json` aunque las rechaces, para que el sistema aprenda qué tipo de propuestas no quieres y deje de proponerlas.

---

## 9. Aislamiento y dependencias

- Las skills son locales a cada proyecto (`<proyecto>/.claude/skills/`). Un cambio en una skill de `buscador-lic` NO se propaga automáticamente a los otros proyectos.
- Si en el futuro se quiere que una mejora de la plantilla baje a los proyectos derivados, se hace explícitamente con un script `sync-from-template.ps1` (fuera del alcance de este spec).
- Cada proyecto puede ejecutarse y evolucionar de forma totalmente independiente.

---

## 10. Orden de implementación

1. Crear `buscador-lic/` completo (estructura + skills genéricas + commands + subagente plantilla + JSONs base + README + bootstrap.ps1 + serve.py).
2. Clonar y personalizar `buscador negocios/` (renombrar `lic-` → `neg-`, añadir `neg-prospector-web` y `neg-mensajero`, ajustar criterios iniciales, dashboard adaptado, comando `/neg-mensaje`).
3. Clonar y personalizar `buscador licitaciones/` (renombrar `lic-` → `lic-`, añadir `lic-comparador-fuentes`, 4 subagentes por fuente, dashboards principal + fuentes, comando `/lic-fuentes`).
4. Verificar que las skills cargan correctamente en cada proyecto abriendo Claude Code en cada carpeta.
5. Sembrar `criterios.json` inicial razonable en cada proyecto (el usuario afinará por feedback).

---

## 11. Out of scope

- No se modifica `buscador_coches`.
- No se construye base de datos compartida — cada proyecto tiene su JSON independiente.
- No se crean integraciones externas (envío de emails, CRM, etc.). Solo generación de contenido y scoring.
- No se implementa autenticación contra plataformas que la requieran (PLACSP es pública sin login para anuncios; si una autonómica exige login, se omite y se documenta).
- El control móvil (`control.html`) se incluye en el template como esqueleto pero su pulido específico no es objetivo de esta primera entrega.

---

## 12. Criterios de aceptación

- ✅ Existen 3 carpetas hermanas (`buscador-lic`, `buscador negocios`, `buscador licitaciones`) con la estructura canónica.
- ✅ Cada proyecto tiene README que explica su propósito y comandos disponibles.
- ✅ Cada proyecto tiene sus skills cargadas (verificable abriendo Claude Code allí).
- ✅ Cada proyecto tiene `criterios.json` sembrado con rúbrica inicial razonable.
- ✅ Cada proyecto tiene un dashboard.html que renderiza sin error aunque el JSON esté vacío.
- ✅ La plantilla incluye `bootstrap.ps1` documentado.
- ✅ El spec está commiteado (o equivalente — repo no es git, así que basta con guardar el archivo).
