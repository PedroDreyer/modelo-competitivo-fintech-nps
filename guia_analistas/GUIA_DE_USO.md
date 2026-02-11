# Guía de Uso - Modelo NPS Competitivo Individuos Fintech

## Introducción

Este modelo genera automáticamente un análisis de variaciones de NPS Competitivo para Individuos en LATAM. Usa Cursor AI como interfaz conversacional.

---

## 1. Cómo Iniciar

### Paso 1: Abrir el proyecto en Cursor
1. Abrir Cursor IDE
2. File → Open Folder → Seleccionar `MODELO_NPS_COMPETITIVO_INDIVIDUOS_FINTECH`

### Paso 2: Iniciar una conversación
Escribir un saludo (ej: "hola") y el modelo responderá pidiendo los parámetros:
- **País/Site**: Argentina (MLA), Brasil (MLB), México (MLM) o Chile (MLC)
- **Player**: La marca a analizar
- **Quarters**: El período a comparar (ej: 25Q3 vs 25Q4)

### Ejemplo de prompt inicial:
```
Analizar Mercado Pago en Brasil, 25Q3 vs 25Q4
```

---

## 2. Qué Genera el Modelo

El modelo genera un **HTML interactivo** con:

1. **Diagnóstico Principal**
   - Variación de NPS con causas principales
   - Formato: `NPS +Xp.p., (I) causa 1... (II) causa 2...`
   - Alertas de Principalidad y Seguridad

2. **Análisis de Quejas (Waterfall)**
   - Motivos que deterioraron el NPS (más quejas)
   - Motivos que mejoraron el NPS (menos quejas)
   - Subcausas y comentarios de ejemplo

3. **Impacto por Productos**
   - Mix Effect: cambio por penetración del producto
   - NPS Effect: cambio por satisfacción del producto

4. **Principalidad y Seguridad**
   - Evolución de share of wallet
   - Motivos de inseguridad

5. **Triangulación con Noticias**
   - Contexto del mercado que valida el diagnóstico

---

## 3. Prompts Útiles para Análisis Adicionales

### Profundizar en un motivo específico
```
Profundiza en los comentarios de usuarios que se quejan de Financiamiento
```

### Ver histórico de NPS
```
Dame una tabla con el histórico de NPS de Mercado Pago en Brasil desde 24Q1
```

### Comparar con competencia
```
Compara el NPS de Mercado Pago vs Nubank en Brasil, 25Q3 vs 25Q4
```

### Analizar un producto específico
```
Profundiza en el impacto de Crédito en el NPS de Mercado Pago
```

### Buscar noticias adicionales
```
Busca noticias de Mercado Pago Brasil sobre rendimientos en 2025
```

### Exportar datos
```
Dame los datos del waterfall en formato tabla para copiar a Excel
```

### Analizar comentarios por subcausa
```
Muéstrame más comentarios de usuarios que se quejan de tasas altas
```

---

## 4. Umbrales del Modelo

El modelo usa los siguientes umbrales para el diagnóstico:

| Umbral | Valor | Descripción |
|--------|-------|-------------|
| UMBRAL_NPS_ESTABLE | ±1p.p. | NPS se considera "sin cambio" |
| UMBRAL_PRINCIPAL | 0.5p.p. | Motivos en dirección del NPS |
| UMBRAL_COMPENSACION | 0.9p.p. | Motivos opuestos (compensaciones) |

---

## 5. Estructura del Output

El HTML se guarda en: `outputs/Resumen_NPS_{Player}_{Quarter}.html`

### Secciones del HTML:
1. **Resumen Ejecutivo** - Diagnóstico principal (copiable para presentaciones)
2. **Contexto del Mercado** - Triangulación con noticias
3. **Deep Dive de Quejas** - Waterfall con acordeones expandibles
4. **Impacto por Productos** - Tabla con Mix Effect y NPS Effect
5. **Principalidad** - Evolución y motivos
6. **Seguridad** - Percepción y motivos de inseguridad

---

## 6. Tips para Analistas

### Para presentaciones:
- El texto del "Resumen Ejecutivo" está diseñado para copiar directo a slides
- Usa el formato `(I), (II), (III)` para enumerar causas

### Para profundizar:
- Click en los acordeones del waterfall para ver subcausas y comentarios
- Los comentarios son REALES (no generados por IA)

### Para validar:
- Revisar la sección de "Triangulación" para ver si las noticias coinciden con los drivers
- Si falta contexto, pedir al modelo que busque noticias adicionales

### Para casos especiales:
- Si BigQuery no está disponible, el modelo funciona pero las subcausas de MP/Nubank serán limitadas
- Para players con datos desde CSV (BBVA, Ualá, etc.), las subcausas vienen del motivo declarado

---

## 7. Troubleshooting

### "No se generó el HTML"
- Verificar que los datos estén en la carpeta `data/`
- Revisar que el player y site sean correctos

### "Faltan comentarios para un motivo"
- Es normal para algunos motivos genéricos como "Otro"
- El modelo mostrará "Sin comentarios suficientes"

### "Las noticias no son relevantes"
- Pedir al modelo: "Busca noticias más recientes de [tema]"
- Las noticias se cachean en `data/noticias_cache.json`

---

## 8. Contacto

Para dudas o mejoras, contactar al equipo de CX Fintech.
