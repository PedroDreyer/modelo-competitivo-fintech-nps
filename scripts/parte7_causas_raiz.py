# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 7: ANÁLISIS INTELIGENTE DE CAUSA RAÍZ
═══════════════════════════════════════════════════════════════════════════════

Genera subcausas para cada motivo del waterfall comparando Q1 vs Q2.
Esta parte requiere INTERVENCIÓN DE IA - Cursor actúa como agente analítico.

Uso:
    from scripts.parte7_causas_raiz import analizar_causas_raiz
    resultado = analizar_causas_raiz(resultado_parte6, resultado_parte5, df_player, config)
"""

import pandas as pd
import random
import re
import json
from collections import Counter
from pathlib import Path

# ==============================================================================
# COMPETIDORES POR SITE
# ==============================================================================

COMPETIDORES_POR_SITE = {
    'MLB': [  # Brasil
        'nubank', 'nu bank', 'roxinho', 'inter', 'banco inter', 'c6', 'c6 bank',
        'picpay', 'pic pay', 'pagbank', 'pagseguro', 'next', 'bradesco',
        'itaú', 'itau', 'iti', 'santander', 'caixa', 'bb', 'banco do brasil',
        'neon', 'original', 'will bank', 'will', 'ame', 'ame digital'
    ],
    'MLA': [  # Argentina
        'ualá', 'uala', 'naranja x', 'naranja', 'brubank', 'bru bank',
        'galicia', 'santander', 'bbva', 'macro', 'icbc', 'hsbc',
        'banco nación', 'banco nacion', 'provincia', 'ciudad',
        'reba', 'personal pay', 'modo', 'cuenta dni', 'dni'
    ],
    'MLM': [  # México
        'nubank', 'nu', 'stori', 'klar', 'rappi', 'rappicard',
        'bbva', 'bancomer', 'santander', 'banorte', 'citibanamex', 'banamex',
        'hsbc', 'scotiabank', 'hey banco', 'hey', 'albo', 'fondeadora',
        'spin', 'oxxo', 'flink'
    ],
    'MLC': [  # Chile
        'mach', 'tenpo', 'fintual', 'racional', 'bice', 'banco estado',
        'santander', 'bci', 'scotiabank', 'itaú', 'falabella',
        'banco chile', 'security', 'ripley', 'cencosud'
    ]
}

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def normalizar_encoding(texto):
    """Corrige encoding roto (UTF-8 mal interpretado)"""
    reemplazos = {
        'Ã£': 'ã', 'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã§': 'ç', 'Ã': 'í', 'Ãª': 'ê', 'Ã´': 'ô', 'Ã¢': 'â',
        'confianã': 'confiança', 'seguranã': 'segurança', 'promoã': 'promoção',
        'crã©dito': 'crédito', 'crã': 'cré', 'taxã': 'taxa', 'aplicaã': 'aplicaç',
    }
    for mal, bien in reemplazos.items():
        texto = texto.replace(mal, bien)
    return texto


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
            # Normalizar nombres
            if 'nubank' in comp or 'roxinho' in comp or 'nu bank' in comp:
                nombre = 'Nubank'
            elif 'inter' in comp:
                nombre = 'Banco Inter'
            elif 'c6' in comp:
                nombre = 'C6 Bank'
            elif 'picpay' in comp:
                nombre = 'PicPay'
            elif 'pagbank' in comp or 'pagseguro' in comp:
                nombre = 'PagBank'
            elif 'ualá' in comp or 'uala' in comp:
                nombre = 'Ualá'
            elif 'naranja' in comp:
                nombre = 'Naranja X'
            elif 'brubank' in comp:
                nombre = 'Brubank'
            elif 'itaú' in comp or 'itau' in comp:
                nombre = 'Itaú'
            elif 'caixa' in comp:
                nombre = 'Caixa'
            elif 'bb' in comp or 'banco do brasil' in comp:
                nombre = 'Banco Do Brasil'
            
            if nombre not in competidores_encontrados:
                competidores_encontrados.add(nombre)
                menciones[nombre] = {
                    'menciones': count,
                    'porcentaje': round((count / total_comentarios) * 100, 1)
                }
    
    return sorted([{'nombre': k, **v} for k, v in menciones.items()],
                  key=lambda x: x['menciones'], reverse=True)


def analizar_tendencias_q1_q2(kw_q1, kw_q2):
    """Analiza cambios en keywords entre Q1 y Q2"""
    nuevos = {k: v for k, v in kw_q2.items() if k not in kw_q1 and v >= 3}
    nuevos_sorted = sorted(nuevos.items(), key=lambda x: x[1], reverse=True)[:5]
    
    crecientes = []
    for k in set(kw_q1.keys()) & set(kw_q2.keys()):
        diff = kw_q2[k] - kw_q1[k]
        if diff > 0 and kw_q1[k] > 0:
            pct = round((diff / kw_q1[k]) * 100)
            if pct >= 20:
                crecientes.append((k, pct, kw_q2[k]))
    crecientes = sorted(crecientes, key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'nuevos_temas': [k for k, v in nuevos_sorted],
        'temas_crecientes': [(k, pct) for k, pct, _ in crecientes],
    }


def mapear_motivo_categoria(motivo):
    """Mapea motivos a categorías unificadas.
    
    Soporta tanto categorías granulares de BigQuery (ej: 'Acceso a crédito o tarjeta de crédito')
    como categorías ya simplificadas (ej: 'Financiamiento', 'Complejidad').
    """
    if pd.isna(motivo) or str(motivo).strip() in ['', '.', 'nan']:
        return 'Sin opinión'
    m = str(motivo).strip()
    m_lower = m.lower()
    m_lower = m_lower.replace('ã§', 'ç').replace('ã£', 'ã').replace('ã©', 'é')
    m_lower = m_lower.replace('ã³', 'ó').replace('ã­', 'í').replace('ãº', 'ú')
    
    # Match exacto de categorías simplificadas (BigQuery a veces devuelve estos directamente)
    MAPEO_EXACTO = {
        'financiamiento': 'Financiamiento',
        'financiamento': 'Financiamiento',
        'rendimientos': 'Rendimientos',
        'rendimentos': 'Rendimientos',
        'complejidad': 'Complejidad',
        'complexidade': 'Complejidad',
        'promociones': 'Promociones',
        'promoções': 'Promociones',
        'promo': 'Promociones',
        'seguridad': 'Seguridad',
        'segurança': 'Seguridad',
        'atención': 'Atención',
        'atencion': 'Atención',
        'atendimento': 'Atención',
        'tarifas': 'Tarifas',
        'funcionalidades': 'Funcionalidades',
        'inversion': 'Rendimientos',
        'inversiones': 'Rendimientos',
        'investimento': 'Rendimientos',
        'investimentos': 'Rendimientos',
    }
    if m_lower in MAPEO_EXACTO:
        return MAPEO_EXACTO[m_lower]
    
    # Match por keywords (para categorías granulares de BigQuery)
    if any(x in m_lower for x in ['taxa', 'juros', 'tasa', 'interes', 'crédito', 'credito', 
                             'limite', 'empréstimo', 'préstamo', 'cartão', 'tarjeta',
                             'financ']):
        return 'Financiamiento'
    if any(x in m_lower for x in ['atendimento', 'atención', 'atencion', 'cliente', 'suporte', 'soporte']):
        return 'Atención'
    if any(x in m_lower for x in ['rendimento', 'rendimiento', 'cdi', 'poupança',
                             'inversion', 'inversión', 'invertir', 'opcion', 'dinero en cuenta']):
        return 'Rendimientos'
    if any(x in m_lower for x in ['segurança', 'seguridad', 'fraude', 'golpe', 'roubo']):
        return 'Seguridad'
    if any(x in m_lower for x in ['promoç', 'promoc', 'desconto', 'descuento', 'cashback', 
                             'benefício', 'beneficio', 'promocion', 'promociones', 'promo']):
        return 'Promociones'
    if any(x in m_lower for x in ['tarifa', 'mensalidade', 'cuota', 'cobrança']):
        return 'Tarifas'
    if any(x in m_lower for x in ['comodidade', 'facilidade', 'dificuldade', 'dificultad', 
                             'problema', 'complexidade', 'complejidad', 'uso', 'app', 'bug']):
        return 'Complejidad'
    if any(x in m_lower for x in ['funcionalidade', 'funcionalidad', 'oferta', 'feature']):
        return 'Funcionalidades'
    if any(x in m_lower for x in ['não uso', 'no uso', 'sem opinião', 'sin opinión']):
        return 'Sin opinión'
    return 'Otro'


# ==============================================================================
# GENERADOR DE PROMPT PARA CURSOR (INTERVENCIÓN IA)
# ==============================================================================

def generar_prompt_subcausas(motivo, comentarios, player, quarter_label):
    """
    Genera el prompt para que Cursor analice subcausas.
    
    IMPORTANTE: Este prompt será procesado por Cursor como agente analítico.
    """
    if not comentarios or len(comentarios) < 1:
        return None
    
    sample_size = min(50, len(comentarios))
    sample = random.sample(comentarios, sample_size)
    comentarios_texto = '\n'.join([f"{i+1}. \"{c}\"" for i, c in enumerate(sample)])
    
    prompt = f"""Analiza estos {sample_size} comentarios sobre "{motivo}" ({quarter_label}).

