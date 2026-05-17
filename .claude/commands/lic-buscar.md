---
description: Lanza una ejecución completa del buscador — confirma parámetros, dispara N lotes en paralelo, consolida y genera dashboard
argument-hint: "[parámetros opcionales en lenguaje natural, ej: 'sector clínicas en Bilbao', 'PLACSP solo']"
---

Eres el orquestador de este buscador. Sigue el flujo definido en la skill `lic-orquestador`:

1. Carga `data/config.json`, `data/criterios.json`, `data/historial_analizados.json`
2. Si hay `$ARGUMENTS`, interpreta como overrides temporales
3. **Pide confirmación** al usuario con resumen de parámetros
4. Invoca `lic-recolector` para slices
5. Despacha N subagentes (`lic-lote-investigador` o equivalente del dominio)
6. Consolida con `lic-historial` + `lic-evaluador`
7. Regenera `dashboards/dashboard.html` con `lic-dashboard`
8. Invoca `lic-automejora` y aplica solo lo confirmado
9. Resumen final con métricas, top y rutas

Reglas: no saltes la confirmación, no inventes datos, documenta limitaciones.
