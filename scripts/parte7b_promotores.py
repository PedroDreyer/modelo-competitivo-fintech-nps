# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 7B: ANÁLISIS DE PROMOTORES - ¿POR QUÉ NOS RECOMIENDAN?
═══════════════════════════════════════════════════════════════════════════════

Analiza los motivos de satisfacción de los promotores (NPS=1).
Replica EXACTAMENTE el código del notebook original.

Uso:
    from scripts.parte7b_promotores import analizar_promotores
    resultado = analizar_promotores(df_player, config)
"""

import pandas as pd
import random
import re
from collections import Counter
from pathlib import Path

# ==============================================================================
# COMPETIDORES POR SITE
# ==============================================================================

COMPETIDORES_POR_SITE = {
    'MLB': [
        'nubank', 'nu bank', 'roxinho', 'inter', 'banco inter', 'c6', 'c6 bank',
        'picpay', 'pic pay', 'pagbank', 'pagseguro', 'next', 'bradesco',
        'itaú', 'itau', 'iti', 'santander', 'caixa', 'bb', 'banco do brasil',
        'neon', 'original', 'will bank', 'will', 'ame', 'ame digital'
    ],
    'MLA': [
        'ualá', 'uala', 'naranja x', 'naranja', 'brubank', 'bru bank',
        'galicia', 'santander', 'bbva', 'macro', 'icbc', 'hsbc',
        'banco nación', 'banco nacion', 'provincia', 'ciudad',
        'reba', 'personal pay', 'modo', 'cuenta dni', 'dni'
    ],
    'MLM': [
        'nubank', 'nu', 'stori', 'klar', 'rappi', 'rappicard',
        'bbva', 'bancomer', 'santander', 'banorte', 'citibanamex', 'banamex',
        'hsbc', 'scotiabank', 'hey banco', 'hey', 'albo', 'fondeadora',
        'spin', 'oxxo', 'flink'
    ],
    'MLC': [
        'mach', 'tenpo', 'fintual', 'racional', 'bice', 'banco estado',
        'santander', 'bci', 'scotiabank', 'itaú', 'falabella',
        'banco chile', 'security', 'ripley', 'cencosud'
    ]
}

# ==============================================================================
# CATEGORÍAS DE SATISFACCIÓN (POSITIVAS)
# ==============================================================================

CATEGORIAS_POSITIVAS = {
    'MLB': {  # Brasil - Portugués
        'Facilidade de uso': ['fácil', 'simples', 'prático', 'intuitivo', 'rápido', 'usabilidade', 'app'],
        'Rendimentos': ['rendimento', 'cdi', 'poupança', 'rende', 'investimento', 'guardar dinheiro'],
        'Atendimento': ['atendimento', 'suporte', 'ajuda', 'resolver', 'rápido atendimento'],
        'Segurança': ['seguro', 'segurança', 'confiança', 'confiável', 'proteção'],
        'Cashback/Promoções': ['cashback', 'desconto', 'promoção', 'benefício', 'vantagem', 'pontos'],
        'Cartão/Crédito': ['cartão', 'crédito', 'limite', 'sem anuidade', 'taxa baixa'],
        'Taxas/Gratuidade': ['grátis', 'gratuito', 'sem taxa', 'sem tarifa', 'barato', 'econômico'],
        'Funcionalidades': ['pix', 'transferência', 'pagamento', 'qr code', 'funcionalidade'],
        'Confiança na marca': ['confiança', 'marca', 'sério', 'transparente', 'honesto'],
        'Geral positivo': ['bom', 'ótimo', 'excelente', 'recomendo', 'gosto', 'melhor']
    },
    'MLA': {  # Argentina - Español
        'Facilidad de uso': ['fácil', 'simple', 'práctico', 'intuitivo', 'rápido', 'usabilidad', 'app'],
        'Rendimientos': ['rendimiento', 'interés', 'ahorro', 'rinde', 'inversión', 'guardar plata'],
        'Atención al cliente': ['atención', 'soporte', 'ayuda', 'resolver', 'rápida atención'],
        'Seguridad': ['seguro', 'seguridad', 'confianza', 'confiable', 'protección'],
        'Cashback/Promociones': ['cashback', 'descuento', 'promoción', 'beneficio', 'ventaja', 'puntos'],
        'Tarjeta/Crédito': ['tarjeta', 'crédito', 'límite', 'sin mantenimiento', 'tasa baja'],
        'Costos/Gratuidad': ['gratis', 'gratuito', 'sin costo', 'sin comisión', 'barato', 'económico'],
        'Funcionalidades': ['transferencia', 'pago', 'qr', 'funcionalidad', 'cvu'],
        'Confianza en la marca': ['confianza', 'marca', 'serio', 'transparente', 'honesto'],
        'General positivo': ['bueno', 'excelente', 'recomiendo', 'me gusta', 'mejor']
    },
    'MLM': {  # México - Español
        'Facilidad de uso': ['fácil', 'simple', 'práctico', 'intuitivo', 'rápido', 'app'],
        'Rendimientos': ['rendimiento', 'interés', 'ahorro', 'rinde', 'inversión'],
        'Atención al cliente': ['atención', 'soporte', 'ayuda', 'resolver'],
        'Seguridad': ['seguro', 'seguridad', 'confianza', 'confiable'],
        'Cashback/Promociones': ['cashback', 'descuento', 'promoción', 'beneficio'],
        'Tarjeta/Crédito': ['tarjeta', 'crédito', 'límite', 'sin comisión'],
        'Costos/Gratuidad': ['gratis', 'gratuito', 'sin costo', 'barato'],
        'Funcionalidades': ['transferencia', 'pago', 'spei', 'funcionalidad'],
        'Confianza en la marca': ['confianza', 'marca', 'serio', 'transparente'],
        'General positivo': ['bueno', 'excelente', 'recomiendo', 'me gusta']
    }
}

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def normalizar_encoding(texto):
    """Corrige encoding roto"""
    if pd.isna(texto):
        return str(texto)
    texto = str(texto)
    reemplazos = {
        'Ã£': 'ã', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã§': 'ç', 'Ãª': 'ê', 'Ã´': 'ô', 'Ã¢': 'â', 'Ã£o': 'ão',
        'Ãµ': 'õ', 'Ã¼': 'ü', 'Ã±': 'ñ',
    }
    for mal, bien in reemplazos.items():
        texto = texto.replace(mal, bien)
    return texto


def clasificar_motivo_positivo(comentario, categorias):
    """Clasifica un comentario de promotor en categoría de satisfacción"""
    if pd.isna(comentario) or str(comentario).strip() in ['', '.', 'nan']:
        return 'Sin especificar'
    
    texto = str(comentario).lower()
    texto = texto.replace('ã§', 'ç').replace('ã£', 'ã').replace('ã©', 'é')
    texto = texto.replace('ã³', 'ó').replace('ã­', 'í').replace('ãº', 'ú')
    
    scores = {}
    for categoria, keywords in categorias.items():
        score = sum(1 for kw in keywords if kw in texto)
        if score > 0:
            scores[categoria] = score
    
    if scores:
        return max(scores, key=scores.get)
    
    if len(texto.split()) <= 3:
        return 'General positivo'
    
    return 'Otros positivos'


def extraer_keywords(comentarios_list, top_n=15):
    """Extrae keywords más frecuentes"""
    stopwords_pt = {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com',
                    'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como',
                    'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou', 'ser'}
    stopwords_es = {'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por',
                    'un', 'para', 'con', 'no', 'una', 'su', 'al', 'es', 'lo', 'como', 'más',
                    'pero', 'sus', 'le', 'ya', 'o', 'fue', 'este', 'ha', 'sí', 'porque'}
    stopwords = stopwords_pt | stopwords_es | {'usar', 'usa', 'uso', 'ter', 'fazer', 'muy', 'bien', 'mal'}
    
    if not comentarios_list:
        return {}
    
    texto = normalizar_encoding(' '.join(comentarios_list).lower())
    palabras = re.findall(r'\b[a-záéíóúãõàâêôçñü]{4,}\b', texto)
    palabras_filtradas = [p for p in palabras if p not in stopwords]
    
    return dict(Counter(palabras_filtradas).most_common(top_n))


def detectar_competidores(comentarios_list, competidores, player_actual):
    """Detecta menciones de competidores"""
    if not comentarios_list:
        return []
    
    menciones = {}
    texto_lower = ' '.join(comentarios_list).lower()
    total_comentarios = len(comentarios_list)
    
    competidores_encontrados = set()
    for comp in competidores:
        if comp.lower() in player_actual.lower():
            continue
        
        count = len(re.findall(r'\b' + re.escape(comp) + r'\b', texto_lower))
        if count > 0:
            nombre = comp.title()
            if 'nubank' in comp or 'roxinho' in comp:
                nombre = 'Nubank'
            elif 'inter' in comp:
                nombre = 'Banco Inter'
            elif 'c6' in comp:
                nombre = 'C6 Bank'
            elif 'ualá' in comp or 'uala' in comp:
                nombre = 'Ualá'
            elif 'naranja' in comp:
                nombre = 'Naranja X'
            
            if nombre not in competidores_encontrados:
                competidores_encontrados.add(nombre)
                menciones[nombre] = {
                    'menciones': count,
                    'porcentaje': round((count / total_comentarios) * 100, 1)
                }
    
    return sorted([{'nombre': k, **v} for k, v in menciones.items()],
                  key=lambda x: x['menciones'], reverse=True)


def calcular_distribucion(df_q):
    """Calcula distribución de motivos como % de promotores del quarter"""
    if 'MOTIVO_SATISFACCION' not in df_q.columns or len(df_q) == 0:
        return {}
    
    total_promotores = len(df_q)
    conteo = df_q['MOTIVO_SATISFACCION'].value_counts()
    distribucion = {}
    
    for motivo, count in conteo.items():
        pct = (count / total_promotores * 100) if total_promotores > 0 else 0
        distribucion[motivo] = {
            'count': count,
            'pct': pct
        }
    
    return distribucion


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def analizar_promotores(df_player, config, verbose=True):
    """
    Analiza los motivos de satisfacción de los promotores.
    
    Args:
        df_player: DataFrame con datos del player
        config: Diccionario de configuración
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con promotores_data, distribucion, comentarios
    """
    
    # Extraer configuración
    site = config['site']
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    col_nps = 'NPS'
    col_ola = 'OLA'
    col_comentario = 'COMENTARIO'
    
    # Competidores y categorías del site
    COMPETIDORES = COMPETIDORES_POR_SITE.get(site, COMPETIDORES_POR_SITE['MLA'])
    CATEGORIAS = CATEGORIAS_POSITIVAS.get(site, CATEGORIAS_POSITIVAS['MLA'])
    
    if verbose:
        print(f"🌟 PARTE 7B: Análisis de Promotores - {BANDERA} {NOMBRE_PAIS}")
        print("=" * 70)
        print("📊 ¿Por qué nos recomiendan? Deep Dive en motivos de satisfacción")
        print("=" * 70)
    
    # Filtrar SOLO PROMOTORES (NPS = 1)
    df_promotores = df_player[df_player[col_nps] == 1].copy()
    
    if verbose:
        print(f"\n📊 PROMOTORES - {player}")
        print("=" * 70)
    
    # Promotores por quarter
    df_q1 = df_promotores[df_promotores[col_ola] == q_ant].copy()
    df_q2 = df_promotores[df_promotores[col_ola] == q_act].copy()
    
    # NPS general (para contexto)
    df_q1_all = df_player[df_player[col_ola] == q_ant]
    df_q2_all = df_player[df_player[col_ola] == q_act]
    
    nps_prev = df_q1_all[col_nps].mean() * 100 if len(df_q1_all) > 0 else 0
    nps_last = df_q2_all[col_nps].mean() * 100 if len(df_q2_all) > 0 else 0
    delta_nps = nps_last - nps_prev
    
    # % Promotores
    pct_prom_q1 = (len(df_q1) / len(df_q1_all) * 100) if len(df_q1_all) > 0 else 0
    pct_prom_q2 = (len(df_q2) / len(df_q2_all) * 100) if len(df_q2_all) > 0 else 0
    delta_prom = pct_prom_q2 - pct_prom_q1
    
    if verbose:
        print(f"   {q_ant}: {len(df_q1):,} promotores ({pct_prom_q1:.1f}%)")
        print(f"   {q_act}: {len(df_q2):,} promotores ({pct_prom_q2:.1f}%)")
        print(f"   Delta promotores: {delta_prom:+.1f}pp")
        print(f"\n   NPS: {nps_prev:.1f} → {nps_last:.1f} ({delta_nps:+.1f}pp)")
    
    # Buscar columna de MOTIVO PROMOTORES
    col_motivo_prom = None
    for col in df_promotores.columns:
        col_upper = col.upper()
        if col_upper in ['MOTIVO_PROM', 'M_PROM', 'MOTIVO_PROMO', 'MOTIVO_PROMOTOR']:
            col_motivo_prom = col
            break
        if 'prom' in col.lower() and 'motivo' in col.lower():
            col_motivo_prom = col
            break
    
    if verbose:
        if col_comentario in df_promotores.columns:
            print(f"\n✅ Columna de comentarios: {col_comentario}")
        if col_motivo_prom:
            print(f"✅ Columna motivo promotores: {col_motivo_prom}")
        else:
            print(f"⚠️ No se encontró columna MOTIVO_PROM - se usará clasificación automática")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLASIFICAR MOTIVOS DE SATISFACCIÓN
    # ═══════════════════════════════════════════════════════════════════════════
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"🏷️ CLASIFICANDO MOTIVOS DE SATISFACCIÓN")
        print("=" * 70)
    
    # Determinar fuente de motivos
    col_motivo_fuente = col_motivo_prom if col_motivo_prom and col_motivo_prom in df_promotores.columns else col_comentario
    
    if col_motivo_fuente and col_motivo_fuente in df_promotores.columns:
        n_unicos = df_promotores[col_motivo_fuente].nunique()
        n_registros = len(df_promotores)
        es_texto_libre = n_unicos > 50
        
        if verbose:
            print(f"📋 Columna fuente: {col_motivo_fuente}")
            print(f"   Valores únicos: {n_unicos:,} de {n_registros:,} registros")
        
        if es_texto_libre:
            if verbose:
                print(f"   🔄 Detectado como TEXTO LIBRE → Clasificando automáticamente...")
            df_promotores['MOTIVO_SATISFACCION'] = df_promotores[col_motivo_fuente].apply(
                lambda x: clasificar_motivo_positivo(x, CATEGORIAS)
            )
            if verbose:
                n_categorias = df_promotores['MOTIVO_SATISFACCION'].nunique()
                print(f"   ✅ Agrupado en {n_categorias} categorías")
        else:
            if verbose:
                print(f"   ✅ Detectado como OPCIONES PREDEFINIDAS → Usando directo")
            df_promotores['MOTIVO_SATISFACCION'] = df_promotores[col_motivo_fuente].fillna('Sin especificar')
        
        if verbose:
            print(f"\n   📊 Distribución de categorías:")
            for motivo, count in df_promotores['MOTIVO_SATISFACCION'].value_counts().head(8).items():
                pct = count / n_registros * 100
                motivo_limpio = normalizar_encoding(str(motivo))[:40]
                print(f"      • {motivo_limpio}: {count:,} ({pct:.1f}%)")
    else:
        df_promotores['MOTIVO_SATISFACCION'] = 'Sin especificar'
        if verbose:
            print(f"❌ Sin columna de motivos - análisis limitado")
    
    # Recalcular para Q1 y Q2
    df_q1 = df_promotores[df_promotores[col_ola] == q_ant].copy()
    df_q2 = df_promotores[df_promotores[col_ola] == q_act].copy()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULAR DISTRIBUCIÓN DE MOTIVOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    dist_q1 = calcular_distribucion(df_q1)
    dist_q2 = calcular_distribucion(df_q2)
    
    # Calcular deltas
    todos_motivos = set(dist_q1.keys()) | set(dist_q2.keys())
    motivos_con_delta = []
    
    for motivo in todos_motivos:
        pct_q1 = dist_q1.get(motivo, {}).get('pct', 0)
        pct_q2 = dist_q2.get(motivo, {}).get('pct', 0)
        delta = pct_q2 - pct_q1
        count_q1 = dist_q1.get(motivo, {}).get('count', 0)
        count_q2 = dist_q2.get(motivo, {}).get('count', 0)
        
        motivos_con_delta.append({
            'motivo': motivo,
            'pct_q1': pct_q1,
            'pct_q2': pct_q2,
            'delta': delta,
            'count_q1': count_q1,
            'count_q2': count_q2
        })
    
    motivos_con_delta.sort(key=lambda x: x['pct_q2'], reverse=True)
    
    if verbose:
        print(f"\n📊 DISTRIBUCIÓN DE MOTIVOS DE SATISFACCIÓN")
        print("─" * 70)
        print(f"{'Motivo':<30} {q_ant:>10} {q_act:>10} {'Delta':>10}")
        print("─" * 70)
        
        for m in motivos_con_delta:
            if m['pct_q2'] > 2 or abs(m['delta']) > 1:
                emoji = "📈" if m['delta'] > 1 else "📉" if m['delta'] < -1 else "➡️"
                motivo_limpio = normalizar_encoding(str(m['motivo']))[:30]
                print(f"{motivo_limpio:<30} {m['pct_q1']:>9.1f}% {m['pct_q2']:>9.1f}% {m['delta']:>+9.1f}pp {emoji}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXTRAER COMENTARIOS REALES PARA ANÁLISIS DE CURSOR
    # ═══════════════════════════════════════════════════════════════════════════
    
    comentarios_promotores = {}
    
    if col_comentario in df_promotores.columns:
        for motivo in list(dist_q2.keys())[:8]:  # Top 8 motivos
            df_motivo_q1 = df_q1[df_q1['MOTIVO_SATISFACCION'] == motivo]
            df_motivo_q2 = df_q2[df_q2['MOTIVO_SATISFACCION'] == motivo]
            
            comms_q1 = df_motivo_q1[col_comentario].dropna().astype(str).tolist()
            comms_q1 = [normalizar_encoding(c) for c in comms_q1 if len(c) > 10]
            
            comms_q2 = df_motivo_q2[col_comentario].dropna().astype(str).tolist()
            comms_q2 = [normalizar_encoding(c) for c in comms_q2 if len(c) > 10]
            
            comentarios_promotores[motivo] = {
                'q1': comms_q1[:25],
                'q2': comms_q2[:25],
                'count_q1': len(comms_q1),
                'count_q2': len(comms_q2)
            }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RESUMEN
    # ═══════════════════════════════════════════════════════════════════════════
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"📋 RESUMEN - ¿POR QUÉ NOS RECOMIENDAN?")
        print("=" * 70)
        
        print(f"\n🌟 Promotores: {pct_prom_q1:.1f}% → {pct_prom_q2:.1f}% ({delta_prom:+.1f}pp)")
        print(f"📊 NPS: {nps_prev:.1f} → {nps_last:.1f} ({delta_nps:+.1f}pp)")
        
        # Top 3 motivos
        print(f"\n🏆 TOP 3 POR QUÉ NOS RECOMIENDAN:")
        for i, m in enumerate(motivos_con_delta[:3], 1):
            motivo_limpio = normalizar_encoding(str(m['motivo']))[:50]
            print(f"   {i}. {motivo_limpio} ({m['pct_q2']:.1f}% de promotores)")
        
        # Motivos que mejoraron
        mejoraron = [m for m in motivos_con_delta if m['delta'] > 1]
        if mejoraron:
            print(f"\n📈 MOTIVOS QUE CRECIERON:")
            for m in mejoraron[:3]:
                motivo_limpio = normalizar_encoding(str(m['motivo']))[:40]
                print(f"   • {motivo_limpio}: {m['delta']:+.1f}pp")
        
        # Motivos que empeoraron
        empeoraron = [m for m in motivos_con_delta if m['delta'] < -1]
        if empeoraron:
            print(f"\n📉 MOTIVOS QUE BAJARON:")
            for m in empeoraron[:3]:
                motivo_limpio = normalizar_encoding(str(m['motivo']))[:40]
                print(f"   • {motivo_limpio}: {m['delta']:+.1f}pp")
        
        print(f"\n{'='*70}")
        print(f"✅ PARTE 7B OK - {len(motivos_con_delta)} motivos de satisfacción analizados")
        print("=" * 70)
    
    return {
        'promotores_data': motivos_con_delta,
        'distribucion_q1': dist_q1,
        'distribucion_q2': dist_q2,
        'comentarios_promotores': comentarios_promotores,
        'pct_prom_q1': pct_prom_q1,
        'pct_prom_q2': pct_prom_q2,
        'delta_prom': delta_prom,
        'nps_prev': nps_prev,
        'nps_last': nps_last,
        'delta_nps': delta_nps,
        'df_promotores': df_promotores
    }


# ==============================================================================
# FUNCIÓN PARA EXPORTAR COMENTARIOS DE PROMOTORES PARA CURSOR
# ==============================================================================

def exportar_comentarios_promotores(resultado_7b, config, max_comentarios=20, verbose=True):
    """
    Exporta comentarios REALES de promotores para que Cursor los analice.
    
    IMPORTANTE: Esta función NUNCA inventa comentarios.
    Todos los comentarios provienen de la base de datos real.
    """
    
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    player = config['player']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    comentarios = resultado_7b['comentarios_promotores']
    
    if verbose:
        print("=" * 80)
        print(f"📝 COMENTARIOS REALES DE PROMOTORES - {BANDERA} {NOMBRE_PAIS}")
        print(f"   Player: {player}")
        print(f"   Quarters: {q_ant} vs {q_act}")
        print("=" * 80)
        print("\n⚠️  IMPORTANTE: Todos los comentarios son REALES de la base de datos.")
        print("    Cursor debe analizarlos para entender por qué nos recomiendan.\n")
    
    for motivo, data in comentarios.items():
        if data['count_q2'] < 5:
            continue
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"🌟 MOTIVO: {motivo}")
            print(f"   Comentarios: {data['count_q1']} ({q_ant}) → {data['count_q2']} ({q_act})")
            print("=" * 80)
            
            if data['q2']:
                print(f"\n💬 Lo que dicen los promotores ({q_act}):")
                print("-" * 60)
                for i, c in enumerate(data['q2'][:max_comentarios], 1):
                    c_truncado = c[:150] + "..." if len(c) > 150 else c
                    print(f"   {i}. \"{c_truncado}\"")
    
    return comentarios


# ==============================================================================
# ANÁLISIS SEMÁNTICO DE PROMOTORES (Deep Dive con LLM)
# ==============================================================================

def preparar_analisis_semantico_promotores(resultado_7b, df_player, config,
                                            max_comentarios_por_motivo=100, verbose=True):
    """
    Prepara comentarios de promotores por motivo para análisis semántico con LLM.

    Similar a preparar_analisis_semantico() de causas_raiz, pero para feedback positivo.
    Identifica las causas de satisfacción emergentes de forma semántica.

    Args:
        resultado_7b: Dict con resultado de analizar_promotores()
        df_player: DataFrame del player
        config: Dict de configuración
        max_comentarios_por_motivo: Máximo de comentarios a incluir por motivo
        verbose: Si True, imprime info

    Returns:
        dict con:
            - prompt_path: path al archivo de prompt generado
            - datos_por_motivo: dict con comentarios preparados por motivo
    """
    site = config['site']
    player = config['player']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    col_ola = 'OLA'
    col_nps = 'NPS'

    if verbose:
        print(f"\n🌟 ANÁLISIS SEMÁNTICO DE PROMOTORES")
        print("=" * 70)

    # Obtener datos de promotores y comentarios
    promotores_data = resultado_7b.get('promotores_data', [])
    comentarios_dict = resultado_7b.get('comentarios_promotores', {})

    # Detectar columna de comentarios
    col_comentario = None
    for col_name in ['COMENTARIO', 'Comentarios', 'comentario']:
        if col_name in df_player.columns:
            valores = df_player[col_name].dropna()
            if len(valores[valores.astype(str).str.len() > 3]) > 10:
                col_comentario = col_name
                break

    if not col_comentario:
        if verbose:
            print("   ⚠️ No se encontró columna de comentarios")
        return {'prompt_path': None, 'datos_por_motivo': {}}

    # Filtrar SOLO PROMOTORES (NPS = 1)
    df_promotores = df_player[df_player[col_nps] == 1].copy()

    # Obtener columna de motivo clasificado (si existe)
    col_motivo = None
    for col in df_promotores.columns:
        if 'MOTIVO_CLASIFICADO' in col.upper():
            col_motivo = col
            break

    if not col_motivo:
        if verbose:
            print("   ⚠️ No se encontró columna MOTIVO_CLASIFICADO")
        return {'prompt_path': None, 'datos_por_motivo': {}}

    # Filtrar motivos relevantes - excluir genéricos
    motivos_excluir = ['Otro', 'Otros', 'Outros', 'General positivo', 'Geral positivo']

    # Preparar comentarios por motivo
    datos_por_motivo = {}

    # Ordenar por delta descendente (mejores mejoras primero)
    promotores_ordenados = sorted(promotores_data, key=lambda x: x.get('delta', 0), reverse=True)

    for motivo_data in promotores_ordenados:
        motivo = motivo_data.get('motivo', '')

        # Saltar motivos genéricos
        if motivo in motivos_excluir:
            continue

        delta = motivo_data.get('delta', 0)
        pct_q2 = motivo_data.get('pct_q2', 0)
        pct_q1 = motivo_data.get('pct_q1', 0)

        # Filtrar por motivo
        df_motivo = df_promotores[df_promotores[col_motivo] == motivo]

        # Q2 (actual) - priorizamos el quarter actual
        df_q2 = df_motivo[df_motivo[col_ola] == q_act]
        comms_q2 = df_q2[col_comentario].dropna().astype(str).tolist()
        comms_q2 = [normalizar_encoding(c) for c in comms_q2 if len(c.strip()) > 15]

        # Q1 (anterior)
        df_q1 = df_motivo[df_motivo[col_ola] == q_ant]
        comms_q1 = df_q1[col_comentario].dropna().astype(str).tolist()
        comms_q1 = [normalizar_encoding(c) for c in comms_q1 if len(c.strip()) > 15]

        if len(comms_q2) < 5:
            if verbose:
                print(f"   ⏭️  {motivo}: muy pocos comentarios en {q_act}, skip")
            continue

        # Limitar comentarios (solo Q2)
        if len(comms_q2) > max_comentarios_por_motivo:
            comms_q2 = random.sample(comms_q2, max_comentarios_por_motivo)

        datos_por_motivo[motivo] = {
            'delta': delta,
            'pct_actual': pct_q2,
            'pct_anterior': pct_q1,
            'comentarios_q2': comms_q2,
            'comentarios_q1_count': len(comms_q1),
            'comentarios_q2_count': len(comms_q2),
        }

        if verbose:
            emoji = "🔥" if delta > 1 else "✅" if delta > 0 else "➡️"
            print(f"   {emoji} {motivo}: {delta:+.1f}pp, {len(comms_q2)} comentarios")

    if not datos_por_motivo:
        if verbose:
            print("   ⚠️ No hay motivos con suficientes comentarios para analizar")
        return {'prompt_path': None, 'datos_por_motivo': {}}

    # Generar prompt
    prompt = _generar_prompt_semantico_promotores(datos_por_motivo, player, site, q_ant, q_act)

    # Guardar prompt - carpeta prompts/ en la raíz del proyecto
    script_dir = Path(__file__).resolve().parent
    prompts_dir = script_dir.parent / 'prompts'
    prompts_dir.mkdir(exist_ok=True)
    prompt_filename = f'prompt_promotores_{player}_{q_act}.txt'
    prompt_path = prompts_dir / prompt_filename

    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)

    if verbose:
        print(f"\n   ✅ Prompt generado: {prompt_path}")
        print(f"   📋 {len(datos_por_motivo)} motivos con comentarios para analizar")

    return {
        'prompt_path': str(prompt_path),
        'datos_por_motivo': datos_por_motivo,
    }


def _generar_prompt_semantico_promotores(datos_por_motivo, player, site, q_ant, q_act):
    """Genera el prompt estructurado para análisis semántico de causas de satisfacción."""

    prompt = f"""
