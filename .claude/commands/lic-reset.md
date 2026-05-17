---
description: Limpia el estado del sistema (historial, seleccionados, lotes) — pide confirmación explícita
argument-hint: "[opcional: 'historial' | 'seleccionados' | 'lotes' | 'todo' (default 'todo')]"
---

**Acción destructiva.** Antes de tocar nada:

1. Lee el estado actual y muestra al usuario qué se va a borrar:
   - cuántos items en historial
   - cuántos items en top actual
   - cuántos archivos en data/lotes/

2. **Pide confirmación explícita** ("sí, borra todo"). Si la respuesta es ambigua, NO borres.

3. Según `$ARGUMENTS`:
   - `historial` → vacía `historial_analizados.json` (deja schema)
   - `seleccionados` → vacía `seleccionados.json` (deja schema)
   - `lotes` → mueve `data/lotes/*.json` a `data/lotes_archivados/<timestamp>/`
   - `todo` (default) → todo lo anterior

4. NO borres `criterios.json`, `feedback.json`, `propuestas_mejora.json`, `ejecuciones.json` (son memoria del sistema).

5. Confirma al usuario lo que se borró y lo que se conservó.
