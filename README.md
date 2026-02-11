# Modelo NPS Competitivo Individuos Fintech

Modelo de análisis de NPS Competitivo de Individuos en LATAM.

---

## Guía Rápida para Analistas

### Paso 1: Abrir el proyecto en Cursor

1. Abrir Cursor IDE
2. `File > Open Folder` → seleccionar la carpeta `MODELO_FINAL_CURSOR`

### Paso 2: Instalar dependencias (solo la primera vez)

Abrir terminal en Cursor (`Ctrl + ñ` o `View > Terminal`) y ejecutar:

```bash
# Opción A: Todas las dependencias (incluye BigQuery para MP/Nubank)
pip install -r requirements.txt

# Opción B: Solo dependencias básicas (sin BigQuery)
pip install -r requirements-minimal.txt
```

> **Nota:** Si solo vas a analizar players como Ualá, BBVA, Naranja X, etc., usá `requirements-minimal.txt` que es más rápido de instalar.

### Paso 3: Ejecutar el modelo

**Opción A - Desde el chat de Cursor:**
> "Corre el modelo para Mercado Pago México 25Q3 vs 25Q4"

**Opción B - Desde terminal:**
```bash
python correr_modelo.py --site MLM --player "Mercado Pago" --q1 25Q3 --q2 25Q4
```

### Paso 4: Ver el resultado

El HTML se genera en `outputs/Resumen_NPS_{Player}_{Quarter}.html`

Se abre automáticamente en el navegador.

---

## Sites y Players Disponibles

| Site | País | Players |
|------|------|---------|
| **MLB** | Brasil 🇧🇷 | Mercado Pago, Nubank, PicPay, Banco Inter, C6 Bank, Itaú, Bradesco, PagBank |
| **MLA** | Argentina 🇦🇷 | Mercado Pago, Ualá, Naranja X, Brubank, Personal Pay, MODO |
| **MLM** | México 🇲🇽 | Mercado Pago, Nubank, BBVA, Banamex, Santander, Hey Banco, Stori, Klar |
| **MLC** | Chile 🇨🇱 | Mercado Pago, Tenpo, MACH, Banco Estado |

---

## Ejemplos de uso

```bash
# Brasil - Nubank
python correr_modelo.py --site MLB --player "Nubank" --q1 25Q3 --q2 25Q4

# Argentina - Ualá
python correr_modelo.py --site MLA --player "Ualá" --q1 25Q3 --q2 25Q4

# México - BBVA
python correr_modelo.py --site MLM --player "BBVA" --q1 25Q3 --q2 25Q4
```

---

## Estructura del Proyecto

```
MODELO_FINAL_CURSOR/
├── correr_modelo.py          # Punto de entrada principal
├── requirements.txt          # Dependencias Python
├── README.md                 # Esta guía
├── config/
│   └── config.yaml           # Configuración por defecto
├── scripts/
│   ├── ejecutar_modelo.py    # Orquestador del modelo
│   ├── parte1_carga_datos.py # Carga de datos
│   ├── parte3_calculo_nps.py # Cálculo de NPS
│   ├── parte6_waterfall.py   # Waterfall NPS por motivo
│   ├── parte7_causas_raiz.py # Análisis de causas (deep dive)
│   ├── parte8_productos.py   # Impacto por productos
│   ├── parte9_principalidad.py
│   ├── parte10_seguridad.py
│   ├── analisis_automatico.py # Noticias y triangulación
│   └── generar_html.py       # Generador de HTML
├── data/                     # CSVs por site (BASE_CRUDA_*.csv)
│   └── noticias_cache.json   # Cache de noticias para triangulación
└── outputs/                  # HTMLs y gráficos generados
```

---

## Output del Modelo

El HTML generado incluye:

1. **Diagnóstico Principal**
   - Resumen narrativo automático (copiable para presentaciones)
   - Métricas: NPS, Principalidad, Seguridad
   - Quejas clave: Deterioros vs Mejoras
   - Productos clave por impacto

2. **Triangulación con Noticias**
   - Contexto del mercado
   - Noticias relacionadas a los drivers identificados

3. **Deep Dive**
   - Causas detalladas de variación
   - Subcausas con comentarios de usuarios

4. **Waterfall y Quejas**
   - Gráfico waterfall NPS por motivo
   - Evolución de quejas

5. **Productos**
   - Tabla de uso de productos
   - Impacto por mix effect y NPS effect

---

## Requisitos por Player

| Player | Requisitos | Sin BigQuery |
|--------|------------|--------------|
| **Mercado Pago** | BigQuery (categorías de comentarios) | ⚠️ Funciona pero motivos = "Otros" |
| **Nubank** | BigQuery (categorías de comentarios) | ⚠️ Funciona pero motivos = "Otros" |
| **Todos los demás** | Solo CSV local | ✅ Funciona 100% offline |

### Configurar BigQuery (solo para MP/Nubank)

Si necesitás analizar Mercado Pago o Nubank con categorización completa:

1. Instalar: `pip install google-cloud-bigquery`
2. Autenticarse: `gcloud auth application-default login`
3. Tener acceso a: `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`

Sin BigQuery, el modelo **no falla** pero los comentarios se marcan como "Otros".

---

## Troubleshooting

### Error: "No se encontraron datos para el player"
- Verificar que el nombre del player esté escrito correctamente (ver tabla arriba)
- El nombre es case-sensitive para algunos players

### Error: "ModuleNotFoundError"
- Ejecutar `pip install -r requirements.txt`

### El HTML no se abre automáticamente
- Buscar manualmente en `outputs/Resumen_NPS_*.html`

### Warning "BigQuery NO disponible" para MP/Nubank
- Es informativo, el modelo continúa
- Para categorización completa, configurar BigQuery (ver arriba)

---

## Contacto

Para dudas o mejoras, contactar al equipo de CX Fintech.
