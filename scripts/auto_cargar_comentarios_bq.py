#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script automático que detecta nuevos quarters en CSVs y los sube a BigQuery.

Trigger: Se ejecuta cuando se modifica data/BASE_CRUDA_*.csv

Uso:
    python scripts/auto_cargar_comentarios_bq.py

Autor: Equipo CX Fintech
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
import json
import sys
from validators import validate_required_columns, validate_csv_encoding

# Configuración
TRACKER_FILE = Path("data/.ultimo_quarter_cargado.json")

SITE_CONFIG = {
    'MLA': {
        'csv': 'data/BASE_CRUDA_MLA.csv',
        'tabla_bq': 'meli-bi-data.SBOX_NPS_ANALYTICS.BASE_COMENTARIOS_ARGENTINA',
        'encoding': 'utf-8',
        'sep': ';'
    },
    'MLB': {
        'csv': 'data/BASE_CRUDA_MLB.csv',
        'tabla_bq': 'meli-bi-data.SBOX_NPS_ANALYTICS.BASE_COMENTARIOS_BRASIL',
        'encoding': 'latin-1',
        'sep': ';'
    },
    'MLM': {
        'csv': 'data/BASE_CRUDA_MLM.csv',
        'tabla_bq': 'meli-bi-data.SBOX_NPS_ANALYTICS.BASE_COMENTARIOS_MEXICO',
        'encoding': 'utf-8',
        'sep': ';'
    }
}

def cargar_tracker():
    """Carga el registro de últimos quarters cargados."""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {}

def guardar_tracker(tracker):
    """Guarda el registro de quarters cargados."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2)

def detectar_nuevos_quarters(csv_path, site, ultimo_q_cargado):
    """
    Lee CSV y detecta quarters nuevos (no cargados aún).
    Retorna lista de quarters a cargar.
    """
    cfg = SITE_CONFIG[site]

    # Leer solo columna OLA
    df = pd.read_csv(
        csv_path,
        sep=cfg['sep'],
        encoding=cfg['encoding'],
        skiprows=1,
        usecols=['OLA']
    )

    quarters_en_csv = sorted(df['OLA'].unique())

    # Detectar nuevos
    if not ultimo_q_cargado:
        # Primera vez: cargar solo el más reciente
        nuevos = [quarters_en_csv[-1]]
    else:
        # Cargar quarters posteriores al último cargado
        nuevos = [q for q in quarters_en_csv if q > ultimo_q_cargado]

    return nuevos

def preparar_comentarios_para_bq(csv_path, site, quarter):
    """
    Extrae comentarios del CSV para un quarter específico.
    Solo comentarios detractores/neutrals con MOTIVO_IA llenado.
    """
    cfg = SITE_CONFIG[site]

    print(f"   📥 Leyendo {csv_path} (quarter: {quarter})...")

    # Validar encoding del CSV antes de leer
    validate_csv_encoding(str(csv_path), cfg['encoding'])

    # Leer CSV completo
    df = pd.read_csv(
        csv_path,
        sep=cfg['sep'],
        encoding=cfg['encoding'],
        skiprows=1,
        low_memory=False
    )

    # Validar columnas requeridas
    required_cols = ['OLA', 'P5', 'Comentarios']
    validate_required_columns(df, required_cols, f"CSV {site}")

    # Filtrar quarter específico
    df = df[df['OLA'] == quarter].copy()
    print(f"   Total registros en {quarter}: {len(df):,}")

    # Solo detractores y neutrals (P5 = 0-6)
    df = df[df['P5'].isin([0,1,2,3,4,5,6])].copy()
    print(f"   Detractores + Neutrals: {len(df):,}")

    # Solo los que tienen MOTIVO_IA (clasificación manual)
    if 'MOTIVO_IA' not in df.columns:
        print(f"   ⚠️  No existe columna MOTIVO_IA")
        return None

    df = df[df['MOTIVO_IA'].notna()].copy()
    df = df[df['MOTIVO_IA'].str.strip() != ''].copy()
    print(f"   Con MOTIVO_IA clasificado: {len(df):,}")

    if len(df) == 0:
        print(f"   ⚠️  No hay comentarios clasificados manualmente")
        return None

    # Preparar DataFrame para BigQuery
    df_bq = pd.DataFrame({
        'numericalId': range(1, len(df) + 1),
        'OLA': df['OLA'],
        'MARCA_REGISTRO': df['PAGO'],  # O ajustar según CSV
        'NPS': df['P5'].apply(lambda x: -1 if x <= 6 else (0 if x <= 8 else 1)),
        'Comentarios': df['Comentarios'],
        'MOTIVO_DETRA': df.get('P6', ''),
        'MOTIVO_NEUTRO': df.get('P7', ''),
        'MOTIVO_IA': df['MOTIVO_IA']
    })

    return df_bq

def subir_a_bigquery(df, tabla_bq, site, quarter):
    """Sube DataFrame a BigQuery."""

    if df is None or len(df) == 0:
        return False

    print(f"   📤 Subiendo {len(df):,} comentarios a BigQuery...")

    client = bigquery.Client()

    # Configuración
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND"
    )

    # Subir
    job = client.load_table_from_dataframe(df, tabla_bq, job_config=job_config)
    job.result()

    print(f"   ✅ Cargado a {tabla_bq}")
    return True

def procesar_site(site):
    """Procesa un site específico."""

    cfg = SITE_CONFIG[site]
    csv_path = Path(cfg['csv'])

    if not csv_path.exists():
        print(f"⚠️  {site}: CSV no encontrado: {csv_path}")
        return

    print(f"\n{'='*70}")
    print(f"🌎 PROCESANDO {site}")
    print(f"{'='*70}")

    # Cargar tracker
    tracker = cargar_tracker()
    ultimo_q = tracker.get(site)

    # Detectar nuevos quarters
    nuevos_qs = detectar_nuevos_quarters(csv_path, site, ultimo_q)

    if not nuevos_qs:
        print(f"   ✅ No hay quarters nuevos (último: {ultimo_q})")
        return

    print(f"   🆕 Quarters nuevos detectados: {nuevos_qs}")

    # Procesar cada quarter nuevo
    for quarter in nuevos_qs:
        print(f"\n   📊 Procesando {quarter}...")

        # Extraer comentarios
        df = preparar_comentarios_para_bq(csv_path, site, quarter)

        # Subir a BigQuery
        if subir_a_bigquery(df, cfg['tabla_bq'], site, quarter):
            # Actualizar tracker
            tracker[site] = quarter
            guardar_tracker(tracker)
            print(f"   ✅ {quarter} cargado y registrado")
        else:
            print(f"   ⚠️  {quarter} sin datos para cargar")

    print(f"\n✅ {site} completado")

def main():
    """Punto de entrada principal."""

    print("\n" + "="*70)
    print("🤖 AUTO-CARGA DE COMENTARIOS A BIGQUERY")
    print("="*70)

    # Procesar cada site
    for site in ['MLA', 'MLB', 'MLM']:
        try:
            procesar_site(site)
        except Exception as e:
            print(f"\n❌ Error en {site}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO")
    print("="*70)
    print("\nPróximos pasos:")
    print("1. Ejecutar n8n automation: 'Reclasificación comentarios'")
    print("2. Ejecutar modelo: python correr_modelo.py ...")

if __name__ == '__main__':
    main()
