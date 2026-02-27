# 📚 Documentación del Modelo NPS Competitivo

Esta carpeta contiene toda la documentación operativa y técnica del modelo.

## 📄 Documentos Disponibles

### [GUIA_CARGA_CLASIFICACION_MANUAL.md](GUIA_CARGA_CLASIFICACION_MANUAL.md)
**Guía completa para analistas**

Contiene:
- Flujo paso a paso para clasificar comentarios manualmente
- Configuración de triggers automáticos (GitHub Actions)
- Scripts de auto-carga a BigQuery
- Troubleshooting completo
- Queries BigQuery útiles

**Cuándo usar:** Cuando llega una nueva base con 26Q1 y necesitás procesarla.

---

## 🚀 Quick Start

```bash
# 1. Clasificar comentarios en Excel
# Abrir data/BASE_CRUDA_MLM.csv
# Llenar columna MOTIVO_IA

# 2. Subir al repo
git add data/BASE_CRUDA_MLM.csv
git commit -m "feat: Clasificación manual 26Q1 MLM"
git push

# 3. (Automático) Script detecta y sube a BigQuery

# 4. Ejecutar n8n automation
# Workflow: "Reclasificación comentarios"

# 5. Ejecutar modelo
python correr_modelo.py --site MLM --player "Mercado Pago" --q1 25Q4 --q2 26Q1
```

---

## 📞 Soporte

Para dudas o issues:
- GitHub Issues del repositorio
- Equipo CX Fintech
