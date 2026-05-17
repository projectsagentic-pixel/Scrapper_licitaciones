---
name: lic-recolector
description: Diseña la estrategia de búsqueda — calcula slices disjuntos para repartir entre subagentes, sugiere queries y aplica el protocolo de integridad de datos. Úsala cuando el orquestador necesite definir cómo cubrir el dominio sin solapes.
---

# Skill — lic-recolector

Generas N slices disjuntos para que los subagentes investiguen el dominio sin solaparse.

## Inputs

- `data/config.json` — `lotes_por_ejecucion`, `items_por_lote`, `fuentes_activas`, `filtros_globales`
- `data/criterios.json` — para conocer descartes automáticos y no proponer slices imposibles

## Output

Lista de N objetos `slice` que el orquestador pasa a cada subagente:

```jsonc
{
  "slice_id": "lote_NNN",
  "descripcion": "texto humano corto del slice",
  "fuente": "<fuente concreta dentro de fuentes_activas>",
  "filtros_extra": { /* cualquier filtro adicional propio del slice */ },
  "objetivo_items": <items_por_lote>
}
```

## Estrategia genérica

Maximizar **cobertura** y minimizar **solape**:

1. Si hay varias fuentes → al menos un slice por fuente.
2. Si hay varias categorías/sectores/zonas → reparte por la dimensión con más cardinalidad.
3. Si solo hay una dimensión grande (ej. presupuesto) → particiona en sub-rangos disjuntos.
4. Si N > nº de divisiones naturales → duplica slices con orden distinto (ej. `recientes` vs `mejor valorados`).

Cada slice tiene una `descripcion` legible que aparece en logs y en el dashboard. Ejemplo:
- `"Lote 1: clínicas dentales en Bilbao zona centro, rating 4+"`
- `"Lote 3: PLACSP, CPV 72000000, presupuesto 50k-200k"`

## Reglas

- Slices **disjuntos** entre sí dentro de una ejecución.
- Cada slice debe poder cumplirse: si un slice no tiene fuente válida, omítelo y avisa.
- Documenta el solape estimado entre slices al orquestador.