COMENTARIOS:
{comentarios_texto}

TAREA: Identifica 3-4 SUBCAUSAS ESPECÍFICAS de "{motivo}".

FORMATO (JSON):
[
  {{"subcausa": "descripción corta", "porcentaje": 45}},
  {{"subcausa": "descripción corta", "porcentaje": 30}}
]

REGLAS:
1. SOLO subcausas relacionadas con "{motivo}"
2. NO mezclar categorías (ej: no poner "atención" en "Rendimientos")
3. Porcentajes suman ~100%
4. Máximo 4 subcausas
5. Responde en ESPAÑOL

Responde SOLO el JSON."""

    return prompt


def comparar_subcausas(subcausas_q1, subcausas_q2):
    """Compara subcausas entre Q1 y Q2, calcula deltas"""
    
    dict_q1 = {sc['subcausa'].lower().strip(): sc['porcentaje'] for sc in subcausas_q1}
    
    comparacion = []
    usados_q1 = set()
    
    for sc in subcausas_q2:
        nombre = sc['subcausa']
        nombre_key = nombre.lower().strip()
        pct_q2 = sc['porcentaje']
        
        # Buscar match en Q1
        pct_q1 = None
        matched_key = None
        
        if nombre_key in dict_q1:
            pct_q1 = dict_q1[nombre_key]
            matched_key = nombre_key
        else:
            # Fuzzy match
            for k1 in dict_q1:
                if nombre_key[:15] in k1 or k1[:15] in nombre_key:
                    pct_q1 = dict_q1[k1]
                    matched_key = k1
                    break
        
        if pct_q1 is not None and matched_key:
            usados_q1.add(matched_key)
            comparacion.append({
                'subcausa': nombre,
                'pct_q1': pct_q1,
                'pct_q2': pct_q2,
                'delta': pct_q2 - pct_q1,
                'es_nueva': False
            })
        else:
            comparacion.append({
                'subcausa': nombre,
                'pct_q1': 0,
                'pct_q2': pct_q2,
                'delta': pct_q2,
                'es_nueva': True
            })
    
    # Subcausas que desaparecieron
    for k1, v1 in dict_q1.items():
        if k1 not in usados_q1:
            comparacion.append({
                'subcausa': k1.title(),
                'pct_q1': v1,
                'pct_q2': 0,
                'delta': -v1,
                'es_nueva': False
            })
    
    return sorted(comparacion, key=lambda x: abs(x['delta']), reverse=True)


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def analizar_causas_raiz(resultado_parte6, resultado_parte5, df_player, config, 
                          generar_subcausas_ia=False, verbose=True):
    """
    Analiza causas raíz de cada motivo del waterfall.
    
    Args:
        resultado_parte6: Diccionario con waterfall_data_comparativo
        resultado_parte5: Diccionario con df_final_categorizado
        df_player: DataFrame con datos del player
        config: Diccionario de configuración
        generar_subcausas_ia: Si True, genera prompts para intervención de Cursor
        verbose: Si True, imprime información
    
    Returns:
        dict: Diccionario con causas_raiz_data, prompts_subcausas
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
    
    # Competidores del site
    COMPETIDORES = COMPETIDORES_POR_SITE.get(site, COMPETIDORES_POR_SITE['MLA'])
    
    if verbose:
        print(f"🔍 PARTE 7: Análisis de Causa Raíz - {BANDERA} {NOMBRE_PAIS}")
        print("=" * 70)
    
    # Obtener datos
    df_waterfall = resultado_parte6['waterfall_data_comparativo']
    df_comentarios = resultado_parte5['df_final_categorizado'].copy()
    
    # Crear columna MOTIVO_CATEGORIA
    if 'MOTIVO_IA' in df_comentarios.columns:
        df_comentarios['MOTIVO_CATEGORIA'] = df_comentarios['MOTIVO_IA'].apply(mapear_motivo_categoria)
        if verbose:
            print(f"✅ Columna MOTIVO_CATEGORIA creada")
    
    # Detectar columna de comentarios
    col_comentario = None
    for col_name in ['COMENTARIO', 'Comentarios', 'comentario']:
        if col_name in df_comentarios.columns:
            valores = df_comentarios[col_name].dropna()
            if len(valores[valores.astype(str).str.len() > 3]) > 10:
                col_comentario = col_name
                break
    
    if verbose:
        print(f"✅ Columna de comentarios: {col_comentario}")
    
    # Calcular NPS por quarter
    df_q1 = df_player[df_player[col_ola] == q_ant]
    df_q2 = df_player[df_player[col_ola] == q_act]
    
    nps_q1 = df_q1[col_nps].mean() * 100
    nps_q2 = df_q2[col_nps].mean() * 100
    delta_nps = nps_q2 - nps_q1
    
    if verbose:
        print(f"\n📊 RESUMEN - {player}")
        print("=" * 70)
        print(f"   {q_ant}: NPS {nps_q1:.1f}")
        print(f"   {q_act}: NPS {nps_q2:.1f}")
        print(f"   Delta: {delta_nps:+.1f} puntos")
    
    # Motivos del waterfall (excluir residuales)
    motivos_excluir = ['Sin opinión', 'Não uso ou sem opinião', 'No uso o sin opinión', 'Otro', 'Otros', 'Outros']
    df_waterfall_filtrado = df_waterfall[~df_waterfall['Motivo'].isin(motivos_excluir)].copy()
    
    if verbose:
        print(f"\n📊 MOTIVOS A ANALIZAR:")
        for _, row in df_waterfall_filtrado.iterrows():
            delta = row.get('Delta', 0)
            emoji = "✅" if delta < 0 else "🔥"
            print(f"   {emoji} {row['Motivo']:<20} {delta:+.1f}pp")
    
    # Analizar cada motivo
    if verbose:
        print(f"\n{'='*70}")
        print(f"🔍 DEEP DIVE - ANÁLISIS Q1 vs Q2")
        print("=" * 70)
    
    resultados_analisis = []
    prompts_subcausas = []
    
    for _, row in df_waterfall_filtrado.iterrows():
        motivo = row['Motivo']
        impacto_act = row['Impacto_Actual']
        impacto_ant = row.get('Impacto_Anterior', 0)
        delta = row.get('Delta', 0)
        
        if verbose:
            emoji = "✅" if delta < 0 else "🔥"
            print(f"\n{emoji} {motivo}")
            print(f"   Cambio: {delta:+.1f}pp ({impacto_ant:.1f}% → {impacto_act:.1f}%)")
        
        # Filtrar comentarios por motivo y quarter
        if 'MOTIVO_CATEGORIA' in df_comentarios.columns:
            df_motivo = df_comentarios[df_comentarios['MOTIVO_CATEGORIA'] == motivo]
        else:
            df_motivo = df_comentarios[df_comentarios['MOTIVO_IA'].apply(mapear_motivo_categoria) == motivo]
        
        df_motivo_q1 = df_motivo[df_motivo[col_ola] == q_ant]
        df_motivo_q2 = df_motivo[df_motivo[col_ola] == q_act]
        
        # Extraer comentarios
        comms_q1 = []
        comms_q2 = []
        
        if col_comentario:
            comms_q1 = df_motivo_q1[col_comentario].dropna().astype(str).tolist()
            comms_q1 = [c for c in comms_q1 if len(c) > 10]
            
            comms_q2 = df_motivo_q2[col_comentario].dropna().astype(str).tolist()
            comms_q2 = [c for c in comms_q2 if len(c) > 10]
        
        if verbose:
            print(f"   📊 Comentarios: {len(comms_q1)} ({q_ant}) → {len(comms_q2)} ({q_act})")
        
        # Keywords
        kw_q1 = extraer_keywords(comms_q1)
        kw_q2 = extraer_keywords(comms_q2)
        
        if verbose and kw_q2:
            top_kw = ', '.join(list(kw_q2.keys())[:5])
            print(f"   🔑 Keywords: {top_kw}")
        
        # Tendencias
        tendencias = analizar_tendencias_q1_q2(kw_q1, kw_q2)
        if verbose and tendencias['nuevos_temas']:
            print(f"   🆕 Nuevos: {', '.join(tendencias['nuevos_temas'][:3])}")
        
        # Competidores mencionados
        competidores_mencionados = detectar_competidores(comms_q2, COMPETIDORES, player)
        if verbose and competidores_mencionados:
            nombres = ', '.join([c['nombre'] for c in competidores_mencionados[:3]])
            print(f"   🏆 Mencionan: {nombres}")
        
        # Generar prompts para subcausas (si está habilitado)
        prompt_q1 = None
        prompt_q2 = None
        
        if generar_subcausas_ia:
            if len(comms_q1) >= 1:
                prompt_q1 = generar_prompt_subcausas(motivo, comms_q1, player, q_ant)
            if len(comms_q2) >= 1:
                prompt_q2 = generar_prompt_subcausas(motivo, comms_q2, player, q_act)
            
            if prompt_q1 or prompt_q2:
                prompts_subcausas.append({
                    'motivo': motivo,
                    'prompt_q1': prompt_q1,
                    'prompt_q2': prompt_q2,
                    'comentarios_q1': len(comms_q1),
                    'comentarios_q2': len(comms_q2)
                })
        
        # Ejemplos de comentarios
        ejemplos = []
        if comms_q2:
            sample = random.sample(comms_q2, min(3, len(comms_q2)))
            ejemplos = [normalizar_encoding(c)[:150] + '...' if len(c) > 150 else normalizar_encoding(c) for c in sample]
        
        resultado_motivo = {
            'motivo': motivo,
            'delta': delta,
            'impacto_anterior': impacto_ant,
            'impacto_actual': impacto_act,
            'num_comentarios_q1': len(comms_q1),
            'num_comentarios_q2': len(comms_q2),
            'keywords': list(kw_q2.keys())[:10],
            'tendencias': tendencias,
            'competidores_mencionados': competidores_mencionados,
            'ejemplos': ejemplos,
            'subcausas': [],  # Se llenará con intervención de Cursor
            'subcausas_q1': [],
            'subcausas_q2': []
        }
        
        resultados_analisis.append(resultado_motivo)
    
    # Resumen
    if verbose:
        print(f"\n{'='*70}")
        print(f"📊 RESUMEN CAUSA RAÍZ")
        print("=" * 70)
        
        if delta_nps > 0:
            print(f"✅ NPS mejoró {delta_nps:+.1f}pp")
        else:
            print(f"⚠️ NPS empeoró {delta_nps:.1f}pp")
        
        print(f"\n🎯 TOP MOTIVOS POR VARIACIÓN:")
        for res in sorted(resultados_analisis, key=lambda x: abs(x['delta']), reverse=True)[:5]:
            emoji = "✅" if res['delta'] < 0 else "🔥"
            print(f"   {emoji} {res['motivo']}: {res['delta']:+.1f}pp")
        
        print(f"\n{'='*70}")
        print(f"✅ PARTE 7 OK - {len(resultados_analisis)} motivos analizados")
        if prompts_subcausas:
            print(f"   📝 {len(prompts_subcausas)} prompts generados para subcausas")
        print("=" * 70)
    
    return {
        'causas_raiz_data': resultados_analisis,
        'prompts_subcausas': prompts_subcausas,
        'nps_q1': nps_q1,
        'nps_q2': nps_q2,
        'delta_nps': delta_nps
    }


