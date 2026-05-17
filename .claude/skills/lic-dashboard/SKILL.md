---
name: lic-dashboard
description: Genera el dashboard.html final autocontenido a partir de data/seleccionados.json + data/historial_analizados.json. Úsala cuando el usuario invoque /lic-dashboard o cuando el orquestador termine una ejecución.
---

# Skill — lic-dashboard

Generas `dashboards/dashboard.html` autocontenido (HTML + CSS + JS inline, sin dependencias remotas) que renderiza el top vigente con scoring claro, herramientas de feedback y plantillas de presentación.

## Inputs

- `data/seleccionados.json` (top_actual)
- `data/historial_analizados.json` (estadísticas)
- `data/criterios.json` (para mostrar pesos vigentes y nombres de factores)
- `data/ejecuciones.json` (última ejecución, fecha)
- `data/perfil_empresa.json` (taglines de posicionamiento — ver más abajo, lic-orquestador lo crea/actualiza)

## Estructura del HTML

### 1. Header
- Dominio, fecha de generación, versión criterios vigente, total items analizados, top mostrado, modo de búsqueda.
- Botón "📥 Exportar feedback (JSON)" — descarga del localStorage el feedback acumulado para que el usuario lo pegue en la próxima conversación con Claude.
- Botón "📤 Importar feedback (JSON)" — sube un JSON previo para restaurar.
- Banner: "Tu feedback se guarda en este navegador (localStorage). Exporta el JSON cuando quieras alimentar el modelo."

### 2. Sección "Memoria de empresa" (acordeón colapsable, plegado por defecto)
Renderiza desde `data/perfil_empresa.json`:
- **Taglines** (lista de 6-10 frases gancho que definen quiénes somos / qué vendemos / por qué somos diferentes).
- **Prompt para generar memoria técnica por licitación** (bloque de texto copiable con `📋 Copiar`).

### 3. Filtros sobre el top
- Por score (rangos)
- Por `tipo_objeto` (entregable_definido / mixto / indeterminado — los `horas_servicio` ya están descartados)
- Por `lugar_prestacion` (remoto / infra_cliente / mixto / indeterminado)
- Por fuente (PLACSP / BOE / AUTONOMICO)
- Por rango de presupuesto, plazo
- Por estado de feedback (like / dislike / favorito / sin tocar)
- Búsqueda de texto libre sobre título y órgano

### 4. Tabla rankeada principal
Una fila por item del top. Columnas:
| # | Score | Like/Dislike/⭐ | Título (truncado) | Órgano | Presupuesto | Plazo | tipo_objeto | lugar_prestacion | Fuente | Acciones |

- **Score**: badge grande con la nota total (3-6 = naranja, 6-7.5 = amarillo, 7.5+ = verde). Tooltip al hover muestra desglose por factor: `modelo_entrega 9 × 0.25 = 2.25 / autonomia_infra 8 × 0.20 = 1.60 / ...`
- **Like/Dislike/⭐**: 3 botones (`👍 👎 ⭐`) inline, click cambia estado en localStorage. Estado visible (verde/rojo/amarillo).
- **Acciones**: 🔗 abrir pliego, 📄 ver detalle (expande ficha), 📋 copiar título, 💬 comentar.

### 5. Ficha expandible por item
Click en fila → abre detalle con:
- **Score destacado arriba** (badge grande) + desglose por factor con peso y aportación.
- Tabla factor-a-factor: factor, valor, peso, aportación al score, justificación (`por_que` + `evidencia` cuando exista).
- Campos del item: descripción completa, órgano, presupuesto, plazo, CPV, lugar de ejecución, URL del pliego.
- Banderas: `tipo_objeto` + `evidencia_tipo_objeto`, `lugar_prestacion` + `evidencia_lugar_prestacion`.
- **Sección "Presentación inicial" (acordeón, plegado por defecto)** con dos pestañas:
  - **Email previo al órgano**: texto generable. Hasta que el usuario lo genere, muestra el botón `✨ Generar email previo` que abre un prompt prerellenado al usuario para copiar a Claude/ChatGPT (incluye los datos del item). Si el usuario pega la respuesta en el textarea, se guarda en localStorage por id_oficial.
  - **Carta inicial de la oferta** (apertura de memoria técnica): igual mecánica con su botón y prompt.
- **Comentarios**: textarea libre, guarda en localStorage con timestamp.
- Botón `📥 Exportar feedback de este item`.

### 6. Footer
- Rúbrica vigente con pesos y umbral_top.
- Versión criterios.json.
- Comando para regenerar: `/lic-dashboard`.
- Comando para nueva búsqueda: `/lic-buscar`.

## Persistencia del feedback

