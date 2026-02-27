# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 1: CARGA DUAL - BASE COMPLETA + BASE CON SALDO - MULTISITE
═══════════════════════════════════════════════════════════════════════════════

Este script replica EXACTAMENTE la lógica del notebook original:
1. Carga SOLO columnas específicas por índice (optimización memoria)
2. Renombra columnas con nombres estándar
3. Filtra usuarios CON SALDO (variable principal)
4. Exporta df_completo, df_competitivo, df_competitivo_saldo

Uso:
    from scripts.parte1_carga_datos import cargar_datos
    resultados = cargar_datos()
"""

import pandas as pd
import numpy as np
import yaml
import gc
from pathlib import Path
from validators import (
    validate_required_columns,
    validate_dataframe_not_empty,
    validate_csv_encoding,
    validate_site_code
)

# ==============================================================================
# CONFIGURACIÓN DE RUTAS
# ==============================================================================

def obtener_ruta_base():
    """Obtiene la ruta base del proyecto MODELO_FINAL_CURSOR"""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent

RUTA_BASE = obtener_ruta_base()
RUTA_CONFIG = RUTA_BASE / "config" / "config.yaml"
RUTA_DATA = RUTA_BASE / "data"
RUTA_OUTPUTS = RUTA_BASE / "outputs"

# ==============================================================================
# MAPEOS POR SITE - Columnas específicas para optimizar memoria
# ==============================================================================

# BRASIL (MLB) - 333 columnas originales → ~45 necesarias
COLS_NECESARIAS_MLB = [
    0, 1, 2, 3, 4, 5, 6,  # ID, OLA, GÉNERO, EDAD, ESTADO, REGIÓN, NSE
    12,  # TIENE_SALDO
    33, 34,  # MARCA, NPS
    36, 37, 38, 39,  # MOTIVOS (detra, neutro, prom, comentario)
    42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60,  # PRODUCTOS (19)
    119,  # ANTIGUEDAD
    120, 124,  # SEGURIDAD
    217, 227  # FLAG_PRINCIPALIDAD, MOTIVO_PRINCIPALIDAD
]

NOMBRES_COLUMNAS_MLB = {
    0: 'ID', 1: 'OLA', 2: 'GENERO', 3: 'EDAD', 4: 'ESTADO', 5: 'REGION', 6: 'NSE',
    12: 'TIENE_SALDO',
    33: 'MARCA', 34: 'NPS',
    36: 'MOTIVO_DETRA', 37: 'MOTIVO_NEUTRO', 38: 'MOTIVO_PROM', 39: 'COMENTARIO',
    42: 'USO_PAGOS_ONLINE', 43: 'USO_TRANSFERENCIAS', 44: 'USO_PAGO_BOLETOS',
    45: 'USO_CRIPTO', 46: 'USO_CREDITO', 47: 'USO_CARTAO_CREDITO',
    48: 'USO_SAQUE', 49: 'USO_RECARGA_CEL', 50: 'USO_RECARGA_TRANSP',
    51: 'USO_RECEBER_SALARIO', 52: 'USO_CARTAO_DEBITO', 53: 'USO_QR',
    54: 'USO_POUPANCA', 55: 'USO_SEGUROS', 56: 'USO_MOEDA_ESTRANG',
    57: 'USO_INVESTIMENTOS', 58: 'USO_RENDIMENTOS', 59: 'USO_MERCADOLIVRE', 60: 'USO_OUTROS',
    119: 'ANTIGUEDAD',
    120: 'VALORACION_SEGURIDAD', 124: 'MOTIVO_INSEGURIDAD',
    217: 'FLAG_PRINCIPALIDAD', 227: 'MOTIVO_PRINCIPALIDAD'
}

# ARGENTINA (MLA) - 494 columnas originales (26Q1) → ~47 necesarias
# Indices verificados contra header de codigos del CSV (fila 2)
COLS_NECESARIAS_MLA = [
    0, 1, 2, 3, 5, 7,  # ID, OLA, GÉNERO, EDAD, PROVINCIA, NSE
    13,  # TIENE_SALDO (P3)
    19, 20,  # MARCA (PAGO), NPS
    22, 24, 26,  # MOTIVOS (P6=detra, P7=neutro, P8=promo)
    28,  # COMENTARIO (Comentarios)
    38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,  # PRODUCTOS (P10#1..P10#98, 22 cols)
    78,  # ANTIGUEDAD (P11)
    122,  # MOTIVO_PRINCIPALIDAD (P14A)
    158,  # VALORACION_SEGURIDAD (A2)
    198,  # MOTIVO_INSEGURIDAD (A20A)
    367  # FLAG_PRINCIPALIDAD
]

NOMBRES_COLUMNAS_MLA = {
    0: 'ID', 1: 'OLA', 2: 'GENERO', 3: 'EDAD', 5: 'ESTADO', 7: 'NSE',
    13: 'TIENE_SALDO',
    19: 'MARCA', 20: 'NPS',
    22: 'MOTIVO_DETRA', 24: 'MOTIVO_NEUTRO', 26: 'MOTIVO_PROM',
    28: 'COMENTARIO',
    38: 'USO_PAGOS_ONLINE', 39: 'USO_TRANSFERENCIAS', 40: 'USO_PAGO_SERVICIOS',
    41: 'USO_CRIPTO', 42: 'USO_ACCESO_CREDITOS', 43: 'USO_CREDITOS',
    44: 'USO_TARJETA_CREDITO', 45: 'USO_EFECTIVO', 46: 'USO_RECARGA_CEL',
    47: 'USO_RECARGA_TRANSP', 48: 'USO_COBRAR_SUELDO', 49: 'USO_TARJETA_DEBITO',
    50: 'USO_QR', 51: 'USO_AHORRO_INVERSION', 52: 'USO_SEGUROS',
    53: 'USO_MONEDA_EXTRANJ', 54: 'USO_INVERSIONES', 55: 'USO_RENDIMIENTOS',
    56: 'USO_MERCADOLIBRE', 57: 'USO_FRASCOS', 58: 'USO_RESERVAS', 59: 'USO_OTROS',
    78: 'ANTIGUEDAD',
    122: 'MOTIVO_PRINCIPALIDAD',
    158: 'VALORACION_SEGURIDAD',
    198: 'MOTIVO_INSEGURIDAD',
    367: 'FLAG_PRINCIPALIDAD',
}

# MÉXICO (MLM) - Mapeo completo
COLS_NECESARIAS_MLM = [
    0, 1, 2, 3, 4, 5, 11, 13, 14, 16, 18, 20, 22,
    23, 24, 25, 26, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,  # Quitado 27 (créditos viejo)
    43, 63, 68, 72, 87, 94, 236, 264  # 87 = USO_CREDITOS (columna CJ, correcta)
]

NOMBRES_COLUMNAS_MLM = {
    0: 'ID', 1: 'OLA', 2: 'GENERO', 3: 'EDAD', 4: 'ESTADO', 5: 'NSE',
    11: 'TIENE_SALDO', 13: 'MARCA', 14: 'NPS', 16: 'MOTIVO_DETRA',
    18: 'MOTIVO_NEUTRO', 20: 'MOTIVO_PROM', 22: 'COMENTARIO',
    23: 'USO_PAGO_ONLINE', 24: 'USO_TRANSFERENCIAS', 25: 'USO_PAGO_SERVICIOS',
    26: 'USO_CRIPTO', 28: 'USO_TDC',  # Quitado 27 (créditos viejo), ahora usa 87
    29: 'USO_EFECTIVO', 30: 'USO_RECARGA_CEL', 31: 'USO_RECARGA_TRANSP',
    32: 'USO_COBRAR_SUELDO', 33: 'USO_TARJETA_DEBITO', 34: 'USO_QR',
    35: 'USO_AHORRO_INVERSION', 36: 'USO_SEGUROS', 37: 'USO_MONEDA_EXTRANJ',
    38: 'USO_REMESAS', 39: 'USO_MERCADOLIBRE', 40: 'USO_RENDIMIENTOS',
    41: 'USO_INVERSIONES', 42: 'USO_OTROS', 43: 'ANTIGUEDAD',
    63: 'MOTIVO_PRINCIPALIDAD',
    68: 'MOTIVO_CREACION', 
    72: 'VALORACION_SEGURIDAD',
    87: 'USO_CREDITOS', 
    94: 'USO_TDC_30D',
    236: 'MOTIVO_INSEGURIDAD',
    264: 'FLAG_PRINCIPALIDAD'
}

# ==============================================================================
# CONFIGURACIÓN DE SITES
# ==============================================================================

SITE_CONFIG = {
    'MLB': {
        'archivo': 'BASE_CRUDA_MLB.csv', 
        'encoding': 'latin-1', 
        'sep': ';', 
        'skiprows': 1,
        'col_marca': 'MARCA', 
        'col_nps': 'NPS', 
        'col_ola': 'OLA',
        'saldo_keywords': ['teve saldo', 'saldo'], 
        'saldo_valor': 'Sim',
        'cols_necesarias': COLS_NECESARIAS_MLB,
        'nombres_columnas': NOMBRES_COLUMNAS_MLB,
        'nombre_pais': 'Brasil',
        'bandera': '🇧🇷'
    },
    'MLA': {
        'archivo': 'BASE_CRUDA_MLA.csv', 
        'encoding': 'utf-8', 
        'sep': ';', 
        'skiprows': 1,
        'col_marca': 'MARCA', 
        'col_nps': 'NPS', 
        'col_ola': 'OLA',
        'saldo_col': 'TIENE_SALDO',  # Columna ya renombrada
        'saldo_valor': 'Si',
        'cols_necesarias': COLS_NECESARIAS_MLA,
        'nombres_columnas': NOMBRES_COLUMNAS_MLA,
        'nombre_pais': 'Argentina',
        'bandera': '🇦🇷'
    },
    'MLM': {
        'archivo': 'BASE_CRUDA_MLM.csv', 
        'encoding': 'utf-8', 
        'sep': ';', 
        'skiprows': 2,
        'col_marca': 'MARCA', 
        'col_nps': 'NPS', 
        'col_ola': 'OLA',
        'saldo_col': 'TIENE_SALDO',
        'saldo_regex': r'^s[ií]$',
        'cols_necesarias': COLS_NECESARIAS_MLM,
        'nombres_columnas': NOMBRES_COLUMNAS_MLM,
        'nombre_pais': 'México',
        'bandera': '🇲🇽'
    },
    'MLC': {
        'archivo': 'BASE_CRUDA_MLC.csv',
        'encoding': 'utf-8',
        'sep': ';',
        'skiprows': 0,
        'col_marca': 'MARCA',
        'col_nps': 'NPS',
        'col_ola': 'OLA',
        'saldo_col': 'TIENE_SALDO',
        'saldo_valor': 'Si',
        # MLC usa mapeo por nombre de columna (no por índice) - se cargan todas las columnas
        # y se renombran según el CSV. Si el CSV tiene estructura distinta, ajustar aquí.
        'cols_necesarias': None,  # None = cargar todas las columnas
        'nombres_columnas': None,  # None = usar nombres del CSV directamente
        'nombre_pais': 'Chile',
        'bandera': '🇨🇱'
    }
}

# ==============================================================================
# FUNCIONES DE UTILIDAD
# ==============================================================================

def leer_config():
    """Lee el archivo de configuración YAML"""
    with open(RUTA_CONFIG, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ==============================================================================
# FUNCIÓN PRINCIPAL: CARGAR DATOS
# ==============================================================================

def cargar_datos(site=None, player=None, periodo_1=None, periodo_2=None, verbose=True):
    """
    Carga datos replicando EXACTAMENTE la lógica del notebook original.
    
    1. Carga SOLO columnas necesarias por índice
    2. Renombra columnas con nombres estándar  
    3. Filtra usuarios CON SALDO
    4. Retorna diccionario con todas las variables
    
    Args:
        site: Código del site (MLA, MLB, MLM). Si None, usa el del config.
        player: Nombre del player a analizar. Si None, usa el del config.
        periodo_1: Período inicial. Si None, usa el del config.
        periodo_2: Período final. Si None, usa el del config.
        verbose: Si True, imprime información de progreso.
    
    Returns:
        dict: Diccionario con df_completo, df_competitivo, df_competitivo_saldo, config
    """
    
    # Leer configuración YAML
    config_yaml = leer_config()
    
    # Usar parámetros del config si no se especifican
    site = site or config_yaml['site']
    player = player or config_yaml['player_analizar']
    periodo_1 = periodo_1 or config_yaml['periodo_1']
    periodo_2 = periodo_2 or config_yaml['periodo_2']
    
    # Validar site
    validate_site_code(site)

    # Obtener configuración del site
    if site not in SITE_CONFIG:
        raise ValueError(f"Site '{site}' no soportado. Disponibles: {list(SITE_CONFIG.keys())}")

    cfg = SITE_CONFIG[site]
    BANDERA = cfg['bandera']
    NOMBRE_PAIS = cfg['nombre_pais']
    
    if verbose:
        print("=" * 70)
        print(f"{BANDERA} CARGANDO BASE DE DATOS - {NOMBRE_PAIS} ({site})")
        print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════
    # PASO 1: CARGAR SOLO COLUMNAS NECESARIAS (OPTIMIZACIÓN MEMORIA)
    # ═══════════════════════════════════════════════════════════════════
    
    archivo = RUTA_DATA / cfg['archivo']
    
    if not archivo.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {archivo}")

    # Validar y detectar encoding del CSV
    if verbose:
        print(f"\n🔍 Detectando encoding del CSV...")

    # Auto-detectar encoding para mayor robustez (especialmente MLB)
    try:
        import chardet
        with open(archivo, 'rb') as f:
            raw_sample = f.read(100000)  # Leer primeros 100KB
            detection = chardet.detect(raw_sample)
            detected_encoding = detection['encoding']
            confidence = detection['confidence']

        # Si el encoding detectado difiere del configurado, usar el detectado
        if detected_encoding and detected_encoding.lower() != cfg['encoding'].lower():
            if verbose:
                print(f"   ℹ️ Encoding detectado: {detected_encoding} (confianza: {confidence*100:.0f}%)")
                print(f"   ℹ️ Encoding configurado: {cfg['encoding']}")
                print(f"   ℹ️ Usando encoding detectado: {detected_encoding}")
            encoding_to_use = detected_encoding
        else:
            encoding_to_use = cfg['encoding']
    except ImportError:
        if verbose:
            print(f"   ⚠️ chardet no disponible, usando encoding configurado: {cfg['encoding']}")
        encoding_to_use = cfg['encoding']
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Error en detección automática: {e}")
            print(f"   ℹ️ Usando encoding configurado: {cfg['encoding']}")
        encoding_to_use = cfg['encoding']

    if verbose:
        print(f"\n📂 PASO 1: Cargando BASE COMPLETA...")
    
    # Parámetros de lectura (usar encoding detectado)
    read_params = {
        'sep': cfg['sep'],
        'encoding': encoding_to_use,
        'on_bad_lines': 'skip',
        'dtype': str,
        'engine': 'python'
    }
    
    if cfg.get('skiprows', 0) > 0:
        read_params['skiprows'] = cfg['skiprows']
    
    # Cargar columnas
    cols_necesarias = cfg.get('cols_necesarias')
    nombres_columnas = cfg.get('nombres_columnas')
    
    if cols_necesarias is not None:
        # Modo índice: cargar columnas específicas por posición
        read_params['header'] = None
        read_params['usecols'] = cols_necesarias
    else:
        # Modo nombre: cargar todas las columnas con sus nombres del CSV
        pass  # header=0 por defecto en pandas
    
    try:
        df_raw = pd.read_csv(archivo, **read_params)
    except UnicodeDecodeError as e:
        # Fallback inteligente: probar encodings alternativos
        alternative_encodings = ['latin-1', 'utf-8', 'iso-8859-1', 'cp1252']
        if encoding_to_use in alternative_encodings:
            alternative_encodings.remove(encoding_to_use)

        for alt_encoding in alternative_encodings:
            try:
                if verbose:
                    print(f"   ⚠️ Error de encoding con {encoding_to_use}, probando {alt_encoding}...")
                read_params['encoding'] = alt_encoding
                df_raw = pd.read_csv(archivo, **read_params)
                if verbose:
                    print(f"   ✅ CSV leído exitosamente con encoding: {alt_encoding}")
                break
            except (UnicodeDecodeError, Exception):
                continue
        else:
            # Si ningún encoding funcionó, re-lanzar el error original
            raise UnicodeDecodeError(
                encoding_to_use, b'', 0, 0,
                f"No se pudo leer el CSV con ningún encoding. Intentados: {encoding_to_use}, {', '.join(alternative_encodings)}"
            )
    
    # Renombrar columnas según mapeo
    if cols_necesarias is not None and nombres_columnas is not None:
        # Modo índice: renombrar por posición
        df_completo = pd.DataFrame()
        for i, col_idx in enumerate(cols_necesarias):
            if i < df_raw.shape[1]:
                nombre_col = nombres_columnas.get(col_idx, f'COL_{col_idx}')
                df_completo[nombre_col] = df_raw.iloc[:, i]
    else:
        # Modo nombre: usar DataFrame tal cual (renombrar si hay mapeo en config.yaml)
        df_completo = df_raw.copy()
        # Normalizar nombres de columnas comunes
        col_renames = {}
        for col in df_completo.columns:
            col_lower = col.lower().strip()
            if 'marca' in col_lower and 'MARCA' not in df_completo.columns:
                col_renames[col] = 'MARCA'
            elif col_lower == 'nps' or col_lower == 'nps_score':
                col_renames[col] = 'NPS'
            elif col_lower == 'ola' or col_lower == 'wave':
                col_renames[col] = 'OLA'
            elif 'comentario' in col_lower and 'COMENTARIO' not in df_completo.columns:
                col_renames[col] = 'COMENTARIO'
        if col_renames:
            df_completo = df_completo.rename(columns=col_renames)
    
    del df_raw
    gc.collect()

    # Validar que el DataFrame no esté vacío
    validate_dataframe_not_empty(df_completo, f"BASE COMPLETA {site}")

    # Validar columnas requeridas básicas
    required_cols = [cfg['col_marca'], cfg['col_nps'], cfg['col_ola']]
    validate_required_columns(df_completo, required_cols, f"BASE_{site}")

    n_productos = len([c for c in df_completo.columns if c.startswith('USO_')])
    
    if verbose:
        print(f"   ✅ {NOMBRE_PAIS}: {len(df_completo.columns)} columnas cargadas (incluye {n_productos} productos)")
        print(f"✅ Base cargada: {df_completo.shape[0]:,} filas x {df_completo.shape[1]} columnas")
    
    # ═══════════════════════════════════════════════════════════════════
    # PASO 2: LIMPIEZA BÁSICA
    # ═══════════════════════════════════════════════════════════════════
    
    if verbose:
        print(f"\n🧹 PASO 2: Limpiando datos...")
    
    filas_originales = len(df_completo)
    
    # Limpiar nombres de columnas
    df_completo.columns = df_completo.columns.str.strip().str.replace('\xa0', '').str.replace('\u00a0', '')
    if verbose:
        print(f"   ✅ Columnas limpiadas")
    
    # Detectar columnas clave
    col_marca = cfg['col_marca']
    col_nps = cfg['col_nps']
    col_ola = cfg['col_ola']
    
    # Verificar que existen las columnas
    for col, nombre in [(col_marca, 'marca'), (col_nps, 'NPS'), (col_ola, 'OLA')]:
        if col not in df_completo.columns:
            for c in df_completo.columns:
                if nombre.upper() in c.upper():
                    if nombre == 'marca': col_marca = c
                    elif nombre == 'NPS': col_nps = c
                    elif nombre == 'OLA': col_ola = c
                    if verbose:
                        print(f"   ℹ️ {nombre} detectado como: '{c}'")
                    break
    
    # Eliminar headers que se colaron como datos
    if verbose:
        print(f"   1️⃣ Eliminando headers en datos...")
    if col_nps in df_completo.columns:
        mask_invalido = df_completo[col_nps].astype(str).str.upper().isin(['NPS', 'OLA', 'MARCA'])
        if mask_invalido.sum() > 0:
            df_completo = df_completo[~mask_invalido].copy()
            if verbose:
                print(f"      ❌ Eliminadas {mask_invalido.sum()} filas header")
    
    # Convertir NPS a numérico
    if verbose:
        print(f"   2️⃣ Convirtiendo NPS a numérico...")
    if col_nps in df_completo.columns:
        df_completo[col_nps] = pd.to_numeric(df_completo[col_nps], errors='coerce')
        if verbose:
            print(f"      ✅ NPS convertido")
    
    # Limpiar nombres de marcas
    if verbose:
        print(f"   3️⃣ Limpiando nombres de marcas...")
    if col_marca in df_completo.columns:
        df_completo[col_marca] = df_completo[col_marca].astype(str).str.strip()
        df_completo = df_completo[df_completo[col_marca].notna() & (df_completo[col_marca] != '') & (df_completo[col_marca] != 'nan')]
        if verbose:
            print(f"      ✅ Marcas limpiadas")
    
    # Eliminar filas completamente vacías
    if verbose:
        print(f"   4️⃣ Eliminando filas vacías...")
    filas_antes = len(df_completo)
    df_completo = df_completo.dropna(how='all')
    if verbose:
        print(f"      ❌ Eliminadas {filas_antes - len(df_completo)} filas vacías")
    
    if verbose:
        print(f"\n✅ LIMPIEZA COMPLETADA:")
        print(f"   • Filas originales: {filas_originales:,}")
        print(f"   • Filas finales: {len(df_completo):,}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PASO 3: FILTRAR USUARIOS CON SALDO
    # ═══════════════════════════════════════════════════════════════════
    
    if verbose:
        print("\n" + "=" * 70)
        print(f"💰 PASO 3: FILTRAR USUARIOS CON SALDO")
        print("=" * 70)
    
    # Guardar base completa antes del filtro
    df_competitivo = df_completo.copy()
    
    # Buscar columna de saldo
    columna_saldo = None
    
    if 'saldo_col' in cfg and cfg['saldo_col']:
        columna_saldo = cfg['saldo_col']
    elif 'saldo_keywords' in cfg:
        for col in df_completo.columns:
            if any(kw in col.lower() for kw in cfg['saldo_keywords']):
                columna_saldo = col
                break
    
    if columna_saldo and columna_saldo in df_completo.columns:
        if verbose:
            print(f"\n📊 Columna de saldo: '{columna_saldo}'")
            print(f"   Distribución:")
            print(df_completo[columna_saldo].value_counts().head(5).to_string())
        
        # Filtrar según tipo de site
        if cfg.get('saldo_regex'):
            import re
            pattern = re.compile(cfg['saldo_regex'], re.IGNORECASE)
            mask_saldo = df_completo[columna_saldo].fillna('').astype(str).str.strip().str.match(pattern)
        else:
            mask_saldo = df_completo[columna_saldo] == cfg['saldo_valor']
        
        df_con_saldo = df_completo[mask_saldo].copy()
        
        if verbose:
            print(f"\n✅ FILTRADO POR SALDO:")
            print(f"   • Base COMPLETA: {len(df_completo):,} usuarios")
            print(f"   • Base CON SALDO: {len(df_con_saldo):,} usuarios")
            print(f"   • % con saldo: {(len(df_con_saldo)/len(df_completo)*100):.1f}%")
    else:
        if verbose:
            print(f"   ⚠️ Columna de saldo no encontrada, usando base completa")
        df_con_saldo = df_completo.copy()
    
    # ═══════════════════════════════════════════════════════════════════
    # OPTIMIZAR MEMORIA Y CREAR VARIABLES
    # ═══════════════════════════════════════════════════════════════════
    
    if verbose:
        print(f"\n🔧 Optimizando memoria...")
    
    # Convertir columnas de texto a category
    for col in [col_marca, col_ola]:
        if col in df_con_saldo.columns:
            try:
                df_con_saldo[col] = df_con_saldo[col].astype('category')
            except (ValueError, TypeError):
                pass
    
    gc.collect()
    if verbose:
        print(f"   ✅ Memoria optimizada")
    
    # ═══════════════════════════════════════════════════════════════════
    # RESUMEN
    # ═══════════════════════════════════════════════════════════════════
    
    if verbose:
        print("\n" + "=" * 70)
        print(f"📊 RESUMEN - {BANDERA} {NOMBRE_PAIS}")
        print("=" * 70)
        
        print(f"\n✅ VARIABLES CREADAS:")
        print(f"   • df_competitivo       = {len(df_competitivo):,} usuarios (completa)")
        print(f"   • df_competitivo_saldo = {len(df_con_saldo):,} usuarios (con saldo)")
        print(f"   • df_completo / df     = {len(df_con_saldo):,} usuarios (principal)")
        
        print(f"\n🏢 Top 5 marcas:")
        for marca, count in df_con_saldo[col_marca].value_counts().head(5).items():
            print(f"   - {marca}: {count:,}")
        
        print(f"\n📅 Quarters: {sorted(df_con_saldo[col_ola].dropna().unique())}")
        
        print(f"\n" + "=" * 70)
        print(f"✅ PARTE 1 OK | Marca: {col_marca} | NPS: {col_nps} | OLA: {col_ola}")
        print("=" * 70)
        print(f"\n🚀 Continúa con PARTE 2")
    
    # ═══════════════════════════════════════════════════════════════════
    # PREPARAR RETORNO
    # ═══════════════════════════════════════════════════════════════════
    
    # Configuración para siguientes partes
    config_dict = {
        'site': site,
        'site_nombre': NOMBRE_PAIS,
        'site_bandera': BANDERA,
        'player': player,
        'periodo_1': periodo_1,
        'periodo_2': periodo_2,
        'col_marca': col_marca,
        'col_nps': col_nps,
        'col_ola': col_ola,
        'categorias_motivos': config_yaml.get('categorias_motivos', {}),
        'dominios_confiables': config_yaml.get('dominios_confiables', {}),
        'parametros': config_yaml.get('parametros', {})
    }
    
    return {
        'df_completo': df_con_saldo,  # Variable principal (CON SALDO)
        'df': df_con_saldo,  # Alias
        'df_competitivo': df_competitivo,  # Base COMPLETA (todos los usuarios)
        'df_competitivo_saldo': df_con_saldo,  # Base CON SALDO
        'config': config_dict,
        'col_marca': col_marca,
        'col_nps': col_nps,
        'col_ola': col_ola
    }

# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 PRUEBA DE CARGA DE DATOS")
    print("=" * 70)
    
    try:
        resultado = cargar_datos(verbose=True)
        
        df = resultado['df_completo']
        config = resultado['config']
        
        print("\n📋 Columnas del DataFrame resultante:")
        print(f"   {list(df.columns)}")
        
        print("\n📋 Primeras filas:")
        cols_mostrar = ['MARCA', 'OLA', 'NPS', 'TIENE_SALDO']
        cols_disponibles = [c for c in cols_mostrar if c in df.columns]
        print(df[cols_disponibles].head(10))
        
        print("\n✅ Prueba completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
