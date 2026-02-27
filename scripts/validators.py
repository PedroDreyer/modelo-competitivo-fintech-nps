#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de validación para NPS Model.

FIX: Agregar validaciones estrictas para prevenir errores silenciosos.
     - Validar columnas requeridas
     - Validar valores de config
     - Validar formatos de quarter
     - Validar tipos de datos

"""

import pandas as pd
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class ValidationError(Exception):
    """Excepción personalizada para errores de validación."""
    pass


# ═════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE COLUMNAS
# ═════════════════════════════════════════════════════════════════════════════

def validate_required_columns(df: pd.DataFrame,
                               required_cols: List[str],
                               file_name: str = "DataFrame") -> None:
    """
    Valida que un DataFrame contenga todas las columnas requeridas.

    Args:
        df: DataFrame a validar
        required_cols: Lista de columnas requeridas
        file_name: Nombre del archivo (para mensajes de error)

    Raises:
        ValidationError: Si faltan columnas

    Examples:
        >>> df = pd.DataFrame({'A': [1], 'B': [2]})
        >>> validate_required_columns(df, ['A', 'B'], 'test.csv')  # OK
        >>> validate_required_columns(df, ['A', 'C'], 'test.csv')  # Raises
    """
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        available = list(df.columns[:20])  # Mostrar primeras 20 columnas
        raise ValidationError(
            f"\n[ERROR] {file_name} - Faltan columnas requeridas:\n"
            f"  Faltantes: {missing}\n"
            f"  Disponibles: {available}\n"
            f"  Total disponibles: {len(df.columns)}"
        )


def validate_column_types(df: pd.DataFrame,
                           column_types: Dict[str, type],
                           file_name: str = "DataFrame") -> None:
    """
    Valida que las columnas tengan los tipos esperados.

    Args:
        df: DataFrame a validar
        column_types: Dict {column_name: expected_type}
        file_name: Nombre del archivo

    Raises:
        ValidationError: Si los tipos no coinciden

    Examples:
        >>> df = pd.DataFrame({'A': [1, 2], 'B': ['x', 'y']})
        >>> validate_column_types(df, {'A': int}, 'test.csv')  # OK
    """
    errors = []

    for col, expected_type in column_types.items():
        if col not in df.columns:
            errors.append(f"  - {col}: columna no existe")
            continue

        # Obtener tipo actual
        actual_dtype = df[col].dtype

        # Validar según tipo esperado
        if expected_type == int or expected_type == float:
            if not pd.api.types.is_numeric_dtype(actual_dtype):
                errors.append(f"  - {col}: esperado numérico, actual {actual_dtype}")
        elif expected_type == str:
            if not pd.api.types.is_string_dtype(actual_dtype) and actual_dtype != 'object':
                errors.append(f"  - {col}: esperado string, actual {actual_dtype}")

    if errors:
        raise ValidationError(
            f"\n[ERROR] {file_name} - Tipos de columnas incorrectos:\n" +
            "\n".join(errors)
        )


def validate_non_empty(df: pd.DataFrame,
                        columns: List[str],
                        file_name: str = "DataFrame",
                        max_null_pct: float = 0.5) -> None:
    """
    Valida que las columnas no estén mayormente vacías.

    Args:
        df: DataFrame a validar
        columns: Lista de columnas a verificar
        file_name: Nombre del archivo
        max_null_pct: Porcentaje máximo de nulos permitido (default 50%)

    Raises:
        ValidationError: Si hay demasiados nulos

    Examples:
        >>> df = pd.DataFrame({'A': [1, 2, None, None]})
        >>> validate_non_empty(df, ['A'], max_null_pct=0.3)  # Raises (50% null > 30%)
    """
    errors = []

    for col in columns:
        if col not in df.columns:
            continue

        null_count = df[col].isna().sum()
        null_pct = null_count / len(df)

        if null_pct > max_null_pct:
            errors.append(
                f"  - {col}: {null_pct*100:.1f}% nulos ({null_count}/{len(df)})"
            )

    if errors:
        raise ValidationError(
            f"\n[ERROR] {file_name} - Columnas con demasiados valores nulos:\n" +
            "\n".join(errors) +
            f"\n  Máximo permitido: {max_null_pct*100:.1f}%"
        )


# ═════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE CONFIG
# ═════════════════════════════════════════════════════════════════════════════

def validate_config_keys(config: Dict[str, Any],
                          required_keys: List[str],
                          config_name: str = "config") -> None:
    """
    Valida que un diccionario de configuración tenga las claves requeridas.

    Args:
        config: Diccionario de configuración
        required_keys: Lista de claves requeridas
        config_name: Nombre del config (para error messages)

    Raises:
        ValidationError: Si faltan claves

    Examples:
        >>> cfg = {'site': 'MLM', 'player': 'Nubank'}
        >>> validate_config_keys(cfg, ['site', 'player'])  # OK
        >>> validate_config_keys(cfg, ['site', 'quarter'])  # Raises
    """
    missing = [key for key in required_keys if key not in config]

    if missing:
        available = list(config.keys())
        raise ValidationError(
            f"\n[ERROR] {config_name} - Faltan claves requeridas:\n"
            f"  Faltantes: {missing}\n"
            f"  Disponibles: {available}"
        )


def validate_site_code(site: str) -> None:
    """
    Valida que un código de site sea válido.

    Args:
        site: Código de site

    Raises:
        ValidationError: Si el site no es válido

    Examples:
        >>> validate_site_code('MLM')  # OK
        >>> validate_site_code('XXX')  # Raises
    """
    valid_sites = ['MLA', 'MLB', 'MLM', 'MLC']

    if site not in valid_sites:
        raise ValidationError(
            f"\n[ERROR] Site inválido: '{site}'\n"
            f"  Sites válidos: {valid_sites}"
        )


def validate_quarter_format(quarter: str) -> None:
    """
    Valida que un quarter tenga formato correcto.

    Args:
        quarter: String de quarter (ej: "25Q3")

    Raises:
        ValidationError: Si el formato es inválido

    Examples:
        >>> validate_quarter_format('25Q3')  # OK
        >>> validate_quarter_format('2025Q3')  # Raises
        >>> validate_quarter_format('25Q5')  # Raises
    """
    if not re.match(r'^\d{2}Q[1-4]$', str(quarter).strip()):
        raise ValidationError(
            f"\n[ERROR] Formato de quarter inválido: '{quarter}'\n"
            f"  Formato esperado: YYQ[1-4]\n"
            f"  Ejemplos válidos: 25Q1, 25Q2, 26Q3"
        )


def validate_player_name(player: str, site: str) -> None:
    """
    Valida que un nombre de player sea válido para un site.

    Args:
        player: Nombre del player
        site: Código del site

    Raises:
        ValidationError: Si el player no existe para ese site

    Note:
        Esta es una validación laxa. No falla si el player no está en la lista,
        solo imprime un warning.
    """
    # Lista de players conocidos por site
    known_players = {
        'MLA': ['Mercado Pago', 'Ualá', 'Naranja X', 'Brubank', 'Personal Pay', 'MODO'],
        'MLB': ['Mercado Pago', 'Nubank', 'PicPay', 'Banco Inter', 'C6 Bank', 'Itaú', 'Bradesco', 'PagBank'],
        'MLM': ['Mercado Pago', 'Nubank', 'BBVA', 'Banamex', 'Santander', 'Hey Banco', 'Stori', 'Klar', 'Didi'],
        'MLC': ['Mercado Pago', 'Tenpo', 'MACH', 'Banco Estado']
    }

    if site in known_players:
        if player not in known_players[site]:
            # Solo warning, no error
            print(
                f"\n[WARN] Player '{player}' no está en la lista conocida para {site}\n"
                f"  Players conocidos: {known_players[site]}\n"
                f"  El análisis continuará de todas formas..."
            )


# ═════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE DATOS
# ═════════════════════════════════════════════════════════════════════════════

def validate_nps_values(df: pd.DataFrame,
                         nps_col: str = 'NPS',
                         max_invalid_pct: float = 0.1) -> None:
    """
    Valida que los valores de NPS estén en el rango correcto.

    Args:
        df: DataFrame con columna NPS
        nps_col: Nombre de la columna NPS
        max_invalid_pct: Porcentaje máximo de valores inválidos permitido

    Raises:
        ValidationError: Si hay demasiados valores fuera de rango

    Examples:
        >>> df = pd.DataFrame({'NPS': [-1, 0, 1, -1, 0]})
        >>> validate_nps_values(df)  # OK
        >>> df2 = pd.DataFrame({'NPS': [5, 10, 15]})
        >>> validate_nps_values(df2)  # Raises
    """
    if nps_col not in df.columns:
        return  # Skip si no existe la columna

    # NPS debe estar en rango [-1, 0, 1] o [0-10]
    valid_discrete = df[nps_col].isin([-1, 0, 1])
    valid_score = (df[nps_col] >= 0) & (df[nps_col] <= 10)
    valid = valid_discrete | valid_score

    invalid_count = (~valid & df[nps_col].notna()).sum()
    invalid_pct = invalid_count / len(df)

    if invalid_pct > max_invalid_pct:
        raise ValidationError(
            f"\n[ERROR] Valores de NPS fuera de rango:\n"
            f"  Inválidos: {invalid_count}/{len(df)} ({invalid_pct*100:.1f}%)\n"
            f"  Máximo permitido: {max_invalid_pct*100:.1f}%\n"
            f"  Rangos válidos: [-1, 0, 1] o [0-10]"
        )


def validate_dataframe_not_empty(df: pd.DataFrame,
                                   name: str = "DataFrame") -> None:
    """
    Valida que un DataFrame no esté vacío.

    Args:
        df: DataFrame a validar
        name: Nombre del DataFrame (para error messages)

    Raises:
        ValidationError: Si el DataFrame está vacío

    Examples:
        >>> df = pd.DataFrame({'A': [1, 2]})
        >>> validate_dataframe_not_empty(df)  # OK
        >>> empty = pd.DataFrame()
        >>> validate_dataframe_not_empty(empty)  # Raises
    """
    if df is None or len(df) == 0:
        raise ValidationError(
            f"\n[ERROR] {name} está vacío\n"
            f"  No se puede continuar sin datos"
        )


# ═════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN DE ARCHIVOS
# ═════════════════════════════════════════════════════════════════════════════

def validate_file_exists(file_path: str) -> None:
    """
    Valida que un archivo exista.

    Args:
        file_path: Ruta al archivo

    Raises:
        ValidationError: Si el archivo no existe

    Examples:
        >>> validate_file_exists('README.md')  # OK (si existe)
        >>> validate_file_exists('noexiste.csv')  # Raises
    """
    path = Path(file_path)

    if not path.exists():
        raise ValidationError(
            f"\n[ERROR] Archivo no encontrado: {file_path}\n"
            f"  Verificar que la ruta sea correcta"
        )


def validate_csv_encoding(file_path: str,
                            expected_encoding: str = 'utf-8') -> str:
    """
    Detecta y valida el encoding de un archivo CSV.

    Args:
        file_path: Ruta al archivo CSV
        expected_encoding: Encoding esperado

    Returns:
        str: Encoding detectado

    Raises:
        Warning: Si el encoding detectado difiere del esperado

    Examples:
        >>> validate_csv_encoding('data.csv', 'utf-8')
        'utf-8'
    """
    try:
        import chardet

        with open(file_path, 'rb') as f:
            raw = f.read(100000)  # Leer primeros 100KB
            result = chardet.detect(raw)
            detected_encoding = result['encoding']
            confidence = result['confidence']

        if detected_encoding.lower() != expected_encoding.lower():
            print(
                f"\n[WARN] Encoding mismatch: {file_path}\n"
                f"  Esperado: {expected_encoding}\n"
                f"  Detectado: {detected_encoding} (confianza: {confidence*100:.0f}%)\n"
                f"  Se recomienda verificar el encoding del archivo"
            )

        return detected_encoding

    except ImportError:
        print("[WARN] chardet no instalado, no se puede detectar encoding automáticamente")
        return expected_encoding


# ═════════════════════════════════════════════════════════════════════════════
# TESTS
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Ejecutando tests de validators.py...\n")

    # Test 1: Validar columnas
    print("Test 1: Validacion de columnas")
    df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    validate_required_columns(df, ['A', 'B'], 'test.csv')  # OK
    try:
        validate_required_columns(df, ['A', 'C'], 'test.csv')  # Debe fallar
        assert False, "Debería haber fallado"
    except ValidationError:
        pass  # Expected
    print("PASS: Test 1")

    # Test 2: Validar site
    print("\nTest 2: Validacion de site")
    validate_site_code('MLM')  # OK
    try:
        validate_site_code('XXX')  # Debe fallar
        assert False, "Debería haber fallado"
    except ValidationError:
        pass  # Expected
    print("PASS: Test 2")

    # Test 3: Validar quarter
    print("\nTest 3: Validacion de quarter")
    validate_quarter_format('25Q3')  # OK
    try:
        validate_quarter_format('2025Q3')  # Debe fallar
        assert False, "Debería haber fallado"
    except ValidationError:
        pass  # Expected
    print("PASS: Test 3")

    # Test 4: Validar NPS
    print("\nTest 4: Validacion de NPS")
    df_nps = pd.DataFrame({'NPS': [-1, 0, 1, -1, 0, 1]})
    validate_nps_values(df_nps)  # OK
    print("PASS: Test 4")

    # Test 5: DataFrame no vacío
    print("\nTest 5: DataFrame no vacio")
    validate_dataframe_not_empty(df)  # OK
    try:
        validate_dataframe_not_empty(pd.DataFrame())  # Debe fallar
        assert False, "Debería haber fallado"
    except ValidationError:
        pass  # Expected
    print("PASS: Test 5")

    print("\n" + "="*50)
    print("PASS: TODOS LOS TESTS PASARON")
    print("="*50)