# 🌟 ANÁLISIS SEMÁNTICO DE PROMOTORES - NPS COMPETITIVO

## Contexto
Analiza los comentarios de usuarios promotores de **{player}** en **{site}** para identificar
las **causas de satisfacción** específicas de cada motivo de recomendación.

**Quarters comparados:** {q_ant} → {q_act}
**Motivos a analizar:** {len(datos_por_motivo)}

## Instrucciones

Para cada motivo:
1. **Leer TODOS los comentarios** del quarter actual ({q_act})
2. **Identificar patrones semánticos** (no solo palabras, sino fortalezas subyacentes)
3. **Agrupar por causa de satisfacción** (mínimo 2, máximo 4 causas por motivo)
4. **Generar título descriptivo** (específico y accionable, no genérico)
5. **Calcular frecuencia** de cada causa (% y cantidad)
6. **Seleccionar 2-3 ejemplos** representativos

## Formato de salida REQUERIDO

Responde ÚNICAMENTE con un JSON válido:

```json
{{
  "metadata": {{
    "player": "{player}",
    "site": "{site}",
    "quarter": "{q_act}",
    "metodo": "analisis_semantico_promotores"
  }},
  "causas_por_motivo": {{
    "NombreMotivo": {{
      "total_comentarios_analizados": 50,
      "delta_pp": 1.5,
      "causas_satisfaccion": [
        {{
          "titulo": "Título descriptivo y específico",
          "descripcion": "Explicación breve de la fortaleza identificada",
          "frecuencia_pct": 45,
          "frecuencia_abs": 22,
          "ejemplos": [
            "comentario real del usuario...",
            "otro comentario real..."
          ]
        }}
      ]
    }}
  }}
}}
```

