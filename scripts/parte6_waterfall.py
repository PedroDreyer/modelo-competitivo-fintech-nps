# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 6: WATERFALL NPS + EVOLUCIÓN QUEJAS
═══════════════════════════════════════════════════════════════════════════════

Genera:
1. Tabla Waterfall NPS comparando dos periodos
2. Gráfico Waterfall
3. Gráfico Evolución de Quejas (últimos 5 quarters)

Replica EXACTAMENTE el código del notebook original.

Uso:
    from scripts.parte6_waterfall import generar_waterfall
    resultado = generar_waterfall(resultado_parte5, df_player, config)
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os

# ==============================================================================
# MAPEO DE MOTIVOS (MULTISITE) - CORREGIDO
# ==============================================================================

def mapear_motivo(motivo):
    """
    Agrupa categorías granulares en categorías principales.
    Soporta categorías en español y portugués.
    CORREGIDO: unifica Beneficios→Promociones y agrega keywords de inversion
    """
    if pd.isna(motivo) or str(motivo).strip() in ['', '.', 'nan']: 
        return 'Sin opinión'
    
    m = str(motivo).strip()
    
    # Normalizar encoding
    m = m.replace('ã§','ç').replace('ã£','ã').replace('ã©','é').replace('ã³','ó').replace('ã­','í')
    m = m.replace('Ã§','ç').replace('Ã£','ã').replace('Ã©','é').replace('Ã³','ó').replace('Ã­','í')
    
    m_lower = m.lower()
    
    # === TARIFAS (cobros, comisiones, mensualidades - NO tasas de interés) ===
    # IMPORTANTE: Evaluar ANTES de Financiamiento para que no se confunda con "tasa"
    # FIX: "Tarifas y tasas" → Tarifas (tarifa siempre gana sobre tasa cuando coexisten)
    if any(x in m_lower for x in [
        'tarifa', 'cobrança', 'cobranza', 'comisión', 'comision', 'comissão',
        'mensualidad', 'mensalidade', 'costo de', 'custo de', 'cobro'
    ]) and 'tasa de' not in m_lower and 'taxa de' not in m_lower:
        return 'Tarifas'
    
    # === FINANCIAMIENTO (incluye crédito, tarjeta, límites, tasas de interés) ===
    if any(x in m_lower for x in [
        'financ', 'crédit', 'credit', 'cartão', 'tarjeta', 'limite', 
        'empréstimo', 'préstamo', 'prestamo', 'taxa', 'tasa', 'juro',
        'acesso a créd', 'acesso a cred'
    ]):
        return 'Financiamiento'
    
    # === RENDIMIENTOS (incluye inversiones) - CORREGIDO PARA TODOS LOS SITES ===
    if any(x in m_lower for x in [
        'rendimento', 'rendimiento', 'investimento', 'inversiones', 'inversión',
        'poupança', 'ahorro', 'cdi', 'saldo da conta',
        'inversion', 'invertir', 'opcion',
        'ganancia', 'ganancias', 'dinero en cuenta'  # AGREGADO PARA MÉXICO
    ]):
        return 'Rendimientos'
    
    # === COMPLEJIDAD / DIFICULTAD ===
    if any(x in m_lower for x in [
        'dificuldade', 'dificultad', 'problema', 'complexidade', 'complejidad',
        'comodidade', 'facilidade', 'facilidad', 'complicado', 'difícil'
    ]):
        return 'Complejidad'
    
    # === FUNCIONALIDADES ===
    if any(x in m_lower for x in [
        'funcionalidade', 'funcionalidad', 'oferta de func', 'maior oferta',
        'feature', 'recurso'
    ]):
        return 'Funcionalidades'
    
    # === SEGURIDAD ===
    if any(x in m_lower for x in [
        'segurança', 'seguridad', 'seguro', 'fraude', 'golpe', 'roubo', 'robo'
    ]):
        return 'Seguridad'
    
    # === ATENCIÓN ===
    if any(x in m_lower for x in [
        'atendimento', 'atención', 'atencion', 'cliente', 'suporte', 'soporte', 'sac'
    ]):
        return 'Atención'
    
    # === PROMOCIONES (unifica Beneficios) - CORREGIDO ===
    if any(x in m_lower for x in [
        'benefício', 'beneficio', 'desconto', 'descuento', 'promoção', 'promoción',
        'cashback', 'recompensa', 'reward', 'promocion', 'promociones', 'promo'  # AGREGADO
    ]):
        return 'Promociones'  # CAMBIADO de 'Beneficios' a 'Promociones'
    
    # === SIN OPINIÓN ===
    if any(x in m_lower for x in [
        'não uso', 'no uso', 'sem opinião', 'sin opinión', 'sin opinion'
    ]):
        return 'Sin opinión'
    
    # === OTROS (unificar todas las variantes: otro, otros, outros, other) ===
    if any(x in m_lower for x in ['outro', 'otros', 'other', 'otro']):
        return 'Otro'
    # Capturar también si es exactamente "otro" o variantes
    if m_lower.strip() in ['otro', 'otros', 'outros', 'other', 'otra', 'outras']:
        return 'Otro'
    
    # === VALORES INVÁLIDOS / ERRORES DE EXCEL → Otro ===
    if any(x in m_lower for x in ['#¡valor!', '#valor!', '#value!', '#n/a', '#ref!']):
        return 'Otro'
    
    # === NA / Na / N/A → Otro ===
    if m_lower.strip() in ['na', 'n/a', 'nan', 'null', 'none', '-']:
        return 'Otro'
    
    # === OFERTA → Funcionalidades ===
    if 'oferta' in m_lower and 'func' not in m_lower:
        return 'Funcionalidades'
    
    # === APP (problemas con la app) → Complejidad ===
    if m_lower.strip() == 'app':
        return 'Complejidad'
    
    # Si no matchea nada, devolver tal cual
    return m

