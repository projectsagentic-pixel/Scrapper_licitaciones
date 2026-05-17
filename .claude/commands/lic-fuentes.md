---
description: Panel comparativo entre fuentes de licitaciones — qué aporta cada una, solapamiento, tendencia
---

Invoca la skill `lic-comparador-fuentes` para recalcular las métricas y luego abre `dashboards/fuentes.html` con los datos vigentes.

Flujo:

1. Invoca `lic-comparador-fuentes` para regenerar `data/metricas_fuentes.json`.
2. Invoca `lic-dashboard` con `solo_fuentes=true` (o equivalente) para regenerar `dashboards/fuentes.html`.
3. Muestra al usuario:
   - tabla resumen por fuente (n items, ratio top, score medio, tendencia)
   - solapamiento entre fuentes
   - diagnóstico textual
4. Indica al usuario:
   - ruta a `dashboards/fuentes.html`
   - si hay propuestas de `lic-automejora` derivadas, recordar que las aplique con `/lic-feedback` o invocando directamente `lic-automejora`
