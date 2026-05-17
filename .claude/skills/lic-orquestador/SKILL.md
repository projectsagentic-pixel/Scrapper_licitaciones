---
name: lic-orquestador
description: Orquesta una ejecución completa de búsqueda de licitaciones — lee config.json, valida con el usuario, despacha N subagentes (uno por fuente), consolida con dedup cruzado entre fuentes, dispara dashboard principal + dashboard de fuentes + auto-mejora. Úsala cuando el usuario invoque /lic-buscar o pida explícitamente "buscar licitaciones".
---

# Skill — lic-orquestador

Coordinas la ejecución end-to-end del buscador de licitaciones.

## Inputs

- `data/config.json` — fuentes activas, prioridades, filtros (CPV, presupuesto, etc.)
- `data/criterios.json` — rúbrica vigente con 3 ejes IA + 3 factores adicionales
- `data/historial_analizados.json` — hashes a evitar
- argumentos opcionales del usuario al invocar `/lic-buscar`

## Flujo obligatorio

### 1. Carga de estado
Lee los 3 JSONs. Aborta si falta o está corrupto.

### 2. Procesa argumentos opcionales
Interpreta como overrides temporales sobre `config.json`. Ejemplos:
- "solo PLACSP" → habilita solo esa fuente para esta ejecución
- "CPV 72200000" → fuerza ese filtro de CPV
- "presupuesto > 100k" → ajusta filtro
NO persistas salvo que el usuario lo pida.

### 3. Confirmación obligatoria
Presenta resumen y **espera respuesta**:

> Voy a buscar licitaciones con estos parámetros:
> - **Fuentes activas:** {lista con prioridades}
> - **CPV objetivo:** {lista}
> - **Presupuesto:** {min}–{max} €
> - **Plazo mínimo:** {n} días
> - **Lotes:** {N} (uno por fuente activa) × {por_lote} = {total}
> - **Paralelo:** {sí/no}
> - **Historial vigente:** {total} licitaciones ya vistas
> - **Criterios versión:** {version}
>
> ¿Confirmas o ajustas algo?

### 4. Despacho de lotes
Para cada `fuente` con `habilitada=true` en `config.json.fuentes_activas`, despacha un subagente con la herramienta `Agent`:
- `subagent_type`: el `subagente` declarado en la fuente (ej. `lic-placsp-investigador`)
- `description`: 3-5 palabras tipo "Lote PLACSP CPV 72000000"
- `prompt`: prompt autocontenido con filtros, criterios, hashes a evitar, output_path

Si `lotes_en_paralelo: true`, lanza todos los `Agent` en una sola message con varias tool calls. Si no, secuencial.

> NOTA: en este dominio NO usamos `lic-recolector` para slicing genérico — los slices son las propias fuentes. Si en algún momento se decide subdividir una fuente (ej. PLACSP por sub-CPV), entonces sí se invoca `lic-recolector`.

### 5. Consolidación con dedup cruzado
Cuando todos los subagentes terminen:
1. Para cada `data/lotes/lote_<fuente>_NNN.json`, invoca `lic-historial.agregar_lote()`.
2. **Dedup cruzado**: dos licitaciones de fuentes distintas son la misma si comparten `id_oficial` interno o si tienen `titulo` ≈ + `presupuesto_base_eur` ≈ + `organo_contratante` igual. Si detectas duplicado:
   - elige la entrada con más datos
   - añade la fuente secundaria a `fuentes_corroboradas[]`
   - registra ambas URLs en `urls_corroboradas{}`
3. Invoca `lic-evaluador` para puntuar/re-puntuar el conjunto vigente con la rúbrica.
4. Invoca `lic-historial.consolidar_top_global()`.
5. Invoca **`lic-comparador-fuentes`** para actualizar métricas por fuente.

### 6. Dashboards
Invoca `lic-dashboard` para regenerar `dashboards/dashboard.html` (ranking principal) y `dashboards/fuentes.html` (comparativa).

### 7. Auto-mejora
Invoca `lic-automejora` con el contexto de la ejecución + el output de `lic-comparador-fuentes`. Presenta propuestas, **espera confirmación por cada una**.

### 8. Resumen final
Muestra: ID de ejecución, duración, licitaciones analizadas (total y nuevas), top global, aporte por fuente, ratio de duplicados cruzados, cambios aplicados, rutas a los dos dashboards.

## Reglas

- **No saltes la confirmación** del paso 3.
- **No inventes datos** ni rellenes lotes vacíos.
- Si una fuente devuelve `ok=false`, regístralo y continúa con las demás.
- El dedup cruzado **conserva la URL de cada fuente**; nunca pierdas info.
