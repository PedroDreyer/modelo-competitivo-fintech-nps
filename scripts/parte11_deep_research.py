# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 11: DEEP RESEARCH - BÚSQUEDA Y ANÁLISIS DE NOTICIAS
═══════════════════════════════════════════════════════════════════════════════

Esta parte prepara los datos para que Cursor actúe como agente de IA
realizando búsquedas web de noticias relacionadas con las variaciones de NPS.

IMPORTANTE: Cursor debe usar WebSearch para buscar noticias reales.

Uso:
    from scripts.parte11_deep_research import preparar_deep_research
    instrucciones = preparar_deep_research(resultado_7, resultado_8, config)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# ==============================================================================
# DOMINIOS CONFIABLES POR SITE
# ==============================================================================

DOMINIOS_CONFIABLES = {
    'MLB': [
        'infomoney.com.br', 'valor.globo.com', 'exame.com', 'estadao.com.br',
        'folha.uol.com.br', 'g1.globo.com', 'canaltech.com.br', 'tecmundo.com.br',
        'mobiletime.com.br', 'reclameaqui.com.br', 'seudinheiro.com',
        'moneytimes.com.br', 'forbes.com.br', 'startse.com'
    ],
    'MLA': [
        'infobae.com', 'lanacion.com.ar', 'clarin.com', 'ambito.com',
        'cronista.com', 'iprofesional.com', 'pagina12.com.ar', 'tn.com.ar',
        'infotechnology.com', 'cace.org.ar', 'bcra.gob.ar', 'forbes.com.ar'
    ],
    'MLM': [
        'elfinanciero.com.mx', 'eleconomista.com.mx', 'expansion.mx',
        'forbes.com.mx', 'milenio.com', 'reforma.com', 'jornada.com.mx',
        'xataka.com.mx', 'hipertextual.com', 'condusef.gob.mx'
    ]
}