**Todo va a `localStorage`** del navegador bajo claves:
```
lic.feedback.v1.likes        → {id_oficial: "like"|"dislike"|null}
lic.feedback.v1.favoritos    → [id_oficial, ...]
lic.feedback.v1.comentarios  → {id_oficial: [{ts, texto}, ...]}
lic.feedback.v1.mensajes     → {id_oficial: {email_previo: "...", carta_inicial: "..."}}
```

Exportar → genera un JSON con todo el contenido + metadatos (ejecución activa, fecha), nombre `feedback_dashboard_YYYY-MM-DD.json`. El usuario lo trae a la conversación y Claude lo mergea con `data/feedback.json` para alimentar al modelo.

## Plantilla del prompt "email previo al órgano"

```
Necesito un email corto al órgano de contratación de esta licitación. Tono: profesional pero cercano, sin lenguaje pomposo. Objetivo: presentarnos como equipo de 2 personas que aporta IA real al desarrollo, mostrar interés en el expediente, pedir aclaración técnica si procede. Máx 180 palabras.

Datos de la licitación:
- Órgano: {organo_contratante}
- Expediente: {id_oficial}
- Objeto: {titulo}
- Presupuesto: {presupuesto_base_eur} €
- Plazo: {plazo_presentacion}
- URL: {url_oficial}

Quiénes somos (taglines):
{taglines_perfil_empresa}

Estructura sugerida:
1. Saludo + presentación breve de nuestra empresa (2 frases).
2. Mención específica del expediente y por qué nos encaja.
3. Pregunta técnica relevante (si hay duda razonable que sugiera atención profesional).
4. Cierre con disponibilidad para reunión breve.

Firma: {firma_usuario}
```

## Plantilla del prompt "carta inicial de la oferta"

```
Escribe la primera página formal de la memoria técnica que abrirá nuestra oferta para esta licitación pública. Tono: formal sin pomposidad, denso en valor, breve (máx 1 página A4 = ~450 palabras).

Datos del expediente:
- Órgano: {organo_contratante}
- Expediente: {id_oficial}
- Objeto: {titulo}
- Descripción completa: {descripcion}
- Presupuesto: {presupuesto_base_eur} €
- Plazo de presentación: {plazo_presentacion}

Quiénes somos (taglines):
{taglines_perfil_empresa}

Estructura obligatoria:
1. **Presentación del licitador** (2 párrafos): equipo de 2 personas con IA como apalancamiento doble (acelerador de desarrollo y funcionalidad de producto).
2. **Comprensión del objeto del contrato** (1 párrafo): reformula con tus palabras lo que el órgano necesita, demuestra que has leído el pliego.
3. **Enfoque propuesto** (1-2 párrafos): cómo abordaríamos el proyecto, mencionando explícitamente que entregamos solución completa (no horas) desde nuestra infraestructura.
4. **Resumen de valor diferencial** (1 párrafo): por qué nosotros y no otro (productividad apalancada en IA, foco en entregable, sin sobrecoste de estructura).

Evita: clichés ("alta calidad", "excelencia", "compromiso firme"). Sé concreto, cita el expediente, demuestra comprensión.
```

## Plantilla del prompt "memoria técnica completa" (en sección "Memoria de empresa")

```
Escribe la memoria técnica completa para esta licitación pública. Tono: formal y técnico. Longitud: la que pida el pliego (típicamente 20-40 páginas).

Datos del expediente:
{datos_item_completos}

Quiénes somos (taglines):
{taglines_perfil_empresa}

Estructura recomendada (adáptala al pliego si exige otra):
1. Presentación del licitador y equipo.
2. Comprensión del objeto.
3. Enfoque metodológico (con énfasis en entrega cerrada + infraestructura propia + uso de IA).
4. Plan de trabajo y cronograma.
5. Arquitectura técnica propuesta.
6. Equipo asignado y roles.
7. Plan de calidad y aceptación.
8. Garantía y soporte post-entrega.
9. Riesgos y plan de mitigación.
10. Mejoras opcionales sobre el pliego.

Para cada sección, sé específico: cita el pliego, propon decisiones técnicas concretas, evita generalidades de consultora.
```

## Reglas técnicas

- **HTML autocontenido**: nada externo. CSS y JS dentro del archivo. Iconos como SVG inline o emoji.
- **Sin frameworks**: vanilla JS. Render rápido aunque haya 100+ items.
- **Datos verificados**: cada enlace que aparezca debe estar en el JSON de origen. Si un dato no está, "—".
- **Sin promesas falsas**: si un item tiene `evaluacion_insuficiente=true`, no aparece.
- **localStorage seguro**: si el usuario borra cookies, advierte que hay un botón "Importar feedback (JSON)" para recuperar desde backup.
- **Accesibilidad básica**: contraste razonable, focus visible en botones, atajos de teclado para like/dislike/favorito (`L`, `D`, `F`) cuando una fila esté seleccionada.
