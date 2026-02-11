# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 9: ANÁLISIS DE PRINCIPALIDAD
═══════════════════════════════════════════════════════════════════════════════

Analiza el % de usuarios que consideran a la marca como su banco principal.
Replica EXACTAMENTE el código del notebook original.

Uso:
    from scripts.parte9_principalidad import analizar_principalidad
    resultado = analizar_principalidad(df_completo, config)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from pathlib import Path

# ==============================================================================
# FUNCIÓN PARA CORREGIR ENCODING
# ==============================================================================

def fix_encoding_text(text):
    """Corrige caracteres con encoding corrupto (común en CSVs latinos)."""
    if not isinstance(text, str):
        return str(text) if text is not None else ''
    
    # Mapeo de caracteres corruptos a correctos
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
    'MLA': ['Mercado Pago', 'Ualá', 'Naranja X', 'Brubank', 'MODO', 'Personal Pay', 'Galicia', 'Santander'],
    'MLM': ['Mercado Pago', 'Nubank', 'BBVA', 'Santander', 'Hey Banco', 'Stori'],
    'MLC': ['Mercado Pago', 'Tenpo', 'Mach', 'Banco Estado', 'BCI']
}

COLORES_MARCAS = {
    'Mercado Pago': '#009ee3', 'MP': '#009ee3',
    'Ualá': '#ec1c24', 'Uala': '#ec1c24',
    'Galicia': '#f7941d',
    'Santander': '#ec0000',
    'Naranja X': '#ff6600',
    'Brubank': '#6b3fa0',
    'MODO': '#00a650',
    'Personal Pay': '#0033a0',
    'Nubank': '#8a05be',
    'Banco Inter': '#ff7a00',
    'C6 Bank': '#1a1a1a',
    'PicPay': '#21c25e',
    'Next': '#00a857',
    'Tenpo': '#00d1a1',
    'Mach': '#ff3366',
    'Banco Estado': '#0033a0',
    'BCI': '#e31837',
    'BBVA': '#004481',
    'Hey Banco': '#ff6200',
    'Stori': '#5c3d9e',
    'Itaú': '#003399',
    'Itau': '#003399',
}

COLORES_MOTIVOS = {
    'Recebo meu salário nesta conta': '#009739',
    'Costume': '#20B2AA',
    'Me gera confiança': '#1E90FF',
    'Oferece uma boa taxa para gerar rendimentos': '#32CD32',
    'Oferece a maior variedade de produtos': '#FF8C00',
    'Oferece acesso a créditos': '#8B4513',
    'Me oferece um cartão de crédito': '#FF6347',
    'Me ajuda a organizar minhas finanças': '#00CED1',
    'Cobro mi salario en esta cuenta': '#009739',
    'Costumbre': '#20B2AA',
    'Me genera confianza': '#1E90FF',
    'Ofrece buena tasa de rendimiento': '#32CD32',
    'Ofrece variedad de productos': '#FF8C00',
    'Ofrece acceso a créditos': '#8B4513',
    'Me ofrece tarjeta de crédito': '#FF6347',
    'Me ayuda a organizar mis finanzas': '#00CED1',
    'Outro motivo': '#A9A9A9', 'Otro motivo': '#A9A9A9',
    'Outro': '#CCCCCC', 'Otro': '#CCCCCC',
}

PALETA_RESPALDO = ['#009739', '#1E90FF', '#32CD32', '#FF8C00', '#9370DB', 
                   '#20B2AA', '#00CED1', '#FF1493', '#8B4513', '#FF6347']

COLUMNAS_MOTIVO_DIRECTO = {
    'MLB': [
        'MOTIVO_PRINCIPALIDAD', 'P14_New',
        'Por que você escolheu [P13] como sua conta principal?',
    ],
    'MLA': [
        'MOTIVO_PRINCIPALIDAD',
        '¿Por qué elegiste a [P13] como tu cuenta principal?',
        '¿Por qué elegiste esta cuenta como tu cuenta principal?',
    ],
    'MLM': [
        'MOTIVO_PRINCIPALIDAD',
        '¿Por qué elegiste a [P13] como tu cuenta principal?',
    ],
    'MLC': [
        'MOTIVO_PRINCIPALIDAD',
        '¿Por qué elegiste esta cuenta como tu cuenta principal?',
    ],
}

