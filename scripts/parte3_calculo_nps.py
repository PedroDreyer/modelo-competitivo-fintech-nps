# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
📊 PARTE 3: CÁLCULO Y VISUALIZACIÓN NPS - MULTISITE
═══════════════════════════════════════════════════════════════════════════════

Este script replica EXACTAMENTE la lógica del notebook original para:
1. Filtrar datos por player
2. Calcular NPS por quarter
3. Calcular delta NPS entre períodos seleccionados
4. Generar gráfico de evolución NPS
5. Exportar variables para las siguientes partes

Uso:
    from scripts.parte3_calculo_nps import calcular_nps
    resultados = calcular_nps(df, config)
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from pathlib import Path
from validators import validate_nps_values, validate_dataframe_not_empty

# ==============================================================================
# FUNCIÓN: ORDENAR QUARTERS
# ==============================================================================

def quarter_order(q):
    """
    Ordena quarters por año y trimestre.
    Ejemplo: '24Q4' -> 2024*4 + 4 = 8100
    """
    try:
        s = str(q).strip()
        if 'Q' in s:
            parts = s.split('Q')
            year = int('20' + parts[0]) if len(parts[0]) == 2 else int(parts[0])
            return year * 4 + int(parts[1][0])
    except (ValueError, IndexError, AttributeError):
        pass
    return 0

# ==============================================================================
# FUNCIÓN PRINCIPAL: CALCULAR NPS
# ==============================================================================

