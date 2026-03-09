# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 8: ANÁLISIS DE PRODUCTOS - SHARE, NPS Y EFECTOS
═══════════════════════════════════════════════════════════════════════════════

Analiza el uso de productos, share, NPS por producto y efectos en el NPS global.
Replica EXACTAMENTE el código del notebook original.

Uso:
    from scripts.parte8_productos import analizar_productos
    resultado = analizar_productos(df_completo, df_player, config)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ==============================================================================
# CONFIGURACIÓN MULTISITE - PATRONES DE COLUMNAS DE PRODUCTOS
# ==============================================================================

PATRONES_PRODUCTOS = {
    'MLB': [
        "Para que você usou sua conta nos últimos 30 dias",
        "Para que vocÃª usou sua conta nos Ãºltimos 30 dias"
    ],
    'MLA': [
        "¿Para qué usaste tu cuenta de",
        "Para que usaste tu cuenta",
        "¿Para qué usó su cuenta"
    ],
    'MLM': [
        "¿Para qué usaste tu cuenta de",
        "Para que usaste tu cuenta",
        "¿Para qué usó su cuenta"
    ],
    'MLC': [
        "¿Para qué usaste tu cuenta de",
        "Para que usaste tu cuenta"
    ]
}

EXCLUIR_PATTERNS = ['Outro(s)', 'Otra(s)', 'Otros(s)', 'Otras(s)', 'Outro uso', 'Outra uso', 'Otro uso', 'Otra uso']

NOMBRES_INVALIDOS = [
    'você poderia', 'por favor', 'explique', 'nos contar',
    'para receber os pagamentos', 'fazer compras no mercado livre',
    'podrías', 'explicar', 'contarnos'
]

# ==============================================================================
# PRODUCTOS CLAVE POR SITE (para análisis detallado)
# ==============================================================================

PRODUCTOS_CLAVE = {
    'MLB': {
        'rendimientos': {
            'keywords': ['rendimentos', 'Rendimentos', 'gerar rendimentos', 'saldo em conta'],
            'nombre_display': '💰 RENDIMENTOS',
            'tipo': 'ahorro'
        },
        'inversiones': {
            'keywords': ['investimento', 'Investimentos', 'Poupar', 'cdb', 'fundos', 'ações', 'criptomoedas'],
            'nombre_display': '📈 INVESTIMENTOS',
            'tipo': 'ahorro'
        },
        'creditos': {
            'keywords': ['acesso a crédito', 'Acesso a crédito', 'crédito', 'empréstimo'],
            'nombre_display': '🏦 CRÉDITO',
            'tipo': 'credito'
        },
        'tarjeta_credito': {
            'keywords': ['cartão de crédito', 'Cartão de crédito', 'cartao de credito'],
            'nombre_display': '💳 CARTÃO DE CRÉDITO',
            'tipo': 'credito'
        }
    },
    'MLA': {
        'rendimientos': {
            'keywords': ['rendimiento', 'generar rendimiento', 'saldo en cuenta'],
            'nombre_display': '💰 RENDIMIENTOS',
            'tipo': 'ahorro'
        },
        'inversiones': {
            'keywords': ['inversión', 'inversiones', 'plazo fijo', 'fondos', 'cripto'],
            'nombre_display': '📈 INVERSIONES',
            'tipo': 'ahorro'
        },
        'creditos': {
            'keywords': ['acceso a crédito', 'préstamo'],
            'nombre_display': '🏦 CRÉDITO',
            'tipo': 'credito'
        },
        'tarjeta_credito': {
            'keywords': ['tarjeta de crédito'],
            'nombre_display': '💳 TARJETA DE CRÉDITO',
            'tipo': 'credito'
        }
    },
    'MLM': {
        'rendimientos': {
            'keywords': ['rendimiento', 'Rendimientos', 'generar rendimiento', 'saldo en cuenta'],
            'nombre_display': '💰 RENDIMIENTOS',
            'tipo': 'ahorro'
        },
        'inversiones': {
            'keywords': ['inversión', 'inversiones', 'Inversiones', 'Ahorro/inversión', 'cetes', 'fondos', 'cripto'],
            'nombre_display': '📈 INVERSIONES',
            'tipo': 'ahorro'
        },
        'creditos': {
            'keywords': ['acceso a crédito', 'Acceso a créditos', 'Créditos', 'préstamo'],
            'nombre_display': '🏦 CRÉDITO',
            'tipo': 'credito'
        },
        'tarjeta_credito': {
            'keywords': ['tarjeta de crédito', 'Tarjeta de crédito', 'Tarjeta crédito'],
            'nombre_display': '💳 TARJETA DE CRÉDITO',
            'tipo': 'credito'
        }
    },
    'MLC': {
        'rendimientos': {
            'keywords': ['rendimiento', 'generar rendimiento', 'saldo en cuenta'],
            'nombre_display': '💰 RENDIMIENTOS',
            'tipo': 'ahorro'
        },
        'inversiones': {
            'keywords': ['inversión', 'inversiones', 'fondos', 'cripto'],
            'nombre_display': '📈 INVERSIONES',
            'tipo': 'ahorro'
        },
        'creditos': {
            'keywords': ['acceso a crédito', 'préstamo', 'crédito'],
            'nombre_display': '🏦 CRÉDITO',
            'tipo': 'credito'
        },
        'tarjeta_credito': {
            'keywords': ['tarjeta de crédito'],
            'nombre_display': '💳 TARJETA DE CRÉDITO',
            'tipo': 'credito'
        }
    }
}

