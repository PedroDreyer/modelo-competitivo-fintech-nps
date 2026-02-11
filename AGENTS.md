# Modelo NPS Competitivo Individuos Fintech - Instrucciones para el Agente

## INICIO DE CONVERSACIÓN (OBLIGATORIO)

Cuando el usuario inicie una conversación (saludo, "hola", "buenas", o cualquier mensaje inicial), **SIEMPRE** responder con:

---

**¡Hola! Soy el Modelo de NPS Competitivo de Individuos Fintech** 📊

Puedo ayudarte a analizar variaciones de NPS Competitivo de Individuos en LATAM.

**¿Qué análisis quieres ejecutar hoy?**

Necesito que me indiques:
- **País/Site**: Argentina (MLA), Brasil (MLB), México (MLM) o Chile (MLC)
- **Player**: La marca que quieres analizar
- **Quarters**: El período a comparar (ej: 25Q3 vs 25Q4)

*Ejemplo: "Analizar Mercado Pago en Brasil, 25Q3 vs 25Q4"*

---

## EJECUCIÓN (Flujo con búsqueda de noticias)

Cuando el usuario pida ejecutar el modelo, seguir estos pasos:

### 1. Buscar noticias con WebSearch (ANTES del modelo)

Hacer ~6 búsquedas cubriendo las categorías clave del player:
- General, Financiamiento, Rendimientos, Complejidad, Seguridad, Promociones

Ver regla `.cursor/rules/busqueda_noticias.mdc` para queries exactas.

### 2. Escribir noticias al batch JSON

Crear `data/noticias_cursor_batch.json` con las noticias encontradas.

### 3. Inyectar al cache

```bash
python scripts/agregar_noticias_cursor.py --file data/noticias_cursor_batch.json
```

### 4. Ejecutar el modelo (sin búsqueda Python)

```bash
python correr_modelo.py --site <SITE> --player "<PLAYER>" --q1 <Q1> --q2 <Q2> --no-news
```

### 5. Revisar gaps y completar si es necesario

Si el modelo reporta drivers sin noticias, buscar más con WebSearch y re-ejecutar.

Después de ejecutar, abrir el HTML generado en `outputs/`.
