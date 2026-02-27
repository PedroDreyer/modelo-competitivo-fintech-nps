# 🔍 PROMPT: Deep Research - Búsqueda de Noticias

## Cuándo usar
- **Parte**: 11 (Deep Research)
- **Trigger**: Después de analizar causas raíz (Parte 7) y productos (Parte 8)
- **Herramienta**: WebSearch de Cursor

---

## Instrucciones para Cursor

```
═══════════════════════════════════════════════════════════════════════════════
🔍 DEEP RESEARCH - BÚSQUEDA DE CONTEXTO EXTERNO
═══════════════════════════════════════════════════════════════════════════════

Tu tarea es buscar noticias y contexto externo que ayuden a explicar las 
variaciones de NPS observadas para {player} en {pais}.

═══════════════════════════════════════════════════════════════════════════════
📅 PARÁMETROS DE BÚSQUEDA
═══════════════════════════════════════════════════════════════════════════════

Player: {player}
País: {pais}
Período: {q_act}
Rango de fechas: {rango_fechas}

═══════════════════════════════════════════════════════════════════════════════
📊 CAMBIOS PRINCIPALES A INVESTIGAR
═══════════════════════════════════════════════════════════════════════════════

🔴 QUEJAS QUE CAMBIARON:
{cambios_quejas}

📦 PRODUCTOS CON IMPACTO:
{cambios_productos}

═══════════════════════════════════════════════════════════════════════════════
🔎 QUERIES SUGERIDAS PARA WebSearch
═══════════════════════════════════════════════════════════════════════════════

{queries_sugeridas}

═══════════════════════════════════════════════════════════════════════════════
📰 DOMINIOS CONFIABLES (priorizar estos)
═══════════════════════════════════════════════════════════════════════════════

{dominios_confiables}

═══════════════════════════════════════════════════════════════════════════════
⚠️ INSTRUCCIONES IMPORTANTES
═══════════════════════════════════════════════════════════════════════════════

1. Usar WebSearch para buscar noticias REALES
2. Priorizar noticias del período {rango_fechas}
3. Buscar noticias que expliquen los cambios observados en quejas/productos
4. Filtrar por dominios confiables cuando sea posible
5. Máximo 5-8 noticias relevantes por análisis
6. Incluir URL de cada noticia encontrada

═══════════════════════════════════════════════════════════════════════════════
📝 FORMATO DE RESPUESTA ESPERADO
═══════════════════════════════════════════════════════════════════════════════

Para cada noticia relevante encontrada, reportar:

{
    "titulo": "Título de la noticia",
    "fuente": "dominio.com",
    "fecha": "YYYY-MM",
    "url": "https://...",
    "resumen": "Resumen breve (2-3 oraciones)",
    "categoria_relacionada": "Rendimientos|Financiamiento|Atención|Seguridad|Funcionalidades|Promociones",
    "impacto_esperado": "positivo|negativo|neutro",
    "relevancia": "alta|media|baja"
}
```

---

## Dominios confiables por país

### 🇧🇷 Brasil (MLB)
- infomoney.com.br
- valor.globo.com
- exame.com
- estadao.com.br
- folha.uol.com.br
- g1.globo.com
- canaltech.com.br
- tecmundo.com.br
- mobiletime.com.br
- reclameaqui.com.br
- seudinheiro.com
- moneytimes.com.br

### 🇦🇷 Argentina (MLA)
- infobae.com
- lanacion.com.ar
- clarin.com
- ambito.com
- cronista.com
- iprofesional.com
- pagina12.com.ar
- tn.com.ar
- infotechnology.com

### 🇲🇽 México (MLM)
- elfinanciero.com.mx
- eleconomista.com.mx
- expansion.mx
- forbes.com.mx
- milenio.com
- reforma.com
- xataka.com.mx

---

## Categorías de noticias

| Categoría | Keywords a buscar |
|-----------|-------------------|
| Rendimientos | rendimiento, CDI, poupança, inversión, ahorro, interés, tasa |
| Financiamiento | crédito, préstamo, empréstimo, límite, tarjeta, cartão |
| Atención | atención, atendimento, soporte, SAC, reclamo, queja |
| Seguridad | seguridad, segurança, fraude, golpe, estafa, hack, phishing |
| Funcionalidades | app, aplicativo, función, feature, actualización, bug |
| Promociones | promoción, promoção, cashback, descuento, beneficio |

---

## Ejemplo de uso

1. Cursor ejecuta `WebSearch` con query: "Mercado Pago Brasil rendimientos 2025"
2. Revisa resultados y filtra por dominios confiables
3. Extrae información relevante
4. Mapea a categoría de queja correspondiente
5. Reporta en formato JSON estructurado

---

## Output esperado

```json
{
    "noticias": [
        {
            "titulo": "Mercado Pago aumenta rendimiento de cuenta remunerada",
            "fuente": "infomoney.com.br",
            "fecha": "2025-10",
            "url": "https://infomoney.com.br/...",
            "resumen": "La fintech aumentó el rendimiento de su cuenta al 105% del CDI...",
            "categoria_relacionada": "Rendimientos",
            "impacto_esperado": "positivo",
            "relevancia": "alta"
        }
    ],
    "total_encontradas": 5,
    "categorias_cubiertas": ["Rendimientos", "Seguridad"]
}
```