# ==============================================================================
# NOMBRES DISPLAY POR SITE
# ==============================================================================

NOMBRES_DISPLAY_MLB = {
    'USO_PAGOS_ONLINE': 'Pagamentos online',
    'USO_TRANSFERENCIAS': 'Transferências',
    'USO_PAGO_BOLETOS': 'Pagar boletos/impostos',
    'USO_CRIPTO': 'Criptomoedas',
    'USO_CREDITO': 'Acesso a crédito',
    'USO_CARTAO_CREDITO': 'Cartão de crédito',
    'USO_SAQUE': 'Sacar dinheiro',
    'USO_RECARGA_CEL': 'Recarga celular',
    'USO_RECARGA_TRANSP': 'Recarga transporte',
    'USO_RECEBER_SALARIO': 'Receber salário',
    'USO_CARTAO_DEBITO': 'Cartão de débito',
    'USO_QR': 'Pagamento QR',
    'USO_POUPANCA': 'Poupar/Investir',
    'USO_SEGUROS': 'Seguros',
    'USO_MOEDA_ESTRANG': 'Moeda estrangeira',
    'USO_INVESTIMENTOS': 'Investimentos',
    'USO_RENDIMENTOS': 'Rendimentos',
    'USO_MERCADOLIVRE': 'Compras no Mercado Livre'
}

NOMBRES_DISPLAY_MLA = {
    'USO_PAGOS_ONLINE': 'Pagos online',
    'USO_TRANSFERENCIAS': 'Transferencias',
    'USO_PAGO_SERVICIOS': 'Pago de servicios',
    'USO_CRIPTO': 'Criptomonedas',
    'USO_ACCESO_CREDITOS': 'Acceso a créditos',
    'USO_CREDITOS': 'Créditos',
    'USO_TARJETA_CREDITO': 'Tarjeta de crédito',
    'USO_EFECTIVO': 'Retiro efectivo',
    'USO_RECARGA_CEL': 'Recarga celular',
    'USO_RECARGA_TRANSP': 'Recarga SUBE',
    'USO_COBRAR_SUELDO': 'Cobrar sueldo',
    'USO_TARJETA_DEBITO': 'Tarjeta de débito',
    'USO_QR': 'Pago con QR',
    'USO_AHORRO_INVERSION': 'Ahorro/inversión',
    'USO_SEGUROS': 'Seguros',
    'USO_MONEDA_EXTRANJ': 'Moneda extranjera',
    'USO_INVERSIONES': 'Inversiones',
    'USO_RENDIMIENTOS': 'Rendimientos',
    'USO_MERCADOLIBRE': 'Compras en Mercado Libre'
}

NOMBRES_DISPLAY_MLM = {
    'USO_PAGO_ONLINE': 'Pago online',
    'USO_TRANSFERENCIAS': 'Transferencias',
    'USO_PAGO_SERVICIOS': 'Pago de servicios',
    'USO_CRIPTO': 'Criptomonedas',
    'USO_ACCESO_CREDITOS': 'Acceso a créditos',
    'USO_TDC': 'Tarjeta de crédito',
    'USO_EFECTIVO': 'Retiro/depósito efectivo',
    'USO_RECARGA_CEL': 'Recarga celular',
    'USO_RECARGA_TRANSP': 'Recarga transporte',
    'USO_COBRAR_SUELDO': 'Cobrar sueldo',
    'USO_TARJETA_DEBITO': 'Tarjeta de débito',
    'USO_QR': 'Pago con QR',
    'USO_AHORRO_INVERSION': 'Ahorro/inversión',
    'USO_SEGUROS': 'Seguros',
    'USO_MONEDA_EXTRANJ': 'Moneda extranjera',
    'USO_REMESAS': 'Remesas',
    'USO_MERCADOLIBRE': 'Compras en Mercado Libre',
    'USO_RENDIMIENTOS': 'Rendimientos',
    'USO_INVERSIONES': 'Inversiones',
    'USO_CREDITOS': 'Créditos',
    'USO_TDC_30D': 'Tarjeta crédito (30 días)'
}