CATEGORIAS_NOTICIAS = {
    'Rendimientos': ['rendimiento', 'CDI', 'poupança', 'inversión', 'ahorro', 'interés', 'tasa'],
    'Financiamiento': ['crédito', 'préstamo', 'empréstimo', 'límite', 'tarjeta', 'cartão'],
    'Atención': ['atención', 'atendimento', 'soporte', 'SAC', 'reclamo', 'queja'],
    'Seguridad': ['seguridad', 'segurança', 'fraude', 'golpe', 'estafa', 'hack'],
    'Funcionalidades': ['app', 'aplicativo', 'función', 'feature', 'actualización', 'bug'],
    'Promociones': ['promoción', 'promoção', 'cashback', 'descuento', 'beneficio'],
    'Complejidad': ['interfaz', 'usabilidad', 'difícil', 'complejo', 'confuso']
}


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def preparar_deep_research(resultado_causas_raiz, resultado_productos, config, verbose=True, causas_semanticas=None):
    """
    Prepara los datos y genera instrucciones para que Cursor
    realice Deep Research buscando noticias relacionadas.
    
    Args:
        resultado_causas_raiz: Resultado de parte7_causas_raiz
        resultado_productos: Resultado de parte8_productos
        config: Diccionario de configuración
        causas_semanticas: Dict de causas raíz semánticas por motivo (del JSON LLM)
        
    Returns:
        dict: Instrucciones y datos para Deep Research
    """
    causas_semanticas = causas_semanticas or {}
    
    site = config['site']
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    # Calcular rango de fechas (formato: 25Q4 -> year=2025, quarter=4)
    year = int('20' + q_act[:2])
    quarter = int(q_act[-1])
    
    meses_quarter = {1: 'Ene-Mar', 2: 'Abr-Jun', 3: 'Jul-Sep', 4: 'Oct-Dic'}
    rango_fechas = f"{meses_quarter[quarter]} {year}"
    
    if verbose:
        print("=" * 80)
        print(f"🔍 PARTE 11: DEEP RESEARCH - {BANDERA} {NOMBRE_PAIS}")
        print("=" * 80)
        print(f"\n🎯 Player: {player}")
        print(f"📅 Período: {q_ant} vs {q_act}")
        print(f"📆 Rango de búsqueda: {rango_fechas}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXTRAER PRINCIPALES CAMBIOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    cambios_quejas = []
    cambios_productos = []
    
    # Extraer cambios de causas raíz
    if resultado_causas_raiz and 'waterfall_data' in resultado_causas_raiz:
        waterfall = resultado_causas_raiz['waterfall_data']
        for item in waterfall:
            if abs(item.get('delta', 0)) >= 1:  # Cambios >= 1pp
                cambios_quejas.append({
                    'categoria': item.get('motivo', 'Desconocido'),
                    'delta': item.get('delta', 0),
                    'direccion': 'aumentó' if item.get('delta', 0) > 0 else 'disminuyó',
                    'pct_q2': item.get('pct_q2', 0)
                })
    
    # Extraer cambios de productos
    if resultado_productos and 'productos_clave' in resultado_productos:
        for prod in resultado_productos['productos_clave']:
            if abs(prod.get('total_effect', 0)) >= 0.3:  # Efecto >= 0.3pp
                cambios_productos.append({
                    'producto': prod.get('nombre_original', 'Desconocido'),
                    'delta_share': prod.get('delta_share', 0),
                    'delta_nps': prod.get('delta_nps_usuario', 0),
                    'total_effect': prod.get('total_effect', 0)
                })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GENERAR QUERIES DE BÚSQUEDA
    # ═══════════════════════════════════════════════════════════════════════════
    
    queries = []
    
    # Query general
    queries.append(f"{player} {NOMBRE_PAIS} {year} noticias fintech")
    
    # Queries por cambio de queja
    for cambio in cambios_quejas[:5]:
        categoria = cambio['categoria']
        if categoria in CATEGORIAS_NOTICIAS:
            keywords = CATEGORIAS_NOTICIAS[categoria][:2]
            queries.append(f"{player} {keywords[0]} {year}")
    
    # Queries por productos
    for prod in cambios_productos[:3]:
        producto = prod['producto'].lower()
        if 'rendim' in producto or 'invest' in producto:
            queries.append(f"{player} rendimientos inversión {year}")
        elif 'créd' in producto or 'tarj' in producto or 'cart' in producto:
            queries.append(f"{player} tarjeta crédito {year}")
    
    # NUEVO: Queries basadas en causas raíz semánticas (más específicas)
    queries_causa_raiz = []
    if causas_semanticas:
        import re
        stopwords = {'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'en', 'por',
                     'para', 'con', 'sin', 'al', 'a', 'y', 'o', 'que', 'se', 'no', 'es'}
        for motivo, datos in causas_semanticas.items():
            causas = datos.get('causas_raiz', [])
            if causas:
                titulo = causas[0].get('titulo', '')
                # Limpiar título → keywords
                limpio = re.sub(r'\([^)]*\)', '', titulo)
                limpio = re.sub(r'\d+[%.,]?\d*%?', '', limpio)
                limpio = re.sub(r'[^\w\sáéíóúñü]', ' ', limpio)
                keywords = [p.lower() for p in limpio.split() if len(p) > 2 and p.lower() not in stopwords]
                if len(keywords) >= 2:
                    kw_text = ' '.join(keywords[:3])
                    q = f"{player} {NOMBRE_PAIS} {kw_text} {year}"
                    queries_causa_raiz.append(q)
                    queries.append(q)
    
    queries = list(set(queries))[:12]  # Máximo 12 queries únicas (ampliado por causas raíz)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GENERAR INSTRUCCIONES PARA CURSOR
    # ═══════════════════════════════════════════════════════════════════════════
    
    dominios = DOMINIOS_CONFIABLES.get(site, DOMINIOS_CONFIABLES['MLA'])
    
    instrucciones = f"""
═══════════════════════════════════════════════════════════════════════════════
🔍 INSTRUCCIONES PARA CURSOR - DEEP RESEARCH
═══════════════════════════════════════════════════════════════════════════════

Player: {player}
País: {NOMBRE_PAIS}
Período: {q_act}
Rango de fechas: {rango_fechas}

═══════════════════════════════════════════════════════════════════════════════
📊 CAMBIOS PRINCIPALES A INVESTIGAR
═══════════════════════════════════════════════════════════════════════════════
"""
    
    if cambios_quejas:
        instrucciones += "\n🔴 QUEJAS QUE CAMBIARON:\n"
        for c in cambios_quejas[:5]:
            emoji = "📈" if c['delta'] > 0 else "📉"
            instrucciones += f"   {emoji} {c['categoria']}: {c['delta']:+.1f}pp ({c['direccion']})\n"
    
    if cambios_productos:
        instrucciones += "\n📦 PRODUCTOS CON IMPACTO:\n"
        for p in cambios_productos[:3]:
            emoji = "🟢" if p['total_effect'] > 0 else "🔴"
            instrucciones += f"   {emoji} {p['producto']}: {p['total_effect']:+.2f}pp en NPS\n"
    
    # NUEVO: Incluir causas raíz semánticas como contexto para que Cursor sepa qué buscar
    if causas_semanticas:
        instrucciones += f"""
═══════════════════════════════════════════════════════════════════════════════
🧠 CAUSAS RAÍZ SEMÁNTICAS (del análisis de comentarios)
═══════════════════════════════════════════════════════════════════════════════
IMPORTANTE: Estas son las causas reales identificadas en los comentarios.
Buscar noticias que CONFIRMEN o EXPLIQUEN estas causas.
"""
        for motivo, datos in causas_semanticas.items():
            causas = datos.get('causas_raiz', [])
            delta = datos.get('delta_pp', 0)
            if causas:
                instrucciones += f"\n   📌 {motivo} ({delta:+.1f}pp):\n"
                for j, causa in enumerate(causas[:3], 1):
                    titulo = causa.get('titulo', '')
                    freq = causa.get('frecuencia_pct', 0)
                    instrucciones += f"      {j}. {titulo} ({freq}% de comentarios)\n"
    
    instrucciones += f"""
═══════════════════════════════════════════════════════════════════════════════
🔎 QUERIES SUGERIDAS PARA WebSearch
═══════════════════════════════════════════════════════════════════════════════
"""
    for i, query in enumerate(queries, 1):
        instrucciones += f"   {i}. {query}\n"
    
    instrucciones += f"""
═══════════════════════════════════════════════════════════════════════════════
📰 DOMINIOS CONFIABLES (priorizar estos)
═══════════════════════════════════════════════════════════════════════════════
{', '.join(dominios[:8])}

═══════════════════════════════════════════════════════════════════════════════
📝 FORMATO DE RESPUESTA ESPERADO
═══════════════════════════════════════════════════════════════════════════════

Para cada noticia relevante encontrada:

{{
    "titulo": "Título de la noticia",
    "fuente": "dominio.com",
    "fecha": "YYYY-MM",
    "resumen": "Resumen breve (2-3 oraciones)",
    "categoria_relacionada": "Rendimientos|Financiamiento|Atención|Seguridad|...",
    "impacto_esperado": "positivo|negativo|neutro",
    "relevancia": "alta|media|baja"
}}

═══════════════════════════════════════════════════════════════════════════════
⚠️ IMPORTANTE
═══════════════════════════════════════════════════════════════════════════════
1. Usar WebSearch para buscar noticias REALES
2. Priorizar noticias del período {rango_fechas}
3. Buscar noticias que expliquen los cambios observados en quejas/productos
4. Filtrar por dominios confiables cuando sea posible
5. Máximo 5-8 noticias relevantes por análisis
"""
    
    if verbose:
        print(instrucciones)
        
        print("\n" + "=" * 80)
        print("✅ PARTE 11 OK - Instrucciones de Deep Research generadas")
        print("=" * 80)
        print("\n⚠️  ACCIÓN REQUERIDA: Cursor debe ejecutar WebSearch con las queries sugeridas")
        print("    y analizar las noticias encontradas para relacionarlas con los cambios de NPS.")
    
    return {
        'instrucciones': instrucciones,
        'queries': queries,
        'queries_causa_raiz': queries_causa_raiz,
        'cambios_quejas': cambios_quejas,
        'cambios_productos': cambios_productos,
        'causas_semanticas_usadas': bool(causas_semanticas),
        'dominios_confiables': dominios,
        'rango_fechas': rango_fechas,
        'config': {
            'player': player,
            'site': site,
            'q_act': q_act,
            'year': year
        }
    }


def procesar_noticias_encontradas(noticias, cambios_quejas, verbose=True):
    """
    Procesa las noticias encontradas por Cursor y las mapea a categorías.
    
    Args:
        noticias: Lista de noticias encontradas (dict)
        cambios_quejas: Cambios de quejas detectados
        
    Returns:
        dict: Noticias procesadas y mapeadas
    """
    
    if verbose:
        print("\n" + "=" * 80)
        print("📰 PROCESANDO NOTICIAS ENCONTRADAS")
        print("=" * 80)
    
    noticias_mapeadas = []
    
    for noticia in noticias:
        categoria = noticia.get('categoria_relacionada', 'Otros')
        
        # Buscar si hay un cambio de queja relacionado
        cambio_relacionado = None
        for cambio in cambios_quejas:
            if cambio['categoria'].lower() in categoria.lower():
                cambio_relacionado = cambio
                break
        
        noticias_mapeadas.append({
            **noticia,
            'cambio_relacionado': cambio_relacionado
        })
        
        if verbose:
            print(f"\n📰 {noticia.get('titulo', 'Sin título')}")
            print(f"   Fuente: {noticia.get('fuente', 'Desconocida')}")
            print(f"   Categoría: {categoria}")
            if cambio_relacionado:
                print(f"   🔗 Relacionado con: {cambio_relacionado['categoria']} ({cambio_relacionado['delta']:+.1f}pp)")
    
    return {
        'noticias_mapeadas': noticias_mapeadas,
        'total_noticias': len(noticias),
        'noticias_con_relacion': len([n for n in noticias_mapeadas if n['cambio_relacionado']])
    }


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 11: DEEP RESEARCH")
    print("=" * 70)
    
    try:
        resultado_carga = cargar_datos(verbose=False)
        config = resultado_carga['config']
        
        # Simular resultados de partes anteriores
        resultado_causas_raiz = {
            'waterfall_data': [
                {'motivo': 'Financiamiento', 'delta': 2.5, 'pct_q2': 15.0},
                {'motivo': 'Rendimientos', 'delta': -1.8, 'pct_q2': 12.0},
                {'motivo': 'Seguridad', 'delta': 1.2, 'pct_q2': 5.0}
            ]
        }
        
        resultado_productos = {
            'productos_clave': [
                {'nombre_original': 'Rendimentos', 'delta_share': -2.3, 'delta_nps_usuario': -1.7, 'total_effect': -0.91},
                {'nombre_original': 'Cartão de crédito', 'delta_share': 0.5, 'delta_nps_usuario': 3.4, 'total_effect': 0.98}
            ]
        }
        
        resultado_11 = preparar_deep_research(resultado_causas_raiz, resultado_productos, config, verbose=True)
        
        print("\n📋 Variables exportadas:")
        print(f"   queries: {len(resultado_11['queries'])} queries")
        print(f"   cambios_quejas: {len(resultado_11['cambios_quejas'])} cambios")
        
        print("\n✅ Prueba PARTE 11 completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
