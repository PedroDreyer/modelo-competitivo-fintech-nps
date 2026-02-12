#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilidades para manejo correcto de quarters.

FIX: Comparación alfabética de quarters es incorrecta.
     "25Q2" < "25Q10" es True alfabéticamente, pero 25Q2 > 25Q10 numéricamente.

Este módulo provee funciones para:
- Convertir quarters a formato numérico comparable
- Filtrar quarters correctamente
- Obtener últimos N quarters
"""

import pandas as pd
import re
from typing import List, Union


def quarter_to_numeric(quarter: str) -> int:
    """
    Convierte quarter string a número comparable.

    Formato esperado: YYQ[1-4] (ej: "25Q3", "24Q4")

    Args:
        quarter: String con formato YYQ[1-4]

    Returns:
        int: Número comparable (año*4 + quarter)

    Examples:
        >>> quarter_to_numeric("25Q1")
        8101  # (2025 * 4 + 1)
        >>> quarter_to_numeric("25Q4")
        8104  # (2025 * 4 + 4)
        >>> quarter_to_numeric("26Q1") > quarter_to_numeric("25Q4")
        True
    """
    try:
        # Validar formato
        match = re.match(r'^(\d{2})Q([1-4])$', str(quarter).strip())
        if not match:
            raise ValueError(f"Formato inválido: {quarter}. Esperado: YYQ[1-4]")

        year_short = int(match.group(1))
        q_num = int(match.group(2))

        # Convertir a año completo (asume 20XX)
        year = 2000 + year_short

        # Fórmula: año * 4 + quarter_num
        # Esto garantiza orden correcto: 25Q4 < 26Q1
        return year * 4 + q_num

    except (ValueError, AttributeError) as e:
        raise ValueError(f"Error al convertir quarter '{quarter}': {e}")


def numeric_to_quarter(numeric: int) -> str:
    """
    Convierte número a quarter string.

    Args:
        numeric: Número en formato (año*4 + quarter)

    Returns:
        str: Quarter en formato YYQ[1-4]

    Examples:
        >>> numeric_to_quarter(8104)
        '25Q4'
        >>> numeric_to_quarter(8101)
        '25Q1'
    """
    q_num = numeric % 4
    if q_num == 0:
        q_num = 4
        year = (numeric // 4) - 1
    else:
        year = numeric // 4

    year_short = year % 100
    return f"{year_short:02d}Q{q_num}"


def sort_quarters(quarters: List[str], ascending: bool = True) -> List[str]:
    """
    Ordena lista de quarters correctamente.

    Args:
        quarters: Lista de quarters en formato YYQ[1-4]
        ascending: Si True, ordena de menor a mayor

    Returns:
        List[str]: Quarters ordenados

    Examples:
        >>> sort_quarters(['25Q3', '25Q1', '25Q4', '24Q4'])
        ['24Q4', '25Q1', '25Q3', '25Q4']
    """
    try:
        # Convertir a numérico, ordenar, reconvertir
        quarters_with_num = [(quarter_to_numeric(q), q) for q in quarters]
        quarters_with_num.sort(key=lambda x: x[0], reverse=not ascending)
        return [q for _, q in quarters_with_num]
    except ValueError as e:
        raise ValueError(f"Error al ordenar quarters: {e}")


def filter_quarters_until(quarters: List[str], max_quarter: str, inclusive: bool = True) -> List[str]:
    """
    Filtra quarters hasta un máximo (inclusive o exclusive).

    Args:
        quarters: Lista de quarters
        max_quarter: Quarter máximo
        inclusive: Si True, incluye max_quarter en resultado

    Returns:
        List[str]: Quarters filtrados

    Examples:
        >>> filter_quarters_until(['24Q4', '25Q1', '25Q2', '25Q3', '25Q4'], '25Q2')
        ['24Q4', '25Q1', '25Q2']
        >>> filter_quarters_until(['24Q4', '25Q1', '25Q2'], '25Q2', inclusive=False)
        ['24Q4', '25Q1']
    """
    max_num = quarter_to_numeric(max_quarter)

    result = []
    for q in quarters:
        q_num = quarter_to_numeric(q)
        if inclusive:
            if q_num <= max_num:
                result.append(q)
        else:
            if q_num < max_num:
                result.append(q)

    return result


def get_last_n_quarters(quarters: List[str], max_quarter: str, n: int = 5) -> List[str]:
    """
    Obtiene los últimos N quarters hasta max_quarter (inclusive).

    Este es el fix principal para el bug detectado en el audit.

    Args:
        quarters: Lista de quarters disponibles
        max_quarter: Quarter máximo (actual)
        n: Cantidad de quarters a retornar

    Returns:
        List[str]: Últimos N quarters ordenados ascendente

    Examples:
        >>> quarters = ['24Q1', '24Q2', '24Q3', '24Q4', '25Q1', '25Q2', '25Q3', '25Q4']
        >>> get_last_n_quarters(quarters, '25Q3', n=5)
        ['24Q4', '25Q1', '25Q2', '25Q3']  # Nota: solo 4 porque pide 5 pero hasta 25Q3

        >>> get_last_n_quarters(quarters, '25Q4', n=5)
        ['25Q1', '25Q2', '25Q3', '25Q4']  # Últimos 5 desde 25Q4 hacia atrás
    """
    # Filtrar hasta max_quarter
    filtered = filter_quarters_until(quarters, max_quarter, inclusive=True)

    # Ordenar
    sorted_qs = sort_quarters(filtered, ascending=True)

    # Tomar últimos N
    return sorted_qs[-n:] if len(sorted_qs) > n else sorted_qs


def filter_dataframe_by_quarters(df: pd.DataFrame,
                                  quarter_col: str,
                                  max_quarter: str,
                                  n_quarters: int = 5) -> pd.DataFrame:
    """
    Filtra DataFrame para incluir solo últimos N quarters.

    Esta función reemplaza el código buggy:
        df[df[quarter_col] <= max_quarter].tail(5)  # ❌ INCORRECTO

    Args:
        df: DataFrame con columna de quarters
        quarter_col: Nombre de la columna con quarters
        max_quarter: Quarter máximo a incluir
        n_quarters: Cantidad de quarters a retornar

    Returns:
        pd.DataFrame: DataFrame filtrado con últimos N quarters

    Examples:
        >>> df = pd.DataFrame({'OLA': ['24Q1', '24Q4', '25Q1', '25Q3'], 'NPS': [50, 52, 55, 58]})
        >>> result = filter_dataframe_by_quarters(df, 'OLA', '25Q3', n_quarters=3)
        >>> list(result['OLA'])
        ['24Q4', '25Q1', '25Q3']
    """
    # Obtener quarters únicos del DataFrame
    available_quarters = df[quarter_col].astype(str).unique().tolist()

    # Obtener últimos N quarters válidos
    valid_quarters = get_last_n_quarters(available_quarters, max_quarter, n_quarters)

    # Filtrar DataFrame
    return df[df[quarter_col].isin(valid_quarters)].copy()


def validate_quarter_format(quarter: str) -> bool:
    """
    Valida que un quarter tenga formato correcto.

    Args:
        quarter: String a validar

    Returns:
        bool: True si el formato es válido

    Examples:
        >>> validate_quarter_format("25Q3")
        True
        >>> validate_quarter_format("2025Q3")
        False
        >>> validate_quarter_format("25Q5")
        False
    """
    return bool(re.match(r'^\d{2}Q[1-4]$', str(quarter).strip()))


def quarters_between(start_q: str, end_q: str, inclusive: bool = True) -> List[str]:
    """
    Genera lista de quarters entre start_q y end_q.

    Args:
        start_q: Quarter inicial
        end_q: Quarter final
        inclusive: Si True, incluye end_q

    Returns:
        List[str]: Lista de quarters

    Examples:
        >>> quarters_between('25Q2', '25Q4')
        ['25Q2', '25Q3', '25Q4']
        >>> quarters_between('24Q4', '25Q2')
        ['24Q4', '25Q1', '25Q2']
    """
    start_num = quarter_to_numeric(start_q)
    end_num = quarter_to_numeric(end_q)

    if start_num > end_num:
        raise ValueError(f"start_q ({start_q}) debe ser <= end_q ({end_q})")

    quarters = []
    current = start_num

    while current < end_num or (inclusive and current == end_num):
        quarters.append(numeric_to_quarter(current))
        current += 1

    return quarters


# Tests unitarios
if __name__ == '__main__':
    print("Ejecutando tests de utils_quarters.py...\n")

    # Test 1: Conversión básica
    print("Test 1: Conversion quarter -> numeric")
    assert quarter_to_numeric("25Q1") == 8101
    assert quarter_to_numeric("25Q4") == 8104
    assert quarter_to_numeric("26Q1") == 8105
    print("PASS: Test 1 passed")

    # Test 2: Comparación correcta
    print("\nTest 2: Comparación de quarters")
    assert quarter_to_numeric("25Q4") < quarter_to_numeric("26Q1")
    assert quarter_to_numeric("25Q2") < quarter_to_numeric("25Q3")
    assert quarter_to_numeric("24Q4") < quarter_to_numeric("25Q1")
    print("PASS: Test 2 passed")

    # Test 3: Ordenamiento
    print("\nTest 3: Ordenamiento")
    quarters = ['25Q3', '24Q4', '25Q1', '25Q4', '25Q2']
    sorted_q = sort_quarters(quarters)
    expected = ['24Q4', '25Q1', '25Q2', '25Q3', '25Q4']
    assert sorted_q == expected, f"Expected {expected}, got {sorted_q}"
    print(f"PASS: Test 3 passed: {sorted_q}")

    # Test 4: Últimos N quarters
    print("\nTest 4: Ultimos N quarters")
    quarters = ['24Q1', '24Q2', '24Q3', '24Q4', '25Q1', '25Q2', '25Q3', '25Q4']
    last_5 = get_last_n_quarters(quarters, '25Q3', n=5)
    expected = ['24Q3', '24Q4', '25Q1', '25Q2', '25Q3']  # Últimos 5 hasta 25Q3
    assert last_5 == expected, f"Expected {expected}, got {last_5}"
    print(f"PASS: Test 4 passed: {last_5}")

    # Test 5: Filtro DataFrame
    print("\nTest 5: Filtro DataFrame")
    df = pd.DataFrame({
        'OLA': ['24Q1', '24Q4', '25Q1', '25Q3', '25Q4'],
        'NPS': [50, 52, 55, 58, 60]
    })
    filtered = filter_dataframe_by_quarters(df, 'OLA', '25Q3', n_quarters=3)
    expected_qs = ['24Q4', '25Q1', '25Q3']
    assert list(filtered['OLA']) == expected_qs
    print(f"PASS: Test 5 passed: {list(filtered['OLA'])}")

    # Test 6: Quarters between
    print("\nTest 6: Quarters between")
    between = quarters_between('24Q4', '25Q2')
    expected = ['24Q4', '25Q1', '25Q2']
    assert between == expected
    print(f"PASS: Test 6 passed: {between}")

    print("\n" + "="*50)
    print("PASS: TODOS LOS TESTS PASARON")
    print("="*50)
