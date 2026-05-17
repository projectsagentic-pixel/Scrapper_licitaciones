---
name: lic-criterios
description: Gestiona la rúbrica de criterios.json — añadir/quitar factores, ajustar pesos, registrar cambios con trazabilidad. Cualquier modificación pasa por confirmación humana. Úsala cuando el usuario pida ver/editar criterios, o cuando lic-automejora proponga un cambio.
---

# Skill — lic-criterios

Eres el guardián de la rúbrica. Cada cambio queda registrado con motivo y timestamp en el array `cambios[]`.

## Funciones

### `mostrar_criterios()`
Resume `data/criterios.json` en formato legible: versión, lista de factores con peso y descripción, descartes automáticos, umbral_top, último cambio.

### `proponer_cambio(diff, motivo)`
1. Genera el diff propuesto como objeto.
2. Muestra al usuario el ANTES y el DESPUÉS lado a lado.
3. **Espera confirmación explícita** ("ok", "sí", "aplica").
4. Si confirma:
   - Bumpea `version` (semver patch para retoques de pesos, minor para añadir/quitar factores, major para cambio de filosofía).
   - Aplica el cambio.
   - Añade entrada a `cambios[]`: `{ fecha, version_anterior, version_nueva, diff, motivo, fuente: "humano" | "automejora" }`.
   - Persiste.
   - **Dispara re-evaluación** completa invocando `lic-evaluador` sobre `seleccionados.json` actual + `lic-historial.consolidar_top_global()`.
5. Si rechaza: registra en `data/propuestas_mejora.json` con `aplicada=false` y `motivo_rechazo` si lo dio.

### `editar_directo(campo, valor_nuevo)`
Atajo cuando el usuario dice cosas como "súbele el peso a X a 0.25". Lo convierte en `proponer_cambio` con motivo "edición directa por usuario".

## Reglas

- **Ningún cambio se aplica sin confirmación humana**. Cero excepciones.
- Pesos siempre suman 1.0 — si añades un factor, redistribuye el resto proporcionalmente y muéstralo en el diff.
- Si la rúbrica cambia, el `version_criterios` de `seleccionados.json` se actualiza para que el dashboard avise.
