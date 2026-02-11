# -*- coding: utf-8 -*-
"""
===============================================================================
PARSER DE PRESENTACIONES PDF - MODELO NPS FINTECH
===============================================================================

Extrae metricas y contexto de presentaciones PDF anteriores (multi-player)
para enriquecer el reporte actual con comparacion vs quarter anterior.

Uso:
    from scripts.parsear_presentacion import cargar_quarter_anterior
    data = cargar_quarter_anterior(site='MLM', player='Nubank', quarter_actual='25Q2')
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime

import yaml

try:
    import pdfplumber
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

# ==============================================================================
# PATHS
# ==============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PRESENTACIONES_DIR = PROJECT_DIR / "presentaciones_anteriores"
CACHE_DIR = PRESENTACIONES_DIR / "_cache"
CONFIG_PATH = PROJECT_DIR / "config" / "config.yaml"

# ==============================================================================
# CATEGORIAS CONOCIDAS (para regex de waterfall/drivers)
# ==============================================================================

CATEGORIAS_CONOCIDAS = [
    'Complejidad', 'Problemas Funcionales', 'Complejidad & Problemas Funcionales',
    'Financiamiento', 'Rendimientos', 'Rendimientos & Inversiones',
    'Seguridad', 'Atención', 'Atención al Cliente',
    'Tarifas', 'Promociones', 'Promociones & Descuentos',
    'Funcionalidades', 'Inversiones',
    # Portugues
    'Complexidade', 'Financiamento', 'Rendimentos',
    'Segurança', 'Atendimento', 'Tarifas',
    'Promoções', 'Funcionalidades',
]

# ==============================================================================
# FUNCIONES DE UTILIDAD
# ==============================================================================

def _calcular_quarter_anterior(quarter: str) -> str:
    """Calcula el quarter anterior. Ej: 25Q2 -> 25Q1, 25Q1 -> 24Q4."""
    match = re.match(r'(\d{2})Q(\d)', quarter)
    if not match:
        return None
    year = int(match.group(1))
    q = int(match.group(2))
    if q == 1:
        return f"{year - 1:02d}Q4"
    else:
        return f"{year:02d}Q{q - 1}"


def _md5_archivo(path: Path) -> str:
    """Calcula MD5 de un archivo."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _cargar_players_config(site: str) -> list:
    """Carga la lista de players para un site desde config.yaml."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        sites_config = config.get('sites', {})
        site_config = sites_config.get(site, {})
        return site_config.get('players', [])
    except Exception:
        # Fallback con players conocidos
        PLAYERS_FALLBACK = {
            'MLM': ['Mercado Pago', 'Nubank', 'BBVA', 'Banamex', 'Santander', 'Hey Banco', 'Stori', 'Klar', 'Didi', 'Ualá'],
            'MLA': ['Mercado Pago', 'Ualá', 'Naranja X', 'Brubank', 'Personal Pay', 'MODO'],
            'MLB': ['Mercado Pago', 'Nubank', 'PicPay', 'Banco Inter', 'C6 Bank', 'Itaú', 'Bradesco', 'PagBank'],
            'MLC': ['Mercado Pago', 'Tenpo', 'MACH', 'Banco Estado'],
        }
        return PLAYERS_FALLBACK.get(site, [])


def _buscar_pdf(site: str, quarter: str) -> Path:
    """Busca un PDF que contenga el quarter y site en el nombre."""
    site_dir = PRESENTACIONES_DIR / site
    if not site_dir.exists():
        return None
    
    quarter_upper = quarter.upper()
    site_upper = site.upper()
    
    for pdf in site_dir.glob('*.pdf'):
        nombre = pdf.name.upper()
        if quarter_upper in nombre and (site_upper in nombre or 'NPS' in nombre):
            return pdf
    
    # Fallback: buscar solo por quarter
    for pdf in site_dir.glob('*.pdf'):
        if quarter_upper in pdf.name.upper():
            return pdf
    
    return None


# ==============================================================================
# EXTRACCION DE TEXTO
# ==============================================================================

def parsear_pdf(pdf_path: Path) -> str:
    """Extrae texto completo del PDF, pagina por pagina."""
    if not PDF_DISPONIBLE:
        print("   [WARN] pdfplumber no instalado. Ejecutar: pip install pdfplumber")
        return ""
    
    texto_completo = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                texto = page.extract_text()
                if texto:
                    texto_completo.append(f"--- PAGINA {i+1} ---\n{texto}")
    except Exception as e:
        print(f"   [WARN] Error leyendo PDF: {e}")
        return ""
    
    return "\n\n".join(texto_completo)


# ==============================================================================
# SEGMENTACION DE TEXTO POR PLAYER
# ==============================================================================

def _segmentar_por_player(texto: str, players: list) -> dict:
    """
    Divide el texto en secciones por player usando 'NPS Competitivo {Player}'
    como delimitadores. Retorna dict {player: texto_seccion}.
    Tambien incluye el headline general (texto antes de la primera seccion).
    """
    secciones = {}
    
    # Buscar todas las posiciones de "NPS Competitivo {Player}"
    marcadores = []
    for player in players:
        # Patron flexible: "NPS Competitivo Player" o "NPS Player"
        for pattern in [
            rf'NPS\s+Competitivo\s+{re.escape(player)}',
            rf'NPS\s+{re.escape(player)}\b',
        ]:
            for m in re.finditer(pattern, texto, re.IGNORECASE):
                marcadores.append((m.start(), player))
    
    # Ordenar por posicion
    marcadores.sort(key=lambda x: x[0])
    
    # Deduplicar: si el mismo player aparece multiples veces, tomar todas sus secciones
    player_texts = {}
    for i, (pos, player) in enumerate(marcadores):
        # Encontrar el final: inicio de la siguiente seccion (de otro player) o fin del texto
        end = len(texto)
        for j in range(i + 1, len(marcadores)):
            if marcadores[j][1] != player:
                end = marcadores[j][0]
                break
        
        seccion = texto[pos:end]
        if player in player_texts:
            player_texts[player] += '\n' + seccion
        else:
            player_texts[player] = seccion
    
    return player_texts


# ==============================================================================
# EXTRACCION DE METRICAS POR PLAYER
# ==============================================================================

def _extraer_nps_delta(texto_global: str, player: str) -> float:
    """
    Extrae el delta de NPS para un player del texto global.
    Busca el patron canonico: "{Player}: NPS {+/-}Xp.p."
    Valida que el delta este en rango razonable (-30 a +30).
    """
    patrones = [
        # Patron canonico: "Mercado Pago: NPS +3p.p."
        rf'{re.escape(player)}:\s*NPS\s*([+-]\d+)\s*p\.?p\.?',
        # "NPS Player +3p.p."  
        rf'NPS\s+{re.escape(player)}\s*([+-]\d+)\s*p\.?p\.?',
        # "Player ... NPS +3p.p." (misma linea)
        rf'{re.escape(player)}[^\n]{{0,50}}?NPS\s*([+-]\d+)\s*p\.?p\.?',
        # "NPS +3p.p." despues de "NPS Competitivo Player"
        rf'NPS\s+Competitivo\s+{re.escape(player)}[^\n]{{0,200}}?NPS\s*([+-]\d+)\s*p\.?p\.?',
    ]
    
    for patron in patrones:
        match = re.search(patron, texto_global, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                val = float(match.group(1))
                if -30 <= val <= 30:  # Rango razonable para delta NPS
                    return val
            except (ValueError, IndexError):
                continue
    return None


def _extraer_waterfall(texto_seccion: str, player: str) -> dict:
    """
    Extrae datos del waterfall de quejas de la seccion especifica del player.
    Busca categorias conocidas + numero en p.p.
    """
    waterfall = {}
    
    for cat in CATEGORIAS_CONOCIDAS:
        # Solo buscar en la seccion del player, no en todo el texto
        patron = rf'{re.escape(cat)}[^\.]*?(\d+)\s*p\.?p\.?'
        match = re.search(patron, texto_seccion, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 0 < val <= 30:  # Rango razonable
                    cat_norm = cat.split('&')[0].strip()
                    if cat_norm not in waterfall:  # Primera ocurrencia
                        waterfall[cat_norm] = val
            except ValueError:
                continue
    
    return waterfall


def _extraer_principalidad(texto_global: str, texto_seccion: str, player: str) -> dict:
    """Extrae datos de principalidad para un player."""
    result = {'valor': None, 'delta': None}
    
    # Buscar en texto global (principalidad suele estar en slides compartidas)
    # Patron: "principalidad.*Player.*X%" o "Player.*principalidad.*X%"
    for fuente in [texto_seccion, texto_global]:
        if result['valor'] is not None:
            break
        patrones_valor = [
            rf'principalidad.*?{re.escape(player)}.*?(\d+)%',
            rf'{re.escape(player)}.*?principalidad.*?(\d+)%',
        ]
        for p in patrones_valor:
            match = re.search(p, fuente, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    val = float(match.group(1))
                    if 0 < val < 100:
                        result['valor'] = val
                        break
                except (ValueError, IndexError):
                    continue
    
    for fuente in [texto_seccion, texto_global]:
        if result['delta'] is not None:
            break
        patrones_delta = [
            rf'principalidad.*?{re.escape(player)}.*?([+-]\d+)\s*p\.?p\.?',
            rf'{re.escape(player)}.*?principalidad.*?([+-]\d+)\s*p\.?p\.?',
            rf'{re.escape(player)}.*?([+-]\d+)\s*p\.?p\.?\s*(?:de\s*)?principalidad',
        ]
        for p in patrones_delta:
            match = re.search(p, fuente, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    val = float(match.group(1))
                    if -20 <= val <= 20:
                        result['delta'] = val
                        break
                except (ValueError, IndexError):
                    continue
    
    return result


def _extraer_seguridad(texto_global: str, texto_seccion: str, player: str) -> dict:
    """Extrae datos de seguridad para un player."""
    result = {'valor': None, 'delta': None}
    
    for fuente in [texto_seccion, texto_global]:
        if result['valor'] is not None:
            break
        patrones_valor = [
            rf'seguridad.*?{re.escape(player)}.*?(\d+)%',
            rf'{re.escape(player)}.*?seguridad.*?(\d+)%',
            rf'{re.escape(player)}.*?(\d+)%.*?seguridad',
        ]
        for p in patrones_valor:
            match = re.search(p, fuente, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    val = float(match.group(1))
                    if 50 <= val <= 100:
                        result['valor'] = val
                        break
                except (ValueError, IndexError):
                    continue
    
    for fuente in [texto_seccion, texto_global]:
        if result['delta'] is not None:
            break
        patrones_delta = [
            rf'seguridad.*?{re.escape(player)}.*?([+-]\d+)\s*p\.?p\.?',
            rf'{re.escape(player)}.*?seguridad.*?([+-]\d+)\s*p\.?p\.?',
        ]
        for p in patrones_delta:
            match = re.search(p, fuente, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    val = float(match.group(1))
                    if -20 <= val <= 20:
                        result['delta'] = val
                        break
                except (ValueError, IndexError):
                    continue
    
    return result


def _extraer_conclusiones(texto_seccion: str, player: str) -> list:
    """Extrae conclusiones/insights principales de la seccion del player."""
    conclusiones = []
    
    # Buscar oraciones que contengan el player + patrones de conclusion
    patrones = [
        rf'({re.escape(player)}[^\.]+NPS[^\.]+\.)',
        rf'({re.escape(player)}[^\.]+(?:por|impulsad|principal)[^\.]+\.)',
    ]
    
    for patron in patrones:
        matches = re.findall(patron, texto_seccion, re.IGNORECASE)
        for m in matches:
            m_clean = m.strip()
            # Filtrar ruido: no page markers, no demasiado corto/largo
            if (20 < len(m_clean) < 200 
                and m_clean not in conclusiones
                and '--- PAGINA' not in m_clean):
                conclusiones.append(m_clean)
                if len(conclusiones) >= 3:
                    break
        if len(conclusiones) >= 3:
            break
    
    return conclusiones


def _extraer_drivers(texto_seccion: str, player: str) -> list:
    """Extrae drivers principales del NPS de la seccion del player."""
    drivers = []
    
    # Patron: "~Xp.p. por {detalle}" 
    patron_driver = rf'[~]?(\d+)\s*p\.?p\.?\s*(?:por|de|en)\s+([^\n\.;]+)'
    matches = re.findall(patron_driver, texto_seccion, re.IGNORECASE)
    
    for pp, detalle in matches:
        try:
            efecto = float(pp)
            if 0 < efecto <= 15:  # Rango razonable
                detalle_clean = detalle.strip()[:120]
                # Filtrar ruido
                if len(detalle_clean) > 5 and '--- PAGINA' not in detalle_clean:
                    drivers.append({
                        'efecto': f"~{efecto:.0f}pp",
                        'detalle': detalle_clean
                    })
                    if len(drivers) >= 5:
                        break
        except ValueError:
            continue
    
    return drivers


# ==============================================================================
# FUNCION PRINCIPAL DE EXTRACCION
# ==============================================================================

def extraer_datos_players(texto: str, site: str) -> dict:
    """
    Extrae datos de todos los players de un texto de presentacion.
    Primero segmenta el texto por player, luego extrae metricas de cada seccion.
    
    Returns:
        dict: {player_name: {nps_delta, drivers, waterfall_quejas, ...}}
    """
    players = _cargar_players_config(site)
    datos = {}
    
    # Segmentar texto por player (secciones "NPS Competitivo {Player}")
    secciones = _segmentar_por_player(texto, players)
    
    for player in players:
        # Verificar que el player aparece en el texto
        if player.lower() not in texto.lower():
            continue
        
        # Usar la seccion especifica del player si existe, sino el texto completo
        texto_seccion = secciones.get(player, '')
        
        # NPS delta se busca en texto global (esta en el headline general)
        nps_delta = _extraer_nps_delta(texto, player)
        
        # Waterfall se busca en la seccion del player
        waterfall = _extraer_waterfall(texto_seccion, player) if texto_seccion else {}
        
        # Principalidad y seguridad: seccion + global como fallback
        principalidad = _extraer_principalidad(texto, texto_seccion, player)
        seguridad = _extraer_seguridad(texto, texto_seccion, player)
        
        # Conclusiones y drivers de la seccion del player
        conclusiones = _extraer_conclusiones(texto_seccion, player) if texto_seccion else []
        drivers = _extraer_drivers(texto_seccion, player) if texto_seccion else []
        
        # Solo incluir player si tenemos algo util
        has_data = (nps_delta is not None or waterfall or drivers 
                    or principalidad.get('valor') or conclusiones)
        
        if has_data:
            datos[player] = {
                'nps_delta': nps_delta,
                'drivers': drivers,
                'waterfall_quejas': waterfall,
                'principalidad': principalidad,
                'seguridad': seguridad,
                'conclusiones': conclusiones,
            }
    
    return datos


def _extraer_resumen_general(texto: str) -> str:
    """Extrae el resumen/headline general de la presentacion (primeras slides)."""
    # Buscar en las primeras paginas un resumen tipo "Principales conclusiones"
    primeras_paginas = texto[:3000]  # Primeras ~3 paginas
    
    # Buscar lineas largas que sean conclusiones
    lineas = primeras_paginas.split('\n')
    for linea in lineas:
        linea_clean = linea.strip()
        if 30 < len(linea_clean) < 200 and any(kw in linea_clean.lower() for kw in 
            ['líder', 'lider', 'posiciona', 'nps', 'gap', 'principal']):
            return linea_clean
    
    return ""


# ==============================================================================
# CACHE
# ==============================================================================

def parsear_y_cachear(site: str, quarter: str) -> dict:
    """
    Busca el PDF de un site/quarter, lo parsea y guarda en cache.
    Si ya existe cache con mismo MD5, retorna cache.
    
    Returns:
        dict con datos parseados, o None si no hay PDF
    """
    pdf_path = _buscar_pdf(site, quarter)
    if not pdf_path:
        return None
    
    # Verificar cache
    cache_path = CACHE_DIR / f"{site}_{quarter}.json"
    pdf_md5 = _md5_archivo(pdf_path)
    
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            if cache.get('md5') == pdf_md5:
                return cache
        except (json.JSONDecodeError, KeyError):
            pass  # Cache corrupto, re-parsear
    
    # Parsear PDF
    print(f"   [PDF] Parseando presentacion: {pdf_path.name}")
    texto = parsear_pdf(pdf_path)
    if not texto:
        return None
    
    # Extraer datos
    players_data = extraer_datos_players(texto, site)
    resumen = _extraer_resumen_general(texto)
    
    resultado = {
        'source_pdf': f"{site}/{pdf_path.name}",
        'parsed_at': datetime.now().strftime('%Y-%m-%d'),
        'site': site,
        'quarter': quarter,
        'md5': pdf_md5,
        'resumen_general': resumen,
        'players': players_data,
    }
    
    # Guardar cache
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f"   [CACHE] Cache guardado: {cache_path.name}")
    except Exception as e:
        print(f"   [WARN] No se pudo guardar cache: {e}")
    
    return resultado


# ==============================================================================
# FUNCION PUBLICA PRINCIPAL
# ==============================================================================

def cargar_quarter_anterior(site: str, player: str, quarter_actual: str) -> dict:
    """
    Carga datos del quarter anterior para un player especifico.
    
    Args:
        site: Codigo del site (MLB, MLA, MLM, MLC)
        player: Nombre del player
        quarter_actual: Quarter actual (ej: 25Q2)
    
    Returns:
        dict con datos del player en el Q anterior, o None si no hay
        Estructura:
        {
            'quarter': '25Q1',
            'source_pdf': 'MLM/25Q1 _ NPS Competitivo MLM.pdf',
            'resumen_general': '...',
            'nps_delta': -4,
            'drivers': [...],
            'waterfall_quejas': {...},
            'principalidad': {...},
            'seguridad': {...},
            'conclusiones': [...]
        }
    """
    q_anterior = _calcular_quarter_anterior(quarter_actual)
    if not q_anterior:
        return None
    
    # Intentar cargar/parsear la presentacion del Q anterior
    datos = parsear_y_cachear(site, q_anterior)
    if not datos:
        return None
    
    # Buscar el player especifico
    players_data = datos.get('players', {})
    
    # Buscar con nombre exacto
    player_data = players_data.get(player)
    
    # Si no lo encuentra, buscar case-insensitive
    if not player_data:
        for p_name, p_data in players_data.items():
            if p_name.lower() == player.lower():
                player_data = p_data
                break
    
    if not player_data:
        return None
    
    # Enriquecer con metadata
    resultado = {
        'quarter': q_anterior,
        'source_pdf': datos.get('source_pdf', ''),
        'resumen_general': datos.get('resumen_general', ''),
    }
    resultado.update(player_data)
    
    return resultado