---

## 📋 COMENTARIOS POR MOTIVO

"""

    for motivo, datos in datos_por_motivo.items():
        delta = datos['delta']
        n_q2 = datos['comentarios_q2_count']
        n_q1 = datos['comentarios_q1_count']
        pct_ant = datos['pct_anterior']
        pct_act = datos['pct_actual']
        comentarios = datos['comentarios_q2']

        emoji = "🔥" if delta > 1 else "✅" if delta > 0 else "➡️"
        direccion = "SUBIÓ" if delta > 0 else "BAJÓ" if delta < 0 else "ESTABLE"

        prompt += f"""
### {emoji} MOTIVO: {motivo} ({delta:+.1f}pp - {direccion})

**Proporción:** {pct_ant:.1f}% → {pct_act:.1f}% | **Comentarios:** {n_q1} ({q_ant}) → {n_q2} ({q_act})

**Comentarios {q_act}:**

"""
        for i, c in enumerate(comentarios, 1):
            c_limpio = c[:250] + '...' if len(c) > 250 else c
            prompt += f'{i}. "{c_limpio}"\n\n'

        prompt += "\n" + "=" * 80 + "\n"

    output_filename = f'promotores_semantico_{player}_{q_act}.json'

    prompt += f"""
## 📝 INSTRUCCIONES FINALES

