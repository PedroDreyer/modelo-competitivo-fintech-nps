# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 5: CORRECCIÓN "Sin opinión" → Motivo Declarado
═══════════════════════════════════════════════════════════════════════════════

Para players que usaron IA (Mercado Pago, Nubank), reemplaza "Sin opinión" 
con el motivo declarado original si existe y es válido.

Replica EXACTAMENTE el código del notebook original.

Uso:
    from scripts.parte5_correccion_sin_opinion import corregir_sin_opinion
    resultado = corregir_sin_opinion(resultado_parte4, config)
"""

import pandas as pd
import unicodedata

# ==============================================================================
# PLAYERS QUE REQUIEREN CORRECCIÓN (usaron IA en Parte 4)
# ==============================================================================

PLAYERS_CON_IA = ['Mercado Pago', 'Nubank']

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def normalizar(t):
    """Normalizar texto para comparación"""
    if pd.isna(t): 
        return ""
    t = unicodedata.normalize('NFD', str(t).lower().strip())
    return ''.join(c for c in t if unicodedata.category(c) != 'Mn')

# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def corregir_sin_opinion(resultado_parte4, config, verbose=True):
    """
    Corrige registros con "Sin opinión" usando el motivo declarado.
    
    Solo aplica a players que usaron IA (Mercado Pago, Nubank).
    Para otros players, simplemente pasa los datos sin modificar.
    
    Args:
        resultado_parte4: Diccionario con df_final_categorizado de PARTE 4
        config: Diccionario de configuración
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con df_final_categorizado actualizado
    """
    
    # Extraer configuración
    site = config['site']
    player_seleccionado = config['player']
    BANDERA = config['site_bandera']
    col_nps = 'NPS'
    
    # Patrón según idioma
    PATRON_SIN_OPINION = 'nao uso|sem opiniao' if site == 'MLB' else 'no uso|sin opinion'
    
    if verbose:
        print("=" * 70)
        print(f"{BANDERA} PARTE 5: CORRECCIÓN 'Sin opinión' - {player_seleccionado}")
        print("=" * 70)
    
    # Verificar si aplica
    if player_seleccionado not in PLAYERS_CON_IA:
        if verbose:
            print(f"\n⏭️ SALTANDO - {player_seleccionado} usa motivo declarado desde Parte 4")
            print(f"\n{'='*70}")
            print(f"✅ PARTE 5 OK")
            print("=" * 70)
        return resultado_parte4
    
    # Obtener DataFrame
    df = resultado_parte4['df_final_categorizado'].copy()
    
    if verbose:
        print(f"✅ Cargado: {len(df):,} registros")
    
    # Detectar columnas motivo declarado
    col_detra, col_neutro = None, None
    
    for c in df.columns:
        cl = c.lower()
        
        # Español
        if 'motivo' in cl and 'detra' in cl and 'outro' not in cl: 
            col_detra = c
        if 'motivo' in cl and 'neutro' in cl and 'outro' not in cl: 
            col_neutro = c
        if 'por qué nos diste' in cl or 'motivo principal' in cl: 
            col_detra = c
        
        # Portugués
        if 'por qual motivo' in cl and 'classificou' in cl and not c.endswith('2'): 
            col_detra = c
        if 'precisa melhorar' in cl: 
            col_neutro = c
    
    if verbose:
        print(f"📋 Col detractores: {col_detra[:50] if col_detra else None}...")
        print(f"📋 Col neutros: {col_neutro[:50] if col_neutro else None}...")
    
    # Buscar "sin opinión"
    df['_norm'] = df['MOTIVO_IA'].apply(normalizar)
    mascara = df['_norm'].str.contains(PATRON_SIN_OPINION, case=False, na=False)
    total = mascara.sum()
    
    if verbose:
        print(f"\n📊 'Sin opinión': {total} ({total/len(df)*100:.1f}%)")
    
    if total == 0:
        if verbose:
            print("✅ Nada que corregir")
    else:
        corregidos = 0
        
        for idx in df[mascara].index:
            row = df.loc[idx]
            motivo = None
            
            # Obtener motivo declarado según tipo de usuario
            if row[col_nps] == -1 and col_detra: 
                motivo = row.get(col_detra)
            elif row[col_nps] == 0 and col_neutro: 
                motivo = row.get(col_neutro)
            
            if motivo and pd.notna(motivo):
                m_str = str(motivo).strip()
                m_norm = normalizar(m_str)
                
                # Verificar que el motivo es válido y no es también "sin opinión"
                patron_check = PATRON_SIN_OPINION.split('|')[0]
                if m_str and m_str not in ['', '.', 'nan', 'None'] and patron_check not in m_norm:
                    df.loc[idx, 'MOTIVO_IA'] = m_str
                    corregidos += 1
        
        if verbose:
            print(f"✅ Corregidos: {corregidos} de {total}")
        
        # Verificar restantes
        df['_norm'] = df['MOTIVO_IA'].apply(normalizar)
        nuevo = df['_norm'].str.contains(PATRON_SIN_OPINION, case=False, na=False).sum()
        
        if verbose:
            print(f"📊 'Sin opinión' restantes: {nuevo} ({nuevo/len(df)*100:.1f}%)")
            
            print(f"\n📊 Nueva distribución:")
            for m, c in df['MOTIVO_IA'].value_counts().head(10).items():
                print(f"   • {str(m)[:45]}: {c} ({c/len(df)*100:.1f}%)")
    
    # Limpiar columna temporal
    df.drop('_norm', axis=1, inplace=True)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"✅ PARTE 5 OK")
        print("=" * 70)
    
    # Actualizar resultado
    resultado_actualizado = resultado_parte4.copy()
    resultado_actualizado['df_final_categorizado'] = df
    
    return resultado_actualizado


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    from parte3_calculo_nps import calcular_nps
    from parte4_categorizacion import categorizar_comentarios
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 5: CORRECCIÓN 'Sin opinión'")
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
        resultado_corregido = corregir_sin_opinion(resultado_cat, config, verbose=True)
        
        print("\n✅ Prueba PARTE 5 completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
