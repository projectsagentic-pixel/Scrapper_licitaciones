---
name: lic-comparador-fuentes
description: Mide qué fuente de licitaciones aporta más y mejores oportunidades — calcula nº items aportados, ratio de score >= umbral, presupuesto medio, solapamiento entre fuentes, evolución temporal. Alimenta lic-automejora con propuestas tipo "baja prioridad de X" o "sube Y". Úsala cuando el orquestador termine una ejecución, o cuando el usuario invoque /lic-fuentes.
---

# Skill — lic-comparador-fuentes

Calculas métricas comparativas entre las fuentes activas para que la auto-mejora pueda decidir dónde invertir más esfuerzo.

## Inputs

- `data/historial_analizados.json` — todas las licitaciones vistas (con `fuentes_corroboradas[]`)
- `data/seleccionados.json` — top vigente
- `data/ejecuciones.json` — historial de ejecuciones (para evolución temporal)
- `data/criterios.json` — para conocer `umbral_top`

## Output

Genera `data/metricas_fuentes.json`:

```jsonc
{
  "fecha_calculo": "ISO8601",
  "version_criterios": "...",
  "fuentes": [
    {
      "nombre": "PLACSP",
      "n_items_total": 240,
      "n_items_unicos": 180,
      "n_items_corroborados": 60,
      "n_en_top_actual": 18,
      "ratio_top_sobre_total": 0.075,
      "score_medio": 5.4,
      "score_medio_top": 7.9,
      "presupuesto_medio_top_eur": 95000,
      "tiempo_medio_aporte_lote_seg": 240,
      "tasa_error_subagente": 0.02,
      "evolucion_ultimos_5_lotes": [3, 5, 4, 6, 5],
      "tendencia": "estable | subiendo | bajando"
    }
  ],
  "solapamiento": {
    "PLACSP_BOE": 42,
    "PLACSP_AUTONOMICO": 8,
    "BOE_AUTONOMICO": 3
  },
  "diagnostico": [
    "PLACSP es la fuente más prolífica y con mejor calidad media (ratio_top 7.5%).",
    "BOE solo aporta 12 unicos (no en PLACSP) en los últimos 5 lotes — considerar bajar prioridad si la tendencia continúa.",
    "AUTONOMICO Catalunya aporta licitaciones únicas no presentes en PLACSP — mantener."
  ]
}
```

## Cómo calcular cada métrica

- **n_items_total** = nº licitaciones donde la fuente aparece en `fuentes_corroboradas[]`
- **n_items_unicos** = nº donde es la ÚNICA fuente
- **n_items_corroborados** = nº donde aparece junto con otra fuente
- **n_en_top_actual** = filtro `top_actual` por `fuente_principal` o por aparición en `fuentes_corroboradas[]`
- **ratio_top_sobre_total** = `n_en_top_actual / n_items_total`
- **score_medio / score_medio_top** = media de `score_total` agrupando
- **presupuesto_medio_top_eur** = media en top
- **evolucion_ultimos_5_lotes** = nº items aportados por la fuente en cada uno de las últimas 5 ejecuciones
- **tendencia** = inferida de la evolución (regresión simple)
- **tasa_error_subagente** = ratio de lotes con `ok=false` / total lotes de esa fuente

## Diagnóstico (texto humano)

Genera 3-5 frases interpretativas que sirvan de input directo a `lic-automejora`. Ejemplos:
- "PLACSP es la mejor fuente — mantener prioridad 1.0."
- "BOE aporta poco solo (mucho solapamiento con PLACSP) — proponer bajar prioridad a 0.5."
- "AGREGADOR está deshabilitada y se nota: posibles licitaciones perdidas — proponer activar y comparar."

## Reglas

- **No tomes decisiones por tu cuenta.** Solo calcula y diagnostica. La acción la decide `lic-automejora` + el humano.
- Si la base es pequeña (< 3 ejecuciones), añade `confianza: "baja"` al diagnóstico.
