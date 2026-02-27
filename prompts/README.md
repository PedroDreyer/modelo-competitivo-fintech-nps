# 📋 Prompts para Cursor AI Agent

Este directorio contiene los prompts específicos que Cursor debe usar en cada parte del modelo NPS.

## Índice de Prompts

| Archivo | Parte | Descripción |
|---------|-------|-------------|
| `SENIOR_ANALYST.md` | Parte 12 | Prompt para generar diagnóstico ejecutivo |
| `DEEP_RESEARCH.md` | Parte 11 | Instrucciones para búsqueda de noticias |
| `CAUSAS_RAIZ.md` | Parte 7 | Análisis de subcausas y tendencias |

## Cuándo usar cada prompt

### 🎯 SENIOR_ANALYST.md (Parte 12)
- **Cuándo**: Después de ejecutar todas las partes (1-11)
- **Qué hace**: Genera el diagnóstico principal triangulando Producto ↔ Queja ↔ Noticia
- **Output esperado**: JSON estructurado con diagnóstico, alertas, y recomendaciones

### 🔍 DEEP_RESEARCH.md (Parte 11)
- **Cuándo**: Después de analizar causas raíz y productos
- **Qué hace**: Buscar noticias relevantes usando WebSearch
- **Output esperado**: Lista de noticias categorizadas

### 🔬 CAUSAS_RAIZ.md (Parte 7)
- **Cuándo**: Después de calcular el waterfall
- **Qué hace**: Analizar subcausas y tendencias en profundidad
- **Output esperado**: Análisis detallado por categoría de queja

## Uso en código

```python
from pathlib import Path

# Leer prompt
prompt_path = Path("prompts/SENIOR_ANALYST.md")
prompt = prompt_path.read_text(encoding='utf-8')

# Formatear con datos
prompt_final = prompt.format(
    player="Mercado Pago",
    nps_q1=61.2,
    nps_q2=61.6,
    delta_nps=0.4,
    # ... más datos
)
```

## Notas importantes

1. **Los prompts son templates**: Tienen placeholders `{variable}` que deben ser reemplazados
2. **Respetar formato de salida**: Cada prompt especifica un formato JSON esperado
3. **Priorizar concisión**: Los diagnósticos deben ser directos, con números exactos
4. **Idioma**: Responder en español (o portugués para MLB si corresponde)
