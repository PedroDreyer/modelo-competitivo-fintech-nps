# -*- coding: utf-8 -*-
"""
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
EJECUTAR MODELO NPS FINTECH - SCRIPT PRINCIPAL
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Este script orquesta todas las partes del modelo NPS Fintech.
Ejecuta secuencialmente las partes 1-12 y genera el HTML final.

Uso:
    python ejecutar_modelo.py
    
    O configurar en config.yaml y ejecutar.
"""

import sys
import os
import warnings
from pathlib import Path

# Suprimir todos los warnings (pandas, matplotlib, etc.)
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

# Agregar el directorio scripts al path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

import pandas as pd
from datetime import datetime

# Variable global para controlar verbose
_VERBOSE = True

def _print(*args, **kwargs):
    """Print condicional que respeta el modo verbose."""
    if _VERBOSE:
        print(*args, **kwargs)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# IMPORTAR MÃ“DULOS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from parte1_carga_datos import cargar_datos
from parte3_calculo_nps import calcular_nps
from parte4_categorizacion import categorizar_comentarios
from parte5_correccion_sin_opinion import corregir_sin_opinion
from parte6_waterfall import generar_waterfall
from parte7_causas_raiz import analizar_causas_raiz, exportar_comentarios_para_cursor, preparar_analisis_semantico
from parte7b_promotores import analizar_promotores, exportar_comentarios_promotores, preparar_analisis_semantico_promotores
from parte8_productos import analizar_productos
from parte9_principalidad import analizar_principalidad
from parte10_seguridad import analizar_seguridad
from parte11_deep_research import preparar_deep_research
from parte12_senior_analyst import generar_resumen_ejecutivo, consolidar_para_html
from analisis_automatico import (
    generar_subcausas_automatico,
    ejecutar_triangulacion,
    enriquecer_waterfall_para_acordeones,
    extraer_keywords_avanzado,
    obtener_noticias_para_reporte,
    triangular_motivos_con_noticias,
    buscar_noticias_por_drivers,
    cargar_noticias_cache,
    filtrar_noticias_por_periodo,
    clasificar_tipo_noticia,
    validar_coherencia_noticia_driver,
    generar_sugerencias_busqueda,
    mostrar_sugerencias_busqueda,
    agregar_noticia_a_cache,
    cargar_causas_raiz_semanticas
)