# ==============================================================================
# ANÁLISIS SEMÁNTICO DE CAUSAS RAÍZ (Replicado del modelo Sellers)
# ==============================================================================

def preparar_analisis_semantico(resultado_parte6, resultado_parte5, df_player, config,
                                 max_comentarios_por_motivo=100, verbose=True):
    """
    Prepara comentarios por motivo para análisis semántico con LLM.
    
    A diferencia del enfoque por keywords, este método envía los comentarios
    al LLM para que identifique temáticas/causas raíz emergentes de forma
    semántica, con título, descripción, frecuencia y ejemplos.
    
    Args:
        resultado_parte6: Dict con waterfall_data_comparativo
        resultado_parte5: Dict con df_final_categorizado
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
    
    if verbose:
        print(f"\n🧠 ANÁLISIS SEMÁNTICO DE CAUSAS RAÍZ")
        print("=" * 70)
    
    # Obtener datos
    df_waterfall = resultado_parte6['waterfall_data_comparativo']
    df_comentarios = resultado_parte5['df_final_categorizado'].copy()
    
    if 'MOTIVO_IA' in df_comentarios.columns:
        df_comentarios['MOTIVO_CATEGORIA'] = df_comentarios['MOTIVO_IA'].apply(mapear_motivo_categoria)
    
    # Detectar columna de comentarios
    col_comentario = None
    for col_name in ['COMENTARIO', 'Comentarios', 'comentario']:
        if col_name in df_comentarios.columns:
            valores = df_comentarios[col_name].dropna()
            if len(valores[valores.astype(str).str.len() > 3]) > 10:
                col_comentario = col_name
                break
    
    if not col_comentario:
        if verbose:
            print("   ⚠️ No se encontró columna de comentarios")
        return {'prompt_path': None, 'datos_por_motivo': {}}
    
    # Filtrar motivos relevantes del waterfall
    motivos_excluir = ['Sin opinión', 'Não uso ou sem opinião', 'No uso o sin opinión', 'Otro', 'Otros', 'Outros']
    df_wf = df_waterfall[~df_waterfall['Motivo'].isin(motivos_excluir)].copy()
    # Ordenar por impacto absoluto
    df_wf = df_wf.reindex(df_wf['Delta'].abs().sort_values(ascending=False).index)
    
    # Preparar comentarios por motivo
    datos_por_motivo = {}
    
    for _, row in df_wf.iterrows():
        motivo = row['Motivo']
        delta = row.get('Delta', 0)
        impacto_act = row.get('Impacto_Actual', 0)
        impacto_ant = row.get('Impacto_Anterior', 0)
        
        # Filtrar por motivo
        if 'MOTIVO_CATEGORIA' in df_comentarios.columns:
            df_motivo = df_comentarios[df_comentarios['MOTIVO_CATEGORIA'] == motivo]
        else:
            continue
        
        # Q2 (actual) - priorizamos el quarter actual
        df_q2 = df_motivo[df_motivo[col_ola] == q_act]
        comms_q2 = df_q2[col_comentario].dropna().astype(str).tolist()
        comms_q2 = [normalizar_encoding(c) for c in comms_q2 if len(c.strip()) > 15]
        
        # Q1 (anterior) 
        df_q1 = df_motivo[df_motivo[col_ola] == q_ant]
        comms_q1 = df_q1[col_comentario].dropna().astype(str).tolist()
        comms_q1 = [normalizar_encoding(c) for c in comms_q1 if len(c.strip()) > 15]
        
        if len(comms_q2) < 1:
            if verbose:
                print(f"   ⏭️  {motivo}: sin comentarios en {q_act}, skip")
            continue
        
        # Limitar comentarios (solo Q2)
        if len(comms_q2) > max_comentarios_por_motivo:
            comms_q2 = random.sample(comms_q2, max_comentarios_por_motivo)
        
        datos_por_motivo[motivo] = {
            'delta': delta,
            'impacto_actual': impacto_act,
            'impacto_anterior': impacto_ant,
            'comentarios_q2': comms_q2,
            'comentarios_q1_count': len(comms_q1),
            'comentarios_q2_count': len(comms_q2),
        }
        
        if verbose:
            emoji = "🔥" if delta > 0 else "✅"
            print(f"   {emoji} {motivo}: {delta:+.1f}pp, {len(comms_q2)} comentarios")
    
    # Generar prompt
    prompt = _generar_prompt_semantico(datos_por_motivo, player, site, q_ant, q_act)
    
    # Guardar prompt - carpeta prompts/ en la raíz del proyecto
    script_dir = Path(__file__).resolve().parent
    prompts_dir = script_dir.parent / 'prompts'
    prompts_dir.mkdir(exist_ok=True)
    prompt_filename = f'prompt_causas_raiz_{player}_{site}_{q_act}.txt'
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


def _generar_prompt_semantico(datos_por_motivo, player, site, q_ant, q_act):
    """Genera el prompt estructurado para análisis semántico de causas raíz."""
    
    prompt = f"""
