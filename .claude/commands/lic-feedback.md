---
description: Captura feedback humano sobre el top, criterios o proceso, lo registra y propone ajustes
argument-hint: "[texto de feedback opcional, ej: 'el #3 no me convence', 'súbele peso a X']"
---

Invoca la skill `lic-feedback`.

Si el usuario dio `$ARGUMENTS`, úsalo como input directo. Si no, pregunta:
> ¿Sobre qué quieres dejar feedback?
> - Sobre un item concreto del top (dame el ID o el número)
> - Sobre la rúbrica (qué factor, cómo cambiarlo)
> - Sobre el proceso (slices, fuentes, queries)

Sigue el flujo de la skill: registrar, interpretar, proponer cambio derivado, esperar confirmación antes de aplicar.