def ejecutar_modelo_completo(verbose=True, site=None, player=None, q1=None, q2=None):
    """
    Ejecuta el modelo NPS completo.
    
    Args:
        verbose: Si False, suprime todos los prints intermedios
        site: Código del site (MLB, MLA, MLM, MLC). Si None, usa config.yaml.
        player: Nombre del player a analizar. Si None, usa config.yaml.
        q1: Período anterior (ej: 25Q3). Si None, usa config.yaml.
        q2: Período actual (ej: 25Q4). Si None, usa config.yaml.
    
    Returns:
        dict: Resultados de todas las partes
    """
    global _VERBOSE
    _VERBOSE = verbose
    
    # Suprimir warnings de pandas/matplotlib en modo silencioso
    if not verbose:
        warnings.filterwarnings('ignore')
    
    resultados = {}
    
    _print("\n" + "â•" * 80)
    _print("🚀 EJECUTANDO MODELO NPS FINTECH COMPLETO")
    _print("â•" * 80)
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 1: CARGA DE DATOS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ“¥ PARTE 1: Cargando datos...")
    resultado_carga = cargar_datos(site=site, player=player, periodo_1=q1, periodo_2=q2, verbose=verbose)
    df_completo = resultado_carga['df_completo']  # Usuarios CON SALDO (para NPS, waterfall, etc.)
    df_todos = resultado_carga['df_competitivo']  # TODOS los usuarios (para principalidad, seguridad)
    config = resultado_carga['config']
    
    player = config['player']
    site = config['site']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    BANDERA = config['site_bandera']
    
    resultados['config'] = config
    resultados['df_completo'] = df_completo
    
    _print(f"   ✅ {len(df_completo):,} registros cargados")
    _print(f"   ðŸŽ¯ Player: {player}")
    _print(f"   ðŸ“… Períodos: {q_ant} vs {q_act}")
    
    # Cargar presentacion del quarter anterior (si existe)
    try:
        from scripts.parsear_presentacion import cargar_quarter_anterior
        pres_anterior = cargar_quarter_anterior(site, player, q_act)
        if pres_anterior:
            _print(f"   Presentacion anterior encontrada: {pres_anterior.get('quarter')}")
        resultados['presentacion_anterior'] = pres_anterior
    except Exception as e:
        _print(f"   No se pudo cargar presentacion anterior: {e}")
        resultados['presentacion_anterior'] = None
    
    # Función para normalizar texto (quitar tildes y caracteres especiales)
    def normalizar_texto(texto):
        if not isinstance(texto, str):
            return str(texto).lower()
        import unicodedata
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        # Mantener solo letras, digitos y espacios (fix para double-encoding Windows)
        texto = ''.join(c for c in texto if c.isalnum() or c.isspace())
        return texto.lower().strip()
    
    # Fix para double-encoding UTF-8 en Windows
    def fix_double_encoding(texto):
        try:
            encoded = texto.encode('latin-1')
            decoded = encoded.decode('utf-8')
            return decoded
        except (UnicodeEncodeError, UnicodeDecodeError):
            return texto
    
    # Intentar arreglar double-encoding del player
    player_fixed = fix_double_encoding(player)
    if player_fixed != player:
        _print(f"   Player encoding fix: {repr(player)} -> {repr(player_fixed)}")
        player = player_fixed
        config['player'] = player
    
    # Buscar player de forma flexible (ignorando tildes y case)
    player_norm = normalizar_texto(player)
    marcas_disponibles = df_completo['MARCA'].dropna().unique()
    
    # Buscar match exacto primero, luego normalizado
    player_encontrado = None
    for marca in marcas_disponibles:
        if marca == player:
            player_encontrado = marca
            break
        if normalizar_texto(marca) == player_norm:
            player_encontrado = marca
            break
    
    if player_encontrado and player_encontrado != player:
        _print(f"   â„¹ï¸ Player normalizado: '{player}' â†’ '{player_encontrado}'")
        player = player_encontrado
        config['player'] = player
    
    # Filtrar por player
    df_player = df_completo[df_completo['MARCA'] == player].copy()
    resultados['df_player'] = df_player
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 3: CÃLCULO NPS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ“Š PARTE 3: Calculando NPS...")
    resultado_nps = calcular_nps(df_completo, config, verbose=verbose)
    resultados['nps'] = resultado_nps
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 4: CATEGORIZACIÃ“N
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ·ï¸ PARTE 4: Categorizando comentarios...")
    resultado_cat = categorizar_comentarios(df_player, config, verbose=verbose)
    resultados['categorizacion'] = resultado_cat
    df_categorizado = resultado_cat['df_categorizado']
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 5: CORRECCIÃ“N SIN OPINIÃ“N
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ”§ PARTE 5: Corrigiendo 'Sin opinión'...")
    resultado_corr = corregir_sin_opinion(resultado_cat, config, verbose=verbose)
    resultados['correccion'] = resultado_corr
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 6: WATERFALL
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ“‰ PARTE 6: Calculando waterfall...")
    resultado_wf = generar_waterfall(resultado_corr, df_player, config, verbose=verbose)
    resultados['waterfall'] = resultado_wf
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 7: CAUSAS RAÍZ
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ” PARTE 7: Analizando causas raíz...")
    resultado_cr = analizar_causas_raiz(resultado_wf, resultado_corr, df_player, config, verbose=verbose)
    resultados['causas_raiz'] = resultado_cr
    
    # Exportar comentarios para análisis automático
    _print("   ðŸ“ Extrayendo comentarios para análisis automático...")
    comentarios_cursor = exportar_comentarios_para_cursor(
        resultado_wf, resultado_corr, df_player, config, 
        max_comentarios=30, verbose=False
    )
    resultados['comentarios_por_motivo'] = comentarios_cursor
    
    # Analisis semantico de causas raiz (genera prompt para LLM)
    _print("   \U0001f9e0 Preparando analisis semantico de causas raiz...")
    resultado_semantico = preparar_analisis_semantico(
        resultado_wf, resultado_corr, df_player, config,
        max_comentarios_por_motivo=100, verbose=False
    )
    resultados['analisis_semantico'] = resultado_semantico
    if resultado_semantico.get('prompt_path'):
        _print(f"   \u2705 Prompt semantico guardado en: {resultado_semantico['prompt_path']}")
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 7B: PROMOTORES
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸŒŸ PARTE 7B: Analizando promotores...")
    resultado_prom = analizar_promotores(df_player, config, verbose=verbose)
    resultados['promotores'] = resultado_prom

    # Analisis semantico de promotores (genera prompt para LLM)
    _print("   \U0001f9e0 Preparando analisis semantico de promotores...")
    resultado_semantico_prom = preparar_analisis_semantico_promotores(
        resultado_prom, df_player, config,
        max_comentarios_por_motivo=100, verbose=False
    )
    resultados['analisis_semantico_promotores'] = resultado_semantico_prom
    if resultado_semantico_prom.get('prompt_path'):
        _print(f"   \u2705 Prompt semantico promotores guardado en: {resultado_semantico_prom['prompt_path']}")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 8: PRODUCTOS
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ“¦ PARTE 8: Analizando productos...")
    resultado_prod = analizar_productos(df_completo, df_player, config, verbose=verbose)
    if 'error' in resultado_prod:
        _print(f"   ⚠️ PARTE 8 WARNING: {resultado_prod['error']}")
    resultados['productos'] = resultado_prod
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 9: PRINCIPALIDAD (movido antes de noticias)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ† PARTE 9: Analizando principalidad...")
    # Principalidad usa TODOS los usuarios, no solo los que tienen saldo
    resultado_princ = analizar_principalidad(df_todos, config, verbose=verbose)
    if 'error' in resultado_princ:
        _print(f"   ⚠️ PARTE 9 WARNING: {resultado_princ['error']}")
    resultados['principalidad'] = resultado_princ
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 10: SEGURIDAD (movido antes de noticias)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ”’ PARTE 10: Analizando seguridad...")
    resultado_seg = analizar_seguridad(df_completo, config, verbose=verbose)
    if 'error' in resultado_seg:
        _print(f"   ⚠️ PARTE 10 WARNING: {resultado_seg['error']}")
    resultados['seguridad'] = resultado_seg
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 8B: CARGA INTELIGENTE DE NOTICIAS Y TRIANGULACIÃ“N
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    # Obtener datos para triangulación
    productos_clave = resultado_prod.get('productos_clave', [])
    
    # Obtener causas del waterfall
    causas_wf = []
    wf_df = resultado_wf.get('waterfall_data_comparativo', None)
    if wf_df is not None and hasattr(wf_df, 'iterrows'):
        for _, row in wf_df.iterrows():
            causas_wf.append({
                'motivo': row.get('Motivo', ''),
                'delta': row.get('Delta', 0),
                'pct_q1': row.get('Impacto_Anterior', 0),
                'pct_q2': row.get('Impacto_Actual', 0),
            })
    
    # Obtener deltas de métricas para búsqueda de noticias
    delta_seg = resultado_seg.get('player_seguridad', {}).get('delta', 0)
    delta_princ = resultado_princ.get('player_principalidad', {}).get('delta', 0)
    
    # =========================================================================
    # CHECKPOINT CRITICO: CAUSAS RAIZ SEMANTICAS (ANTES de noticias)
    # =========================================================================
    # Las causas raiz semanticas DEBEN existir ANTES de buscar noticias.
    # Si no existen, el modelo se DETIENE para que el agente las genere.
    # Esto garantiza: noticias enriquecidas + triangulacion precisa + HTML completo.
    
    _print("\n\U0001f9e0 CHECKPOINT: Verificando causas raiz semanticas...")
    
    causas_semanticas = cargar_causas_raiz_semanticas(player, q_act)
    if causas_semanticas:
        _print(f"   \u2705 Causas raiz semanticas OK: {len(causas_semanticas)} motivos")
        resultados['causas_semanticas'] = causas_semanticas
    else:
        # NO existe JSON semantico - DETENER ANTES de buscar noticias
        prompt_path = resultado_semantico.get('prompt_path', '')
        _print(f"   \u26a0\ufe0f  PAUSA: Se necesita analisis semantico de causas raiz")
        if prompt_path:
            _print(f"   Prompt: {prompt_path}")
        _print(f"   JSON destino: data/causas_raiz_semantico_{player}_{q_act}.json")
        resultados['necesita_causas_raiz'] = True
        resultados['prompt_causas_raiz'] = prompt_path
        resultados['json_destino_causas_raiz'] = f'data/causas_raiz_semantico_{player}_{q_act}.json'
        _print(f"   Modelo detenido. Re-ejecutar despues de generar causas raiz.")
        return resultados
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # CARGA INTELIGENTE DE NOTICIAS (basada en drivers del análisis)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ“° Cargando noticias para triangulación...")
    
    # Las noticias las busca CURSOR (el agente) con WebSearch y las guarda en noticias_cache.json
    # El modelo solo lee el cache. NO hace web scraping.
    noticias_cache = cargar_noticias_cache(site, player)
    _print(f"   Cache: {len(noticias_cache)} noticias cargadas")
    
    # 3. FILTRAR noticias: solo las de los quarters analizados (q_ant y q_act)
    noticias_para_triangular = filtrar_noticias_por_periodo(noticias_cache, q_ant, q_act, verbose=_VERBOSE)
    
    # Resumen de noticias filtradas
    if noticias_para_triangular:
        _print(f"   OK: {len(noticias_para_triangular)} noticias del periodo {q_ant}-{q_act}")
    else:
        _print(f"   AVISO: SIN NOTICIAS del periodo {q_ant}-{q_act} - agregar noticias con fechas correctas")
    
    _print("\nðŸ”— PARTE 8B: Ejecutando triangulación y deep dive automático...")
    
    # Ejecutar triangulación Producto â†” Queja â†” Noticia
    triangulaciones = ejecutar_triangulacion(productos_clave, causas_wf, noticias_para_triangular)
    resultados['triangulaciones'] = triangulaciones
    resultados['noticias'] = noticias_para_triangular
    
    # Triangular MOTIVOS del waterfall directamente con NOTICIAS
    triangulacion_motivos = triangular_motivos_con_noticias(causas_wf, noticias_para_triangular)
    resultados['triangulacion_motivos'] = triangulacion_motivos
    
    # Contar triangulaciones
    tri_con_noticias = len([t for t in triangulaciones if t.get('noticia')])
    tri_motivos_noticias = len(triangulacion_motivos)
    _print(f"   ✅ {len(triangulaciones)} triangulaciones Producto â†” Queja")
    if tri_con_noticias > 0:
        _print(f"   ðŸ”— {tri_con_noticias} con noticias relacionadas")
    if tri_motivos_noticias > 0:
        _print(f"   ðŸ“° {tri_motivos_noticias} motivos triangulados con noticias")
    
    # Enriquecer waterfall con subcausas y keywords para acordeones
    comentarios_por_motivo = resultados.get('comentarios_por_motivo', {})
    causas_enriquecidas = enriquecer_waterfall_para_acordeones(
        causas_wf, 
        comentarios_por_motivo,
        triangulaciones
    )
    resultados['causas_waterfall'] = causas_enriquecidas
    
    # Contar subcausas generadas
    total_subcausas = sum(len(c.get('subcausas', [])) for c in causas_enriquecidas)
    _print(f"   ✅ {total_subcausas} subcausas generadas automáticamente")
    _print(f"   ✅ Keywords y comentarios extraídos para acordeones")
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 11: DEEP RESEARCH (INSTRUCCIONES)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ”Ž PARTE 11: Preparando Deep Research...")
    resultado_dr = preparar_deep_research(resultado_cr, resultado_prod, config, verbose=False)
    resultados['deep_research'] = resultado_dr
    _print("   ✅ Instrucciones de Deep Research generadas")
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 12: RESUMEN EJECUTIVO
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸŽ¯ PARTE 12: Generando resumen ejecutivo...")
    resumen = generar_resumen_ejecutivo(resultados, config, verbose=False)
    resultados['resumen_ejecutivo'] = resumen
    _print("   ✅ Resumen ejecutivo generado")
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # RESUMEN FINAL
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\n" + "â•" * 80)
    _print(f"✅ MODELO COMPLETADO - {BANDERA} {player}")
    _print("â•" * 80)
    
    metricas = resumen['metricas']
    _print(f"\nðŸ“Š MÃ‰TRICAS PRINCIPALES:")
    _print(f"   NPS: {metricas.get('nps_q1', 0):.1f} â†’ {metricas.get('nps_q2', 0):.1f} (Î” {metricas.get('delta_nps', 0):+.1f}pp)")
    
    if 'princ_q1' in metricas:
        _print(f"   Principalidad: {metricas.get('princ_q1', 0):.1f}% â†’ {metricas.get('princ_q2', 0):.1f}%")
    
    if 'seg_q1' in metricas:
        _print(f"   Seguridad: {metricas.get('seg_q1', 0):.1f}% â†’ {metricas.get('seg_q2', 0):.1f}%")
    
    if resumen['drivers_positivos']:
        _print(f"\nðŸŸ¢ DRIVERS POSITIVOS:")
        for d in resumen['drivers_positivos'][:3]:
            _print(f"   â€¢ {d['descripcion']}")
    
    if resumen['drivers_negativos']:
        _print(f"\nðŸ”´ DRIVERS NEGATIVOS:")
        for d in resumen['drivers_negativos'][:3]:
            _print(f"   â€¢ {d['descripcion']}")
    
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # PARTE 13: FLUJO SEMI-ASISTIDO - SUGERENCIAS DE BÃšSQUEDA
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    _print("\nðŸ“‹ PARTE 13: Generando sugerencias de búsqueda...")
    
    # Obtener métricas de seguridad y principalidad para sugerencias
    delta_seg = resultados.get('seguridad', {}).get('player_seguridad', {}).get('delta', 0)
    delta_princ = resultados.get('principalidad', {}).get('player_principalidad', {}).get('delta', 0)
    
    sugerencias = generar_sugerencias_busqueda(
        player=config['player'],
        site=config['site'],
        drivers_waterfall=causas_wf,
        delta_seguridad=delta_seg,
        delta_principalidad=delta_princ,
        noticias_actuales=noticias_para_triangular,
        q_ant=config['periodo_1'],
        q_act=config['periodo_2']
    )
    
    resultados['sugerencias_busqueda'] = sugerencias
    

    # ══════════════════════════════════════════════════════════════════════
    # CHECKPOINT CRÍTICO: BÚSQUEDA DE NOTICIAS (igual que causas raíz)
    # ══════════════════════════════════════════════════════════════════════
    # Si hay drivers significativos SIN noticias, el modelo se DETIENE
    # para que el agente ejecute búsquedas con WebSearch automáticamente.
    # Esto garantiza triangulación completa antes de generar el HTML.

    if sugerencias['gaps_sin_noticia']:
        gaps_count = len(sugerencias['gaps_sin_noticia'])
        _print(mostrar_sugerencias_busqueda(sugerencias))

        _print("\n" + "═" * 80)
        _print("⚠️  CHECKPOINT: BÚSQUEDA DE NOTICIAS REQUERIDA")
        _print("═" * 80)
        _print(f"")
        _print(f"   El modelo necesita noticias para {gaps_count} drivers significativos.")
        _print(f"   Esto asegura triangulación completa en el reporte.")
        _print(f"")
        _print(f"   DRIVERS SIN NOTICIAS:")
        for gap in sugerencias['gaps_sin_noticia']:
            _print(f"   • {gap['motivo']} ({gap['delta']:+.1f}pp)")
        _print(f"")
        _print(f"   INSTRUCCIONES PARA EL AGENTE:")
        _print(f"   1. Ejecutar búsquedas con WebSearch para cada driver")
        _print(f"   2. Las queries están en resultados['sugerencias_busqueda']")
        _print(f"   3. Guardar noticias en: data/noticias_cursor_batch.json")
        _print(f"   4. Inyectar al cache: python scripts/agregar_noticias_cursor.py")
        _print(f"   5. Re-ejecutar: python correr_modelo.py (mismos args)")
        _print(f"")
        _print("═" * 80)

        # Guardar sugerencias para que el agente las use
        resultados['necesita_noticias'] = True
        resultados['queries_busqueda'] = sugerencias.get('busquedas_sugeridas', [])
        resultados['gaps_sin_noticia'] = sugerencias['gaps_sin_noticia']

        # Salir con código 43 = "necesita noticias"
        return resultados
    else:
        _print("   ✅ Todos los drivers principales tienen noticias asociadas")

    return resultados


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# EJECUCIÃ“N PRINCIPAL
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar Modelo NPS Fintech')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser.add_argument('--quiet', '-q', action='store_true', help='Modo silencioso')
    
    args = parser.parse_args()
    
    verbose = not args.quiet
    
    try:
        resultados = ejecutar_modelo_completo(verbose=verbose)
        _print("\n✅ Modelo ejecutado exitosamente")
        
    except Exception as e:
        _print(f"\nâŒ Error al ejecutar el modelo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

