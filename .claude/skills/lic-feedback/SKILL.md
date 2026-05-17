---
name: lic-feedback
description: Captura feedback humano sobre items concretos del top o sobre criterios, lo registra en feedback.json y lo traduce en propuestas de cambio para lic-criterios o el sistema. Úsala cuando el usuario diga "este item no me convence", "súbele peso a X", "no me gustan los Y", o invoque /lic-feedback.
---

# Skill — lic-feedback

Eres la interfaz entre la opinión del usuario y la rúbrica/sistema.

## Tipos de feedback que reconoces

1. **Sobre un item concreto**: "el #3 no me gusta porque…", "el #5 está perfecto", "el #7 está mal puntuado en X"
2. **Sobre la rúbrica**: "súbele peso a X", "añade un factor que mida Y", "no quiero ver más Z"
3. **Sobre el proceso**: "estás buscando demasiado en X fuente", "explora más Y zonas", "los slices son raros"

## Flujo

### 1. Registrar
Añadir entrada a `data/feedback.json`:
```jsonc
{
  "fecha": "ISO8601",
  "tipo": "item | rubrica | proceso",
  "ref": "<id del item afectado, o 'general'>",
  "texto_usuario": "literal",
  "interpretacion": "tu lectura",
  "propuesta_derivada": "<lo que sugieres hacer>"
}
```

### 2. Proponer cambio derivado
Según el tipo:
- **item** → si es queja sobre puntuación, propone ajuste de pesos a `lic-criterios` que coherentemente subiría/bajaría ese item. Si es queja sobre datos faltantes, propone ampliar campos del subagente.
- **rubrica** → invoca `lic-criterios.proponer_cambio()` con el diff inferido.
- **proceso** → propone cambio a `config.json` o a `lic-recolector` y lo presenta al usuario.

### 3. Confirmación
**Siempre** pide confirmación antes de aplicar cambios derivados. Si el usuario solo quería desahogarse, registra el feedback y no toques nada más.

## Reglas

- **Capturar es obligatorio**. Aplicar es opcional y depende del usuario.
- Si el feedback es ambiguo, pregunta: "¿quieres que ajuste los pesos o solo lo registro?"
- Acumula patrones: si veces equivalentes de feedback se repiten, propón un cambio sistemático en lugar de retoque puntual.
