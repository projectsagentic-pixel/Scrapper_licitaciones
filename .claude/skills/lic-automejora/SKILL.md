---
name: lic-automejora
description: Tras una ejecución, analiza patrones (qué falló, qué dudas surgieron, qué se podría hacer mejor) y propone cambios concretos a criterios, slices, prompts del subagente o config — siempre con explicación y pidiendo confirmación. Úsala al final de cada ejecución del orquestador o cuando el usuario pida "analiza y mejora el sistema".
---

# Skill — lic-automejora

Analizas la última ejecución y propones mejoras concretas. Cada propuesta requiere confirmación humana.

## Inputs

- `data/ejecuciones.json` — última ejecución (slices, métricas, duración)
- `data/lotes/lote_*.json` de la última ejecución — qué encontró cada subagente
- `data/feedback.json` — feedback humano del último ciclo
- `data/historial_analizados.json` — para detectar patrones de descarte
- `data/criterios.json` — rúbrica vigente
- `data/propuestas_mejora.json` — historial de propuestas (para no repetir las rechazadas con el mismo argumento)

## Tipos de propuesta que generas

1. **Cambio en criterios** → invoca `lic-criterios.proponer_cambio()` con el diff y un motivo razonado por evidencia.
2. **Cambio en slices/recolector** → "deja de buscar en X, sube prioridad de Y porque…"
3. **Cambio en prompt del subagente** → "el subagente está extrayendo mal el campo Z, reformula así…"
4. **Cambio en config.json** → "sube items_por_lote a 30 porque los lotes están dando margen sobrado"
5. **Cambio en fuentes_activas** → "añade fuente W, la fuente V no está aportando"

## Estructura de cada propuesta

```jsonc
{
  "id": "prop_NNNN",
  "fecha": "ISO8601",
  "tipo": "criterios | slices | prompt_subagente | config | fuentes",
  "diagnostico": "qué patrón observas — con números concretos",
  "propuesta": "qué cambio sugieres",
  "diff": { ... },
  "evidencia": ["ítem_X tenía dato faltante", "el lote 3 trajo solo 2 items por filtro demasiado estrecho", ...],
  "estado_inicial": "pendiente"
}
```

## Flujo

1. Analiza señales por tipo (descartes, faltantes, lotes vacíos, feedback negativo, etc.).
2. Genera entre 0 y 5 propuestas.
3. Presenta al usuario una a una. Para cada una:
   - Muestra `diagnostico`, `propuesta`, `evidencia`.
   - **Espera respuesta**: aplicar / rechazar / modificar.
4. Aplica las aceptadas (delegando en la skill correspondiente — ej. `lic-criterios` para cambios de rúbrica).
5. Loguea TODO en `data/propuestas_mejora.json` (aceptadas y rechazadas), con `motivo_rechazo` si lo dio.

## Reglas

- **Cero auto-aplicación**. Toda mejora pasa por confirmación.
- **Evidencia siempre**: nunca propongas algo "porque te parece". Cita números concretos del lote o del feedback.
- **Aprende de los rechazos**: si una propuesta fue rechazada con el mismo argumento más de 2 veces, no la vuelvas a proponer.
- **Una propuesta = un cambio atómico**. No mezcles cambios de criterios con cambios de slices en una propuesta.
