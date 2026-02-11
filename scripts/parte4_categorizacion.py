# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 4: CATEGORIZACIÓN - BIGQUERY + RAG FALLBACK
═══════════════════════════════════════════════════════════════════════════════

Sistema simplificado (replica EXACTAMENTE el notebook original):
1. Lookup en BigQuery (comentarios ya clasificados por n8n)
2. RAG FAISS + GPT como fallback para comments nuevos
3. Para players que NO requieren IA: usa motivo declarado

Uso:
    from scripts.parte4_categorizacion import categorizar_comentarios
    resultado = categorizar_comentarios(df_player, config, resultados_parte3)
"""

import pandas as pd
import hashlib
import unicodedata
import re
import time
import os
from tqdm.auto import tqdm
from datetime import datetime
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN POR SITE
# ==============================================================================

SITE_CAT_CONFIG = {
    'MLB': {
        'sin_opinion': 'Não uso ou sem opinião',
        'otros': 'Outros',
        'idioma': 'PT',
        'site_code': 'MLB'
    },
    'MLA': {
        'sin_opinion': 'No uso o sin opinión',
        'otros': 'Otros',
        'idioma': 'ES',
        'site_code': 'MLA'
    },
    'MLM': {
        'sin_opinion': 'No uso o sin opinión',
        'otros': 'Otros',
        'idioma': 'ES',
        'site_code': 'MLM'
    },
    'MLC': {
        'sin_opinion': 'No uso o sin opinión',
        'otros': 'Otros',
        'idioma': 'ES',
        'site_code': 'MLC'
    }
}

# Tabla de BigQuery con las clasificaciones (n8n workflow)
BQ_TABLE = "meli-bi-data.SBOX_NPS_ANALYTICS.comentarios_reclasificados_fintech"

# ==============================================================================
# CATEGORÍAS POR IDIOMA
# ==============================================================================

CATEGORIAS_PT = [
    "Taxa de juros de crédito ou cartão",
    "Limites baixos de crédito ou cartão",
    "Acesso a crédito ou cartão de crédito",
    "Rendimentos",
    "Segurança",
    "Promoções e descontos",
    "Atendimento ao cliente",
    "Oferta de funcionalidades",
    "Dificuldade de uso",
    "Tarifas da conta",
    "Não uso ou sem opinião"
]

CATEGORIAS_ES = [
    "Tasa de interés de crédito o tarjeta",
    "Límites bajos de crédito o tarjeta",
    "Acceso a crédito o tarjeta de crédito",
    "Rendimientos",
    "Seguridad",
    "Promociones y descuentos",
    "Atención al cliente",
    "Oferta de funcionalidades",
    "Dificultad de uso",
    "Tarifas de la cuenta",
    "No uso o sin opinión"
]

# Players que requieren IA (Mercado Pago, Nubank)
PLAYERS_CON_IA = ['mercado pago', 'pago', 'mp', 'nubank', 'nu bank', 'nu']

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def normalizar_texto(texto):
    """Normalizar texto para hashing"""
    if pd.isna(texto):
        return ""
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return ' '.join(texto.split())

def hash_comentario(texto):
    """Generar hash MD5 único del comentario"""
    texto_norm = normalizar_texto(texto)
    return hashlib.md5(texto_norm.encode()).hexdigest()

def _strip_acc(txt):
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")

def canonize(txt, categorias_canon, otros):
    """Canonizar texto para categoría más próxima"""
    import difflib
    txt_clean = _strip_acc(txt).casefold()
    canon_clean = [_strip_acc(c).casefold() for c in categorias_canon]
    match = difflib.get_close_matches(txt_clean, canon_clean, n=1, cutoff=0.75)
    return categorias_canon[canon_clean.index(match[0])] if match else otros

def es_player_con_ia(player_name):
    """Determina si el player requiere categorización con IA"""
    if not player_name:
        return False
    player_lower = str(player_name).lower().strip()
    return any(v in player_lower or player_lower in v for v in PLAYERS_CON_IA)

# ==============================================================================
# CONEXIÓN A BIGQUERY
# ==============================================================================

def conectar_bigquery():
    """
    Conecta a BigQuery usando google-cloud-bigquery.
    Requiere credenciales configuradas (GOOGLE_APPLICATION_CREDENTIALS o gcloud auth)
    """
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        return client
    except Exception as e:
        print(f"   ⚠️ Error conectando a BigQuery: {e}")
        return None

def cargar_categorias_bigquery(site_code, verbose=True):
    """
    Carga categorías desde BigQuery.
    
    Returns:
        tuple: (bq_por_clave, bq_por_id, bq_por_hash, bq_disponible)
    """
    bq_por_clave = {}  # Clave compuesta: ID|OLA|MARCA
    bq_por_id = {}     # Fallback solo por ID
    bq_por_hash = {}
    bq_disponible = False
    
    if verbose:
        print(f"\n📦 Cargando categorías desde BigQuery...")
    
    try:
        client = conectar_bigquery()
        if client is None:
            return bq_por_clave, bq_por_id, bq_por_hash, False
        
        query_bq = f"""
        SELECT 
            CAST(numericalId AS STRING) AS numericalId,
            OLA,
            MARCA,
            COMMENTS,
            MOTIVO_RECLASIFICADO
        FROM `{BQ_TABLE}`
        WHERE SITE = '{site_code}'
          AND MOTIVO_RECLASIFICADO IS NOT NULL
          AND TRIM(MOTIVO_RECLASIFICADO) != ''
        """
        
        if verbose:
            print(f"   📡 Consultando BigQuery para SITE={site_code}...")
        
        df_bq = client.query(query_bq).to_dataframe()
        
        if len(df_bq) > 0:
            for _, row in df_bq.iterrows():
                categoria = str(row['MOTIVO_RECLASIFICADO']).strip()
                
                # Índice por clave compuesta: ID|OLA|MARCA (más preciso)
                if pd.notna(row['numericalId']) and pd.notna(row.get('OLA')) and pd.notna(row.get('MARCA')):
                    clave = f"{row['numericalId']}|{row['OLA']}|{row['MARCA']}"
                    bq_por_clave[clave] = categoria
                
                # Índice por ID solo (fallback)
                if pd.notna(row['numericalId']):
                    bq_por_id[str(row['numericalId'])] = categoria
                
                # Índice por hash
                if pd.notna(row['COMMENTS']):
                    hash_com = hash_comentario(str(row['COMMENTS']))
                    bq_por_hash[hash_com] = categoria
            
            bq_disponible = True
            if verbose:
                print(f"   ✅ BigQuery: {len(bq_por_clave):,} por clave (ID|OLA|MARCA), {len(bq_por_hash):,} por hash")
        else:
            if verbose:
                print(f"   ⚠️ No hay datos en BigQuery para SITE={site_code}")
            
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Error BigQuery: {e}")
    
    return bq_por_clave, bq_por_id, bq_por_hash, bq_disponible

# ==============================================================================
# FUNCIÓN PRINCIPAL: CATEGORIZAR COMENTARIOS
# ==============================================================================

def categorizar_comentarios(df_player, config, resultados_parte3=None, verbose=True):
    """
    Categoriza comentarios de neutros y detractores.
    
    Replica EXACTAMENTE la lógica del notebook original:
    1. Filtra neutros (NPS=0) y detractores (NPS=-1)
    2. Filtra últimos 5 quarters
    3. Para players que NO requieren IA: usa motivo declarado
    4. Para players que SÍ requieren IA: BigQuery + fallback
    
    Args:
        df_player: DataFrame con datos del player (de PARTE 3)
        config: Diccionario de configuración
        resultados_parte3: Resultados de PARTE 3 (opcional, para quarters_seleccionados)
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con df_categorizado, df_final_categorizado, etc.
    """
    
    # Extraer configuración
    site = config['site']
    player_seleccionado = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    
    # Configuración por site
    CFG_CAT = SITE_CAT_CONFIG.get(site, SITE_CAT_CONFIG['MLA'])
    SIN_OPINION = CFG_CAT['sin_opinion']
    OTROS = CFG_CAT['otros']
    IDIOMA = CFG_CAT['idioma']
    SITE_CODE = CFG_CAT['site_code']
    
    # Categorías según idioma
    CATEGORIAS_CANON = CATEGORIAS_PT if IDIOMA == 'PT' else CATEGORIAS_ES
    
    # Columnas
    col_nps = 'NPS'
    col_ola = 'OLA'
    col_marca = 'MARCA'
    
    if verbose:
        print("=" * 70)
        print(f"🤖 PARTE 4: CATEGORIZACIÓN - {BANDERA} {NOMBRE_PAIS}")
        print("=" * 70)
        print(f"\n🏢 Player: {player_seleccionado}")
        print(f"📊 Total registros: {len(df_player):,}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PREPARAR DATOS
    # ═══════════════════════════════════════════════════════════════════
    
    todos_quarters = sorted(df_player[col_ola].dropna().unique())
    if verbose:
        print(f"\n📅 Quarters disponibles: {todos_quarters}")
    
    # Filtrar a los últimos 5 quarters
    ultimos_5q = todos_quarters[-5:] if len(todos_quarters) >= 5 else todos_quarters
    if verbose:
        print(f"📅 Últimos 5Q a categorizar: {ultimos_5q}")
    
    # Quarters seleccionados (de PARTE 3)
    quarters_seleccionados = [config['periodo_1'], config['periodo_2']]
    if resultados_parte3 and 'quarters_seleccionados' in resultados_parte3:
        quarters_seleccionados = resultados_parte3['quarters_seleccionados']
    if verbose:
        print(f"📅 Quarters seleccionados para waterfall: {quarters_seleccionados}")
    
    # Filtrar a últimos 5Q primero, luego neutros y detractores
    df_ultimos_5q = df_player[df_player[col_ola].isin(ultimos_5q)].copy()
    df_neutros_detractores = df_ultimos_5q[df_ultimos_5q[col_nps].isin([0, -1])].copy()
    
    if verbose:
        print(f"\n📊 Registros en últimos 5Q: {len(df_ultimos_5q):,}")
        print(f"\n🎯 Neutros e Detratores:")
        print(f"   • Neutros (NPS=0): {(df_neutros_detractores[col_nps]==0).sum():,}")
        print(f"   • Detratores (NPS=-1): {(df_neutros_detractores[col_nps]==-1).sum():,}")
    
    # ═══════════════════════════════════════════════════════════════════
    # DETECTAR MODO: Motivo declarado vs IA
    # ═══════════════════════════════════════════════════════════════════
    
    # Detectar columnas de motivo declarado
    col_motivo_detra = None
    col_motivo_neutro = None
    
    for col in df_neutros_detractores.columns:
        col_upper = col.upper()
        
        if col_upper == 'MOTIVO_DETRA':
            col_motivo_detra = col
        if col_upper == 'MOTIVO_NEUTRO':
            col_motivo_neutro = col
    
    TIENE_MOTIVOS = col_motivo_detra is not None or col_motivo_neutro is not None
    PLAYER_REQUIERE_IA = es_player_con_ia(player_seleccionado)
    USA_MOTIVO_DECLARADO = (not PLAYER_REQUIERE_IA) and TIENE_MOTIVOS
    
    if verbose:
        print(f"\n🎯 Player: '{player_seleccionado}' → {'REQUIERE IA' if PLAYER_REQUIERE_IA else 'Usa motivo declarado'}")
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORIZACIÓN
    # ═══════════════════════════════════════════════════════════════════
    
    if USA_MOTIVO_DECLARADO:
        # ═══════════════════════════════════════════════════════════════
        # MODO RÁPIDO: Usar motivo declarado
        # ═══════════════════════════════════════════════════════════════
        if verbose:
            print(f"\n⚡ MODO RÁPIDO: Usando motivo declarado")
            print(f"   📋 Col detractores: {col_motivo_detra}")
            print(f"   📋 Col neutros: {col_motivo_neutro}")
        
        def get_motivo_declarado(row):
            motivo = None
            if row[col_nps] == -1 and col_motivo_detra:
                motivo = row.get(col_motivo_detra, '')
            elif row[col_nps] == 0 and col_motivo_neutro:
                motivo = row.get(col_motivo_neutro, '')
            
            if pd.isna(motivo) or str(motivo).strip() in ['', '.', 'nan', ' ', 'None']:
                return SIN_OPINION
            return str(motivo).strip()
        
        df_neutros_detractores['MOTIVO_IA'] = df_neutros_detractores.apply(get_motivo_declarado, axis=1)
        df_categorizado = df_neutros_detractores.copy()
        
        if verbose:
            print(f"\n✅ Categorización completada: {len(df_categorizado):,} registros")
    
    else:
        # ═══════════════════════════════════════════════════════════════
        # MODO IA: BigQuery + fallback
        # ═══════════════════════════════════════════════════════════════
        if verbose:
            print(f"\n🤖 MODO IA: BigQuery + fallback")
        
        # Cargar categorías desde BigQuery
        bq_por_clave, bq_por_id, bq_por_hash, bq_disponible = cargar_categorias_bigquery(SITE_CODE, verbose)
        
        # ═══════════════════════════════════════════════════════════════
        # WARNING: Si BigQuery no está disponible para MP/Nubank
        # ═══════════════════════════════════════════════════════════════
        if not bq_disponible:
            print("\n" + "=" * 70)
            print("⚠️  ADVERTENCIA: BigQuery NO disponible")
            print("=" * 70)
            print(f"   Para {player_seleccionado} se requiere acceso a BigQuery")
            print(f"   para obtener las categorías de comentarios clasificados.")
            print(f"\n   Sin BigQuery, los comentarios se marcarán como '{OTROS}'")
            print(f"   y el análisis de motivos será LIMITADO.")
            print(f"\n   Para configurar BigQuery:")
            print(f"   1. pip install google-cloud-bigquery")
            print(f"   2. Configurar credenciales GCP (gcloud auth o service account)")
            print(f"   3. Tener acceso a: {BQ_TABLE}")
            print("=" * 70 + "\n")
        
        # Buscar columna de comentarios
        col_comentarios = None
        posibles = ['COMENTARIO', 'Comentarios', 'Comentario_P4', 'comment', 'comentario']
        
        for col in posibles:
            if col in df_neutros_detractores.columns:
                col_comentarios = col
                break
        
        if not col_comentarios:
            for col in df_neutros_detractores.columns:
                if 'comentario' in col.lower() or 'comment' in col.lower():
                    col_comentarios = col
                    break
        
        if verbose and col_comentarios:
            print(f"   💬 Columna comentarios: '{col_comentarios}'")
        
        # Buscar columna de ID
        col_id = None
        for c in ['ID', 'numericalId', 'id', 'ID_RESPUESTA']:
            if c in df_neutros_detractores.columns:
                col_id = c
                break
        
        if verbose:
            print(f"   🔑 Columna ID: '{col_id}'")
        
        # Separar con/sin comentarios
        if col_comentarios:
            comentarios_validos = (
                df_neutros_detractores[col_comentarios].notna() & 
                (df_neutros_detractores[col_comentarios].astype(str).str.strip() != '')
            )
        else:
            comentarios_validos = pd.Series([False] * len(df_neutros_detractores))
        
        df_con_comentarios = df_neutros_detractores[comentarios_validos].copy()
        df_sin_comentarios = df_neutros_detractores[~comentarios_validos].copy()
        
        if verbose:
            print(f"   📊 Con comentarios: {len(df_con_comentarios):,}")
            print(f"   📊 Sin comentarios: {len(df_sin_comentarios):,}")
            print(f"\n📊 Fuentes disponibles:")
            print(f"   • BigQuery: {'✅ ' + str(len(bq_por_clave)) + ' por clave compuesta' if bq_disponible else '❌'}")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 1: Lookup VECTORIZADO en BigQuery por CLAVE COMPUESTA
        # ═══════════════════════════════════════════════════════════════
        if verbose:
            print(f"\n⚡ Aplicando lookup vectorizado desde BigQuery...")
        
        desde_bigquery = 0
        
        if len(df_con_comentarios) > 0 and col_id:
            # Crear columna de ID como string
            df_con_comentarios['_id_str'] = df_con_comentarios[col_id].astype(str)
            
            # Crear clave compuesta: ID|OLA|MARCA
            if col_marca in df_con_comentarios.columns and col_ola in df_con_comentarios.columns:
                df_con_comentarios['_clave_compuesta'] = (
                    df_con_comentarios[col_id].astype(str) + '|' + 
                    df_con_comentarios[col_ola].astype(str) + '|' + 
                    df_con_comentarios[col_marca].astype(str)
                )
                # Lookup por clave compuesta
                df_con_comentarios['MOTIVO_IA'] = df_con_comentarios['_clave_compuesta'].map(bq_por_clave)
                encontrados_clave = df_con_comentarios['MOTIVO_IA'].notna().sum()
                if verbose:
                    print(f"   ✅ Encontrados por clave (ID|OLA|MARCA): {encontrados_clave:,}")
                
                # Fallback por ID solo
                if encontrados_clave < len(df_con_comentarios):
                    mask_sin_match = df_con_comentarios['MOTIVO_IA'].isna()
                    df_con_comentarios.loc[mask_sin_match, 'MOTIVO_IA'] = \
                        df_con_comentarios.loc[mask_sin_match, '_id_str'].map(bq_por_id)
                    encontrados_id = df_con_comentarios['MOTIVO_IA'].notna().sum() - encontrados_clave
                    if encontrados_id > 0 and verbose:
                        print(f"   ✅ Encontrados por ID solo (fallback): {encontrados_id:,}")
            else:
                df_con_comentarios['MOTIVO_IA'] = df_con_comentarios['_id_str'].map(bq_por_id)
            
            desde_bigquery = df_con_comentarios['MOTIVO_IA'].notna().sum()
            if verbose:
                print(f"   📊 Total BigQuery: {desde_bigquery:,} ({desde_bigquery/max(1,len(df_con_comentarios))*100:.1f}%)")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: Para los no encontrados, intentar por hash
        # ═══════════════════════════════════════════════════════════════
        df_sin_match = df_con_comentarios[df_con_comentarios['MOTIVO_IA'].isna()].copy() if 'MOTIVO_IA' in df_con_comentarios.columns else df_con_comentarios.copy()
        
        if len(df_sin_match) > 0 and bq_disponible and len(bq_por_hash) > 0 and col_comentarios:
            if verbose:
                print(f"   🔍 Buscando {len(df_sin_match):,} restantes por hash...")
            
            df_sin_match['_hash'] = df_sin_match[col_comentarios].apply(lambda x: hash_comentario(str(x)))
            df_sin_match['_motivo_hash'] = df_sin_match['_hash'].map(bq_por_hash)
            
            encontrados_hash = df_sin_match['_motivo_hash'].notna().sum()
            if encontrados_hash > 0:
                df_con_comentarios.loc[df_sin_match.index, 'MOTIVO_IA'] = df_sin_match['_motivo_hash']
                desde_bigquery += encontrados_hash
                if verbose:
                    print(f"   ✅ Encontrados por hash: {encontrados_hash:,}")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 2.5: Usar motivo declarado si no es "Otros" (fallback)
        # ═══════════════════════════════════════════════════════════════
        df_sin_match_2 = df_con_comentarios[df_con_comentarios['MOTIVO_IA'].isna()].copy() if 'MOTIVO_IA' in df_con_comentarios.columns else pd.DataFrame()
        desde_declarado = 0
        
        if len(df_sin_match_2) > 0 and (col_motivo_detra or col_motivo_neutro):
            if verbose:
                print(f"   📋 Buscando {len(df_sin_match_2):,} restantes en motivo declarado...")
            
            VALORES_OTROS = {'otros', 'otro', 'outra', 'outras', 'outras razões', 
                            'otra razón', 'otras razones', '', 'nan', 'none', '.', ' '}
            
            def get_motivo_declarado_valido(row):
                motivo = None
                if col_motivo_detra and row[col_nps] == -1:
                    motivo = row.get(col_motivo_detra, None)
                elif col_motivo_neutro and row[col_nps] == 0:
                    motivo = row.get(col_motivo_neutro, None)
                
                if pd.isna(motivo):
                    return None
                
                motivo_str = str(motivo).strip()
                motivo_lower = motivo_str.lower()
                
                if motivo_lower in VALORES_OTROS:
                    return None
                
                return motivo_str
            
            df_sin_match_2['_motivo_declarado'] = df_sin_match_2.apply(get_motivo_declarado_valido, axis=1)
            
            encontrados_declarado = df_sin_match_2['_motivo_declarado'].notna().sum()
            if encontrados_declarado > 0:
                mask_validos = df_sin_match_2['_motivo_declarado'].notna()
                df_con_comentarios.loc[df_sin_match_2[mask_validos].index, 'MOTIVO_IA'] = \
                    df_sin_match_2.loc[mask_validos, '_motivo_declarado']
                desde_declarado = encontrados_declarado
                if verbose:
                    print(f"   ✅ Encontrados por motivo declarado: {desde_declarado:,}")
        
        # ═══════════════════════════════════════════════════════════════
        # PASO 3: Los que faltan van como OTROS (requieren revisión manual/IA)
        # ═══════════════════════════════════════════════════════════════
        df_necesitan_ia = df_con_comentarios[df_con_comentarios['MOTIVO_IA'].isna()] if 'MOTIVO_IA' in df_con_comentarios.columns else pd.DataFrame()
        desde_ia = 0
        
        if len(df_necesitan_ia) > 0:
            if verbose:
                print(f"   ⚠️ {len(df_necesitan_ia):,} comentarios requieren categorización manual/IA")
                print(f"      (Se marcarán como '{OTROS}' por ahora)")
            
            df_con_comentarios.loc[df_necesitan_ia.index, 'MOTIVO_IA'] = OTROS
            desde_ia = len(df_necesitan_ia)
        
        # Limpiar columnas temporales
        cols_temp = ['_id_str', '_clave_compuesta', '_hash', '_motivo_hash', '_motivo_declarado']
        df_con_comentarios = df_con_comentarios.drop(columns=[c for c in cols_temp if c in df_con_comentarios.columns], errors='ignore')
        
        # Asignar SIN_OPINION a los sin comentarios
        df_sin_comentarios['MOTIVO_IA'] = SIN_OPINION
        
        # Combinar
        df_categorizado = pd.concat([df_con_comentarios, df_sin_comentarios], ignore_index=True)
        
        if verbose:
            total = len(df_con_comentarios)
            print(f"\n💰 RESUMEN:")
            if total > 0:
                print(f"   ✅ Desde BigQuery: {desde_bigquery:,} ({desde_bigquery/total*100:.1f}%)")
                if desde_declarado > 0:
                    print(f"   📋 Desde motivo declarado: {desde_declarado:,} ({desde_declarado/total*100:.1f}%)")
                if desde_ia > 0:
                    print(f"   ⚠️ Marcados como '{OTROS}': {desde_ia:,} ({desde_ia/total*100:.1f}%)")
            
            # Warning final si el análisis fue limitado
            if not bq_disponible and total > 0:
                pct_otros = (desde_ia / total * 100) if total > 0 else 0
                if pct_otros > 50:
                    print(f"\n" + "!" * 70)
                    print(f"   ⚠️ ANÁLISIS LIMITADO: {pct_otros:.0f}% de comentarios como '{OTROS}'")
                    print(f"   Para mejor análisis de {player_seleccionado}, configurar BigQuery")
                    print("!" * 70)
            
            print(f"\n✅ Categorización completada: {len(df_categorizado):,} registros")
    
    # ═══════════════════════════════════════════════════════════════════
    # RESUMEN Y EXPORTAR
    # ═══════════════════════════════════════════════════════════════════
    
    if verbose:
        print("\n" + "=" * 70)
        print("📊 DISTRIBUCIÓN DE CATEGORÍAS")
        print("=" * 70)
        
        for cat, count in df_categorizado['MOTIVO_IA'].value_counts().head(12).items():
            pct = count / len(df_categorizado) * 100
            print(f"   • {str(cat)[:50]}: {count:,} ({pct:.1f}%)")
        
        print("=" * 70)
    
    # Actualizar df_player con MOTIVO_IA
    col_id_merge = None
    for c in ['ID', 'numericalId', 'id', 'ID_RESPUESTA']:
        if c in df_player.columns and c in df_categorizado.columns:
            col_id_merge = c
            break
    
    df_player_actualizado = df_player.copy()
    
    if col_id_merge and len(df_categorizado) > 0:
        df_player_actualizado = df_player_actualizado.merge(
            df_categorizado[[col_id_merge, 'MOTIVO_IA']], 
            on=col_id_merge, 
            how='left',
            suffixes=('', '_nuevo')
        )
        if 'MOTIVO_IA_nuevo' in df_player_actualizado.columns:
            df_player_actualizado['MOTIVO_IA'] = df_player_actualizado['MOTIVO_IA_nuevo'].fillna(df_player_actualizado.get('MOTIVO_IA', ''))
            df_player_actualizado = df_player_actualizado.drop(columns=['MOTIVO_IA_nuevo'])
    
    # Exportar
    df_final_categorizado = df_categorizado.copy()
    
    if verbose:
        print(f"\n✅ Variables exportadas:")
        print(f"   • df_categorizado")
        print(f"   • df_final_categorizado")
        print(f"   • df_player (actualizado)")
        print(f"\n🚀 Listo para PARTE 5/6")
        print(f"{BANDERA} Vamos {NOMBRE_PAIS}!")
        print("=" * 70)
    
    return {
        'df_categorizado': df_categorizado,
        'df_final_categorizado': df_final_categorizado,
        'df_player': df_player_actualizado,
        'CATEGORIAS_CANON': CATEGORIAS_CANON,
        'USA_MOTIVO_DECLARADO': USA_MOTIVO_DECLARADO,
        'SIN_OPINION': SIN_OPINION,
        'OTROS': OTROS,
        'ultimos_5q': ultimos_5q,
        'quarters_seleccionados': quarters_seleccionados
    }

# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    from parte3_calculo_nps import calcular_nps
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 4: CATEGORIZACIÓN")
    print("=" * 70)
    
    try:
        # Cargar datos
        resultado_carga = cargar_datos(verbose=True)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        # Calcular NPS
        resultado_nps = calcular_nps(df_completo, config, generar_grafico=False, verbose=True)
        df_player = resultado_nps['df_player']
        
        # Categorizar
        resultado_cat = categorizar_comentarios(df_player, config, resultado_nps, verbose=True)
        
        print("\n📋 Variables exportadas:")
        for k, v in resultado_cat.items():
            if isinstance(v, pd.DataFrame):
                print(f"   {k}: DataFrame ({len(v)} filas)")
            elif isinstance(v, list):
                print(f"   {k}: {v}")
            else:
                print(f"   {k}: {v}")
        
        print("\n✅ Prueba PARTE 4 completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
