# 🔬 PROMPT: Análisis de Causas Raíz

## Cuándo usar
- **Parte**: 7 (Causas Raíz)
- **Trigger**: Después de calcular el waterfall de quejas
- **Input**: Comentarios de usuarios agrupados por categoría de queja

---

## Instrucciones para análisis de subcausas

```
═══════════════════════════════════════════════════════════════════════════════
🔬 ANÁLISIS DE CAUSAS RAÍZ - SUBCAUSAS Y TENDENCIAS
═══════════════════════════════════════════════════════════════════════════════

Para cada categoría de queja en el waterfall, analizar:

1. SUBCAUSAS Q1 vs Q2:
   - ¿Qué subcausas específicas aumentaron?
   - ¿Qué subcausas disminuyeron?
   - ¿Hay subcausas nuevas que no existían en Q1?

2. KEYWORDS:
   - Extraer las palabras más frecuentes en comentarios
   - Identificar términos técnicos específicos
   - Detectar menciones a competidores

3. TENDENCIAS:
   - ¿La queja viene subiendo/bajando en múltiples quarters?
   - ¿Está por encima/debajo del promedio histórico?
   - ¿Hay estacionalidad?

═══════════════════════════════════════════════════════════════════════════════
📊 DATOS DE ENTRADA
═══════════════════════════════════════════════════════════════════════════════

Categoría: {categoria}
Q1 ({q_ant}): {pct_q1:.1f}% ({n_q1} comentarios)
Q2 ({q_act}): {pct_q2:.1f}% ({n_q2} comentarios)
Delta: {delta:+.1f}pp

Comentarios Q1 (muestra):
{comentarios_q1}

Comentarios Q2 (muestra):
{comentarios_q2}

═══════════════════════════════════════════════════════════════════════════════
📝 FORMATO DE ANÁLISIS ESPERADO
═══════════════════════════════════════════════════════════════════════════════

### {categoria} ({delta:+.1f}pp)

**Subcausas principales:**
| Subcausa | Q1 | Q2 | Δ | Tendencia |
|----------|-----|-----|-----|-----------|
| [Subcausa 1] | X% | Y% | +Zpp | 📈/📉 |
| [Subcausa 2] | X% | Y% | -Zpp | 📈/📉 |

**Keywords emergentes:**
- `keyword1` (N menciones) - NUEVO en Q2
- `keyword2` (N menciones) - +50% vs Q1

**Competidores mencionados:**
- Nubank: N menciones (contexto: "...")
- Ualá: N menciones (contexto: "...")

**Tendencias detectadas:**
- 📈 Subcausa X viene subiendo 3Q consecutivos
- 🆕 Tema Y es nuevo en Q2, no existía antes
- ⚠️ Anomalía: pico inusual en [mes]

**Ejemplos representativos:**
1. "[Comentario que ejemplifica la queja principal]"
2. "[Otro comentario relevante]"
```

---

## Categorías de quejas estándar

| Código | Categoría | Descripción |
|--------|-----------|-------------|
| FIN | Financiamiento | Créditos, préstamos, límites, tarjetas |
| REN | Rendimientos | Tasas, CDI, inversiones, ahorro |
| SEG | Seguridad | Fraudes, hackeos, robos, phishing |
| ATE | Atención | Soporte, chat, respuestas, tiempos |
| COM | Complejidad | UI/UX, dificultad de uso, bugs |
| PRO | Promociones | Cashback, descuentos, beneficios |
| OTR | Otros | No clasificados |

---

## Análisis de tendencias

### Criterios para alertas

1. **Tendencia sostenida**: Queja sube/baja 3+ quarters consecutivos
2. **Pico anómalo**: Cambio >2pp en un quarter sin explicación obvia
3. **Por encima del promedio**: Queja está >1pp sobre promedio histórico
4. **Nueva subcausa**: Tema emerge por primera vez con >3% de menciones

### Formato de alerta

```
⚠️ ALERTA: {categoria} - {tipo_alerta}
   Detalle: {descripcion}
   Impacto: {impacto_estimado}pp en NPS
   Acción sugerida: {recomendacion}
```

---

## Keywords por categoría (referencia)

### Financiamiento
- `límite`, `crédito`, `préstamo`, `negado`, `rechazo`, `aumento`, `interés`, `cuotas`

### Rendimientos
- `rendimiento`, `CDI`, `tasa`, `poupança`, `interés`, `inversión`, `bajo`, `competencia`

### Seguridad
- `fraude`, `robo`, `hackeo`, `phishing`, `estafa`, `golpe`, `bloqueado`, `invadido`

### Atención
- `demora`, `respuesta`, `chat`, `teléfono`, `soporte`, `solución`, `robot`, `humano`

### Complejidad
- `difícil`, `confuso`, `bug`, `error`, `lento`, `traba`, `actualización`, `interfaz`

---

## Output esperado

```json
{
    "categoria": "Financiamiento",
    "delta": 2.5,
    "subcausas": [
        {
            "nombre": "Rechazo de crédito",
            "pct_q1": 5.2,
            "pct_q2": 7.8,
            "delta": 2.6,
            "tendencia": "subiendo"
        }
    ],
    "keywords": {
        "límite": 45,
        "negado": 38,
        "crédito": 32
    },
    "competidores": [
        {"nombre": "Nubank", "menciones": 12, "contexto": "mejor límite"}
    ],
    "alertas": [
        {
            "tipo": "tendencia_sostenida",
            "descripcion": "Rechazo de crédito subiendo 3Q",
            "impacto": 1.5
        }
    ],
    "ejemplos": [
        "Me rechazaron el crédito sin explicación...",
        "Nubank me dio el doble de límite..."
    ]
}
```
