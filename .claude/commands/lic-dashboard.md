---
description: Regenera el dashboard.html final desde el estado actual (top vigente)
---

Invoca la skill `lic-dashboard`. Genera `dashboards/dashboard.html` autocontenido a partir de `data/seleccionados.json` + `data/historial_analizados.json` + `data/criterios.json`.

Al terminar, indica al usuario la ruta y recuerda:
- abrir directamente el archivo, o
- arrancar `python serve.py` y visitarlo desde el móvil