# 🔍 ANÁLISIS SEMÁNTICO DE CAUSAS RAÍZ - NPS COMPETITIVO

## Contexto
Analiza los comentarios de usuarios de **{player}** en **{site}** para identificar
las **causas raíz** específicas de cada motivo de queja.

**Quarters comparados:** {q_ant} → {q_act}
**Motivos a analizar:** {len(datos_por_motivo)}

## Instrucciones

Para cada motivo:
1. **Leer TODOS los comentarios** del quarter actual ({q_act})
2. **Identificar patrones semánticos** (no solo palabras, sino problemas subyacentes)
3. **Agrupar por causa raíz** (mínimo 2, máximo 4 causas por motivo)
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
    "metodo": "analisis_semantico"
  }},
  "causas_por_motivo": {{
    "NombreMotivo": {{
      "total_comentarios_analizados": 50,
      "delta_pp": -1.5,
      "causas_raiz": [
        {{
          "titulo": "Título descriptivo y específico",
          "descripcion": "Explicación breve del problema identificado",
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
        imp_ant = datos['impacto_anterior']
        imp_act = datos['impacto_actual']
        comentarios = datos['comentarios_q2']
        
        emoji = "🔥" if delta > 0 else "✅"
        direccion = "EMPEORÓ" if delta > 0 else "MEJORÓ"
        
        prompt += f"""
### {emoji} MOTIVO: {motivo} ({delta:+.1f}pp - {direccion})

**Impacto:** {imp_ant:.1f}% → {imp_act:.1f}% | **Comentarios:** {n_q1} ({q_ant}) → {n_q2} ({q_act})

**Comentarios {q_act}:**

"""
        for i, c in enumerate(comentarios, 1):
            c_limpio = c[:250] + '...' if len(c) > 250 else c
            prompt += f'{i}. "{c_limpio}"\n\n'
        
        prompt += "\n" + "=" * 80 + "\n"
    
    output_filename = f'causas_raiz_semantico_{player}_{site}_{q_act}.json'
    
    prompt += f"""
## 📝 INSTRUCCIONES FINALES

1. **Guardar el archivo** usando Write tool:
   - **Path:** `data/{output_filename}`
2. **Confirmar** que se guardó correctamente

IMPORTANTE:
- Los títulos deben ser ESPECÍFICOS (no "Problemas con crédito" sino "Rechazo de crédito pese a alta movimentación")
- Cada causa raíz debe ser DIFERENTE a las demás (no solapar)
- Los ejemplos deben ser TEXTUALES de los comentarios arriba
"""
    
    return prompt


# ==============================================================================
# FUNCIÓN PARA EXPORTAR COMENTARIOS PARA ANÁLISIS DE CURSOR
# ==============================================================================

def exportar_comentarios_para_cursor(resultado_parte6, resultado_parte5, df_player, config, 
                                      max_comentarios=30, verbose=True):
    """
    Exporta comentarios REALES de la base para que Cursor los analice.
    
    IMPORTANTE: Esta función NUNCA inventa comentarios. 
    Todos los comentarios provienen de la base de datos real.
    
    Args:
        resultado_parte6: Diccionario con waterfall_data_comparativo
        resultado_parte5: Diccionario con df_final_categorizado
        df_player: DataFrame con datos del player
        config: Diccionario de configuración
        max_comentarios: Máximo de comentarios por motivo/quarter
        verbose: Si True, imprime los comentarios
    
    Returns:
        dict: Diccionario con comentarios por motivo y quarter
    """
    
    # Extraer configuración
    site = config['site']
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    col_ola = 'OLA'
    col_comentario = 'COMENTARIO'
    
    if verbose:
        print("=" * 80)
        print(f"📝 EXTRACCIÓN DE COMENTARIOS REALES - {BANDERA} {NOMBRE_PAIS}")
        print(f"   Player: {player}")
        print(f"   Quarters: {q_ant} vs {q_act}")
        print("=" * 80)
        print("\n⚠️  IMPORTANTE: Todos los comentarios son REALES de la base de datos.")
        print("    Cursor debe analizarlos para generar subcausas.\n")
    
    # Obtener datos
    df_waterfall = resultado_parte6['waterfall_data_comparativo']
    df_comentarios = resultado_parte5['df_final_categorizado'].copy()
    
    # Crear columna MOTIVO_CATEGORIA
    if 'MOTIVO_IA' in df_comentarios.columns:
        df_comentarios['MOTIVO_CATEGORIA'] = df_comentarios['MOTIVO_IA'].apply(mapear_motivo_categoria)
    
    # Motivos a analizar
    motivos_excluir = ['Sin opinión', 'Não uso ou sem opinião', 'No uso o sin opinión', 'Otro', 'Otros', 'Outros']
    df_wf_filtrado = df_waterfall[~df_waterfall['Motivo'].isin(motivos_excluir)]
    
    comentarios_exportados = {}
    
    for _, row in df_wf_filtrado.iterrows():
        motivo = row['Motivo']
        delta = row.get('Delta', 0)
        
        # Filtrar comentarios por motivo
        df_motivo = df_comentarios[df_comentarios['MOTIVO_CATEGORIA'] == motivo]
        
        comentarios_motivo = {'q1': [], 'q2': [], 'delta': delta}
        
        for q, key in [(q_ant, 'q1'), (q_act, 'q2')]:
            df_q = df_motivo[df_motivo[col_ola] == q]
            
            if col_comentario in df_q.columns:
                comms = df_q[col_comentario].dropna().astype(str).tolist()
                comms = [normalizar_encoding(c) for c in comms if len(c) > 15]
                
                # Limitar cantidad
                if len(comms) > max_comentarios:
                    comms = random.sample(comms, max_comentarios)
                
                comentarios_motivo[key] = comms
        
        comentarios_exportados[motivo] = comentarios_motivo
        
        if verbose:
            emoji = "✅" if delta < 0 else "🔥"
            print(f"\n{'='*80}")
            print(f"{emoji} MOTIVO: {motivo} ({delta:+.1f}pp)")
            print("=" * 80)
            
            for q, key, label in [(q_ant, 'q1', 'ANTERIOR'), (q_act, 'q2', 'ACTUAL')]:
                comms = comentarios_motivo[key]
                if comms:
                    print(f"\n📊 {q} ({label}) - {len(comms)} comentarios:")
                    print("-" * 60)
                    for i, c in enumerate(comms[:15], 1):
                        c_truncado = c[:150] + "..." if len(c) > 150 else c
                        print(f"   {i}. \"{c_truncado}\"")
                    if len(comms) > 15:
                        print(f"   ... y {len(comms) - 15} más")
    
    if verbose:
        print("\n" + "=" * 80)
        print("📋 INSTRUCCIONES PARA CURSOR:")
        print("=" * 80)
        print("""
Para cada motivo, Cursor debe:
1. Leer TODOS los comentarios reales
2. Identificar 3-4 SUBCAUSAS específicas
3. Asignar porcentajes que sumen ~100%
4. Incluir EVIDENCIA (citar comentarios reales)

Formato de respuesta esperado:
{
  "motivo": "Nombre del motivo",
  "subcausas": [
    {"subcausa": "Descripción corta", "porcentaje": 35, "evidencia": "comentario real..."},
    {"subcausa": "Descripción corta", "porcentaje": 30, "evidencia": "comentario real..."},
  ]
}
""")
        print("=" * 80)
    
    return comentarios_exportados


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
    from parte6_waterfall import generar_waterfall
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 7: ANÁLISIS CAUSA RAÍZ")
    print("=" * 70)
    
    try:
        # Cargar datos
        resultado_carga = cargar_datos(verbose=False)
        df_completo = resultado_carga['df_completo']
        config = resultado_carga['config']
        
        # Filtrar player
        player = config['player']
        df_player = df_completo[df_completo['MARCA'] == player].copy()
        
        # Calcular NPS
        resultado_nps = calcular_nps(df_player, config, generar_grafico=False, verbose=False)
        
        # Categorizar
        resultado_cat = categorizar_comentarios(resultado_nps['df_player'], config, resultado_nps, verbose=False)
        
        # Corregir sin opinion
        resultado_p5 = corregir_sin_opinion(resultado_cat, config, verbose=False)
        
        # Waterfall
        resultado_p6 = generar_waterfall(resultado_p5, resultado_nps['df_player'], config, 
                                         guardar_graficos=False, verbose=False)
        
        # Análisis causa raíz (sin subcausas aún)
        resultado_p7 = analizar_causas_raiz(resultado_p6, resultado_p5, resultado_nps['df_player'], 
                                            config, generar_subcausas_ia=False, verbose=True)
        
        # Exportar comentarios para análisis de Cursor
        print("\n" + "=" * 80)
        print("📝 EXPORTANDO COMENTARIOS PARA ANÁLISIS DE CURSOR")
        print("=" * 80)
        
        comentarios = exportar_comentarios_para_cursor(
            resultado_p6, resultado_p5, resultado_nps['df_player'], 
            config, max_comentarios=25, verbose=True
        )
        
        print("\n📋 Variables exportadas:")
        print(f"   causas_raiz_data: {len(resultado_p7['causas_raiz_data'])} motivos")
        print(f"   comentarios_reales: {len(comentarios)} motivos con comentarios")
        
        print("\n✅ Prueba PARTE 7 completada")
        print("\n⚠️  SIGUIENTE PASO: Cursor debe analizar los comentarios y generar subcausas")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