1. **Guardar el archivo** usando Write tool:
   - **Path:** `data/{output_filename}`
2. **Confirmar** que se guardó correctamente

IMPORTANTE:
- Los títulos deben ser ESPECÍFICOS (no "Buen servicio" sino "Resolución rápida de problemas en menos de 2 horas")
- Cada causa de satisfacción debe ser DIFERENTE a las demás (no solapar)
- Los ejemplos deben ser TEXTUALES de los comentarios arriba
- Enfócate en las FORTALEZAS que podemos mantener y potenciar
- Usa lenguaje POSITIVO (no "no tiene problemas" sino "funciona sin fricciones")
"""

    return prompt


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    from parte3_calculo_nps import calcular_nps
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 7B: ANÁLISIS DE PROMOTORES")
    print("=" * 70)
    
    try:
        # Cargar datos
        resultado_carga = cargar_datos(verbose=False)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        # Filtrar player
        player = config['player']
        df_player = df_completo[df_completo['MARCA'] == player].copy()
        
        # Analizar promotores
        resultado_7b = analizar_promotores(df_player, config, verbose=True)
        
        # Exportar comentarios para análisis de Cursor
        print("\n")
        comentarios = exportar_comentarios_promotores(resultado_7b, config, max_comentarios=10, verbose=True)
        
        print("\n📋 Variables exportadas:")
        print(f"   promotores_data: {len(resultado_7b['promotores_data'])} motivos")
        print(f"   comentarios_promotores: {len(resultado_7b['comentarios_promotores'])} motivos con comentarios")
        
        print("\n✅ Prueba PARTE 7B completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