def calcular_nps(df_completo, config, generar_grafico=True, guardar_grafico=True, verbose=True):
    """
    Calcula NPS por quarter y genera visualización.
    
    REPLICA EXACTAMENTE la lógica del notebook original.
    
    Args:
        df_completo: DataFrame con todos los datos cargados
        config: Diccionario de configuración (de parte1_carga_datos)
        generar_grafico: Si True, genera gráfico de evolución
        guardar_grafico: Si True, guarda el gráfico en outputs/
        verbose: Si True, imprime información de progreso
    
    Returns:
        dict: Diccionario con todas las variables calculadas
    """
    
    # Extraer configuración
    PLAYER_ANALIZAR = config['player']
    PERIODO_1 = config['periodo_1']
    PERIODO_2 = config['periodo_2']
    BANDERA = config['site_bandera']
    
    # Columnas
    col_marca = 'MARCA'
    col_nps = 'NPS'  # Columna con clasificación -1/0/1 (original del CSV)
    col_ola = 'OLA'
    
    quarters_seleccionados = [PERIODO_1, PERIODO_2]
    
    if verbose:
        print(f"{'='*70}")
        print(f"{BANDERA} PARTE 3: CÁLCULO NPS - {PLAYER_ANALIZAR}")
        print(f"{'='*70}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # FILTRAR Y CALCULAR NPS
    # ══════════════════════════════════════════════════════════════════════════
    
    df_player = df_completo[df_completo[col_marca] == PLAYER_ANALIZAR].copy()

    # Validar que hay datos del player
    validate_dataframe_not_empty(df_player, f"Player {PLAYER_ANALIZAR}")

    if verbose:
        print(f"\n📊 Registros {PLAYER_ANALIZAR}: {len(df_player):,}")
    
    # Convertir NPS a numérico si es necesario
    if df_player[col_nps].dtype == 'object':
        df_player[col_nps] = pd.to_numeric(df_player[col_nps], errors='coerce')

    # Validar valores de NPS
    validate_nps_values(df_player, col_nps, max_invalid_pct=0.1)

    # Calcular NPS por quarter
    # El NPS en el CSV tiene valores -1 (Detractor), 0 (Neutro), 1 (Promotor)
    # NPS Score = mean * 100 = ((Promotores - Detractores) / Total) * 100
    nps_por_quarter = df_player.groupby(col_ola)[col_nps].agg(['mean', 'count']).reset_index()
    nps_por_quarter.columns = [col_ola, 'NPS_medio', 'n_registros']
    nps_por_quarter['NPS_score'] = nps_por_quarter['NPS_medio'] * 100
    nps_por_quarter['order'] = nps_por_quarter[col_ola].apply(quarter_order)
    nps_por_quarter = nps_por_quarter.sort_values('order')
    
    # Filtrar últimos 5 quarters hasta el seleccionado
    N_QUARTERS = 5
    quarter_final = sorted(quarters_seleccionados)[-1]
    all_quarters = nps_por_quarter[col_ola].tolist()
    
    if quarter_final in all_quarters:
        idx_fin = all_quarters.index(quarter_final)
        quarters_grafico = all_quarters[max(0, idx_fin - N_QUARTERS + 1):idx_fin + 1]
    else:
        quarters_grafico = all_quarters[-N_QUARTERS:]
    
    nps_grafico = nps_por_quarter[nps_por_quarter[col_ola].isin(quarters_grafico)].copy()
    
    # NPS de períodos seleccionados
    nps_q1 = nps_por_quarter[nps_por_quarter[col_ola] == PERIODO_1]['NPS_score'].values
    nps_q2 = nps_por_quarter[nps_por_quarter[col_ola] == PERIODO_2]['NPS_score'].values
    nps_q1 = round(nps_q1[0], 1) if len(nps_q1) > 0 else 0
    nps_q2 = round(nps_q2[0], 1) if len(nps_q2) > 0 else 0
    delta_nps = round(nps_q2 - nps_q1, 1)
    
    if verbose:
        print(f"\n📈 EVOLUCIÓN NPS:")
        for _, row in nps_grafico.iterrows():
            marca = "✅" if row[col_ola] in quarters_seleccionados else "  "
            print(f"   {marca} {row[col_ola]}: {row['NPS_score']:.1f} ({row['n_registros']:,} reg)")
        
        print(f"\n{'─'*50}")
        print(f"   📊 {PERIODO_1}: {nps_q1:.1f}")
        print(f"   📊 {PERIODO_2}: {nps_q2:.1f}")
        emoji = '📈' if delta_nps > 0 else '📉' if delta_nps < 0 else '➡️'
        print(f"   {emoji} Delta: {delta_nps:+.1f} pp")
    
    # ══════════════════════════════════════════════════════════════════════════
    # GRÁFICO DE EVOLUCIÓN NPS (EXACTO AL NOTEBOOK ORIGINAL)
    # ══════════════════════════════════════════════════════════════════════════
    
    fig = None
    grafico_base64 = None
    
    if generar_grafico and len(nps_grafico) > 0:
        # Formato exacto del notebook original
        fig, ax = plt.subplots(figsize=(14, 5), facecolor='white')
        ax.set_facecolor('white')
        
        x = range(len(nps_grafico))
        y = nps_grafico['NPS_score'].values
        quarters = nps_grafico[col_ola].values
        
        # Línea con marcadores (estilo original)
        ax.plot(x, y, marker='o', linewidth=2.5, markersize=8, 
               color='#009ee3', markerfacecolor='#009ee3', 
               markeredgecolor='white', markeredgewidth=2, zorder=5)
        
        # Etiquetas sobre cada punto
        for i, (xi, yi) in enumerate(zip(x, y)):
            ax.text(xi, yi + 1.5, f"{yi:.1f}", ha='center', va='bottom', 
                   fontsize=11, fontweight='bold', color='#333')
        
        # Formato de ejes (estilo minimalista del original)
        ax.set_xticks(x)
        ax.set_xticklabels(quarters, fontsize=10, color='#666')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#e0e0e0')
        ax.tick_params(left=False, colors='#666')
        ax.grid(False)
        y_clean = [v for v in y if not (v != v)]  # Filter NaN
        if y_clean:
            ax.set_ylim(min(y_clean) - 5, max(y_clean) + 5)
        ax.legend([PLAYER_ANALIZAR], loc='upper right', frameon=False, fontsize=11)
        
        plt.tight_layout()
        
        # Nota: Los gráficos se embeben en el HTML como base64, no se guardan como archivos separados
        
        # Guardar como base64 para HTML
        import io
        import base64
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='white', edgecolor='none')
        buf.seek(0)
        grafico_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        
        plt.close(fig)
    
    # ══════════════════════════════════════════════════════════════════════════
    # EXPORTAR VARIABLES
    # ══════════════════════════════════════════════════════════════════════════
    
    nps_comparativo = {PERIODO_1: nps_q1, PERIODO_2: nps_q2, 'delta': delta_nps}
    df_q1 = df_player[df_player[col_ola] == PERIODO_1].copy()
    df_q2 = df_player[df_player[col_ola] == PERIODO_2].copy()
    
    resultados = {
        'df_player': df_player,
        'df_q1': df_q1,
        'df_q2': df_q2,
        'df_q1_saldo': df_q1,  # Alias para compatibilidad
        'df_q2_saldo': df_q2,  # Alias para compatibilidad
        'nps_q1': nps_q1,
        'nps_q2': nps_q2,
        'delta_nps': delta_nps,
        'nps_comparativo': nps_comparativo,
        'nps_por_quarter': nps_por_quarter,
        'nps_grafico': nps_grafico,
        'quarters_seleccionados': quarters_seleccionados,
        'fig': fig,
        'grafico_evolucion_nps_base64': grafico_base64  # Para HTML
    }
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"✅ PARTE 3 OK - NPS: {nps_q1:.1f} → {nps_q2:.1f} ({delta_nps:+.1f} pp)")
        print(f"   💾 Variables: df_q1, df_q2, nps_comparativo, nps_por_quarter")
        print(f"{'='*70}")
    
    return resultados