NOMBRES_DISPLAY_MLC = {
    'USO_PAGOS_ONLINE': 'Pagos online',
    'USO_TRANSFERENCIAS': 'Transferencias',
    'USO_PAGO_SERVICIOS': 'Pago de servicios',
    'USO_CRIPTO': 'Criptomonedas',
    'USO_TARJETA_CREDITO': 'Tarjeta de crédito',
    'USO_EFECTIVO': 'Retiro efectivo',
    'USO_RECARGA_CEL': 'Recarga celular',
    'USO_COBRAR_SUELDO': 'Cobrar sueldo',
    'USO_TARJETA_DEBITO': 'Tarjeta de débito',
    'USO_QR': 'Pago con QR',
    'USO_AHORRO_INVERSION': 'Ahorro/inversión',
    'USO_SEGUROS': 'Seguros',
    'USO_MONEDA_EXTRANJ': 'Moneda extranjera',
    'USO_INVERSIONES': 'Inversiones',
    'USO_RENDIMIENTOS': 'Rendimientos',
    'USO_MERCADOLIBRE': 'Compras en Mercado Libre'
}

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def fix_encoding_str(s):
    """Corrige caracteres con encoding corrupto."""
    if not isinstance(s, str):
        return s
    return (s
        .replace('\ufeff', '')
        .replace('Ã§', 'ç').replace('Ã£', 'ã').replace('Ãµ', 'õ')
        .replace('Ã¡', 'á').replace('Ã©', 'é').replace('Ã­', 'í')
        .replace('Ã³', 'ó').replace('Ãº', 'ú').replace('Ãª', 'ê')
        .replace('Ã', 'à').replace('Ã§Ã', 'çõ').replace('Ã§Ã£', 'ção')
    )


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def analizar_productos(df_completo, df_player, config, verbose=True):
    """
    Analiza el uso de productos y su impacto en el NPS.
    
    Args:
        df_completo: DataFrame completo con todas las columnas (incluye USO_*)
        df_player: DataFrame filtrado por player
        config: Diccionario de configuración
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con tabla resumen y análisis de productos clave
    """
    
    site = config['site']
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q1 = config['periodo_1']
    q2 = config['periodo_2']
    
    col_nps = 'NPS'
    col_periodo = 'OLA'
    
    if verbose:
        print("=" * 100)
        print(f"{BANDERA} PARTE 8: ANÁLISE DE PRODUTOS - SHARE, NPS E EFEITOS - {NOMBRE_PAIS}")
        print("=" * 100)
        print(f"\n🎯 Analizando: {player}")
        print(f"📅 Comparando: {q1} vs {q2}")
        print(f"🌍 Site: {site}")
        print("=" * 100)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # IDENTIFICAR Y PREPARAR COLUMNAS DE PRODUCTOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    df_busqueda = df_completo
    
    if verbose:
        print(f"🔍 Buscando columnas de productos en dataframe con {len(df_busqueda.columns)} columnas...")
    
    # Buscar columnas USO_* pre-mapeadas
    product_cols_raw = []
    patron_encontrado = None
    uso_directo = False
    
    uso_cols = [c for c in df_busqueda.columns if c.startswith('USO_') and c not in ['USO_OTROS', 'USO_OUTROS']]
    
    if uso_cols:
        site_nombres = {'MLM': 'México', 'MLB': 'Brasil', 'MLA': 'Argentina', 'MLC': 'Chile'}
        site_nombre = site_nombres.get(site, site)
        if verbose:
            print(f"✅ {site_nombre}: Encontradas {len(uso_cols)} columnas USO_* pre-mapeadas")
        product_cols_raw = uso_cols
        uso_directo = True
        patron_encontrado = 'USO_*'
    
    if not product_cols_raw:
        if verbose:
            print(f"❌ No se encontraron columnas de productos USO_*")
        return {
            'summary': pd.DataFrame(),
            'productos_clave': [],
            'error': 'No se encontraron columnas de productos'
        }
    
    if verbose:
        print(f"\n📦 Productos detectados: {len(product_cols_raw)}")
        print(f"   Usando patrón: '{patron_encontrado}'\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CREAR DATAFRAME CON PRODUCTOS CONVERTIDOS A BINARIO
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Filtrar df_completo por player
    df_productos = df_completo[df_completo['MARCA'] == player].copy()
    
    # Seleccionar mapeo según site
    NOMBRES_DISPLAY_POR_SITE = {
        'MLM': NOMBRES_DISPLAY_MLM,
        'MLB': NOMBRES_DISPLAY_MLB,
        'MLA': NOMBRES_DISPLAY_MLA,
        'MLC': NOMBRES_DISPLAY_MLC,
    }
    nombres_display = NOMBRES_DISPLAY_POR_SITE.get(site, NOMBRES_DISPLAY_MLA)
    
    mapeo_productos = {}
    VALORES_SI = ['Si', 'Sí', 'Sim', '1', 1, 'sim', 'SIM', 'SI', 'sí']
    VALORES_NO = ['No', 'Não', 'NÃ£o', '0', 0, 'no', 'NO', 'não', 'NAO', ' ']
    
    if verbose:
        print(f"📦 Usando columnas USO_* pre-mapeadas de {NOMBRE_PAIS}")
    
    for col in product_cols_raw:
        nombre_display = nombres_display.get(col, col.replace('USO_', '').replace('_', ' ').title())
        mapeo_productos[col] = nombre_display
        
        if col in df_productos.columns:
            valores_unicos = df_productos[col].dropna().unique()
            tiene_si_no = any(str(v).strip() in VALORES_SI + VALORES_NO for v in valores_unicos)
            
            if tiene_si_no or df_productos[col].dtype == 'object':
                df_productos[col] = df_productos[col].apply(
                    lambda x: 1 if str(x).strip() in VALORES_SI else 0
                )
    
    product_cols = list(mapeo_productos.keys())
    
    # Verificar conversión
    convertidos = 0
    for col in product_cols:
        if col in df_productos.columns:
            suma = df_productos[col].sum()
            if suma > 0:
                convertidos += 1
    
    if verbose:
        print(f"✅ {convertidos} productos con datos (de {len(product_cols)} columnas)")
        print(f"✅ {len(product_cols)} productos convertidos a binario")
        print(f"\nProductos analizados:")
        for i, (col, nombre) in enumerate(list(mapeo_productos.items())[:10], 1):
            print(f"   {i:2d}. {nombre}")
        if len(mapeo_productos) > 10:
            print(f"   ... y {len(mapeo_productos)-10} más\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULAR MÉTRICAS
    # ═══════════════════════════════════════════════════════════════════════════
    
    df_q1 = df_productos[df_productos[col_periodo] == q1].copy()
    df_q2 = df_productos[df_productos[col_periodo] == q2].copy()
    
    total_q1 = len(df_q1)
    total_q2 = len(df_q2)
    
    if verbose:
        print(f"📊 Registros por período:")
        print(f"   • {q1}: {total_q1:,} usuarios")
        print(f"   • {q2}: {total_q2:,} usuarios\n")
    
    if total_q1 == 0 or total_q2 == 0:
        return {
            'summary': pd.DataFrame(),
            'productos_clave': [],
            'error': 'No hay datos suficientes para comparar períodos'
        }
    
    # Share (% que usa cada producto)
    share_q1 = {}
    share_q2 = {}
    nps_users_q1 = {}
    nps_users_q2 = {}
    nps_nousers_q1 = {}
    nps_nousers_q2 = {}
    
    for col in product_cols:
        if col not in df_q1.columns or col not in df_q2.columns:
            continue
        
        # Share
        share_q1[col] = df_q1[col].sum() / total_q1 * 100 if total_q1 > 0 else 0
        share_q2[col] = df_q2[col].sum() / total_q2 * 100 if total_q2 > 0 else 0
        
        # NPS usuarios Q1
        users_q1 = df_q1[df_q1[col] == 1][col_nps].mean() * 100 if (df_q1[col] == 1).any() else 0
        nousers_q1 = df_q1[df_q1[col] == 0][col_nps].mean() * 100 if (df_q1[col] == 0).any() else 0
        nps_users_q1[col] = users_q1
        nps_nousers_q1[col] = nousers_q1
        
        # NPS usuarios Q2
        users_q2 = df_q2[df_q2[col] == 1][col_nps].mean() * 100 if (df_q2[col] == 1).any() else 0
        nousers_q2 = df_q2[df_q2[col] == 0][col_nps].mean() * 100 if (df_q2[col] == 0).any() else 0
        nps_users_q2[col] = users_q2
        nps_nousers_q2[col] = nousers_q2
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSTRUIR TABLA FINAL
    # ═══════════════════════════════════════════════════════════════════════════
    
    lbl_producto = 'Produto' if site == 'MLB' else 'Producto'
    lbl_nps_usuario = 'NPS Usuário' if site == 'MLB' else 'NPS Usuario'
    lbl_nps_no_usuario = 'NPS No Usuário' if site == 'MLB' else 'NPS No Usuario'
    
    valid_cols = [col for col in product_cols if col in share_q1]
    
    summary = pd.DataFrame({
        lbl_producto: [mapeo_productos[col] for col in valid_cols],
        f'Share {q1}': [share_q1[col] for col in valid_cols],
        f'Share {q2}': [share_q2[col] for col in valid_cols],
        f'{lbl_nps_usuario} {q1}': [nps_users_q1[col] for col in valid_cols],
        f'{lbl_nps_usuario} {q2}': [nps_users_q2[col] for col in valid_cols],
        f'{lbl_nps_no_usuario} {q1}': [nps_nousers_q1[col] for col in valid_cols],
        f'{lbl_nps_no_usuario} {q2}': [nps_nousers_q2[col] for col in valid_cols],
        f'Lift {q1}': [nps_users_q1[col] - nps_nousers_q1[col] for col in valid_cols],
        f'Lift {q2}': [nps_users_q2[col] - nps_nousers_q2[col] for col in valid_cols],
    })
    
    # Redondear
    for col in summary.columns:
        if col != lbl_producto:
            summary[col] = summary[col].round(1)
    
    # Calcular deltas
    summary['Δ Share'] = (summary[f'Share {q2}'] - summary[f'Share {q1}']).round(1)
    summary[f'Δ {lbl_nps_usuario}'] = (summary[f'{lbl_nps_usuario} {q2}'] - summary[f'{lbl_nps_usuario} {q1}']).round(1)
    summary['Δ Lift'] = (summary[f'Lift {q2}'] - summary[f'Lift {q1}']).round(1)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULAR EFECTOS (MÉTODO CON LIFT)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Mix Effect = Δ Share × Lift / 100
    summary['Mix Effect'] = (summary['Δ Share'] * summary[f'Lift {q2}'] / 100).round(2)
    
    # NPS Effect = Share Q2 × Δ NPS Usuario / 100
    summary['NPS Effect'] = (summary[f'Share {q2}'] * summary[f'Δ {lbl_nps_usuario}'] / 100).round(2)
    
    # Total Effect
    summary['Total Effect'] = (summary['Mix Effect'] + summary['NPS Effect']).round(2)
    
    # Filtrar productos válidos
    mask_valido = (
        (summary[f'Share {q2}'] >= 1.0) &
        (summary[f'Share {q2}'] < 95.0) &
        (~summary[lbl_producto].str.lower().str.contains('|'.join(NOMBRES_INVALIDOS), na=False, regex=True))
    )

    summary_filtrado = summary[mask_valido].copy()
    summary_filtrado = summary_filtrado.sort_values(f'Share {q2}', ascending=False).reset_index(drop=True)

    # Si sigue vacío con 1%, usar summary completo sin filtro de share (evitar HTML sin productos)
    if summary_filtrado.empty:
        mask_minimo = (
            (summary[f'Share {q2}'] > 0) &
            (summary[f'Share {q2}'] < 95.0) &
            (~summary[lbl_producto].str.lower().str.contains('|'.join(NOMBRES_INVALIDOS), na=False, regex=True))
        )
        summary_filtrado = summary[mask_minimo].copy()
        summary_filtrado = summary_filtrado.sort_values(f'Share {q2}', ascending=False).reset_index(drop=True)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDACIÓN NPS GLOBAL
    # ═══════════════════════════════════════════════════════════════════════════
    
    nps_q1_global = df_q1[col_nps].mean() * 100 if len(df_q1) > 0 else 0
    nps_q2_global = df_q2[col_nps].mean() * 100 if len(df_q2) > 0 else 0
    delta_nps_global = nps_q2_global - nps_q1_global
    
    suma_mix = summary_filtrado['Mix Effect'].sum()
    suma_nps_eff = summary_filtrado['NPS Effect'].sum()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY
    # ═══════════════════════════════════════════════════════════════════════════
    
    if verbose and not summary_filtrado.empty:
        print("=" * 100)
        print(f"  {BANDERA} ANÁLISIS DE PRODUCTOS - {player} ({q1} vs {q2})")
        print("=" * 100)
        
        # Mostrar tabla compacta
        display_cols = [
            lbl_producto,
            f'Share {q2}', 'Δ Share',
            f'{lbl_nps_usuario} {q2}', f'Δ {lbl_nps_usuario}',
            f'Lift {q2}',
            'Mix Effect', 'NPS Effect', 'Total Effect'
        ]
        
        tabla_display = summary_filtrado[display_cols].head(15)
        print(f"\n📊 TOP 15 PRODUCTOS POR SHARE:\n")
        print(tabla_display.to_string(index=False))
        
        # Resumen ejecutivo
        print(f"\n{'='*100}")
        print(f"  📈 RESUMEN EJECUTIVO")
        print("=" * 100)
        
        print(f"\n  NPS Global {player}:")
        print(f"    • {q1}: {nps_q1_global:>5.1f}")
        print(f"    • {q2}: {nps_q2_global:>5.1f}")
        print(f"    • Δ:    {delta_nps_global:>5.1f} p.p.\n")
        
        print(f"  Explicación del Δ NPS por Productos (Método con Lift):")
        print(f"    • Σ Mix Effect:   {suma_mix:>6.2f} p.p.  (Δ Share × Lift)")
        print(f"    • Σ NPS Effect:   {suma_nps_eff:>6.2f} p.p.  (Share × Δ NPS Usuario)")
        print(f"    • TOTAL:          {suma_mix + suma_nps_eff:>6.2f} p.p.")
        print(f"    • Δ NPS Real:     {delta_nps_global:>6.1f} p.p.\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ANÁLISIS DE PRODUCTOS CLAVE
    # ═══════════════════════════════════════════════════════════════════════════
    
    productos_clave_config = PRODUCTOS_CLAVE.get(site, PRODUCTOS_CLAVE['MLA'])
    productos_clave_encontrados = {}
    
    for clave, cfg in productos_clave_config.items():
        for _, row in summary_filtrado.iterrows():
            producto_lower = row[lbl_producto].lower()
            if any(kw.lower() in producto_lower for kw in cfg['keywords']):
                productos_clave_encontrados[clave] = {
                    'nombre_original': row[lbl_producto],
                    'nombre_display': cfg['nombre_display'],
                    'tipo': cfg['tipo'],
                    'share_q1': row[f'Share {q1}'],
                    'share_q2': row[f'Share {q2}'],
                    'delta_share': row['Δ Share'],
                    'nps_usuario_q1': row[f'{lbl_nps_usuario} {q1}'],
                    'nps_usuario_q2': row[f'{lbl_nps_usuario} {q2}'],
                    'delta_nps_usuario': row[f'Δ {lbl_nps_usuario}'],
                    'lift_q1': row[f'Lift {q1}'],
                    'lift_q2': row[f'Lift {q2}'],
                    'delta_lift': row['Δ Lift'],
                    'mix_effect': row['Mix Effect'],
                    'nps_effect': row['NPS Effect'],
                    'total_effect': row['Total Effect']
                }
                break

    # Fallback: si ningun keyword matcheo, tomar top 3 productos por share
    if not productos_clave_encontrados and not summary_filtrado.empty:
        tipos_fallback = ['ahorro', 'credito', 'ahorro']
        for i, (_, row) in enumerate(summary_filtrado.head(3).iterrows()):
            clave_fb = f'producto_{i+1}'
            nombre = row[lbl_producto]
            productos_clave_encontrados[clave_fb] = {
                'nombre_original': nombre,
                'nombre_display': nombre,
                'tipo': tipos_fallback[i % 2],
                'share_q1': row.get(f'Share {q1}', 0),
                'share_q2': row.get(f'Share {q2}', 0),
                'delta_share': row.get('Δ Share', 0),
                'nps_usuario_q1': row.get(f'{lbl_nps_usuario} {q1}', 0),
                'nps_usuario_q2': row.get(f'{lbl_nps_usuario} {q2}', 0),
                'delta_nps_usuario': row.get(f'Δ {lbl_nps_usuario}', 0),
                'lift_q1': row.get(f'Lift {q1}', 0),
                'lift_q2': row.get(f'Lift {q2}', 0),
                'delta_lift': row.get('Δ Lift', 0),
                'mix_effect': row.get('Mix Effect', 0),
                'nps_effect': row.get('NPS Effect', 0),
                'total_effect': row.get('Total Effect', 0),
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # HISTÓRICO DE PRODUCTOS CLAVE (últimos 5 quarters)
    # ═══════════════════════════════════════════════════════════════════════════
    
    olas_disponibles = sorted(df_productos[col_periodo].dropna().unique())
    ultimos_5q = olas_disponibles[-5:] if len(olas_disponibles) >= 5 else olas_disponibles
    
    if verbose:
        print(f"\n📅 Calculando histórico de productos clave...")
        print(f"   Quarters disponibles: {olas_disponibles}")
        print(f"   Últimos 5Q: {ultimos_5q}")
    
    for clave, prod_info in productos_clave_encontrados.items():
        # Find the original USO_ column for this product
        col_uso = None
        nombre_orig = prod_info['nombre_original']
        for col_raw, nombre_mapped in mapeo_productos.items():
            if nombre_mapped == nombre_orig:
                col_uso = col_raw
                break
        
        historico_share = []
        historico_nps = []
        historico_quarters = []
        
        if col_uso and col_uso in df_productos.columns:
            for q in ultimos_5q:
                df_q = df_productos[df_productos[col_periodo] == q]
                total_q = len(df_q)
                if total_q == 0:
                    continue
                
                # Share = % de usuarios que usan el producto
                share = df_q[col_uso].sum() / total_q * 100 if total_q > 0 else 0
                
                # NPS usuario = NPS promedio de quienes usan el producto
                usuarios = df_q[df_q[col_uso] == 1]
                nps_u = usuarios[col_nps].mean() * 100 if len(usuarios) > 0 else 0
                
                historico_quarters.append(str(q))
                historico_share.append(round(share, 1))
                historico_nps.append(round(nps_u, 1))
        
        prod_info['historico'] = {
            'quarters': historico_quarters,
            'share': historico_share,
            'nps_usuario': historico_nps
        }
        
        if verbose and historico_quarters:
            print(f"   {prod_info['nombre_display']}: {len(historico_quarters)}Q de data")
            for i, q in enumerate(historico_quarters):
                print(f"      {q}: Share {historico_share[i]:.1f}% | NPS {historico_nps[i]:.1f}")
    
    # Generar análisis
    analisis_productos_clave = []
    
    for clave, data in productos_clave_encontrados.items():
        # Estado
        if data['total_effect'] > 0.3:
            estado, emoji_estado = 'POSITIVO', '🟢'
        elif data['total_effect'] < -0.3:
            estado, emoji_estado = 'NEGATIVO', '🔴'
        else:
            estado, emoji_estado = 'NEUTRAL', '⚪'
        
        # Tendencias
        tendencia_uso = 'CRECIENDO' if data['delta_share'] > 0.5 else ('CAYENDO' if data['delta_share'] < -0.5 else 'ESTABLE')
        tendencia_satisfaccion = 'MEJORANDO' if data['delta_nps_usuario'] > 2 else ('EMPEORANDO' if data['delta_nps_usuario'] < -2 else 'ESTABLE')
        
        # Explicación
        explicacion_parts = []
        if abs(data['delta_share']) >= 0.5:
            if data['delta_share'] > 0:
                explicacion_parts.append(f"Ganó +{data['delta_share']:.1f}pp usuarios con Lift {data['lift_q2']:+.0f} → Mix: {data['mix_effect']:+.2f}pp")
            else:
                explicacion_parts.append(f"Perdió {abs(data['delta_share']):.1f}pp usuarios con Lift {data['lift_q2']:+.0f} → Mix: {data['mix_effect']:+.2f}pp")
        
        if abs(data['delta_nps_usuario']) >= 1:
            if data['delta_nps_usuario'] > 0:
                explicacion_parts.append(f"NPS usuarios subió +{data['delta_nps_usuario']:.1f}pp → NPS Effect: {data['nps_effect']:+.2f}pp")
            else:
                explicacion_parts.append(f"NPS usuarios cayó {data['delta_nps_usuario']:.1f}pp → NPS Effect: {data['nps_effect']:+.2f}pp")
        
        explicacion = " | ".join(explicacion_parts) if explicacion_parts else f"Cambios menores (Total: {data['total_effect']:+.2f}pp)"
        
        analisis = {
            **data,
            'clave': clave,
            'estado': estado,
            'emoji_estado': emoji_estado,
            'tendencia_uso': tendencia_uso,
            'tendencia_satisfaccion': tendencia_satisfaccion,
            'explicacion': explicacion
        }
        analisis_productos_clave.append(analisis)
        
        if verbose:
            print(f"\n{data['nombre_display']} {emoji_estado}")
            print(f"   Producto: {data['nombre_original']}")
            print(f"   ┌─────────────────────────────────────────────────────────")
            print(f"   │ Share:       {data['share_q1']:>5.1f}% → {data['share_q2']:>5.1f}%  (Δ {data['delta_share']:+.1f}pp) {tendencia_uso}")
            print(f"   │ NPS Usuario: {data['nps_usuario_q1']:>5.1f} → {data['nps_usuario_q2']:>5.1f}   (Δ {data['delta_nps_usuario']:+.1f}pp) {tendencia_satisfaccion}")
            print(f"   │ Lift:        {data['lift_q1']:>5.1f} → {data['lift_q2']:>5.1f}   (Δ {data['delta_lift']:+.1f}pp)")
            print(f"   ├─────────────────────────────────────────────────────────")
            print(f"   │ Mix Effect:  {data['mix_effect']:+.2f}pp  (Δ Share × Lift)")
            print(f"   │ NPS Effect:  {data['nps_effect']:+.2f}pp  (Share × Δ NPS Usuario)")
            print(f"   │ ═══════════════════════════════════")
            print(f"   │ TOTAL:       {data['total_effect']:+.2f}pp")
            print(f"   └─────────────────────────────────────────────────────────")
            print(f"   📝 {explicacion}")
    
    # Resumen productos clave
    if verbose and analisis_productos_clave:
        productos_ahorro = [p for p in analisis_productos_clave if p['tipo'] == 'ahorro']
        productos_credito = [p for p in analisis_productos_clave if p['tipo'] == 'credito']
        
        total_ahorro = sum(p['total_effect'] for p in productos_ahorro)
        total_credito = sum(p['total_effect'] for p in productos_credito)
        total_effect_clave = sum(p['total_effect'] for p in analisis_productos_clave)
        total_explicado = suma_mix + suma_nps_eff
        gap = delta_nps_global - total_explicado
        
        lbl_ahorro = 'Poupança (Rendimentos + Investimentos)' if site == 'MLB' else 'Ahorro (Rendimientos + Inversiones)'
        lbl_credito = 'Crédito (Crédito + Cartão)' if site == 'MLB' else 'Crédito (Créditos + Tarjeta)'
        
        print(f"\n{'─'*70}")
        print(f"📊 RESUMEN PRODUCTOS CLAVE (Método con Lift):")
        print(f"\n   💰 {lbl_ahorro}: {total_ahorro:+.2f}pp")
        print(f"   🏦 {lbl_credito}:        {total_credito:+.2f}pp")
        print(f"   ────────────────────────────────────────")
        print(f"   📈 TOTAL PRODUCTOS CLAVE:             {total_effect_clave:+.2f}pp")
        print(f"   📈 TOTAL TODOS LOS PRODUCTOS:         {total_explicado:+.2f}pp")
        print(f"   📈 Δ NPS REAL:                        {delta_nps_global:+.1f}pp")
        
        if total_credito < -0.5:
            print(f"\n🚨 ALERTA: Productos de CRÉDITO restan {abs(total_credito):.2f}pp al NPS")
        if total_ahorro > 0.3:
            print(f"✅ BRIGHT SPOT: Productos de AHORRO suman {total_ahorro:+.2f}pp al NPS")
        
        if abs(gap) > 1:
            print(f"\n🔍 GAP: Δ NPS Real ({delta_nps_global:+.1f}pp) vs Explicado ({total_explicado:+.2f}pp) = {gap:+.2f}pp sin explicar")
        
        print(f"\n{'='*100}")
        print(f"✅ PARTE 8 OK - {len(summary_filtrado)} productos analizados")
        print("=" * 100)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # TODOS LOS PRODUCTOS (para tabla completa)
    # ═══════════════════════════════════════════════════════════════════════════
    
    productos_todos = []
    for _, row in summary_filtrado.iterrows():
        productos_todos.append({
            'nombre_original': row[lbl_producto],
            'share_q1': row[f'Share {q1}'],
            'share_q2': row[f'Share {q2}'],
            'delta_share': row['Δ Share'],
            'nps_usuario_q1': row[f'{lbl_nps_usuario} {q1}'],
            'nps_usuario_q2': row[f'{lbl_nps_usuario} {q2}'],
            'delta_nps_usuario': row[f'Δ {lbl_nps_usuario}'],
            'lift_q1': row[f'Lift {q1}'],
            'lift_q2': row[f'Lift {q2}'],
            'delta_lift': row['Δ Lift'],
            'mix_effect': row['Mix Effect'],
            'nps_effect': row['NPS Effect'],
            'total_effect': row['Total Effect']
        })
    
    return {
        'summary': summary_filtrado,
        'productos_clave': analisis_productos_clave,
        'productos_todos': productos_todos,  # TODOS los productos
        'nps_q1_global': nps_q1_global,
        'nps_q2_global': nps_q2_global,
        'delta_nps_global': delta_nps_global,
        'suma_mix_effect': suma_mix,
        'suma_nps_effect': suma_nps_eff,
        'total_explicado': suma_mix + suma_nps_eff
    }


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 8: ANÁLISIS DE PRODUCTOS")
    print("=" * 70)
    
    try:
        resultado_carga = cargar_datos(verbose=False)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        player = config['player']
        df_player = df_completo[df_completo['MARCA'] == player].copy()
        
        resultado_8 = analizar_productos(df_completo, df_player, config, verbose=True)
        
        print("\n📋 Variables exportadas:")
        print(f"   summary: {len(resultado_8['summary'])} productos")
        print(f"   productos_clave: {len(resultado_8['productos_clave'])} productos clave")
        
        print("\n✅ Prueba PARTE 8 completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