# Colores para TODAS las categorías posibles - CORREGIDO
COLORES = {
    # Categorías principales
    'Financiamiento': '#6bcb77',
    'Rendimientos': '#e63946',
    'Atención': '#c8b6ff',
    'Seguridad': '#2d6a4f',
    'Funcionalidades': '#5f6c7b',
    # Categorías adicionales - CORREGIDO: Promociones unifica Beneficios
    'Promociones': '#7c3aed',  # Unifica Beneficios
    'Complejidad': '#ff9f43',
    'Tasas': '#778ca3',
    'Inversiones': '#0984e3',
    'Tarifas': '#fd79a8',
    'Dificultad': '#fdcb6e',
    # Residuales - UNIFICADO: solo "Otro" (sin plural)
    'Sin opinión': '#d1d8e0',
    'Otro': '#95a5a6',  # Unifica: Otro, Otros, Outros, Other
    'Outros': '#95a5a6',  # Fallback por si viene de BigQuery
    'Otros': '#95a5a6',  # Fallback por si viene de BigQuery
    'Não uso ou sem opinião': '#d1d8e0',
    'Sin desglose': '#bdc3c7',  # Gris claro
}

# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def generar_waterfall(resultado_parte5, df_player, config, guardar_graficos=True, verbose=True):
    """
    Genera Waterfall NPS y gráfico de evolución de quejas.
    
    Args:
        resultado_parte5: Diccionario con df_final_categorizado de PARTE 5
        df_player: DataFrame con datos del player (de PARTE 3)
        config: Diccionario de configuración
        guardar_graficos: Si True, guarda los gráficos en outputs/
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con waterfall_data, nps_comparativo, evolucion_quejas_data
    """
    
    # Extraer configuración
    site = config['site']
    player_seleccionado = config['player']
    BANDERA = config['site_bandera']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    quarters_seleccionados = [q_ant, q_act]
    
    col_nps = 'NPS'
    col_ola = 'OLA'
    
    if verbose:
        print("=" * 70)
        print(f"{BANDERA} PARTE 6: WATERFALL NPS - {player_seleccionado}")
        print("=" * 70)
    
    # Obtener DataFrame categorizado
    df_wf = resultado_parte5['df_final_categorizado'].copy()
    
    # Detectar columna de periodo
    col_periodo = None
    if 'PERIODO' in df_wf.columns:
        col_periodo = 'PERIODO'
    elif col_ola in df_wf.columns:
        col_periodo = col_ola
    else:
        for c in df_wf.columns:
            if 'ola' in c.lower() or 'quarter' in c.lower() or 'periodo' in c.lower():
                col_periodo = c
                break
        if not col_periodo:
            raise ValueError(f"❌ No se encontró columna de periodo. Columnas: {list(df_wf.columns)}")
    
    # Configurar periodos
    periodos = sorted(quarters_seleccionados)
    usar_comp = len(periodos) >= 2
    
    if verbose:
        print(f"🎯 {player_seleccionado}: {q_ant} vs {q_act}" if usar_comp else f"🎯 {player_seleccionado}: {q_act}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULAR CONTRIBUCIONES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def calc_contrib(df_motivos, periodo):
        """Calcula contribución de cada motivo al NPS"""
        df_total = df_player[df_player[col_periodo] == periodo]
        if len(df_total) == 0: 
            return {}, 0, 0
        
        prom = (df_total[col_nps] == 1).sum()
        det = (df_total[col_nps] == -1).sum()
        nps = (prom - det) / len(df_total) * 100
        
        df_p = df_motivos[df_motivos[col_periodo] == periodo]
        contrib = {}
        if 'MOTIVO_IA' in df_p.columns:
            for mot in df_p['MOTIVO_IA'].dropna().unique():
                sub = df_p[df_p['MOTIVO_IA'] == mot]
                d, n = (sub[col_nps] == -1).sum(), (sub[col_nps] == 0).sum()
                contrib[mot] = ((d * 2) + n) / len(df_total) * 100
        return contrib, nps, len(df_total)
    
    # Calcular
    if usar_comp:
        c_ant, nps_ant, t_ant = calc_contrib(df_wf, q_ant)
        c_act, nps_act, t_act = calc_contrib(df_wf, q_act)
        if verbose:
            print(f"\n📊 NPS: {q_ant}={nps_ant:.1f} → {q_act}={nps_act:.1f} (Δ{nps_act-nps_ant:+.1f})")
    else:
        c_ant, nps_ant, t_ant = {}, 0, 0
        c_act, nps_act, t_act = calc_contrib(df_wf, q_act)
        if verbose:
            print(f"\n📊 NPS {q_act}: {nps_act:.1f}")
    
    # Agrupar por categoría
    def agrupar(c): 
        agr = {}
        for m, v in c.items():
            cat = mapear_motivo(m)
            agr[cat] = agr.get(cat, 0) + v
        return agr
    
    c_ant_m, c_act_m = agrupar(c_ant), agrupar(c_act)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSTRUIR DATAFRAME WATERFALL
    # ═══════════════════════════════════════════════════════════════════════════
    
    todos = set(c_ant_m.keys()) | set(c_act_m.keys())
    data = []
    
    for mot in todos:
        imp_act = c_act_m.get(mot, 0)
        imp_ant = c_ant_m.get(mot, 0) if usar_comp else 0
        delta = imp_act - imp_ant if usar_comp else 0
        
        if imp_act > 0:
            row = {'Motivo': mot, 'Impacto_Actual': imp_act}
            if usar_comp: 
                row.update({'Impacto_Anterior': imp_ant, 'Delta': delta})
            data.append(row)
    
    df_wf_final = pd.DataFrame(data)
    
    if not df_wf_final.empty:
        # Ordenar: mayor impacto primero, categorías residuales al final
        residuales = ['Otro', 'Otros', 'Outros', 'Sin opinión', 'Não uso ou sem opinião', 'No uso o sin opinión']
        mask_otros = df_wf_final['Motivo'].isin(residuales)
        df_resto = df_wf_final[~mask_otros].sort_values('Impacto_Actual', ascending=False)
        df_otros = df_wf_final[mask_otros]
        df_wf_final = pd.concat([df_resto, df_otros], ignore_index=True)
    
    if verbose:
        print(f"\n📊 TABLA WATERFALL:")
        print(df_wf_final.round(2).to_string(index=False))
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GRÁFICO WATERFALL
    # ═══════════════════════════════════════════════════════════════════════════
    
    fig_waterfall = None
    grafico_waterfall_base64 = None
    grafico_evolucion_quejas_base64 = None
    
    if not df_wf_final.empty:
        fig, ax = plt.subplots(figsize=(14, 7), facecolor='white')
        ax.set_facecolor('white')
        
        labels = [f'NPS\n{q_act}'] + df_wf_final['Motivo'].tolist() + ['Full\nPotential']
        values = [nps_act] + df_wf_final['Impacto_Actual'].tolist() + [0]
        deltas = [None] + (df_wf_final['Delta'].tolist() if usar_comp else [None]*len(df_wf_final)) + [None]
        
        # Primera barra (NPS)
        ax.bar(0, values[0], color='#00a650', width=0.7, edgecolor='white')
        ax.text(0, values[0]/2, f'{values[0]:.1f}', ha='center', va='center', fontweight='bold', fontsize=14, color='white')
        
        # Barras apiladas
        bottom = values[0]
        for i in range(1, len(values)-1):
            mot = labels[i]
            color = COLORES.get(mot, '#95a5a6')
            ax.bar(i, values[i], bottom=bottom, color=color, width=0.7, edgecolor='white', linewidth=1)
            if values[i] > 2:
                tc = 'white' if color not in ['#c8b6ff','#d1d8e0','#ffd93d'] else '#333'
                ax.text(i, bottom + values[i]/2, f'{values[i]:.1f}', ha='center', va='center', fontsize=9, fontweight='600', color=tc)
            if usar_comp and deltas[i] and abs(deltas[i]) >= 0.3:
                dc = '#d63031' if deltas[i] > 0 else '#00b894'
                ax.text(i, bottom + values[i] + 1.5, f'{deltas[i]:+.1f}', ha='center', fontsize=8, fontweight='bold', color=dc,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6e6' if deltas[i]>0 else '#e6fff2', edgecolor='none'))
            bottom += values[i]
        
        # Full Potential
        ax.bar(len(values)-1, 100, color='#ffd93d', width=0.7, alpha=0.85)
        ax.text(len(values)-1, 50, '100', ha='center', va='center', fontweight='bold', fontsize=14, color='#333')
        
        ax.axhline(y=100, color='#ddd', linestyle=':', linewidth=1.5)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('NPS Score', fontsize=11, fontweight='500')
        ax.set_ylim(0, 110)
        ax.set_title(f'{BANDERA} {player_seleccionado} - Waterfall NPS ({q_act})' + (f' vs {q_ant}' if usar_comp else ''), fontsize=14, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.grid(True, alpha=0.2)
        plt.tight_layout()
        
        fig_waterfall = fig
        
        # Nota: Los gráficos se embeben en el HTML como base64, no se guardan como archivos separados
        
        # Guardar como base64 para HTML
        import io
        import base64
        buf_wf = io.BytesIO()
        fig.savefig(buf_wf, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buf_wf.seek(0)
        grafico_waterfall_base64 = base64.b64encode(buf_wf.read()).decode('utf-8')
        buf_wf.close()
        
        plt.close(fig)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GRÁFICO EVOLUCIÓN QUEJAS (últimos 5 quarters)
    # ═══════════════════════════════════════════════════════════════════════════
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"📊 EVOLUCIÓN QUEJAS POR TRIMESTRE (últimos 5Q)")
        print("=" * 60)
    
    # Obtener últimos 5 quarters disponibles
    olas_disp = sorted(df_player[col_periodo].unique())
    ultimos_5q = olas_disp[-5:] if len(olas_disp) >= 5 else olas_disp
    
    if verbose:
        print(f"📅 Quarters disponibles: {olas_disp}")
        print(f"📅 Últimos 5Q para gráfico: {ultimos_5q}")
    
    # Calcular impacto por quarter
    impacto_por_quarter = {}
    quarters_sin_desglose = []
    
    for q in ultimos_5q:
        contrib_q, nps_q, total_q = calc_contrib(df_wf, q)
        
        if total_q == 0:
            if verbose:
                print(f"   ⚠️ {q}: Sin datos")
            continue
        
        # Agrupar por categoría
        contrib_agrupado = {}
        tiene_desglose = False
        
        for motivo_ia, impacto in contrib_q.items():
            if impacto > 0.01:
                categoria = mapear_motivo(motivo_ia)
                contrib_agrupado[categoria] = contrib_agrupado.get(categoria, 0) + impacto
                if categoria not in ['Sin opinión', 'Otro', 'Otros', 'Outros']:
                    tiene_desglose = True
        
        # Si no tiene desglose real, calcular total de quejas
        if not tiene_desglose or len(contrib_agrupado) <= 1:
            df_q_total = df_player[df_player[col_periodo] == q]
            det_q = (df_q_total[col_nps] == -1).sum()
            neu_q = (df_q_total[col_nps] == 0).sum()
            total_quejas = ((det_q * 2) + neu_q) / len(df_q_total) * 100 if len(df_q_total) > 0 else 0
            impacto_por_quarter[q] = {'Sin desglose': total_quejas}
            quarters_sin_desglose.append(q)
            if verbose:
                print(f"   📊 {q}: Sin desglose → Total quejas: {total_quejas:.1f}pp")
        else:
            impacto_por_quarter[q] = contrib_agrupado
            if verbose:
                print(f"   ✅ {q}: {len(contrib_agrupado)} categorías, Total: {sum(contrib_agrupado.values()):.1f}pp")
    
    # Crear DataFrame para el gráfico
    fig_evolucion = None
    df_evolucion = None
    
    if impacto_por_quarter:
        df_plot = pd.DataFrame(impacto_por_quarter).T.fillna(0)
        df_plot = df_plot.reindex([q for q in ultimos_5q if q in df_plot.index])
        
        # === UNIFICAR VARIANTES DE "OTRO" ===
        # Consolidar: Otros, Outros, Other → Otro
        otros_variantes = ['Otros', 'Outros', 'Other', 'otro', 'otros', 'outros']
        cols_otros = [c for c in df_plot.columns if c in otros_variantes]
        if cols_otros:
            if 'Otro' not in df_plot.columns:
                df_plot['Otro'] = 0
            for col in cols_otros:
                df_plot['Otro'] += df_plot[col]
                df_plot = df_plot.drop(columns=[col])
        
        # === UNIFICAR "Promo" → "Promociones" ===
        promo_variantes = ['Promo', 'promo', 'Beneficios', 'beneficios']
        cols_promo = [c for c in df_plot.columns if c in promo_variantes]
        if cols_promo:
            if 'Promociones' not in df_plot.columns:
                df_plot['Promociones'] = 0
            for col in cols_promo:
                df_plot['Promociones'] += df_plot[col]
                df_plot = df_plot.drop(columns=[col])
        
        # Ordenar columnas
        cols_finales = ['Sin opinión', 'Não uso ou sem opinião', 'No uso o sin opinión', 'Otro', 'Sin desglose']
        cols_principales = [c for c in df_plot.mean().sort_values(ascending=False).index if c not in cols_finales]
        cols_orden = cols_principales + [c for c in cols_finales if c in df_plot.columns]
        df_plot = df_plot[[c for c in cols_orden if c in df_plot.columns]]
        
        # Gráfico
        fig2, ax2 = plt.subplots(figsize=(12, 6), facecolor='white')
        ax2.set_facecolor('white')
        x = np.arange(len(df_plot))
        bottom = np.zeros(len(df_plot))
        
        for mot in df_plot.columns:
            vals = df_plot[mot].values
            color = COLORES.get(mot, '#a5b1c2')
            ax2.bar(x, vals, 0.65, bottom=bottom, label=mot, color=color, edgecolor='white', linewidth=1.5)
            for i, (v, b) in enumerate(zip(vals, bottom)):
                if v >= 3:
                    tc = 'white' if mot not in ['Sin opinión', 'Otro', 'Sin desglose'] else '#333'
                    ax2.text(i, b + v/2, f'{v:.0f}%', ha='center', va='center', fontsize=9, fontweight='600', color=tc)
            bottom += vals
        
        # Total arriba de cada barra
        for i, t in enumerate(bottom): 
            ax2.text(i, t + 0.8, f'{t:.0f}%', ha='center', fontsize=11, fontweight='bold', color='#2d3436')
        
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_plot.index, fontsize=11, fontweight='600')
        ax2.set_ylabel('Impacto (pp)', fontsize=11)
        ax2.set_title(f'Evolución de Quejas - {player_seleccionado}', fontsize=13, fontweight='bold', pad=15)
        # Leyenda FUERA del gráfico (a la derecha)
        ax2.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=9, frameon=True, fancybox=True)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.yaxis.grid(True, alpha=0.15)
        ax2.set_ylim(0, max(bottom) * 1.08 if len(bottom) > 0 else 50)
        plt.tight_layout(rect=[0, 0, 0.82, 1])  # Dejar espacio para la leyenda a la derecha
        
        fig_evolucion = fig2
        df_evolucion = df_plot
        
        # Nota: Los gráficos se embeben en el HTML como base64, no se guardan como archivos separados
        
        # Guardar como base64 para HTML
        import io
        import base64
        buf_evol = io.BytesIO()
        fig2.savefig(buf_evol, format='png', dpi=120, bbox_inches='tight', facecolor='white')
        buf_evol.seek(0)
        grafico_evolucion_quejas_base64 = base64.b64encode(buf_evol.read()).decode('utf-8')
        buf_evol.close()
        
        plt.close(fig2)
        
        # Advertencia si hay quarters sin desglose
        if quarters_sin_desglose and verbose:
            print(f"\n⚠️ Quarters sin desglose de motivos: {quarters_sin_desglose}")
            print(f"   Para tener desglose, ejecuta PARTE 4 con esos quarters seleccionados")
    else:
        if verbose:
            print("⚠️ No hay datos para el gráfico de evolución")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXPORTAR
    # ═══════════════════════════════════════════════════════════════════════════
    
    nps_comparativo = {q_ant: nps_ant, q_act: nps_act, 'delta': nps_act - nps_ant} if usar_comp else {q_act: nps_act}
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"✅ PARTE 6 OK")
        print(f"   💾 waterfall_data_comparativo, nps_comparativo, evolucion_quejas_data")
        print("=" * 70)
    
    return {
        'waterfall_data_comparativo': df_wf_final,
        'nps_comparativo': nps_comparativo,
        'evolucion_quejas_data': df_evolucion,
        'fig_waterfall': fig_waterfall,
        'fig_evolucion': fig_evolucion,
        'ultimos_5q': ultimos_5q,
        'grafico_waterfall_base64': grafico_waterfall_base64,
        'grafico_evolucion_quejas_base64': grafico_evolucion_quejas_base64
    }


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    from parte3_calculo_nps import calcular_nps
    from parte4_categorizacion import categorizar_comentarios
    from parte5_correccion_sin_opinion import corregir_sin_opinion
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 6: WATERFALL NPS")
    print("=" * 70)
    
    try:
        # Cargar datos
        resultado_carga = cargar_datos(verbose=False)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        # Calcular NPS
        resultado_nps = calcular_nps(df_completo, config, generar_grafico=False, verbose=False)
        df_player = resultado_nps['df_player']
        
        # Categorizar
        resultado_cat = categorizar_comentarios(df_player, config, resultado_nps, verbose=False)
        
        # Corregir sin opinión
        resultado_p5 = corregir_sin_opinion(resultado_cat, config, verbose=False)
        
        # Generar Waterfall
        resultado_wf = generar_waterfall(resultado_p5, df_player, config, guardar_graficos=True, verbose=True)
        
        print("\n📋 Variables exportadas:")
        for k, v in resultado_wf.items():
            if isinstance(v, pd.DataFrame):
                print(f"   {k}: DataFrame ({len(v)} filas)")
            elif v is None:
                print(f"   {k}: None (gráfico cerrado)")
            else:
                print(f"   {k}: {type(v).__name__}")
        
        print("\n✅ Prueba PARTE 6 completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