# ==============================================================================
# FUNCIÓN: CALCULAR NPS COMPETITIVO (todos los players)
# ==============================================================================

def calcular_nps_competitivo(df_completo, config, verbose=True):
    """
    Calcula NPS de todos los players para comparación competitiva.
    
    Args:
        df_completo: DataFrame con todos los datos
        config: Diccionario de configuración
        verbose: Si True, imprime información
    
    Returns:
        DataFrame: NPS por player y período
    """
    
    PERIODO_1 = config['periodo_1']
    PERIODO_2 = config['periodo_2']
    col_marca = 'MARCA'
    col_nps = 'NPS'
    col_ola = 'OLA'
    
    # Filtrar períodos
    df_filtrado = df_completo[df_completo[col_ola].isin([PERIODO_1, PERIODO_2])].copy()
    df_filtrado[col_nps] = pd.to_numeric(df_filtrado[col_nps], errors='coerce')
    
    # Calcular NPS por player y período
    nps_competitivo = df_filtrado.groupby([col_marca, col_ola])[col_nps].agg(['mean', 'count']).reset_index()
    nps_competitivo.columns = ['Player', 'Periodo', 'NPS_medio', 'n_registros']
    nps_competitivo['NPS_score'] = nps_competitivo['NPS_medio'] * 100
    
    # Pivot para comparar períodos
    nps_pivot = nps_competitivo.pivot(index='Player', columns='Periodo', values='NPS_score').reset_index()
    
    if PERIODO_1 in nps_pivot.columns and PERIODO_2 in nps_pivot.columns:
        nps_pivot['Delta'] = nps_pivot[PERIODO_2] - nps_pivot[PERIODO_1]
        nps_pivot = nps_pivot.sort_values(PERIODO_2, ascending=False)
    
    if verbose:
        print(f"\n📊 NPS COMPETITIVO ({PERIODO_1} vs {PERIODO_2}):")
        print("-" * 60)
        for _, row in nps_pivot.iterrows():
            p1 = row.get(PERIODO_1, 'N/A')
            p2 = row.get(PERIODO_2, 'N/A')
            delta = row.get('Delta', 0)
            p1_str = f"{p1:.1f}" if isinstance(p1, (int, float)) and not pd.isna(p1) else "N/A"
            p2_str = f"{p2:.1f}" if isinstance(p2, (int, float)) and not pd.isna(p2) else "N/A"
            emoji = '📈' if delta > 0 else '📉' if delta < 0 else '➡️'
            print(f"   {row['Player'][:25]:25} {p1_str:>8} → {p2_str:>8} ({delta:+.1f}) {emoji}")
    
    return nps_pivot

# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    
    print("\n" + "="*70)
    print("🧪 PRUEBA PARTE 3: CÁLCULO NPS")
    print("="*70)
    
    try:
        # Cargar datos usando parte1 (ya incluye filtro por saldo)
        resultado = cargar_datos(verbose=True)
        
        df_completo = resultado['df_completo']  # Base con saldo (principal)
        config = resultado['config']
        
        # Calcular NPS
        resultados = calcular_nps(df_completo, config, generar_grafico=True, guardar_grafico=True)
        
        print("\n📋 Variables exportadas:")
        for k, v in resultados.items():
            if isinstance(v, pd.DataFrame):
                print(f"   {k}: DataFrame ({len(v)} filas)")
            elif isinstance(v, dict):
                print(f"   {k}: {v}")
            elif isinstance(v, (int, float)):
                print(f"   {k}: {v}")
            else:
                print(f"   {k}: {type(v).__name__}")
        
        # Calcular NPS competitivo
        print("\n" + "="*70)
        nps_comp = calcular_nps_competitivo(df_completo, config)
        
        print("\n✅ Prueba PARTE 3 completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
