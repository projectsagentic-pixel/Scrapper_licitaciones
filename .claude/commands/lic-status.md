---
description: Muestra el estado actual del sistema — config, criterios, historial, top vigente, última ejecución
---

Lee y resume:

- `data/config.json` → dominio, fuentes activas, filtros vigentes
- `data/criterios.json` → versión, nº factores, último cambio
- `data/historial_analizados.json` → total items vistos
- `data/seleccionados.json` → tamaño del top, fecha de última actualización
- `data/ejecuciones.json` → última ejecución (id, fecha, duración, lotes)

Formato de salida: tabla compacta con secciones. Resalta:
- si la rúbrica cambió desde la última ejecución
- si hay propuestas de mejora pendientes en `data/propuestas_mejora.json`
- si el dashboard está desactualizado respecto al estado vigente

No modifiques nada. Solo lee y reporta.
