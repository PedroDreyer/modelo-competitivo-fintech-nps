#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuración centralizada de categorías de motivos.

FIX: Múltiples archivos tenían listas diferentes de categorías.
     Este módulo es la única fuente de verdad (single source of truth).

Importar en todos los módulos que necesiten categorías:
    from config_categorias import get_categorias, get_categorias_detalladas, mapear_categoria

"""

# ═════════════════════════════════════════════════════════════════════════════
# CATEGORÍAS DETALLADAS (Para n8n y clasificación manual)
# ═════════════════════════════════════════════════════════════════════════════

CATEGORIAS_DETALLADAS = {
    'ES': [  # Español (MLA, MLM, MLC)
        'Tasa de interés de crédito o tarjeta',
        'Límites bajos de crédito o tarjeta',
        'Acceso a crédito o tarjeta de crédito',
        'Rendimientos',
        'Seguridad',
        'Promociones y descuentos',
        'Atención al cliente',
        'Oferta de funcionalidades',
        'Dificultad de uso',
        'Tarifas de la cuenta',
        'No uso o sin opinión'
    ],
    'PT': [  # Portugués (MLB)
        'Taxa de juros de crédito ou cartão',
        'Limites baixos de crédito ou cartão',
        'Acesso a crédito ou cartão de crédito',
        'Rendimentos',
        'Segurança',
        'Promoções e descontos',
        'Atendimento ao cliente',
        'Oferta de funcionalidades',
        'Dificuldade de uso',
        'Tarifas da conta',
        'Não uso ou sem opinião'
    ]
}

# ═════════════════════════════════════════════════════════════════════════════
# CATEGORÍAS AGREGADAS (Para waterfall y reportes)
# ═════════════════════════════════════════════════════════════════════════════

CATEGORIAS_AGREGADAS = {
    'ES': [
        'Tarifas',
        'Atención',
        'Rendimientos',
        'Funcionalidades',
        'Seguridad',
        'Dificultad',
        'Promociones',
        'Financiamiento',
        'Otros'
    ],
    'PT': [
        'Tarifas',
        'Atendimento',
        'Rendimentos',
        'Funcionalidades',
        'Segurança',
        'Dificuldade',
        'Promoções',
        'Financiamento',
        'Outros'
    ]
}

# ═════════════════════════════════════════════════════════════════════════════
# MAPEO: CATEGORÍA DETALLADA → CATEGORÍA AGREGADA
# ═════════════════════════════════════════════════════════════════════════════

MAPEO_DETALLADA_A_AGREGADA = {
    'ES': {
        'Tasa de interés de crédito o tarjeta': 'Financiamiento',
        'Límites bajos de crédito o tarjeta': 'Financiamiento',
        'Acceso a crédito o tarjeta de crédito': 'Financiamiento',
        'Rendimientos': 'Rendimientos',
        'Seguridad': 'Seguridad',
        'Promociones y descuentos': 'Promociones',
        'Atención al cliente': 'Atención',
        'Oferta de funcionalidades': 'Funcionalidades',
        'Dificultad de uso': 'Dificultad',
        'Tarifas de la cuenta': 'Tarifas',
        'No uso o sin opinión': 'Otros'
    },
    'PT': {
        'Taxa de juros de crédito ou cartão': 'Financiamento',
        'Limites baixos de crédito ou cartão': 'Financiamento',
        'Acesso a crédito ou cartão de crédito': 'Financiamento',
        'Rendimentos': 'Rendimentos',
        'Segurança': 'Segurança',
        'Promoções e descontos': 'Promoções',
        'Atendimento ao cliente': 'Atendimento',
        'Oferta de funcionalidades': 'Funcionalidades',
        'Dificuldade de uso': 'Dificuldade',
        'Tarifas da conta': 'Tarifas',
        'Não uso ou sem opinião': 'Outros'
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# MAPEO: PRODUCTO → CATEGORÍA DE QUEJA RELACIONADA
# ═════════════════════════════════════════════════════════════════════════════

MAPEO_PRODUCTO_QUEJA = {
    'Crédito': 'Financiamiento',
    'Préstamos': 'Financiamiento',
    'Tarjeta de Crédito': 'Financiamiento',
    'Cuenta Remunerada': 'Rendimientos',
    'Inversiones': 'Rendimientos',
    'Rendimientos': 'Rendimientos',
    'Seguridad': 'Seguridad',
    'Atención': 'Atención',
    'Facilidad de uso': 'Dificultad',
}

# ═════════════════════════════════════════════════════════════════════════════
# IDIOMA POR SITE
# ═════════════════════════════════════════════════════════════════════════════

SITE_IDIOMA = {
    'MLA': 'ES',  # Argentina
    'MLB': 'PT',  # Brasil
    'MLM': 'ES',  # México
    'MLC': 'ES'   # Chile
}

# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE ACCESO
# ═════════════════════════════════════════════════════════════════════════════

def get_idioma(site: str) -> str:
    """
    Obtiene el idioma para un site.

    Args:
        site: Código del site (MLA, MLB, MLM, MLC)

    Returns:
        str: Código de idioma ('ES' o 'PT')

    Raises:
        ValueError: Si el site no es válido
    """
    if site not in SITE_IDIOMA:
        raise ValueError(f"Site inválido: {site}. Válidos: {list(SITE_IDIOMA.keys())}")
    return SITE_IDIOMA[site]


def get_categorias_detalladas(site: str) -> list:
    """
    Obtiene lista de categorías detalladas para un site.

    Args:
        site: Código del site (MLA, MLB, MLM, MLC)

    Returns:
        list: Lista de categorías detalladas

    Examples:
        >>> cats = get_categorias_detalladas('MLM')
        >>> 'Tasa de interés de crédito o tarjeta' in cats
        True
    """
    idioma = get_idioma(site)
    return CATEGORIAS_DETALLADAS[idioma]


def get_categorias_agregadas(site: str) -> list:
    """
    Obtiene lista de categorías agregadas para un site.

    Args:
        site: Código del site (MLA, MLB, MLM, MLC)

    Returns:
        list: Lista de categorías agregadas

    Examples:
        >>> cats = get_categorias_agregadas('MLM')
        >>> 'Financiamiento' in cats
        True
    """
    idioma = get_idioma(site)
    return CATEGORIAS_AGREGADAS[idioma]


def mapear_detallada_a_agregada(categoria_detallada: str, site: str) -> str:
    """
    Mapea una categoría detallada a su categoría agregada.

    Args:
        categoria_detallada: Categoría en formato detallado
        site: Código del site

    Returns:
        str: Categoría agregada correspondiente

    Examples:
        >>> mapear_detallada_a_agregada('Tasa de interés de crédito o tarjeta', 'MLM')
        'Financiamiento'
        >>> mapear_detallada_a_agregada('Taxa de juros de crédito ou cartão', 'MLB')
        'Financiamento'
    """
    idioma = get_idioma(site)
    mapeo = MAPEO_DETALLADA_A_AGREGADA[idioma]

    if categoria_detallada in mapeo:
        return mapeo[categoria_detallada]

    # Fallback: si no está mapeada, retornar "Otros"
    return 'Outros' if idioma == 'PT' else 'Otros'


def validar_categoria(categoria: str, site: str, nivel: str = 'detallada') -> bool:
    """
    Valida si una categoría es válida para un site.

    Args:
        categoria: Nombre de la categoría
        site: Código del site
        nivel: 'detallada' o 'agregada'

    Returns:
        bool: True si la categoría es válida

    Examples:
        >>> validar_categoria('Financiamiento', 'MLM', 'agregada')
        True
        >>> validar_categoria('Categoria Invalida', 'MLM', 'detallada')
        False
    """
    if nivel == 'detallada':
        categorias_validas = get_categorias_detalladas(site)
    elif nivel == 'agregada':
        categorias_validas = get_categorias_agregadas(site)
    else:
        raise ValueError(f"Nivel inválido: {nivel}. Válidos: 'detallada', 'agregada'")

    return categoria in categorias_validas


def normalizar_categoria(categoria: str, site: str) -> str:
    """
    Normaliza nombre de categoría (case-insensitive, sin tildes).

    Args:
        categoria: Categoría a normalizar
        site: Código del site

    Returns:
        str: Categoría normalizada o None si no se encuentra

    Examples:
        >>> normalizar_categoria('financiamiento', 'MLM')
        'Financiamiento'
        >>> normalizar_categoria('SEGURIDAD', 'MLM')
        'Seguridad'
    """
    import unicodedata

    def normalize_text(text):
        """Quita tildes y convierte a minúsculas."""
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()

    categoria_norm = normalize_text(categoria)

    # Buscar en agregadas
    for cat in get_categorias_agregadas(site):
        if normalize_text(cat) == categoria_norm:
            return cat

    # Buscar en detalladas
    for cat in get_categorias_detalladas(site):
        if normalize_text(cat) == categoria_norm:
            return cat

    return None


def get_mapeo_producto_queja() -> dict:
    """
    Obtiene el mapeo de productos a categorías de queja.

    Returns:
        dict: Mapeo producto → categoría
    """
    return MAPEO_PRODUCTO_QUEJA.copy()


# ═════════════════════════════════════════════════════════════════════════════
# TESTS
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Ejecutando tests de config_categorias.py...\n")

    # Test 1: Idiomas
    print("Test 1: Idiomas por site")
    assert get_idioma('MLA') == 'ES'
    assert get_idioma('MLB') == 'PT'
    assert get_idioma('MLM') == 'ES'
    print("PASS: Test 1")

    # Test 2: Categorías detalladas
    print("\nTest 2: Categorias detalladas")
    cats_es = get_categorias_detalladas('MLM')
    cats_pt = get_categorias_detalladas('MLB')
    assert 'Tasa de interés de crédito o tarjeta' in cats_es
    assert 'Taxa de juros de crédito ou cartão' in cats_pt
    assert len(cats_es) == 11
    assert len(cats_pt) == 11
    print(f"PASS: Test 2 ({len(cats_es)} categorias ES, {len(cats_pt)} categorias PT)")

    # Test 3: Categorías agregadas
    print("\nTest 3: Categorias agregadas")
    agg_es = get_categorias_agregadas('MLM')
    agg_pt = get_categorias_agregadas('MLB')
    assert 'Financiamiento' in agg_es
    assert 'Financiamento' in agg_pt
    assert len(agg_es) == 9
    print(f"PASS: Test 3 ({len(agg_es)} categorias)")

    # Test 4: Mapeo
    print("\nTest 4: Mapeo detallada -> agregada")
    assert mapear_detallada_a_agregada('Tasa de interés de crédito o tarjeta', 'MLM') == 'Financiamiento'
    assert mapear_detallada_a_agregada('Taxa de juros de crédito ou cartão', 'MLB') == 'Financiamento'
    assert mapear_detallada_a_agregada('Seguridad', 'MLA') == 'Seguridad'
    print("PASS: Test 4")

    # Test 5: Validación
    print("\nTest 5: Validacion de categorias")
    assert validar_categoria('Financiamiento', 'MLM', 'agregada') == True
    assert validar_categoria('Categoria Falsa', 'MLM', 'agregada') == False
    assert validar_categoria('Tasa de interés de crédito o tarjeta', 'MLM', 'detallada') == True
    print("PASS: Test 5")

    # Test 6: Normalización
    print("\nTest 6: Normalizacion")
    assert normalizar_categoria('financiamiento', 'MLM') == 'Financiamiento'
    assert normalizar_categoria('SEGURIDAD', 'MLM') == 'Seguridad'
    assert normalizar_categoria('atencion', 'MLA') == 'Atención'  # Sin tilde -> con tilde
    print("PASS: Test 6")

    print("\n" + "="*50)
    print("PASS: TODOS LOS TESTS PASARON")
    print("="*50)
