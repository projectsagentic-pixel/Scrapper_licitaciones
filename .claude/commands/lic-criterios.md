---
description: Ver o editar criterios (factores, pesos, descartes automáticos)
argument-hint: "[acción opcional: 'mostrar' (default), o cambio en lenguaje natural ej. 'sube peso de calidad a 0.3']"
---

Invoca la skill `lic-criterios`.

- Sin `$ARGUMENTS` o con "mostrar" → ejecuta `mostrar_criterios()`.
- Con cambio en lenguaje natural → tradúcelo a `proponer_cambio()` y pasa por la confirmación humana antes de aplicar.

Si aplicas un cambio, dispara automáticamente la re-evaluación con `lic-evaluador` + `lic-historial.consolidar_top_global()` + `lic-dashboard`.
