# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 10: ANÁLISIS DE SEGURIDAD
═══════════════════════════════════════════════════════════════════════════════

Analiza la percepción de seguridad de las marcas y motivos de inseguridad.
Replica EXACTAMENTE el código del notebook original.

Uso:
    from scripts.parte10_seguridad import analizar_seguridad
    resultado = analizar_seguridad(df_completo, config)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import io
import base64

# ==============================================================================
# FUNCIÓN PARA CORREGIR ENCODING
# ==============================================================================

def fix_encoding_text(text):
    """Corrige caracteres con encoding corrupto (común en CSVs latinos)."""
    if not isinstance(text, str):
        return str(text) if text is not None else ''
    
    replacements = {
        'Ã§': 'ç', 'Ã£': 'ã', 'Ãµ': 'õ', 'Ã¡': 'á', 'Ã©': 'é',
        'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú', 'Ãª': 'ê', 'Ã\xa0': 'à',
        'Ã¢': 'â', 'Ã´': 'ô', 'Ã±': 'ñ', 'Ã¼': 'ü',
        'Ã‰': 'É', 'Ã"': 'Ó', 'Ã\x81': 'Á', 'Ãš': 'Ú',
        'ÃŠ': 'Ê', 'Ã\x91': 'Ñ', 'Ãœ': 'Ü',
        '\ufeff': '',
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result

# ==============================================================================
# CONFIGURACIÓN MULTISITE
# ==============================================================================

TOP_PLAYERS_CONFIG = {
    'MLB': ['Nubank', 'Banco Inter', 'C6 Bank', 'PicPay', 'Next', 'Mercado Pago'],
    'MLA': ['Mercado Pago', 'Ualá', 'Naranja X', 'Brubank', 'MODO', 'Personal Pay'],
    'MLM': ['Mercado Pago', 'Nubank', 'BBVA', 'Santander', 'Hey Banco', 'Stori'],
    'MLC': ['Mercado Pago', 'Tenpo', 'Mach', 'Banco Estado', 'BCI']
}

MOTIVOS_INSEGURIDAD = {
    'MLB': {  # Portugués - Brasil
        'no_confia': ('não confi', 'nao confi', 'nã£o confi'),
        'no_conoce': ('não conheç', 'nao conhec', 'nã£o conheã§'),
        'insuficiente': ('insuficiente',),
        'fraude': ('golpe', 'fraude', 'roub', 'hack'),
        'noticias': ('conhecid', 'notícia', 'redes'),
        'labels': {
            'no_confia': 'Não confia nas Fintechs',
            'no_conoce': 'Não conhece as medidas de segurança',
            'insuficiente': 'As medidas de segurança são insuficientes',
            'fraude': 'Fraudes / Roubos / Ataques',
            'noticias': 'Conhecidos / notícias',
            'sin_motivo': 'Sem motivo especificado',
            'otro': 'Outro motivo'
        }
    },
    'MLA': {  # Español - Argentina
        'no_confia': ('no confí', 'no confi', 'desconfi', 'digital'),
        'no_conoce': ('no conoz', 'no conoç', 'desconoz', 'no conozco las medidas'),
        'insuficiente': ('insuficiente', 'me parecen insuficientes'),
        'fraude': ('fraude', 'robo', 'hack', 'estafa', 'invadida', 'robaron'),
        'noticias': ('conocid', 'noticia', 'redes', 'desconfio'),
        'labels': {
            'no_confia': 'No confía en las Fintechs',
            'no_conoce': 'No conoce las medidas de seguridad',
            'insuficiente': 'Las medidas de seguridad son insuficientes',
            'fraude': 'Estafas / Robos / Hackeos',
            'noticias': 'Conocidos / noticias',
            'sin_motivo': 'Sin motivo especificado',
            'otro': 'Otro motivo'
        }
    },
    'MLM': {  # Español - México (ajustado a textos reales del CSV)
        # IMPORTANTE: El orden de evaluación en simplificar_motivo() es:
        # no_confia -> no_conoce -> insuficiente -> fraude -> noticias
        # Por eso 'noticias' tiene patrones MUY específicos que no se solapan
        'no_confia': ('no confio mucho en bancos digitales', 'bancos digitales'),  # SIN 'desconfi' para no capturar noticias
        'no_conoce': ('no conozco las medidas de seguridad',),  # Específico
        'insuficiente': ('me parecen insuficientes',),  # Específico
        'fraude': ('estafa', 'perdi dinero', 'robaron la tarjeta', 'usaron mi dinero', 'hackeo', 'cuenta fue invadida'),
        'noticias': ('por conocidos que tuvieron', 'vi una noticia', 'inconvenientes de seguridad', 'desconfio de'),  # Sin tilde
        'labels': {
            'no_confia': 'No confía en Fintechs',
            'no_conoce': 'No conoce las medidas de seguridad',
            'insuficiente': 'Medidas de seguridad insuficientes',
            'fraude': 'Fraudes / Robos / Hackeos',
            'noticias': 'Conocidos / noticias',
            'sin_motivo': 'Sin motivo especificado',
            'otro': 'Otro motivo'
        }
    },
    'DEFAULT': {  # Español genérico (MLC y otros)
        'no_confia': ('no confí', 'no confi', 'desconfi', 'digital', 'virtual'),
        'no_conoce': ('no conoz', 'no conoç', 'desconoz', 'no sé'),
        'insuficiente': ('insuficiente', 'falta', 'pocas medidas'),
        'fraude': ('fraude', 'robo', 'hack', 'estafa', 'clon'),
        'noticias': ('conocid', 'noticia', 'redes', 'escuch'),
        'labels': {
            'no_confia': 'No confía en Fintechs',
            'no_conoce': 'No conoce las medidas de seguridad',
            'insuficiente': 'Medidas de seguridad insuficientes',
            'fraude': 'Fraudes / Robos / Hackeos',
            'noticias': 'Conocidos / noticias',
            'sin_motivo': 'Sin motivo especificado',
            'otro': 'Otro motivo'
        }
    }
}

# Colores fijos por categoría de motivo (consistentes cross-site)
COLORES_MOTIVOS_INSEGURIDAD = {
    'No conoce las medidas de seguridad': '#D4A84B',      # Amarillo/Dorado
    'Não conhece as medidas de segurança': '#D4A84B',     # Portugués
    'Medidas de seguridad insuficientes': '#1E3A5F',      # Azul oscuro
    'Las medidas de seguridad son insuficientes': '#1E3A5F',
    'As medidas de segurança são insuficientes': '#1E3A5F',
    'No confía en Fintechs': '#8B8B8B',                   # Gris
    'No confía en las Fintechs': '#8B8B8B',
    'Não confia nas Fintechs': '#8B8B8B',
    'Fraudes / Robos / Hackeos': '#C41E7E',               # Magenta/Rosa fuerte
    'Estafas / Robos / Hackeos': '#C41E7E',
    'Fraudes / Roubos / Ataques': '#C41E7E',
    'Conocidos / noticias': '#E8D89A',                    # Amarillo claro/crema
    'Conhecidos / notícias': '#E8D89A',
    'Otro motivo': '#D3D3D3',                             # Gris claro
    'Outro motivo': '#D3D3D3',
    'Sin motivo especificado': '#F5F5F5',                 # Gris muy claro
    'Sem motivo especificado': '#F5F5F5',
}

COLUMNAS_MOTIVO_INSEG_DIRECTO = {
    'MLB': [
        'MOTIVO_INSEGURIDAD',
        'Por que você não sente segurança ao usar',
    ],
    'MLA': [
        'MOTIVO_INSEGURIDAD',
        '¿Por qué no te sientes seguro',
    ],
    'MLM': [
        'MOTIVO_INSEGURIDAD',
        '¿Por qué no te sientes seguro',
    ],
    'MLC': [
        'MOTIVO_INSEGURIDAD',
        '¿Por qué no te sientes seguro',
    ],
}


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def analizar_seguridad(df_completo, config, verbose=True):
    """
    Analiza la percepción de seguridad.
    
    Args:
        df_completo: DataFrame completo con VALORACION_SEGURIDAD
        config: Diccionario de configuración
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con seguridad_por_ola, motivos_inseguridad
    """
    
    site = config['site']
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    col_periodo = 'OLA'
    col_marca = 'MARCA'
    
    if verbose:
        print("=" * 70)
        print(f"{BANDERA} PARTE 10: ANÁLISIS DE SEGURIDAD - {NOMBRE_PAIS}")
        print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DETECTAR COLUMNA DE VALORACIÓN
    # ═══════════════════════════════════════════════════════════════════════════
    
    col_valoracion = None
    for col in df_completo.columns:
        col_lower = col.lower()
        if ('segura' in col_lower or 'seguridad' in col_lower) and ('1' in col_lower or '5' in col_lower):
            col_valoracion = col
            break
    
    if not col_valoracion:
        for col in df_completo.columns:
            col_lower = col.lower()
            if ('segura' in col_lower or 'seguridad' in col_lower) and 'por que' not in col_lower and 'porque' not in col_lower:
                col_valoracion = col
                break
    
    if not col_valoracion:
        if 'VALORACION_SEGURIDAD' in df_completo.columns:
            col_valoracion = 'VALORACION_SEGURIDAD'
    
    if not col_valoracion:
        if verbose:
            print("❌ Columna de seguridad no encontrada")
            cols_segur = [c for c in df_completo.columns if 'segur' in c.lower()]
            print(f"   Columnas con 'segur': {cols_segur[:5]}")
        return {
            'seguridad_por_ola': pd.DataFrame(),
            'motivos_inseguridad': pd.DataFrame(),
            'error': 'No se encontró columna de valoración de seguridad'
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DETECTAR COLUMNA DE MOTIVOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    col_motivo = None
    columnas_directas = COLUMNAS_MOTIVO_INSEG_DIRECTO.get(site, [])
    
    for col_directa in columnas_directas:
        if col_directa in df_completo.columns:
            col_motivo = col_directa
            if verbose:
                print(f"✅ Columna motivos inseguridad: {col_motivo}")
            break
    
    if not col_motivo:
        patrones_motivo = [
            lambda c: ('por qu' in c or 'porque' in c) and ('segura' in c or 'seguridad' in c),
            lambda c: 'no es segura' in c or 'não sente segurança' in c,
            lambda c: 'insegura' in c and ('por' in c or 'motivo' in c),
        ]
        
        for patron in patrones_motivo:
            for col in df_completo.columns:
                col_lower = col.lower()
                if patron(col_lower):
                    col_motivo = col
                    break
            if col_motivo:
                break
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURAR ANÁLISIS
    # ═══════════════════════════════════════════════════════════════════════════
    
    TOP_PLAYERS = TOP_PLAYERS_CONFIG.get(site, TOP_PLAYERS_CONFIG['MLA'])
    
    if player not in TOP_PLAYERS:
        TOP_PLAYERS = [player] + TOP_PLAYERS[:5]
    
    # Quarters dinámicos
    olas_disponibles = sorted(df_completo[col_periodo].unique())
    
    if q_act in olas_disponibles:
        idx_final = olas_disponibles.index(q_act)
        ultimos_5q = olas_disponibles[max(0, idx_final-4):idx_final+1]
    else:
        ultimos_5q = olas_disponibles[-5:] if len(olas_disponibles) >= 5 else olas_disponibles
    
    if verbose:
        print(f"✅ Valoración: {col_valoracion}")
        if col_motivo:
            print(f"✅ Motivos: {col_motivo}")
        print(f"📅 Trimestres: {ultimos_5q[0]} → {ultimos_5q[-1]}")
    
    # Filtrar datos
    df = df_completo[
        (df_completo[col_marca].isin(TOP_PLAYERS)) &
        (df_completo[col_periodo].isin(ultimos_5q))
    ].copy()
    
    if verbose:
        print(f"📊 Registros: {len(df):,}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONVERTIR VALORACIONES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def to_num(val):
        if pd.isna(val):
            return np.nan
        s = str(val)
        for i in ['5', '4', '3', '2', '1']:
            if i in s:
                return int(i)
        return np.nan
    
    df['VAL'] = df[col_valoracion].apply(to_num)
    df = df[df['VAL'].notna()]
    
    if verbose:
        print(f"✅ Válidos: {len(df):,}")
    
    if len(df) == 0:
        return {
            'seguridad_por_ola': pd.DataFrame(),
            'motivos_inseguridad': pd.DataFrame(),
            'error': 'No hay datos válidos de seguridad'
        }
    
    # Seguro = valoración 4 o 5
    df['SEG'] = (df['VAL'] >= 4).astype(int)
    
    result = df.groupby([col_periodo, col_marca]).agg(
        Total=('VAL', 'count'),
        Seguros=('SEG', 'sum')
    ).reset_index()
    
    result['% Seguridad Marca'] = (result['Seguros'] / result['Total'] * 100).round(1)
    result['Inseguros'] = result['Total'] - result['Seguros']
    result['% Inseguridad Marca'] = (result['Inseguros'] / result['Total'] * 100).round(1)
    
    base_total_ola = result.groupby(col_periodo)['Total'].transform('sum')
    result['Base_Total'] = base_total_ola
    result['% Seguridad'] = (result['Seguros'] / base_total_ola * 100).round(2)
    result['% Inseguridad'] = (result['Inseguros'] / base_total_ola * 100).round(2)
    
    result = result.rename(columns={col_marca: 'MARCA'})
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MOTIVOS DE INSEGURIDAD
    # ═══════════════════════════════════════════════════════════════════════════
    
    motivos_inseguridad = pd.DataFrame()
    n_inseguros = len(df[df['VAL'] <= 3])
    
    if verbose:
        print(f"\n📊 Análisis de motivos de inseguridad:")
        print(f"   • Columna motivos: {'✅ ' + col_motivo if col_motivo else '❌ No encontrada'}")
        print(f"   • Usuarios inseguros (1-3): {n_inseguros:,}")
    
    if col_motivo and n_inseguros > 0:
        df_inseg = df[df['VAL'] <= 3].copy()
        
        motivos_config = MOTIVOS_INSEGURIDAD.get(site, MOTIVOS_INSEGURIDAD['DEFAULT'])
        labels = motivos_config['labels']
        
        def simplificar_motivo(m):
            if pd.isna(m) or str(m).strip() in ['', '.', ' ']:
                return labels['sin_motivo']
            m = str(m).lower()
            if any(k in m for k in motivos_config['no_confia']):
                return labels['no_confia']
            if any(k in m for k in motivos_config['no_conoce']):
                return labels['no_conoce']
            if any(k in m for k in motivos_config['insuficiente']):
                return labels['insuficiente']
            if any(k in m for k in motivos_config['fraude']):
                return labels['fraude']
            if any(k in m for k in motivos_config['noticias']):
                return labels['noticias']
            return labels['otro']
        
        df_inseg['MOTIVO_INSEG'] = df_inseg[col_motivo].apply(simplificar_motivo)
        
        mot_count = df_inseg.groupby([col_periodo, col_marca, 'MOTIVO_INSEG']).size().reset_index(name='Cantidad')
        tot_inseg = df_inseg.groupby([col_periodo, col_marca]).size().reset_index(name='Total_Inseguros')
        
        motivos_inseguridad = mot_count.merge(tot_inseg, on=[col_periodo, col_marca])
        motivos_inseguridad['% Motivo'] = (motivos_inseguridad['Cantidad'] / motivos_inseguridad['Total_Inseguros'] * 100).round(1)
        
        motivos_inseguridad = motivos_inseguridad.merge(
            result[[col_periodo, 'MARCA', '% Inseguridad Marca', 'Total']].rename(columns={'MARCA': col_marca}),
            on=[col_periodo, col_marca], how='left'
        )
        motivos_inseguridad['% Ponderado Base'] = (
            motivos_inseguridad['% Motivo'] * motivos_inseguridad['% Inseguridad Marca'] / 100
        ).round(2)
        
        if verbose:
            print(f"   ✅ Motivos procesados: {len(motivos_inseguridad)} registros")
            print(f"   📋 Categorías encontradas: {motivos_inseguridad['MOTIVO_INSEG'].nunique()}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANÁLISIS DEL PLAYER
    # ═══════════════════════════════════════════════════════════════════════════
    
    player_q1 = result[(result['MARCA'] == player) & (result[col_periodo] == q_ant)]
    player_q2 = result[(result['MARCA'] == player) & (result[col_periodo] == q_act)]
    
    seg_q1 = player_q1['% Seguridad Marca'].values[0] if len(player_q1) > 0 else 0
    seg_q2 = player_q2['% Seguridad Marca'].values[0] if len(player_q2) > 0 else 0
    delta_seg = seg_q2 - seg_q1
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🔒 SEGURIDAD {player}")
        print("=" * 70)
        print(f"   {q_ant}: {seg_q1:.1f}%")
        print(f"   {q_act}: {seg_q2:.1f}%")
        print(f"   Delta: {delta_seg:+.1f}pp")
        
        # Ranking de seguridad
        top_seg = result[result[col_periodo] == q_act].sort_values('% Seguridad Marca', ascending=False).head(5)
        print(f"\n🏆 RANKING SEGURIDAD ({q_act}):")
        print("=" * 70)
        for i, (_, row) in enumerate(top_seg.iterrows(), 1):
            emoji = "🔒" if i == 1 else f"{i}."
            print(f"   {emoji} {row['MARCA']:<25} {row['% Seguridad Marca']:.1f}%")
        
        # Motivos del player
        if not motivos_inseguridad.empty:
            motivos_player = motivos_inseguridad[
                (motivos_inseguridad[col_marca] == player) & 
                (motivos_inseguridad[col_periodo] == q_act)
            ].sort_values('% Motivo', ascending=False).head(5)
            
            if not motivos_player.empty:
                print(f"\n⚠️ MOTIVOS DE INSEGURIDAD - {player} ({q_act}):")
                print("─" * 70)
                for _, row in motivos_player.iterrows():
                    print(f"   • {row['MOTIVO_INSEG']}: {row['% Motivo']:.1f}%")
        
        print(f"\n{'='*100}")
        print(f"✅ PARTE 10 OK - Análisis de seguridad completado")
        print("=" * 100)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GRÁFICOS (EXACTO AL NOTEBOOK ORIGINAL)
    # ═══════════════════════════════════════════════════════════════════════════
    
    grafico_seguridad_base64 = None
    grafico_motivos_inseg_base64 = None
    
    # Datos de evolución del player
    datos_evol = result[result['MARCA'] == player].sort_values(col_periodo)
    
    # GRÁFICO 1: EVOLUCIÓN DE SEGURIDAD
    if len(datos_evol) > 0:
        fig_evol, ax_evol = plt.subplots(figsize=(10, 5), facecolor='white')
        ax_evol.set_facecolor('white')
        
        ax_evol.plot(datos_evol[col_periodo], datos_evol['% Seguridad Marca'], 
                    marker='o', linewidth=3, markersize=10, color='#009739')
        
        for _, r in datos_evol.iterrows():
            ax_evol.annotate(f"{r['% Seguridad Marca']:.1f}%", 
                            (r[col_periodo], r['% Seguridad Marca']),
                            textcoords="offset points", xytext=(0, 10), 
                            ha='center', fontsize=10, fontweight='bold', color='#009739')
        
        ax_evol.set_title(f'{player} - Evolución de Seguridad', fontsize=13, fontweight='bold')
        ax_evol.grid(True, alpha=0.3, linestyle='--')
        ax_evol.spines['top'].set_visible(False)
        ax_evol.spines['right'].set_visible(False)
        
        max_val = datos_evol['% Seguridad Marca'].max()
        min_val = datos_evol['% Seguridad Marca'].min()
        if pd.notna(max_val) and pd.notna(min_val):
            y_margin = (max_val - min_val) * 0.15 if max_val != min_val else 2
            ax_evol.set_ylim(max(0, min_val - y_margin), min(100, max_val + y_margin))
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig_evol.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        grafico_seguridad_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig_evol)
    
    # GRÁFICO 2: MOTIVOS DE INSEGURIDAD PONDERADOS (BARRAS APILADAS)
    # Usa % Ponderado Base = % Motivo × % Inseguridad Marca / 100
    # Así la barra total = % Inseguridad del player (no 100%)
    if not motivos_inseguridad.empty and '% Ponderado Base' in motivos_inseguridad.columns:
        # Obtener últimos 5 quarters
        olas_disp = sorted(df_completo[col_periodo].unique())
        ultimos_5q = olas_disp[-5:] if len(olas_disp) >= 5 else olas_disp
        
        mot_player = motivos_inseguridad[
            (motivos_inseguridad[col_marca] == player) &
            (motivos_inseguridad[col_periodo].isin(ultimos_5q))
        ]
        
        if len(mot_player) > 0:
            # Pivot con % Ponderado Base (ponderado por % inseguridad de la marca)
            pivot_mot = mot_player.pivot_table(
                index=col_periodo, columns='MOTIVO_INSEG',
                values='% Ponderado Base', fill_value=0  # CAMBIO: usar valores ponderados
            )
            
            if len(pivot_mot) > 0:
                # Ordenar por total y tomar top 6
                cols_ordenadas = pivot_mot.sum().sort_values(ascending=False)
                top_cols = cols_ordenadas.head(6).index.tolist()
                df_grafico = pivot_mot[top_cols].copy()
                
                # Colores fijos por categoría (consistentes cross-site)
                def get_color_motivo(motivo):
                    return COLORES_MOTIVOS_INSEGURIDAD.get(motivo, '#95a5a6')  # Gris por defecto
                
                fig_mot, ax_mot = plt.subplots(figsize=(12, 6), facecolor='white')
                ax_mot.set_facecolor('white')
                
                x_pos = np.arange(len(df_grafico))
                bottom = np.zeros(len(df_grafico))
                
                for idx, motivo in enumerate(df_grafico.columns):
                    valores = df_grafico[motivo].values
                    color = get_color_motivo(motivo)
                    
                    # Corregir encoding del label
                    motivo_limpio = fix_encoding_text(str(motivo))
                    ax_mot.bar(x_pos, valores, bottom=bottom, 
                              label=motivo_limpio[:35] + '...' if len(motivo_limpio) > 35 else motivo_limpio,
                              color=color, width=0.7, edgecolor='white', linewidth=0.5)
                    
                    # Mostrar % si es >= 1pp (valores ponderados son más pequeños)
                    for i, (val, bot) in enumerate(zip(valores, bottom)):
                        if val >= 1:
                            ax_mot.text(i, bot + val/2, f'{val:.1f}%',
                                       ha='center', va='center', fontsize=8, 
                                       fontweight='bold', color='white')
                    
                    bottom += valores
                
                # Totales arriba = % Inseguridad del player
                for i, t in enumerate(bottom):
                    ax_mot.text(i, t + 0.3, f'{t:.1f}%', ha='center', fontsize=10, fontweight='bold')
                
                # Línea de evolución % Inseguridad (eje derecho)
                ax_mot_twin = ax_mot.twinx()
                inseg_evol = datos_evol.set_index(col_periodo).reindex(df_grafico.index)
                if '% Inseguridad Marca' in inseg_evol.columns:
                    ax_mot_twin.plot(x_pos, inseg_evol['% Inseguridad Marca'].values,
                                    color='#dc2626', marker='D', linewidth=2.5, markersize=8,
                                    label='% Inseguridad', linestyle='--', alpha=0.8)
                    ax_mot_twin.set_ylabel('% Inseguridad', fontsize=11, fontweight='bold', color='#dc2626')
                    ax_mot_twin.tick_params(axis='y', labelcolor='#dc2626')
                    # Escala dinámica: máximo de los datos + margen, mínimo 30%
                    max_inseg = inseg_evol['% Inseguridad Marca'].max() if len(inseg_evol) > 0 else 20
                    ylim_inseg = max(30, max_inseg * 1.2)
                    ax_mot_twin.set_ylim(0, ylim_inseg)
                
                ax_mot.set_xticks(x_pos)
                ax_mot.set_xticklabels(df_grafico.index, fontsize=10)
                ax_mot.set_ylabel('% sobre Base Total (ponderado)', fontsize=11, fontweight='bold')
                ax_mot.set_title(f'Motivos de Inseguridad - {player} (Ponderado)', fontsize=13, fontweight='bold')
                ax_mot.legend(loc='upper left', bbox_to_anchor=(1.12, 1), fontsize=8)
                ax_mot.spines['top'].set_visible(False)
                max_val = max(bottom) if len(bottom) > 0 else 15
                ax_mot.set_ylim(0, max(max_val * 1.3, 20))  # Mínimo 20% para ver bien
                
                plt.tight_layout(rect=[0, 0, 0.85, 1])
                
                buf_mot = io.BytesIO()
                fig_mot.savefig(buf_mot, format='png', dpi=120, bbox_inches='tight', facecolor='white')
                buf_mot.seek(0)
                grafico_motivos_inseg_base64 = base64.b64encode(buf_mot.read()).decode('utf-8')
                buf_mot.close()
                plt.close(fig_mot)
    
    return {
        'seguridad_por_ola': result,
        'motivos_inseguridad': motivos_inseguridad,
        'player_seguridad': {
            'player': player,
            'q_ant': q_ant,
            'q_act': q_act,
            'seg_q1': seg_q1,
            'seg_q2': seg_q2,
            'delta': delta_seg
        },
        'col_valoracion': col_valoracion,
        'col_motivo': col_motivo,
        'grafico_seguridad_base64': grafico_seguridad_base64,
        'grafico_motivos_inseg_base64': grafico_motivos_inseg_base64
    }


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 10: ANÁLISIS DE SEGURIDAD")
    print("=" * 70)
    
    try:
        resultado_carga = cargar_datos(verbose=False)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        resultado_10 = analizar_seguridad(df_completo, config, verbose=True)
        
        print("\n📋 Variables exportadas:")
        print(f"   seguridad_por_ola: {len(resultado_10['seguridad_por_ola'])} registros")
        print(f"   motivos_inseguridad: {len(resultado_10['motivos_inseguridad'])} registros")
        
        print("\n✅ Prueba PARTE 10 completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
