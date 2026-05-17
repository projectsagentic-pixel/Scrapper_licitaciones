---
name: lic-historial
description: Gestiona la persistencia y el dedup de items analizados — calcula hashes, evita repeticiones entre lotes y ejecuciones, mantiene historial_analizados.json y seleccionados.json. Úsala antes de añadir nuevos items al estado, o cuando haya que comprobar si un item ya fue visto.
---

# Skill — lic-historial

Eres el guardián del estado persistente. Garantizas que ningún item se duplica y que el top global está siempre coherente.

## Funciones

### `agregar_lote(lote_path)`
1. Lee `lote_path` → obtiene `anuncios_observados[]` (o el campo equivalente del dominio).
2. Para cada item, calcula `hash` (sha256 sobre el ID estable de la fuente — ver "Cómo hashear" abajo).
3. Si el hash ya está en `historial_analizados.items` → ignora (es duplicado).
4. Si es nuevo → añade a `items` con timestamp y referencia al lote de origen.
5. Actualiza `total`.
6. Persiste `data/historial_analizados.json`.

### `consolidar_top_global()`
1. Toma todos los items con `descartado_automaticamente=false` y `evaluacion_insuficiente=false`.
2. Re-rankea por `score_total` descendente.
3. Aplica `umbral_top` de criterios.json — solo entran al top los que lo superan.
4. Conserva el `top_actual` anterior en `historico_tops[]` con timestamp.
5. Escribe nuevo `top_actual` con los items rankeados.
6. Persiste `data/seleccionados.json`.

### `verificar_hash(hash)` → bool
Para que un subagente compruebe si un item ya está visto antes de invertir esfuerzo en enriquecerlo.

## Cómo hashear

El hash debe ser **determinístico** sobre un identificador estable de la fuente:
- URL canónica del item (sin parámetros de tracking)
- O ID interno de la fuente (ej. número de licitación PLACSP, ID de Wallapop)

```python
import hashlib
hash_corto = hashlib.sha256(id_estable.encode()).hexdigest()[:16]
```

## Reglas

- **Nunca borres del historial** — solo `lic-reset` puede limpiarlo y siempre con confirmación humana.
- **El top global se reconstruye desde cero** cada `consolidar_top_global()`. No es incremental.
- Si un item del historial cambia (re-evaluación), conserva el hash y actualiza el resto.
