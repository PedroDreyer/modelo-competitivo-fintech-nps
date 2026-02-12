# 📘 GUÍA COMPLETA: CLASIFICACIÓN MANUAL Y CARGA AUTOMATIZADA

**Modelo NPS Competitivo Individuos Fintech**
**Versión:** 2.0
**Última actualización:** Febrero 2026
**Para:** Mercado Pago y Nubank

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Flujo Paso a Paso](#flujo-paso-a-paso)
4. [Guía para Analistas](#guía-para-analistas)
5. [Scripts y Automatización](#scripts-y-automatización)
6. [Configuración Técnica](#configuración-técnica)
7. [Troubleshooting](#troubleshooting)

---

## 1. RESUMEN EJECUTIVO

### ¿Qué hace este sistema?

Permite clasificar manualmente comentarios de NPS para Mercado Pago y Nubank cuando llega una nueva base (ej: 26Q1), y automatiza la carga a BigQuery para que el modelo NPS pueda procesarlos.

### Flujo Simplificado

```
Analista recibe CSV → Clasifica comentarios → Push a Git
        ↓
Script automático detecta cambio → Sube a BigQuery
        ↓
Analista corre n8n automation → Guarda en tabla del modelo
        ↓
Analista ejecuta modelo → HTML generado
```

### Tiempo Estimado

- **Clasificación manual:** 1-2 horas (según cantidad de comentarios)
- **Carga automática:** 5-10 minutos (automático)
- **Ejecución n8n:** 15-30 minutos
- **Ejecución modelo:** 5-10 minutos

**Total:** ~2-3 horas

---

## 2. ARQUITECTURA DEL SISTEMA

### Tablas BigQuery Involucradas

```
┌─────────────────────────────────────┐
│  BASE_COMENTARIOS_MEXICO            │  ← Tabla intermedia
│  BASE_COMENTARIOS_ARGENTINA         │     (recibe clasificación manual)
│  BASE_COMENTARIOS_BRASIL            │
└────────────────┬────────────────────┘
                 │
                 │ n8n automation
                 │ (copia y valida)
                 ↓
┌─────────────────────────────────────┐
│  comentarios_reclasificados_fintech │  ← Tabla que lee el modelo
└─────────────────────────────────────┘
```

### Flujo de Datos

```
1. CSV Local (clasificación manual)
   ↓
2. Git Push (trigger)
   ↓
3. Script Python (extrae + sube a BigQuery)
   ↓
4. BASE_COMENTARIOS_* (tabla intermedia)
   ↓
5. n8n automation (validación + copia)
   ↓
6. comentarios_reclasificados_fintech
   ↓
7. Modelo NPS (lectura)
```

---

## 3. FLUJO PASO A PASO

### PASO 1: Recepción de Nueva Base

**Input:**
- `BASE_CRUDA_MLA.csv` (Argentina)
- `BASE_CRUDA_MLB.csv` (Brasil)
- `BASE_CRUDA_MLM.csv` (México)

**Características:**
- Contiene data histórica + nuevo quarter (ej: 26Q1)
- Formato: CSV delimitado por `;`
- Encoding: UTF-8 (MLA/MLM) o Latin-1 (MLB)
- Tamaño: ~150-200MB por archivo

---

### PASO 2: Clasificación Manual

**Ubicación:** Columna `MOTIVO_IA` en el CSV

**Proceso:**

1. Abrir CSV en Excel
2. Buscar/crear columna `MOTIVO_IA`
3. Filtrar `OLA = "26Q1"`
4. Filtrar `P5 IN (0,1,2,3,4,5,6)` (solo detractores/neutrals)
5. Para cada comentario, asignar UNA categoría

**Categorías Válidas (Español - MLM/MLA):**

| Categoría | Cuándo Usar | Ejemplo |
|-----------|-------------|---------|
| **Tasa de interés de crédito o tarjeta** | Menciona "tasa", "interés", "APR", "TNA" | "Los intereses son muy altos" |
| **Límites bajos de crédito o tarjeta** | Menciona "límite", "límite bajo", "aumentar límite" | "No me suben el límite" |
| **Acceso a crédito o tarjeta de crédito** | Menciona "no conseguí crédito", "negaron tarjeta" | "Me rechazaron el préstamo" |
| **Rendimientos** | Menciona "rendimiento", "rentabilidad", "inversiones" | "El CDI es bajo" |
| **Seguridad** | Menciona "fraude", "robo", "seguridad", "hackeo" | "Tuve un fraude en mi cuenta" |
| **Promociones y descuentos** | Menciona "cashback", "descuento", "promoción" | "Quitaron el cashback" |
| **Atención al cliente** | Menciona "atención", "soporte", "chat", "demora" | "El chat nunca responde" |
| **Oferta de funcionalidades** | Pide nueva función, "falta", "debería tener" | "No tiene pago por QR" |
| **Dificultad de uso** | Menciona "difícil", "confuso", "bug", "se traba" | "La app se cuelga" |
| **Tarifas de la cuenta** | Menciona "tarifa", "comisión", "cobro mensual" | "Me cobran $150 al mes" |
| **No uso o sin opinión** | Comentario vacío/genérico sin detalle específico | "Nada", "Ok", "Bueno" |

**Categorías Válidas (Portugués - MLB):**

| Categoría | Cuándo Usar |
|-----------|-------------|
| Taxa de juros de crédito ou cartão | Menciona "taxa", "juros", "APR" |
| Limites baixos de crédito ou cartão | Menciona "limite", "limite baixo" |
| Acesso a crédito ou cartão de crédito | Menciona "não consegui crédito" |
| Rendimentos | Menciona "rendimento", "CDI", "poupança" |
| Segurança | Menciona "fraude", "golpe", "segurança" |
| Promoções e descontos | Menciona "cashback", "desconto" |
| Atendimento ao cliente | Menciona "atendimento", "SAC", "chat" |
| Oferta de funcionalidades | Pide "funcionalidade", "Pix", "recurso" |
| Dificuldade de uso | Menciona "difícil", "bug", "travando" |
| Tarifas da conta | Menciona "tarifa", "taxa de manutenção" |
| Não uso ou sem opinião | Comentario vacío/genérico |

**⚠️ REGLA CRÍTICA:**

**Comentarios vagos/genéricos → SIEMPRE "No uso o sin opinión"**

Ejemplos:
- ❌ "Muy bueno" → NO clasificar como nada específico
- ✅ "Muy bueno" → "No uso o sin opinión"
- ❌ "Debe mejorar" → NO clasificar como nada específico
- ✅ "Debe mejorar" → "No uso o sin opinión"

Solo clasificar específicamente si el comentario **menciona algo concreto**.

---

### PASO 3: Subir al Repositorio

**Comandos Git:**

```bash
# Ir al directorio del proyecto
cd MODELO_NPS_COMPETITIVO_INDIVIDUOS_FINTECH

# Verificar cambios
git status

# Agregar CSV modificado
git add data/BASE_CRUDA_MLM.csv

# Commit con mensaje descriptivo
git commit -m "feat: Agregar clasificación manual 26Q1 MLM - Mercado Pago"

# Push al repositorio
git push origin main
```

**¿Qué pasa automáticamente después del push?**

1. **GitHub Action se activa** (si está configurado)
2. Script `auto_cargar_comentarios_bq.py` se ejecuta
3. Detecta que 26Q1 es un quarter nuevo
4. Extrae comentarios clasificados del CSV
5. Los sube a BigQuery tabla `BASE_COMENTARIOS_MEXICO`
6. Actualiza tracker `.ultimo_quarter_cargado.json`
7. Hace commit automático del tracker

**Verificar que funcionó:**

- Ver logs en GitHub Actions (tab "Actions" en GitHub)
- Buscar mensaje: `✅ 26Q1 cargado y registrado`

---

### PASO 4: Ejecutar n8n Automation

**Propósito:** Validar categorías y copiar a tabla del modelo

**Pasos:**

1. Ir a n8n (URL interna de Meli)
2. Buscar workflow: `Reclasificación comentarios`
3. Clic en nodo `TRIGGER`
4. Clic en `Execute Workflow`
5. Esperar ~15-30 minutos (procesa 1,500 comentarios: 500 x 3 países)

**¿Qué hace el n8n?**

```
BASE_COMENTARIOS_MEXICO
  ↓ (lee comentarios con MOTIVO_IA)
Validación de categorías (Filter node)
  ↓ (solo pasan categorías válidas)
INSERT en comentarios_reclasificados_fintech
  ↓
Copia: MOTIVO_IA → MOTIVO_RECLASIFICADO
```

**Verificar en BigQuery:**

```sql
SELECT
    SITE,
    OLA,
    MARCA,
    COUNT(*) as total,
    COUNT(DISTINCT MOTIVO_RECLASIFICADO) as categorias_unicas
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
WHERE OLA = '26Q1'
GROUP BY SITE, OLA, MARCA
ORDER BY total DESC
```

**Output esperado:**

| SITE | OLA | MARCA | total | categorias_unicas |
|------|-----|-------|-------|-------------------|
| MLM | 26Q1 | Mercado Pago | 1,245 | 8 |
| MLM | 26Q1 | Nubank | 892 | 7 |

---

### PASO 5: Ejecutar Modelo NPS

**Comando:**

```bash
python correr_modelo.py --site MLM --player "Mercado Pago" --q1 25Q4 --q2 26Q1
```

**Flujo del Modelo:**

```
1ra Ejecución:
  ├─> Carga datos
  ├─> Calcula NPS
  ├─> Lee clasificaciones de BigQuery ✅
  ├─> Genera waterfall
  ├─> PAUSA: Pide causas raíz semánticas
  └─> EXIT CODE 42

Analista/Cursor genera causas raíz:
  ├─> Lee prompt generado
  ├─> Analiza comentarios
  ├─> Guarda JSON: data/causas_raiz_semantico_Mercado Pago_MLM_26Q1.json
  └─> Busca noticias con WebSearch

2da Ejecución:
  ├─> Carga causas raíz ✅
  ├─> Carga noticias ✅
  ├─> Triangula Producto ↔ Queja ↔ Noticia
  ├─> Genera HTML
  └─> outputs/Resumen_NPS_Mercado_Pago_26Q1.html
```

**Output Final:**

HTML con 3 tabs:
1. **Resumen:** Diagnóstico ejecutivo + métricas clave
2. **Drivers NPS:** Waterfall + evolución de quejas
3. **Análisis Cualitativo:** Causas raíz semánticas detalladas

---

## 4. GUÍA PARA ANALISTAS

### Checklist Previo

Antes de empezar, verificar:

- [ ] Tengo acceso al repositorio Git
- [ ] Tengo acceso a BigQuery (proyecto `meli-bi-data`)
- [ ] Tengo acceso a n8n
- [ ] Tengo Python 3.10+ instalado
- [ ] Tengo `gcloud` CLI configurado
- [ ] Conozco las categorías de clasificación

### Guía Rápida (TL;DR)

```bash
# 1. Clasificar
# Abrir data/BASE_CRUDA_MLM.csv en Excel
# Llenar columna MOTIVO_IA para quarter 26Q1
# Guardar

# 2. Subir
git add data/BASE_CRUDA_MLM.csv
git commit -m "feat: Clasificación manual 26Q1 MLM"
git push

# 3. Esperar auto-carga (GitHub Action)
# Ver logs en GitHub > Actions

# 4. Ejecutar n8n
# Abrir workflow "Reclasificación comentarios"
# Ejecutar

# 5. Ejecutar modelo
python correr_modelo.py --site MLM --player "Mercado Pago" --q1 25Q4 --q2 26Q1
```

### Template para Clasificación

**Archivo Excel de Referencia:**

| numericalId | OLA | MARCA | P5 | Comentarios | MOTIVO_IA |
|-------------|-----|-------|----|--------------|--------------------|
| (auto) | 26Q1 | Mercado Pago | 2 | "Las tasas son muy altas" | Tasa de interés de crédito o tarjeta |
| (auto) | 26Q1 | Mercado Pago | 4 | "No aumentan mi límite" | Límites bajos de crédito o tarjeta |
| (auto) | 26Q1 | Nubank | 3 | "El app se traba mucho" | Dificultad de uso |

### FAQ Analistas

**P: ¿Debo clasificar TODOS los comentarios?**
R: Solo detractores y neutrals (P5 = 0-6). Promotores (9-10) no necesitan clasificación de quejas.

**P: ¿Qué hago si un comentario tiene múltiples temas?**
R: Elegir el tema PRINCIPAL que menciona el usuario. Si es 50/50, priorizar el más negativo.

**P: ¿Puedo usar abreviaciones de las categorías?**
R: NO. Debe ser el nombre EXACTO. Usa copy-paste de la lista de categorías.

**P: ¿Qué pasa si me equivoco en una clasificación?**
R: Podés corregir en el CSV, hacer commit y re-ejecutar el proceso.

**P: ¿Cuánto tiempo lleva clasificar 1,000 comentarios?**
R: Aproximadamente 1-2 horas (30-60 comentarios por hora).

---

## 5. SCRIPTS Y AUTOMATIZACIÓN

### Script 1: auto_cargar_comentarios_bq.py

**Ubicación:** `scripts/auto_cargar_comentarios_bq.py`

**Función:** Detecta cambios en CSVs y sube comentarios clasificados a BigQuery automáticamente.

**Trigger:**
- Git push a `data/BASE_CRUDA_*.csv` (GitHub Action)
- Post-commit hook (local)

**Lógica:**

```python
1. Lee archivo tracker: .ultimo_quarter_cargado.json
   Ejemplo: {"MLM": "25Q4", "MLA": "25Q3", "MLB": "25Q4"}

2. Lee CSV y detecta quarters disponibles
   CSV tiene: [24Q1, 24Q2, 24Q3, 24Q4, 25Q1, 25Q2, 25Q3, 25Q4, 26Q1]

3. Compara con tracker
   Último cargado: 25Q4
   Nuevos: [26Q1]

4. Para cada quarter nuevo:
   - Extrae comentarios con MOTIVO_IA llenado
   - Filtra solo detractores/neutrals
   - Sube a BASE_COMENTARIOS_MEXICO

5. Actualiza tracker
   {"MLM": "26Q1", ...}
```

**Columnas que extrae del CSV:**

| CSV Original | BigQuery |
|--------------|----------|
| (índice auto) | numericalId |
| OLA | OLA |
| PAGO | MARCA_REGISTRO |
| P5 → convertido | NPS (-1, 0, +1) |
| Comentarios | Comentarios |
| P6 | MOTIVO_DETRA |
| P7 | MOTIVO_NEUTRO |
| MOTIVO_IA | MOTIVO_IA |

**Ejecución Manual:**

```bash
python scripts/auto_cargar_comentarios_bq.py
```

**Output:**

```
══════════════════════════════════════════════════════════════════════
🤖 AUTO-CARGA DE COMENTARIOS A BIGQUERY
══════════════════════════════════════════════════════════════════════

🌎 PROCESANDO MLM
══════════════════════════════════════════════════════════════════════
   🆕 Quarters nuevos detectados: ['26Q1']
   📊 Procesando 26Q1...
   📥 Leyendo data/BASE_CRUDA_MLM.csv (quarter: 26Q1)...
   Total registros en 26Q1: 5,234
   Detractores + Neutrals: 2,145
   Con MOTIVO_IA clasificado: 1,892
   📤 Subiendo 1,892 comentarios a BigQuery...
   ✅ Cargado a meli-bi-data.SBOX_NPS_ANALYTICS.BASE_COMENTARIOS_MEXICO
   ✅ 26Q1 cargado y registrado

✅ MLM completado

══════════════════════════════════════════════════════════════════════
✅ PROCESO COMPLETADO
══════════════════════════════════════════════════════════════════════

Próximos pasos:
1. Ejecutar n8n automation: 'Reclasificación comentarios'
2. Ejecutar modelo: python correr_modelo.py ...
```

---

### Script 2: Tracker de Quarters

**Ubicación:** `data/.ultimo_quarter_cargado.json`

**Función:** Registro de últimos quarters procesados por site.

**Formato:**

```json
{
  "MLA": "25Q4",
  "MLB": "25Q4",
  "MLM": "26Q1"
}
```

**Uso:**
- Evita reprocesar quarters ya cargados
- Se actualiza automáticamente después de cada carga exitosa
- Se versiona en Git para mantener sincronía entre ambientes

---

## 6. CONFIGURACIÓN TÉCNICA

### Opción A: GitHub Action (Recomendado para Producción)

**Archivo:** `.github/workflows/auto_upload_bigquery.yml`

**Trigger:** Push a `data/BASE_CRUDA_*.csv`

**Configuración:**

```yaml
name: Auto-carga Comentarios a BigQuery

on:
  push:
    paths:
      - 'data/BASE_CRUDA_*.csv'

jobs:
  upload-to-bigquery:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout código
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Instalar dependencias
        run: |
          pip install pandas google-cloud-bigquery

      - name: Autenticar BigQuery
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_CREDENTIALS }}

      - name: Ejecutar auto-carga
        run: |
          python scripts/auto_cargar_comentarios_bq.py

      - name: Commit tracker actualizado
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/.ultimo_quarter_cargado.json
          git commit -m "chore: Actualizar tracker quarters cargados" || true
          git push || true
```

**Setup Requerido:**

1. Ir a GitHub Repo > Settings > Secrets and variables > Actions
2. Agregar secret: `GCP_CREDENTIALS`
3. Valor: JSON del service account de BigQuery
4. Service account necesita permisos:
   - `BigQuery Data Editor`
   - `BigQuery Job User`

**Verificar que funciona:**

1. Hacer push de CSV
2. Ir a GitHub > Actions
3. Ver workflow ejecutándose
4. Verificar logs

---

### Opción B: Git Hook Local (Desarrollo/Testing)

**Archivo:** `.git/hooks/post-commit`

```bash
#!/bin/bash

# Detectar si se modificaron CSVs
if git diff --name-only HEAD~1 | grep -q "data/BASE_CRUDA_.*\.csv"; then
    echo "🔍 Detectado cambio en CSVs, ejecutando auto-carga..."
    python scripts/auto_cargar_comentarios_bq.py
fi
```

**Instalación:**

```bash
# Crear el hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
if git diff --name-only HEAD~1 | grep -q "data/BASE_CRUDA_.*\.csv"; then
    echo "🔍 Detectado cambio en CSVs, ejecutando auto-carga..."
    python scripts/auto_cargar_comentarios_bq.py
fi
EOF

# Hacerlo ejecutable
chmod +x .git/hooks/post-commit
```

**Testing:**

```bash
# Modificar CSV
echo "test" >> data/BASE_CRUDA_MLM.csv

# Commit (trigger automático)
git add data/BASE_CRUDA_MLM.csv
git commit -m "test: trigger hook"

# Ver output del script en la terminal
```

---

### Dependencias Python

**Archivo:** `requirements.txt`

```
pandas>=2.0.0
google-cloud-bigquery>=3.0.0
```

**Instalación:**

```bash
pip install -r requirements.txt
```

---

### Autenticación BigQuery

**Opción 1: gcloud CLI (Local)**

```bash
gcloud auth application-default login
```

**Opción 2: Service Account (GitHub Actions)**

1. Crear service account en GCP Console
2. Descargar JSON key
3. Agregar a GitHub Secrets como `GCP_CREDENTIALS`

---

## 7. TROUBLESHOOTING

### Error: "No se encontró columna MOTIVO_IA"

**Síntoma:**
```
⚠️ No existe columna MOTIVO_IA
⚠️ No hay comentarios clasificados manualmente
```

**Causa:** El CSV no tiene la columna MOTIVO_IA

**Solución:**
1. Abrir CSV en Excel
2. Agregar columna `MOTIVO_IA` (después de `Comentarios`)
3. Clasificar comentarios
4. Guardar y hacer push nuevamente

---

### Error: "Categoría inválida"

**Síntoma:**
```
❌ ERROR: Categorías inválidas encontradas:
   numericalId: 123456
   MOTIVO_RECLASIFICADO: "Tasas altas"
```

**Causa:** La categoría no coincide exactamente con las válidas

**Solución:**
1. Verificar que copiaste el nombre EXACTO (incluyendo tildes)
2. No uses abreviaciones
3. Usa copy-paste de la lista de categorías

**Categorías correctas:**
- ✅ `Tasa de interés de crédito o tarjeta`
- ❌ `Tasas altas`
- ❌ `Tasa de interes` (falta tilde)

---

### Error: "BigQuery permission denied"

**Síntoma:**
```
403 Forbidden: Access Denied
```

**Causa:** No tenés permisos en BigQuery

**Solución:**

**Local:**
```bash
gcloud auth application-default login
```

**GitHub Actions:**
1. Verificar que el secret `GCP_CREDENTIALS` existe
2. Verificar que el service account tiene permisos:
   - BigQuery Data Editor
   - BigQuery Job User

---

### Error: "El n8n no procesa mis comentarios"

**Síntoma:** Comentarios están en `BASE_COMENTARIOS_*` pero no en `comentarios_reclasificados_fintech`

**Diagnóstico:**

```sql
-- Ver comentarios en tabla base
SELECT COUNT(*)
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.BASE_COMENTARIOS_MEXICO`
WHERE OLA = '26Q1' AND MOTIVO_IA IS NOT NULL

-- Ver comentarios en tabla destino
SELECT COUNT(*)
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
WHERE SITE = 'MLM' AND OLA = '26Q1'
```

**Solución:**
1. Verificar que ejecutaste el n8n workflow
2. Ver logs del n8n para errores
3. Verificar que las categorías son válidas
4. Re-ejecutar n8n si es necesario

---

### Error: "El modelo no encuentra datos para 26Q1"

**Síntoma:**
```
❌ ERROR: No se encontraron datos para Mercado Pago en 26Q1
```

**Diagnóstico:**

```sql
SELECT DISTINCT OLA, MARCA
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
WHERE SITE = 'MLM'
ORDER BY OLA DESC
```

**Solución:**
1. Verificar que corriste los pasos anteriores (auto-carga + n8n)
2. Verificar que hay datos en BigQuery
3. Verificar que el nombre del player coincide exactamente

---

### Warning: "Duplicados detectados"

**Síntoma:**
```
⚠️ Warning: Se encontraron 145 registros duplicados
```

**Causa:** Se ejecutó la carga múltiples veces para el mismo quarter

**Solución:**

```sql
-- Eliminar duplicados
DELETE FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
WHERE ROWID NOT IN (
    SELECT MIN(ROWID)
    FROM `meli-bi-data.SBOX_NPS_COMPETITIVO.comentarios_reclasificados_fintech`
    GROUP BY SURVEY_ID, SITE, OLA, MARCA
)
AND SITE = 'MLM' AND OLA = '26Q1'
```

Luego re-ejecutar la carga.

---

### El HTML se ve incompleto

**Síntoma:** HTML generado no tiene causas raíz o noticias

**Diagnóstico:**

```bash
# Verificar que existe JSON de causas raíz
ls -lh data/causas_raiz_semantico_Mercado\ Pago_MLM_26Q1.json

# Verificar que hay noticias
cat data/noticias_cache.json | grep "26Q1"
```

**Solución:**
1. Generar causas raíz con Cursor AI (ver Paso 4.3 en guía principal)
2. Buscar noticias con WebSearch (ver Paso 4.5)
3. Re-ejecutar modelo

---

## 8. ANEXOS

### A. Mapeo de Categorías a Dimensiones del Modelo

| Categoría n8n/Manual | Dimensión Modelo NPS |
|---------------------|---------------------|
| Tasa de interés de crédito o tarjeta | Financiamiento |
| Límites bajos de crédito o tarjeta | Financiamiento |
| Acceso a crédito o tarjeta de crédito | Financiamiento |
| Rendimientos | Rendimientos |
| Seguridad | Seguridad |
| Promociones y descuentos | Promociones |
| Atención al cliente | Atención |
| Oferta de funcionalidades | Funcionalidades |
| Dificultad de uso | Dificultad |
| Tarifas de la cuenta | Tarifas |
| No uso o sin opinión | (Filtrado) |

---

### B. Estructura de Carpetas Completa

```
MODELO_NPS_COMPETITIVO_INDIVIDUOS_FINTECH/
│
├── .github/
│   └── workflows/
│       └── auto_upload_bigquery.yml        # GitHub Action trigger
│
├── config/
│   └── config.yaml                         # Configuración del modelo
│
├── data/
│   ├── BASE_CRUDA_MLA.csv                  # CSV Argentina
│   ├── BASE_CRUDA_MLB.csv                  # CSV Brasil
│   ├── BASE_CRUDA_MLM.csv                  # CSV México
│   ├── .ultimo_quarter_cargado.json        # Tracker automático
│   ├── noticias_cache.json                 # Cache de noticias
│   └── causas_raiz_semantico_*.json        # Causas raíz por análisis
│
├── scripts/
│   ├── auto_cargar_comentarios_bq.py       # Script auto-carga BigQuery
│   ├── ejecutar_modelo.py                  # Orquestador modelo
│   ├── generar_html.py                     # Generador HTML
│   ├── parte1_carga_datos.py               # Módulo carga
│   ├── parte4_categorizacion.py            # Módulo categorización
│   └── ...                                 # Otros módulos
│
├── outputs/
│   └── Resumen_NPS_*.html                  # HTMLs generados
│
├── correr_modelo.py                        # Punto de entrada
├── requirements.txt                        # Dependencias
└── README.md                               # Documentación
```

---

### C. Queries BigQuery Útiles

**Ver todos los quarters cargados:**

```sql
SELECT
    SITE,
    OLA,
    COUNT(*) as total_comentarios,
    COUNT(DISTINCT MARCA) as players,
    MIN(FECHA_PROCESAMIENTO) as primera_carga,
    MAX(FECHA_PROCESAMIENTO) as ultima_carga
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
GROUP BY SITE, OLA
ORDER BY SITE, OLA DESC
```

**Ver distribución de categorías:**

```sql
SELECT
    SITE,
    OLA,
    MARCA,
    MOTIVO_RECLASIFICADO,
    COUNT(*) as cantidad,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY SITE, OLA, MARCA), 1) as porcentaje
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
WHERE OLA = '26Q1'
GROUP BY SITE, OLA, MARCA, MOTIVO_RECLASIFICADO
ORDER BY SITE, MARCA, cantidad DESC
```

**Buscar comentarios específicos:**

```sql
SELECT
    SITE,
    OLA,
    MARCA,
    COMMENTS,
    MOTIVO_RECLASIFICADO
FROM `meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech`
WHERE OLA = '26Q1'
  AND SITE = 'MLM'
  AND MARCA = 'Mercado Pago'
  AND MOTIVO_RECLASIFICADO = 'Seguridad'
LIMIT 10
```

---

### D. Contactos y Soporte

**Para issues técnicos:**
- GitHub Issues: [repo]/issues
- Equipo CX Fintech

**Para dudas sobre clasificación:**
- Revisar esta guía, sección "Categorías Válidas"
- Consultar con lead del equipo

---

## CONTROL DE VERSIONES

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | Ene 2026 | Versión inicial con n8n manual |
| 2.0 | Feb 2026 | Agregado flujo automatizado con triggers |

---

## APÉNDICE: COMANDOS RÁPIDOS

```bash
# Clasificación y carga
git add data/BASE_CRUDA_MLM.csv
git commit -m "feat: Clasificación manual 26Q1 MLM"
git push  # Trigger automático

# Verificar carga en BigQuery
# (ejecutar query en BigQuery Console)

# Ejecutar modelo
python correr_modelo.py --site MLM --player "Mercado Pago" --q1 25Q4 --q2 26Q1

# Ver HTML
start outputs/Resumen_NPS_Mercado_Pago_26Q1.html  # Windows
open outputs/Resumen_NPS_Mercado_Pago_26Q1.html   # Mac
```

---

**FIN DEL DOCUMENTO**
