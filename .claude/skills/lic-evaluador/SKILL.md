---
name: lic-evaluador
description: Aplica la rúbrica de criterios.json a una lista de items y devuelve puntuación + justificación factor-a-factor. Úsala cuando haya que puntuar items nuevos, re-rankear el top global tras un nuevo lote, o reaplicar criterios después de un cambio de pesos.
---

# Skill — lic-evaluador

Puntúas items según `data/criterios.json` (vigente: v0.2.0). Cada factor 0-10, justificación breve citando el dato del pliego, score total ponderado.

## Inputs

- Lista de items a evaluar (cada uno con sus campos del dominio, incluyendo `tipo_objeto`, `evidencia_tipo_objeto`, `lugar_prestacion`, `evidencia_lugar_prestacion` extraídos por los subagentes)
- `data/criterios.json` con `factores`, `pesos`, `descartes_automaticos`, `umbral_top`
- `data/config.json` para conocer `modo_busqueda` (mixto / solo_ia_en_producto / sin_ia_en_producto)

## Output por item

```jsonc
{
  "id": "<id>",
  "scoring": {
    "modelo_entrega":      { "valor": 8, "por_que": "...", "evidencia": "frase literal del pliego" },
    "autonomia_infra":     { "valor": 9, "por_que": "...", "evidencia": "frase literal del pliego" },
    "facilidad_ia":        { "valor": 8, "por_que": "..." },
    "utilidad_ia":         { "valor": 5, "por_que": "..." },
    "encaje_perfil":       { "valor": 7, "por_que": "..." },
    "dificultad":          { "valor": 4, "por_que": "..." },
    "presupuesto_atractivo": { "valor": 7, "por_que": "..." },
    "plazo_realista":      { "valor": 9, "por_que": "..." }
  },
  "score_total": 7.82,
  "descartado_automaticamente": false,
  "razon_descarte": null,
  "evaluacion_insuficiente": false
}
```

Si un item dispara un `descarte_automatico` → marca `descartado_automaticamente=true`, `razon_descarte` con la regla disparada, y `score_total=0`.

Si faltan datos para evaluar más del 30% de los factores → `evaluacion_insuficiente=true`. No entra al top.

## Cómo puntuar cada factor

### `modelo_entrega` (peso 0.25, factor crítico)
Lee `datos.tipo_objeto` + `datos.evidencia_tipo_objeto` + el texto de `descripcion`.

| `tipo_objeto` | nota base | matiz |
|---|---|---|
| `entregable_definido` | 9-10 | 10 si producto nombrado con precio cerrado claro; 9 si entregables claros pero alcance algo abierto |
| `mixto` | 4-6 | 6 si entregable >> horas, 4 si horas >> entregable |
| `horas_servicio` | **DESCARTE automático** | razón: "bolsa de horas / asistencia técnica / cuerpo de consultores explícito" |
| `indeterminado` | 5 | nota neutra; baja confianza |

Si `tipo_objeto = indeterminado` pero el texto contiene señales fuertes de bolsa de horas (ej. "horas estimadas", "perfiles a demanda" como unidad de contratación), trata como `horas_servicio` y dispara descarte.

### `autonomia_infra` (peso 0.20, factor crítico)
Lee `datos.lugar_prestacion` + `datos.evidencia_lugar_prestacion`.

| `lugar_prestacion` | nota base | matiz |
|---|---|---|
| `remoto` | 9-10 | 10 si SaaS o entrega de artefacto; 9 si requiere alguna sesión puntual en cliente |
| `infra_cliente` | 5-7 | desarrollo remoto, despliegue en infra cliente. 7 si IaC propio + soporte remoto, 5 si requiere acceso continuo VPN |
| `presencial_continuada` | **DESCARTE automático** | razón: "presencia física continuada en sede del cliente o habilitación de seguridad personal" |
| `mixto` | 5-7 | según peso relativo de cada modalidad |
| `indeterminado` | 5 | nota neutra |

### `facilidad_ia` (peso 0.20)
Lee `scoring_local.facilidad_ia` propuesto por el subagente como punto de partida; refina leyendo descripción. Stack moderno acelerable (web, CRUD, APIs REST, CMS, workflows, integraciones documentadas) → 7-9. Legacy / hardware específico / driver bajo nivel → 3-5.

### `utilidad_ia` (peso 0.13)
- Modo `mixto`: evalúa honestamente 0-10 según valor real de la IA en el objetivo.
- Modo `solo_ia_en_producto`: si valor <6, marca el item para no entrar al pool.
- Modo `sin_ia_en_producto`: fuerza valor=0 y `por_que="N/A en modo sin_ia_en_producto"`.

### `encaje_perfil`, `dificultad`, `presupuesto_atractivo`, `plazo_realista`
Igual que en v0.1.0. `dificultad` se invierte para el score (10 - dificultad). `plazo_realista` ≥14 días = 10, 7-13 días = escala lineal, <7 días = descarte automático.

## Cálculo del score

```
score = sum(factor.valor * factor.peso) salvo dificultad → (10 - dificultad.valor) * dificultad.peso
score_total = redondeado a 2 decimales
```

## Reglas

- **No inventes datos** para rellenar factores. Si falta el dato, di "dato no disponible" y baja el peso efectivo del factor.
- **Justifica cada nota** con un texto corto que apunte al dato concreto. Para `modelo_entrega` y `autonomia_infra` cita la `evidencia_*` del subagente.
- **Si los descartes nuevos disparan**, registra qué señal lo activó (texto literal del pliego en `razon_descarte`).
- Re-evalúa todo el `seleccionados.json` y `historial_analizados.json` cuando se cambia la rúbrica (paso disparado por `lic-criterios`).
- **Trazabilidad**: cada item evaluado guarda `version_criterios_aplicada` (la `version` de criterios.json al momento de evaluar).
