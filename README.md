# buscador licitaciones — viabilidad-IA en concursos públicos ES

Sistema agéntico modular sobre Claude Code que rastrea **licitaciones públicas españolas de software/servicios IT** en varias fuentes oficiales (PLACSP, BOE, plataformas autonómicas, agregadores), las puntúa por viabilidad-IA en 3 ejes (dificultad, facilidad-IA, utilidad-IA) y compara qué fuente aporta mejores oportunidades.

> Derivado de `buscador-template`. Los 3 proyectos hermanos (`buscador_coches`, `buscador negocios`, `buscador licitaciones`) comparten el mismo patrón pero evolucionan de forma independiente.

## Filosofía

> **Cada dato del informe debe coincidir exactamente con la fuente origen, y cada enlace debe llevar exactamente al recurso que la tarjeta promete. Si no se puede verificar, no se afirma.**

Aplicado a este dominio: cada licitación tiene URL oficial verificable, presupuesto y plazo se citan exactamente como aparecen en el pliego/anuncio. Si una fuente da datos discrepantes para la misma licitación, se documentan ambos.

## Estructura

```
buscador licitaciones/
├── .claude/
│   ├── commands/        # 7 slash commands (6 base + lic-fuentes)
│   ├── agents/          # 4 subagentes por fuente
│   └── skills/          # 9 skills (8 base + lic-comparador-fuentes)
├── data/
│   ├── config.json
│   ├── criterios.json           # rúbrica con 3 ejes IA + presupuesto + plazo + encaje_perfil
│   ├── historial_analizados.json
│   ├── seleccionados.json
│   ├── feedback.json
│   ├── ejecuciones.json
│   ├── propuestas_mejora.json
│   └── lotes/
├── dashboards/
│   ├── dashboard.html           # ranking principal con racionales + ideas clave
│   ├── fuentes.html             # comparador entre fuentes
│   └── control.html
├── scripts/
├── README.md
└── serve.py
```

## Slash commands

| Comando | Función |
|---|---|
| `/lic-buscar` | Maestro: confirma parámetros, lanza N subagentes (uno por fuente), consolida con dedup cruzado, dashboard |
| `/lic-status` | Estado actual: licitaciones en historial, top vigente, última ejecución, salud por fuente |
| `/lic-feedback` | Feedback humano sobre licitaciones, rúbrica o pesos por fuente |
| `/lic-criterios` | Ver/editar rúbrica con confirmación |
| `/lic-dashboard` | Regenera dashboard.html y fuentes.html |
| `/lic-reset` | Limpia historial (con confirmación) |
| `/lic-fuentes` | Panel comparativo: nº licitaciones, calidad media, solapamiento, evolución |

## Skills (9)

8 base heredadas del template + 1 específica:
- `lic-comparador-fuentes` — mide qué fuente aporta más/mejores licitaciones. Alimenta auto-mejora con propuestas tipo "baja prioridad de X, sube Y".

## Subagentes (4 — uno por fuente)

| Subagente | Fuente | Cobertura |
|---|---|---|
| `lic-placsp-investigador` | Plataforma de Contratación del Sector Público | Estatal oficial (AGE + CCAA/EELL adheridas) |
| `lic-boe-investigador` | BOE — anuncios de licitación | Licitaciones publicadas solo en BOE o que validan PLACSP |
| `lic-autonomico-investigador` | Plataformas autonómicas (Euskadi, Catalunya, Madrid, Andalucía, Galicia… configurable en `config.json`) | Licitaciones que solo se publican en la plataforma regional |
| `lic-agregador-investigador` | Agregadores libres (contratosdelsector, etc.) — opcional | Cobertura adicional, calidad variable |

## Schema de una licitación (`seleccionados.json` → `top_actual[]`)

```jsonc
{
  "id": "lic_<hash>",
  "titulo": "...",
  "descripcion": "...",
  "organo_contratante": "...",
  "fuente_principal": "PLACSP",
  "fuentes_corroboradas": ["PLACSP", "BOE"],
  "url_oficial": "...",
  "urls_corroboradas": { "PLACSP": "...", "BOE": "..." },
  "presupuesto_base_eur": 120000,
  "presupuesto_total_eur": 145200,
  "plazo_presentacion": "2026-06-30",
  "cpv_codigos": ["72000000"],
  "lugar_ejecucion": "...",

  "dificultad":   { "valor": 6, "por_que": "..." },
  "facilidad_ia": { "valor": 8, "por_que": "..." },
  "utilidad_ia":  { "valor": 9, "por_que": "..." },
  "score_total": 7.8,

  "principales_desafios": ["...", "..."],
  "ideas_clave": ["...", "..."],

  "hash": "...",
  "ultima_actualizacion": "ISO8601"
}
```

## Auto-mejora

Tras cada ejecución, `lic-automejora` + `lic-comparador-fuentes` proponen (con confirmación):
- Bajar/subir peso a fuentes según ratio de calidad
- Nuevos códigos CPV relevantes detectados en licitaciones bien puntuadas
- Ajustar pesos de los 3 ejes IA si el feedback humano muestra divergencia sistemática
- Sugerir nuevas plataformas autonómicas si detecta hueco geográfico