# Valores que indican "es principal"
VALORES_PRINCIPAL_EXACTOS = ['sí', 'si', 'sim', 'yes', '1', 'true', 'principal', 's']
VALORES_NO_PRINCIPAL = ['no', 'não', 'no principal', 'não principal', '0', 'false', 'n']


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def analizar_principalidad(df_completo, config, verbose=True):
    """
    Analiza la principalidad de las marcas.
    
    Args:
        df_completo: DataFrame completo con FLAG_PRINCIPALIDAD
        config: Diccionario de configuración
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con principalidad_por_ola, motivos, gráficos
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
        print("=" * 100)
        print(f"{BANDERA} PARTE 9: ANÁLISIS DE PRINCIPALIDAD - {NOMBRE_PAIS}")
        print("=" * 100)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DETECTAR COLUMNA FLAG_PRINCIPALIDAD
    # ═══════════════════════════════════════════════════════════════════════════
    
    col_flag = None
    for c in ['FLAG_PRINCIPALIDADE', 'FLAG_PRINCIPALIDAD', 'PRINCIPALIDAD', 'PRINCIPALIDADE']:
        if c in df_completo.columns:
            col_flag = c
            break
    
    if not col_flag:
        for c in df_completo.columns:
            if 'principal' in c.lower() and 'flag' in c.lower():
                col_flag = c
                break
    
    if not col_flag:
        if verbose:
            print("❌ No se encontró columna de principalidad (FLAG_PRINCIPALIDAD)")
            cols_principal = [c for c in df_completo.columns if 'principal' in c.lower()]
            print(f"   Columnas con 'principal': {cols_principal[:5]}")
        return {
            'principalidad_por_ola': pd.DataFrame(),
            'motivos_principalidad': pd.DataFrame(),
            'error': 'No se encontró columna FLAG_PRINCIPALIDAD'
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURAR ANÁLISIS
    # ═══════════════════════════════════════════════════════════════════════════
    
    TOP_PLAYERS = TOP_PLAYERS_CONFIG.get(site, TOP_PLAYERS_CONFIG['MLA'])
    
    if player not in TOP_PLAYERS:
        TOP_PLAYERS = [player] + TOP_PLAYERS[:5]
        if verbose:
            print(f"📌 Player seleccionado agregado: {player}")
    
    # Quarters dinámicos
    olas_disponibles = sorted(df_completo[col_periodo].unique())
    
    if q_act in olas_disponibles:
        idx_final = olas_disponibles.index(q_act)
        idx_inicio = max(0, idx_final - 4)
        ultimos_5q = olas_disponibles[idx_inicio:idx_final + 1]
    else:
        ultimos_5q = olas_disponibles[-5:] if len(olas_disponibles) >= 5 else olas_disponibles
    
    if verbose:
        print(f"\n🎯 Analizando: {', '.join(TOP_PLAYERS[:3])}, ...")
        print(f"📅 {len(ultimos_5q)} trimestres: {ultimos_5q[0]} → {ultimos_5q[-1]}")
        print(f"📊 Base: {len(df_completo):,} registros")
        print(f"🏷️ Columna FLAG: {col_flag}\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULAR % PRINCIPALIDAD
    # ═══════════════════════════════════════════════════════════════════════════
    
    df_princ_top = df_completo[
        (df_completo[col_marca].isin(TOP_PLAYERS)) &
        (df_completo[col_periodo].isin(ultimos_5q))
    ].copy()
    
    # Detectar valor de "Principal"
    valores_flag = df_princ_top[col_flag].value_counts()
    
    if verbose:
        print(f"📋 Valores en {col_flag}:")
        for v, c in valores_flag.head(5).items():
            print(f"   • '{v}': {c:,}")
    
    valor_principal = None
    
    for v in valores_flag.index:
        if pd.notna(v):
            v_str = str(v).lower().strip()
            
            if v_str in VALORES_NO_PRINCIPAL or v_str.startswith('no ') or v_str.startswith('não '):
                continue
            
            if v_str in VALORES_PRINCIPAL_EXACTOS or v_str == 'principal':
                valor_principal = v
                if verbose:
                    print(f"   ✅ Valor principal detectado: '{valor_principal}'")
                break
    
    if valor_principal is None:
        for v in valores_flag.index:
            if pd.notna(v):
                v_str = str(v).lower().strip()
                if 'principal' in v_str and not v_str.startswith('no'):
                    valor_principal = v
                    if verbose:
                        print(f"   ✅ Valor principal (fallback): '{valor_principal}'")
                    break
    
    if valor_principal is None:
        if verbose:
            print(f"   ❌ No se pudo detectar valor principal automáticamente")
        return {
            'principalidad_por_ola': pd.DataFrame(),
            'motivos_principalidad': pd.DataFrame(),
            'error': 'No se pudo detectar valor principal'
        }
    
    # Calcular base total por ola
    base_total_ola = df_princ_top.groupby(col_periodo).size().reset_index(name='Base_Total')
    
    # Calcular principalidad por marca y período
    def calc_principalidad(x):
        return pd.Series({
            'Total': len(x),
            'Principales': (x[col_flag] == valor_principal).sum(),
            '% Principalidad Marca': (x[col_flag] == valor_principal).sum() / len(x) * 100 if len(x) > 0 else 0
        })
    
    principalidad_ola = df_princ_top.groupby([col_periodo, col_marca]).apply(
        calc_principalidad, include_groups=False
    ).reset_index()
    
    principalidad_ola = principalidad_ola.merge(base_total_ola, on=col_periodo, how='left')
    principalidad_ola['% Principalidad'] = (
        principalidad_ola['Principales'] / principalidad_ola['Base_Total'] * 100
    ).round(2)
    
    principalidad_ola = principalidad_ola.rename(columns={col_marca: 'MARCA'})
    
    if verbose:
        print(f"\n✅ Principalidad calculada para {len(principalidad_ola)} combinaciones marca-período")
        
        # Verificación
        print(f"\n📊 Verificación ({ultimos_5q[-1]}):")
        for marca in TOP_PLAYERS[:6]:
            dato = principalidad_ola[(principalidad_ola['MARCA'] == marca) & 
                                      (principalidad_ola[col_periodo] == ultimos_5q[-1])]
            if len(dato) > 0:
                print(f"   • {marca}: {dato['% Principalidad Marca'].values[0]:.1f}%")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # BUSCAR MOTIVOS DE PRINCIPALIDAD
    # ═══════════════════════════════════════════════════════════════════════════
    
    col_motivo = None
    columnas_directas = COLUMNAS_MOTIVO_DIRECTO.get(site, [])
    
    if verbose:
        print(f"\n🔍 Buscando columna de motivos principalidad...")
    
    for col_directa in columnas_directas:
        if col_directa in df_completo.columns:
            col_motivo = col_directa
            if verbose:
                print(f"   ✅ Columna de motivos: '{col_motivo[:60]}...'")
            break
    
    if not col_motivo:
        keywords_motivo = ['elegiste', 'escolheu', 'motivo_princip', 'motivo princip', 'por qué', 'por que']
        for c in df_completo.columns:
            c_lower = c.lower()
            for kw in keywords_motivo:
                if kw in c_lower and ('principal' in c_lower or 'motivo' in c_lower):
                    col_motivo = c
                    if verbose:
                        print(f"   ✅ Columna de motivos (keyword): '{col_motivo[:60]}...'")
                    break
            if col_motivo:
                break
    
    motivos_final = pd.DataFrame()
    
    if col_motivo:
        df_principales = df_princ_top[df_princ_top[col_flag] == valor_principal].copy()
        
        if len(df_principales) > 0:
            if verbose:
                print(f"   📊 Registros principales: {len(df_principales):,}")
            
            # Calcular motivos
            motivos_principalidad = df_principales.groupby([col_periodo, col_marca, col_motivo]).size().reset_index(name='Cantidad')
            totales_principales = df_principales.groupby([col_periodo, col_marca]).size().reset_index(name='Total_Principales')
            
            motivos_con_pct = motivos_principalidad.merge(totales_principales, on=[col_periodo, col_marca], how='left')
            motivos_con_pct['% Motivo'] = (motivos_con_pct['Cantidad'] / motivos_con_pct['Total_Principales'] * 100).round(1)
            
            # Merge con principalidad
            motivos_final = motivos_con_pct.merge(
                principalidad_ola[[col_periodo, 'MARCA', '% Principalidad', '% Principalidad Marca', 'Total']].rename(columns={'MARCA': col_marca}),
                on=[col_periodo, col_marca], how='left'
            )
            motivos_final['% Ponderado Base'] = (motivos_final['% Motivo'] * motivos_final['% Principalidad Marca'] / 100).round(2)
            motivos_final = motivos_final[motivos_final[col_motivo].notna() & (motivos_final[col_motivo].astype(str).str.strip() != '')]
            motivos_final = motivos_final.rename(columns={col_motivo: 'Motivo'})
            
            if verbose:
                print(f"   📊 Motivos únicos: {motivos_final['Motivo'].nunique()}")
    else:
        if verbose:
            print("   ⚠️ Columna de motivos no encontrada")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANÁLISIS DEL PLAYER SELECCIONADO
    # ═══════════════════════════════════════════════════════════════════════════
    
    player_q1 = principalidad_ola[(principalidad_ola['MARCA'] == player) & (principalidad_ola[col_periodo] == q_ant)]
    player_q2 = principalidad_ola[(principalidad_ola['MARCA'] == player) & (principalidad_ola[col_periodo] == q_act)]
    
    princ_q1 = player_q1['% Principalidad Marca'].values[0] if len(player_q1) > 0 else 0
    princ_q2 = player_q2['% Principalidad Marca'].values[0] if len(player_q2) > 0 else 0
    delta_princ = princ_q2 - princ_q1
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"📊 PRINCIPALIDAD {player}")
        print("=" * 70)
        print(f"   {q_ant}: {princ_q1:.1f}%")
        print(f"   {q_act}: {princ_q2:.1f}%")
        print(f"   Delta: {delta_princ:+.1f}pp")
        
        # Top principalidad
        top_princ = principalidad_ola[principalidad_ola[col_periodo] == q_act].sort_values('% Principalidad Marca', ascending=False).head(5)
        print(f"\n🏆 TOP PRINCIPALIDAD ({q_act}):")
        print("=" * 70)
        for i, (_, row) in enumerate(top_princ.iterrows(), 1):
            emoji = "👑" if i == 1 else f"{i}."
            print(f"   {emoji} {row['MARCA']:<25} {row['% Principalidad Marca']:.1f}%")
        
        # Motivos del player
        if not motivos_final.empty:
            motivos_player = motivos_final[
                (motivos_final[col_marca] == player) & 
                (motivos_final[col_periodo] == q_act)
            ].sort_values('% Motivo', ascending=False).head(5)
            
            if not motivos_player.empty:
                print(f"\n📋 TOP MOTIVOS DE PRINCIPALIDAD - {player} ({q_act}):")
                print("─" * 70)
                for _, row in motivos_player.iterrows():
                    motivo_limpio = str(row['Motivo'])[:45]
                    print(f"   • {motivo_limpio}: {row['% Motivo']:.1f}%")
        
        print(f"\n{'='*100}")
        print(f"✅ PARTE 9 OK - Análisis de principalidad completado")
        print("=" * 100)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GRÁFICOS (EXACTO AL NOTEBOOK ORIGINAL)
    # ═══════════════════════════════════════════════════════════════════════════
    
    grafico_principalidad_base64 = None
    grafico_motivos_princ_base64 = None
    
    # Paleta de colores para motivos
    PALETA_RESPALDO = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
    
    COLORES_MOTIVOS_PRINC = {
        'Facilidad de uso': '#2ecc71',
        'Beneficios': '#3498db',
        'Seguridad': '#e74c3c',
        'Servicio al cliente': '#f39c12',
        'Costos bajos': '#9b59b6',
        'Rendimientos': '#1abc9c',
        'Otro': '#95a5a6'
    }
    
    # GRÁFICO 1: EVOLUCIÓN DE PRINCIPALIDAD (LÍNEAS POR MARCA)
    # FILTRAR SOLO ÚLTIMOS 5 QUARTERS
    principalidad_grafico = principalidad_ola[principalidad_ola[col_periodo].isin(ultimos_5q)].copy()
    marcas_grafico = [m for m in TOP_PLAYERS if m in principalidad_grafico['MARCA'].unique()]
    
    if len(marcas_grafico) > 0:
        fig1, ax1 = plt.subplots(figsize=(12, 6), facecolor='white')
        ax1.set_facecolor('white')
        
        for marca in marcas_grafico:
            datos_marca = principalidad_grafico[principalidad_grafico['MARCA'] == marca].sort_values(col_periodo)
            if len(datos_marca) > 0 and datos_marca['% Principalidad Marca'].sum() > 0:
                color = COLORES_MARCAS.get(marca, '#95a5a6')
                linewidth = 3 if marca == player else 2
                
                ax1.plot(datos_marca[col_periodo], datos_marca['% Principalidad Marca'], 
                        marker='o', linewidth=linewidth, markersize=8, color=color, label=marca)
                
                # Etiquetas de valor
                for _, row in datos_marca.iterrows():
                    ax1.annotate(f"{row['% Principalidad Marca']:.0f}%",
                                (row[col_periodo], row['% Principalidad Marca']),
                                textcoords="offset points", xytext=(0, 8),
                                ha='center', fontsize=9, fontweight='bold', color=color)
        
        ax1.set_xlabel('Trimestre', fontsize=11, fontweight='bold')
        ax1.set_ylabel('% Principalidad', fontsize=11, fontweight='bold')
        ax1.set_title(f'Evolución de Principalidad', fontsize=14, fontweight='bold', pad=15)
        ax1.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize=10)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        max_val = principalidad_ola['% Principalidad Marca'].max()
        ax1.set_ylim(0, max(max_val * 1.15, 10) if pd.notna(max_val) else 100)
        
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        plt.tight_layout()
        
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buf1.seek(0)
        grafico_principalidad_base64 = base64.b64encode(buf1.read()).decode('utf-8')
        buf1.close()
        plt.close(fig1)
    
    # GRÁFICO 2: MOTIVOS DE PRINCIPALIDAD PONDERADOS (BARRAS APILADAS)
    # Usa % Ponderado Base = % Motivo × % Principalidad Marca / 100
    # Así la barra total = % Principalidad del player (no 100%)
    
    # Datos de evolución del player para la línea superpuesta
    datos_evol = principalidad_ola[principalidad_ola['MARCA'] == player].copy()
    
    if not motivos_final.empty and 'Motivo' in motivos_final.columns and '% Ponderado Base' in motivos_final.columns:
        # FILTRAR SOLO ÚLTIMOS 5 QUARTERS
        motivos_player_chart = motivos_final[
            (motivos_final[col_marca] == player) & 
            (motivos_final[col_periodo].isin(ultimos_5q))
        ]
        
        if len(motivos_player_chart) > 0:
            # Usar % Ponderado Base (ponderado por % principalidad de la marca)
            pivot_motivos = motivos_player_chart.pivot_table(
                index=col_periodo, 
                columns='Motivo', 
                values='% Ponderado Base',  # CAMBIO: usar valores ponderados
                aggfunc='sum', 
                fill_value=0
            )
            
            # Reordenar para mostrar quarters en orden cronológico
            pivot_motivos = pivot_motivos.reindex([q for q in ultimos_5q if q in pivot_motivos.index])
            
            if len(pivot_motivos) > 0:
                # Top 6 motivos
                top_motivos = pivot_motivos.sum().nlargest(6).index.tolist()
                df_plot = pivot_motivos[top_motivos].copy()
                
                # Agregar "Otros" si hay más
                otros_cols = [c for c in pivot_motivos.columns if c not in top_motivos]
                if len(otros_cols) > 0:
                    df_plot['Otro'] = pivot_motivos[otros_cols].sum(axis=1)
                
                fig2, ax2 = plt.subplots(figsize=(12, 6), facecolor='white')
                ax2.set_facecolor('white')
                
                x_pos = np.arange(len(df_plot))
                bottom = np.zeros(len(df_plot))
                
                for idx, motivo in enumerate(df_plot.columns):
                    valores = df_plot[motivo].values
                    color = COLORES_MOTIVOS_PRINC.get(motivo, PALETA_RESPALDO[idx % len(PALETA_RESPALDO)])
                    # Corregir encoding y truncar
                    motivo_limpio = fix_encoding_text(str(motivo))
                    mot_label = motivo_limpio[:30] + '...' if len(motivo_limpio) > 30 else motivo_limpio
                    
                    ax2.bar(x_pos, valores, bottom=bottom, label=mot_label, 
                           color=color, width=0.6, edgecolor='white', linewidth=0.5)
                    
                    # Mostrar % si es >= 2pp (más estricto porque son valores ponderados pequeños)
                    for i, (val, bot) in enumerate(zip(valores, bottom)):
                        if val >= 2:
                            ax2.text(i, bot + val/2, f'{val:.1f}%', ha='center', va='center', 
                                    fontsize=8, fontweight='bold', color='white')
                    
                    bottom += valores
                
                # Total arriba de cada barra = % Principalidad del player
                for i, total in enumerate(bottom):
                    ax2.text(i, total + 0.5, f'{total:.1f}%', ha='center', va='bottom',
                            fontsize=10, fontweight='bold', color='#333')
                
                # Línea de evolución % Principalidad (eje derecho)
                ax2_twin = ax2.twinx()
                princ_evol = datos_evol.set_index(col_periodo).reindex(df_plot.index)
                if '% Principalidad Marca' in princ_evol.columns:
                    ax2_twin.plot(x_pos, princ_evol['% Principalidad Marca'].values,
                                 color='#1e40af', marker='D', linewidth=2.5, markersize=8,
                                 label='% Principalidad', linestyle='--', alpha=0.8)
                    ax2_twin.set_ylabel('% Principalidad', fontsize=11, fontweight='bold', color='#1e40af')
                    ax2_twin.tick_params(axis='y', labelcolor='#1e40af')
                    ax2_twin.set_ylim(0, 100)
                
                ax2.set_xticks(x_pos)
                ax2.set_xticklabels(df_plot.index, fontsize=11, fontweight='600')
                ax2.set_ylabel('% sobre Base Total (ponderado)', fontsize=11, fontweight='bold')
                ax2.set_title(f'{player} - Motivos de Principalidad (Ponderado)', fontsize=14, fontweight='bold', pad=15)
                ax2.legend(loc='upper left', bbox_to_anchor=(1.12, 1), fontsize=9)
                ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
                ax2.spines['top'].set_visible(False)
                max_val = max(bottom) if len(bottom) > 0 else 50
                ax2.set_ylim(0, max(max_val * 1.2, 40))  # Mínimo 40% para ver bien
                
                plt.tight_layout(rect=[0, 0, 0.85, 1])
                
                buf2 = io.BytesIO()
                fig2.savefig(buf2, format='png', dpi=120, bbox_inches='tight', facecolor='white')
                buf2.seek(0)
                grafico_motivos_princ_base64 = base64.b64encode(buf2.read()).decode('utf-8')
                buf2.close()
                plt.close(fig2)
    
    return {
        'principalidad_por_ola': principalidad_ola,
        'motivos_principalidad': motivos_final,
        'player_principalidad': {
            'player': player,
            'q_ant': q_ant,
            'q_act': q_act,
            'princ_q1': princ_q1,
            'princ_q2': princ_q2,
            'delta': delta_princ
        },
        'valor_principal': valor_principal,
        'col_flag': col_flag,
        'grafico_principalidad_base64': grafico_principalidad_base64,
        'grafico_motivos_princ_base64': grafico_motivos_princ_base64
    }


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 9: ANÁLISIS DE PRINCIPALIDAD")
    print("=" * 70)
    
    try:
        resultado_carga = cargar_datos(verbose=False)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        resultado_9 = analizar_principalidad(df_completo, config, verbose=True)
        
        print("\n📋 Variables exportadas:")
        print(f"   principalidad_por_ola: {len(resultado_9['principalidad_por_ola'])} registros")
        print(f"   motivos_principalidad: {len(resultado_9['motivos_principalidad'])} registros")
        
        print("\n✅ Prueba PARTE 9 completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
