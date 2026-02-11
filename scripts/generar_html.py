# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
GENERADOR HTML - MODELO NPS FINTECH
═══════════════════════════════════════════════════════════════════════════════

Genera el HTML del resumen ejecutivo NPS con estructura PYRAMID PRINCIPLE.

ESTRUCTURA TAB RESUMEN (Pyramid Principle - Conclusión primero):
1. DIAGNÓSTICO EXPANDIDO (conclusión + métricas + quejas clave + productos clave)
2. GRÁFICO NPS (el número duro)
3. TRIANGULACIÓN (evidencia externa que valida el diagnóstico)
4. DEEP DIVE (causas detalladas para profundizar)
5. WATERFALL + QUEJAS (datos granulares)
6. PRODUCTOS (tabla detallada)
"""

import html as html_module
import random
from pathlib import Path
from datetime import datetime

# ==============================================================================
# THRESHOLDS CENTRALIZADOS
# Todos los umbrales numéricos del modelo en un solo lugar
# ==============================================================================

# Diagnóstico narrativo
UMBRAL_QUEJA_CRITICA = 2.0      # p.p. delta para considerar una queja "crítica" en diagnóstico
UMBRAL_QUEJA_SIGNIFICATIVA = 3.0 # p.p. delta para destacar una queja en headline
UMBRAL_PRODUCTO_RELEVANTE = 0.3  # p.p. total_effect mínimo para mencionar un producto
UMBRAL_NPS_ESTABLE = 0.5        # p.p. abs(delta) para considerar NPS "estable" (con formato :.0f)
UMBRAL_BALANCE_CERO = 0.1       # p.p. abs(balance) para considerar balance "sin cambio"

# Métricas complementarias
UMBRAL_PRINCIPALIDAD_RELEVANTE = 1.5  # p.p. delta para mencionar principalidad en narrativa
UMBRAL_SEGURIDAD_RELEVANTE = 2.0      # p.p. delta para mencionar seguridad en narrativa

# Productos - coherencia
UMBRAL_NPS_PRODUCTO_RELEVANTE = 0.5   # p.p. delta NPS usuario para mencionar en coherencia
UMBRAL_SHARE_RELEVANTE = 0.3          # p.p. delta share para mencionar en coherencia

# Tabla de productos
UMBRAL_PRODUCTO_DESTACAR = 0.3        # p.p. total_effect para highlight en tabla

# Búsqueda de noticias (en analisis_automatico.py)
UMBRAL_DRIVER_SIGNIFICATIVO = 0.3     # p.p. delta mínimo para buscar noticias de un driver
UMBRAL_SEGURIDAD_NOTICIA = 1.0        # p.p. delta seguridad para buscar noticias
UMBRAL_PRINCIPALIDAD_NOTICIA = 2.0    # p.p. delta principalidad para buscar noticias

# ==============================================================================
# CONFIGURACIÓN MULTISITE - TODO EN ESPAÑOL
# ==============================================================================

TEXTOS = {
    'titulo_resumen': 'Resumen Ejecutivo NPS',
    'periodo_analizado': 'Período analizado',
    'resumen': 'Resumen',
    'evolucion_quejas': 'Evolución Quejas',
    'seguridad': 'Seguridad',
    'principalidad': 'Principalidad',
    'productos': 'Productos',
    'promotores': 'Promotores',
    'evolucion_nps': 'Evolución de NPS',
    'diagnostico_principal': 'DIAGNÓSTICO PRINCIPAL',
    'analisis_quejas': 'ANÁLISIS DE QUEJAS',
    'deep_dive': 'Deep Dive: Causas de la variación',
    'impacto_productos': 'Impacto por Productos',
    'exportado': 'Exportado',
    'generado_desde': 'Generado desde',
    'modelo': 'Modelo CX Fintech',
    'mejoras': 'MEJORAS (menos quejas → mejor NPS)',
    'deterioros': 'DETERIOROS (más quejas → peor NPS)',
    'porque_recomiendan': '¿Por qué nos recomiendan?',
    'contexto_mercado': 'Contexto del Mercado',
}

BANDERAS = {'MLB': '🇧🇷', 'MLA': '🇦🇷', 'MLM': '🇲🇽', 'MLC': '🇨🇱'}
NOMBRES_PAIS = {'MLB': 'Brasil', 'MLA': 'Argentina', 'MLM': 'México', 'MLC': 'Chile'}


# ==============================================================================
# CORRECCIÓN DE ENCODING - UTF-8 mal interpretado como Latin-1
# ==============================================================================

def corregir_encoding(texto):
    """
    Corrige texto con encoding corrupto (UTF-8 leído como Latin-1).
    
    Ejemplos de corrección:
    - "opÃ§Ãµes" → "opções"
    - "SeguranÃ§a" → "Segurança"
    - "crÃ©dito" → "crédito"
    """
    if not isinstance(texto, str):
        return texto
    
    # Detectar si hay caracteres corruptos típicos
    patrones_corruptos = ['Ã§', 'Ã£', 'Ã©', 'Ãµ', 'Ã¡', 'Ã³', 'Ãº', 'Ã­', 'Ã', 'Ã¢', 'Ãª', 'Ã´']
    
    if any(p in texto for p in patrones_corruptos):
        try:
            # Re-encode: interpretar como Latin-1 y decodificar como UTF-8
            return texto.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Si falla, usar reemplazos manuales
            reemplazos = {
                'Ã§': 'ç', 'Ã£': 'ã', 'Ã©': 'é', 'Ãµ': 'õ',
                'Ã¡': 'á', 'Ã³': 'ó', 'Ãº': 'ú', 'Ã­': 'í',
                'Ã¢': 'â', 'Ãª': 'ê', 'Ã´': 'ô', 'Ã': 'À',
                'Ã±': 'ñ', 'Ã¼': 'ü', 'Ã¨': 'è', 'Ã²': 'ò',
            }
            for corrupto, correcto in reemplazos.items():
                texto = texto.replace(corrupto, correcto)
            return texto
    return texto


def corregir_encoding_dict(d):
    """Corrige encoding en todos los valores string de un diccionario."""
    if isinstance(d, dict):
        return {k: corregir_encoding_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [corregir_encoding_dict(item) for item in d]
    elif isinstance(d, str):
        return corregir_encoding(d)
    return d


def cargar_css():
    """Carga el CSS del template."""
    template_path = Path(__file__).parent.parent / 'templates' / 'template_base.html'
    if not template_path.exists():
        return ""
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    import re
    css_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
    return css_match.group(1) if css_match else ""


def valor_class(val):
    """Retorna clase CSS según valor."""
    if val > 0: return 'valor-positivo'
    if val < 0: return 'valor-negativo'
    return ''


def _detectar_alerta_tendencia(resultados, nps_delta):
    """
    Detecta si hay una tendencia preocupante que requiere alerta visual.
    
    Criterios:
    1. NPS cae más de 2p.p. → Alerta crítica
    2. Quejas subiendo 3+ quarters consecutivos
    3. Queja específica sube más de 3p.p.
    
    Returns:
        str: HTML del badge de alerta o string vacío
    """
    alertas = []
    
    # 1. Caída significativa de NPS
    if nps_delta < -2:
        alertas.append({
            'tipo': 'critica',
            'texto': f'⚠️ Caída significativa',
            'detalle': f'{nps_delta:.0f}pp'
        })
    elif nps_delta < -1:
        alertas.append({
            'tipo': 'warning',
            'texto': '📉 Tendencia negativa',
            'detalle': f'{nps_delta:.0f}pp'
        })
    
    # 2. Verificar waterfall - quejas que subieron mucho
    wf_data = resultados.get('waterfall', {})
    causas = wf_data.get('causas_waterfall', [])
    
    if not causas:
        # Intentar con waterfall_data_comparativo
        wf_df = wf_data.get('waterfall_data_comparativo', None)
        if wf_df is not None and hasattr(wf_df, 'iterrows'):
            for _, row in wf_df.iterrows():
                delta = row.get('Delta', 0)
                if delta > UMBRAL_QUEJA_SIGNIFICATIVA:  # Queja subió significativamente
                    motivo = row.get('Motivo', 'Queja')
                    alertas.append({
                        'tipo': 'warning',
                        'texto': f'📈 {motivo} +{delta:.0f}pp',
                        'detalle': 'en aumento'
                    })
                    break  # Solo una alerta de este tipo
    else:
        for c in causas:
            delta = c.get('delta', 0)
            if delta > UMBRAL_QUEJA_SIGNIFICATIVA:
                motivo = c.get('motivo', 'Queja')
                alertas.append({
                    'tipo': 'warning',
                    'texto': f'📈 {motivo} +{delta:.0f}pp',
                    'detalle': 'en aumento'
                })
                break
    
    # 3. Verificar tendencias en deep_research
    dr_data = resultados.get('deep_research', {})
    cambios_quejas = dr_data.get('cambios_quejas', [])
    
    quejas_criticas = [c for c in cambios_quejas if c.get('delta', 0) > UMBRAL_QUEJA_CRITICA]
    if len(quejas_criticas) >= 2 and not alertas:
        alertas.append({
            'tipo': 'warning',
            'texto': '⚠️ Múltiples quejas subiendo',
            'detalle': f'{len(quejas_criticas)} categorías'
        })
    
    # Generar HTML de alerta
    if not alertas:
        return ''
    
    # Tomar la alerta más crítica
    alerta = alertas[0]
    
    if alerta['tipo'] == 'critica':
        return f'''
        <span class="badge-alerta" style="
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 15px;
            animation: pulse 2s infinite;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.4);
        ">{alerta['texto']}</span>
        <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
        </style>
        '''
    else:
        return f'''
        <span class="badge-alerta" style="
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 15px;
            box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
        ">{alerta['texto']}</span>
        '''


# ==============================================================================
# SECCIÓN EVOLUCIÓN HISTÓRICA (contexto del Q anterior desde presentaciones PDF)
# ==============================================================================

def _generar_seccion_evolucion(resultados):
    """
    Genera la sección de contexto histórico del quarter anterior.
    Si no hay presentación anterior disponible, retorna string vacío (graceful degradation).
    """
    pres = resultados.get('presentacion_anterior')
    if not pres:
        return ""
    
    config = resultados.get('config', {})
    player = config.get('player', '')
    q_anterior = pres.get('quarter', '?')
    
    # NPS delta del Q anterior
    nps_delta_prev = pres.get('nps_delta')
    nps_html = ""
    if nps_delta_prev is not None:
        nps_color = '#10b981' if nps_delta_prev > 0 else '#ef4444' if nps_delta_prev < 0 else '#6b7280'
        nps_signo = '+' if nps_delta_prev > 0 else ''
        nps_html = f"""
        <div style="display: inline-block; background: {nps_color}20; color: {nps_color}; 
                    padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 18px; margin-right: 12px;">
            NPS {nps_signo}{nps_delta_prev:.0f}p.p.
        </div>"""
    
    # Principalidad y Seguridad
    metricas_html = ""
    princ = pres.get('principalidad', {})
    seg = pres.get('seguridad', {})
    if princ.get('delta') is not None or seg.get('delta') is not None:
        metricas_items = []
        if princ.get('delta') is not None:
            p_val = f" ({princ['valor']:.0f}%)" if princ.get('valor') is not None else ""
            metricas_items.append(f"Principalidad: {princ['delta']:+.0f}p.p.{p_val}")
        if seg.get('delta') is not None:
            s_val = f" ({seg['valor']:.0f}%)" if seg.get('valor') is not None else ""
            metricas_items.append(f"Seguridad: {seg['delta']:+.0f}p.p.{s_val}")
        if metricas_items:
            metricas_html = '<div style="margin-top: 8px; font-size: 13px; color: #64748b;">' + ' | '.join(metricas_items) + '</div>'
    
    # Drivers del Q anterior
    drivers = pres.get('drivers', [])
    drivers_html = ""
    if drivers:
        items = []
        for d in drivers[:5]:
            efecto = d.get('efecto', '')
            detalle = d.get('detalle', '')
            items.append(f'<li style="margin-bottom: 4px;">{efecto} {detalle}</li>')
        drivers_html = f"""
        <div style="margin-top: 12px;">
            <strong style="font-size: 13px; color: #374151;">Drivers reportados:</strong>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 13px; color: #4b5563;">
                {''.join(items)}
            </ul>
        </div>"""
    
    # Waterfall del Q anterior
    wf = pres.get('waterfall_quejas', {})
    wf_html = ""
    if wf:
        wf_items = sorted(wf.items(), key=lambda x: x[1], reverse=True)[:5]
        bars = []
        max_val = max(v for _, v in wf_items) if wf_items else 1
        for cat, val in wf_items:
            width_pct = min(100, (val / max_val) * 100)
            bars.append(f"""
            <div style="display: flex; align-items: center; margin-bottom: 4px;">
                <span style="width: 120px; font-size: 12px; color: #6b7280; text-align: right; padding-right: 8px;">{cat}</span>
                <div style="flex: 1; background: #f1f5f9; border-radius: 4px; height: 16px; overflow: hidden;">
                    <div style="width: {width_pct:.0f}%; background: #94a3b8; height: 100%; border-radius: 4px;"></div>
                </div>
                <span style="width: 45px; text-align: right; font-size: 12px; color: #64748b; padding-left: 6px;">{val:.0f}p.p.</span>
            </div>""")
        wf_html = f"""
        <div style="margin-top: 12px;">
            <strong style="font-size: 13px; color: #374151;">Quejas principales (waterfall):</strong>
            <div style="margin-top: 6px;">{''.join(bars)}</div>
        </div>"""
    
    # Conclusiones del Q anterior
    conclusiones = pres.get('conclusiones', [])
    conclusiones_html = ""
    if conclusiones:
        items = [f'<li style="margin-bottom: 3px;">{c}</li>' for c in conclusiones[:3]]
        conclusiones_html = f"""
        <div style="margin-top: 12px;">
            <strong style="font-size: 13px; color: #374151;">Conclusiones del reporte anterior:</strong>
            <ul style="margin: 4px 0 0 0; padding-left: 20px; font-size: 13px; color: #4b5563;">
                {''.join(items)}
            </ul>
        </div>"""
    
    # Comparación: persistencia de drivers
    # Esto se llena desde el modelo actual vs los drivers del Q anterior
    wf_actual = resultados.get('waterfall', {}).get('causas_waterfall', [])
    comparacion_html = ""
    if drivers and wf_actual:
        motivos_anteriores = set()
        for d in drivers:
            det = d.get('detalle', '').lower()
            for cat in ['complejidad', 'seguridad', 'rendimiento', 'financiamiento', 
                        'promocion', 'atencion', 'tarifa', 'funcionalidad']:
                if cat in det:
                    motivos_anteriores.add(cat.capitalize())
        
        motivos_actuales = set()
        for c in wf_actual:
            if isinstance(c, dict):
                m = c.get('motivo', '').lower()
                for cat in ['complejidad', 'seguridad', 'rendimiento', 'financiamiento',
                            'promocion', 'atencion', 'tarifa', 'funcionalidad']:
                    if cat in m:
                        motivos_actuales.add(cat.capitalize())
        
        persistentes = motivos_anteriores & motivos_actuales
        nuevos = motivos_actuales - motivos_anteriores
        resueltos = motivos_anteriores - motivos_actuales
        
        comp_items = []
        if persistentes:
            comp_items.append(f'<span style="color: #f59e0b;">⚠ Persisten: {", ".join(sorted(persistentes))}</span>')
        if nuevos:
            comp_items.append(f'<span style="color: #ef4444;">🆕 Nuevos: {", ".join(sorted(nuevos))}</span>')
        if resueltos:
            comp_items.append(f'<span style="color: #10b981;">✓ Resueltos: {", ".join(sorted(resueltos))}</span>')
        
        if comp_items:
            comparacion_html = f"""
            <div style="margin-top: 14px; padding: 10px 14px; background: #fefce8; border-radius: 8px; border-left: 3px solid #f59e0b;">
                <strong style="font-size: 13px; color: #92400e;">Continuidad de drivers:</strong><br>
                <span style="font-size: 13px;">{'<br>'.join(comp_items)}</span>
            </div>"""
    
    # Resumen general
    resumen = pres.get('resumen_general', '')
    resumen_html = f'<div style="font-size: 13px; color: #64748b; font-style: italic; margin-top: 6px;">{resumen}</div>' if resumen else ''
    
    source_pdf = pres.get('source_pdf', '')
    source_html = f'<div style="font-size: 11px; color: #9ca3af; margin-top: 10px;">Fuente: {source_pdf}</div>' if source_pdf else ''
    
    return f"""
    <div class="content-main" style="padding: 20px 25px; border: 1px solid #e5e7eb; border-radius: 12px; 
                margin: 20px 0; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);">
        <div style="display: flex; align-items: center; margin-bottom: 14px; border-bottom: 2px solid #64748b; padding-bottom: 10px;">
            <span style="font-size: 20px; margin-right: 8px;">📋</span>
            <span style="font-weight: 700; font-size: 16px; color: #1e293b;">
                Contexto: {player} en {q_anterior}
            </span>
        </div>
        {nps_html}
        {metricas_html}
        {resumen_html}
        {drivers_html}
        {wf_html}
        {conclusiones_html}
        {comparacion_html}
        {source_html}
    </div>
    """


# ==============================================================================
# GENERADOR HTML PRINCIPAL (estructura EXACTA del notebook)
# ==============================================================================

def generar_html_completo(resultados, diagnostico_gpt=None):
    """
    Genera el HTML completo del resumen NPS.
    Replica EXACTAMENTE la estructura del notebook original.
    """
    # ==========================================================================
    # CORRECCIÓN DE ENCODING - Aplicar a todos los datos de entrada
    # ==========================================================================
    resultados = corregir_encoding_dict(resultados)
    if diagnostico_gpt:
        diagnostico_gpt = corregir_encoding(diagnostico_gpt)
    
    config = resultados['config']
    player = config['player']
    site = config['site']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    BANDERA = BANDERAS.get(site, '🌎')
    NOMBRE_PAIS = NOMBRES_PAIS.get(site, '')
    TXT = TEXTOS
    
    CSS = cargar_css()
    
    # ==========================================================================
    # CARGAR CAUSAS RAÍZ SEMÁNTICAS (para diagnóstico + waterfall)
    # ==========================================================================
    import json as _json
    _causas_semanticas = {}
    _data_dir = Path(__file__).parent.parent / 'data'
    _json_cr = _data_dir / f'causas_raiz_semantico_{player}_{q_act}.json'
    if _json_cr.exists():
        try:
            with open(_json_cr, 'r', encoding='utf-8') as _f:
                _cr_data = _json.load(_f)
                _causas_semanticas = _cr_data.get('causas_por_motivo', {})
        except Exception:
            pass
    
    # ==========================================================================
    # DATOS NPS
    # ==========================================================================
    nps_data = resultados.get('nps', {})
    _nps_q1_raw = nps_data.get('nps_q1')
    _nps_q2_raw = nps_data.get('nps_q2')
    # Detectar datos faltantes: None o dict vacío → mostrar alerta
    nps_datos_faltantes = (_nps_q1_raw is None or _nps_q2_raw is None)
    nps_q1 = round(_nps_q1_raw, 1) if _nps_q1_raw is not None else 0
    nps_q2 = round(_nps_q2_raw, 1) if _nps_q2_raw is not None else 0
    nps_delta = round(nps_q2 - nps_q1, 1)
    
    # Alinear tendencia con formateo :.0f (threshold 0.5 para que no diga "estable" y muestre ±1pp)
    tendencia = "manteniéndose estable" if abs(nps_delta) < 0.5 else ("mejorando" if nps_delta > 0 else "cayendo")
    delta_clase = "highlight-positivo" if nps_delta > 0 else "highlight-negativo" if nps_delta < 0 else "highlight-neutro"
    
    # ==========================================================================
    # ALERTA DE TENDENCIA PREOCUPANTE
    # ==========================================================================
    alerta_tendencia = _detectar_alerta_tendencia(resultados, nps_delta)
    
    # ==========================================================================
    # GRÁFICOS BASE64
    # ==========================================================================
    grafico_nps_b64 = nps_data.get('grafico_evolucion_nps_base64', '')
    
    wf_data = resultados.get('waterfall', {})
    grafico_quejas_b64 = wf_data.get('grafico_evolucion_quejas_base64', '')
    grafico_wf_b64 = wf_data.get('grafico_waterfall_base64', '')
    
    # USAR CAUSAS ENRIQUECIDAS (con subcausas, keywords, comentarios)
    # Si existen las causas enriquecidas de analisis_automatico.py, usarlas
    causas_waterfall = resultados.get('causas_waterfall', [])
    
    # Si no hay causas enriquecidas, transformar desde DataFrame
    if not causas_waterfall:
        wf_df = wf_data.get('waterfall_data_comparativo', None)
        if wf_df is not None:
            try:
                if hasattr(wf_df, 'to_dict'):
                    for _, row in wf_df.iterrows():
                        causas_waterfall.append({
                            'motivo': row.get('Motivo', ''),
                            'delta': row.get('Delta', 0) if 'Delta' in row else 0,
                            'pct_q1': row.get('Impacto_Anterior', 0) if 'Impacto_Anterior' in row else 0,
                            'pct_q2': row.get('Impacto_Actual', 0),
                            'subcausas': [],
                            'keywords': {},
                            'ejemplos_comentarios': []
                        })
                elif isinstance(wf_df, list):
                    causas_waterfall = wf_df
            except Exception as e:
                print(f"⚠️ Error transformando waterfall: {e}")
                causas_waterfall = []
    
    # Obtener triangulaciones
    triangulaciones = resultados.get('triangulaciones', [])
    
    seg_data = resultados.get('seguridad', {})
    grafico_seg_b64 = seg_data.get('grafico_seguridad_base64', '')
    grafico_mot_inseg_b64 = seg_data.get('grafico_motivos_inseg_base64', '')
    
    princ_data = resultados.get('principalidad', {})
    grafico_princ_b64 = princ_data.get('grafico_principalidad_base64', '')
    grafico_mot_princ_b64 = princ_data.get('grafico_motivos_princ_base64', '')
    
    prod_data = resultados.get('productos', {})
    productos = prod_data.get('productos_clave', [])
    productos_todos = prod_data.get('productos_todos', productos)  # Todos los productos para tabla
    
    prom_data = resultados.get('promotores', {})
    
    # ==========================================================================
    # HEADER (EXACTO del notebook)
    # ==========================================================================
    html_header = f"""
    <div class="header-top">
        <div class="header-top-left">
            <h2>{BANDERA} {TXT['titulo_resumen']} - {player}</h2>
            <div class="subtitulo">{TXT['periodo_analizado']}: {q_ant} → {q_act} | {NOMBRE_PAIS}</div>
        </div>
        <div class="header-top-right">
            <div><strong>{TXT['exportado']}:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            <div><strong>{TXT['generado_desde']}:</strong> {TXT['modelo']}</div>
        </div>
    </div>

    <div class="tabs-nav">
        <button class="tab-btn active" onclick="showTab('resumen')">📊 {TXT['resumen']}</button>
        <button class="tab-btn" onclick="showTab('anexo1')">📈 {TXT['evolucion_quejas']}</button>
        <button class="tab-btn" onclick="showTab('anexo2')">🔒 {TXT['seguridad']}</button>
        <button class="tab-btn" onclick="showTab('anexo3')">🏠 {TXT['principalidad']}</button>
        <button class="tab-btn" onclick="showTab('anexo4')">📦 {TXT['productos']}</button>
        <button class="tab-btn" onclick="showTab('anexo5')">🌟 {TXT['promotores']}</button>
        <button class="tab-btn" onclick="showTab('anexo6')">🔍 Causas Raíz</button>
    </div>

    <script>
    function showTab(tabId) {{
        document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
        const target = document.getElementById(tabId);
        if (target) target.style.display = 'block';
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
    }}
    </script>
    """
    
    # ==========================================================================
    # GRÁFICO EVOLUCIÓN NPS (Chart.js interactivo)
    # ==========================================================================
    nps_grafico_df = nps_data.get('nps_grafico')
    col_ola_nps = None
    if nps_grafico_df is not None and len(nps_grafico_df) > 0:
        # Detectar columna de ola
        for c in ['OLA', 'ola', 'QUARTER', 'quarter']:
            if c in nps_grafico_df.columns:
                col_ola_nps = c
                break
        if col_ola_nps is None:
            col_ola_nps = nps_grafico_df.columns[0]
        
        nps_labels = nps_grafico_df[col_ola_nps].tolist()
        nps_values = [round(v, 1) for v in nps_grafico_df['NPS_score'].tolist()]
        
        import json
        grafico_evolucion_html = f'''
            <div class="grafico-box">
                <div class="grafico-box-titulo">{TXT['evolucion_nps']}</div>
                <div style="padding: 15px; position: relative; height: 300px;">
                    <canvas id="chartNpsEvolucion"></canvas>
                </div>
            </div>
            <script>
            (function() {{
                const ctx = document.getElementById('chartNpsEvolucion').getContext('2d');
                const labels = {json.dumps(nps_labels)};
                const data = {json.dumps(nps_values)};
                const minVal = Math.min(...data);
                const maxVal = Math.max(...data);
                
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: '{player}',
                            data: data,
                            borderColor: '#009ee3',
                            backgroundColor: 'rgba(0, 158, 227, 0.08)',
                            borderWidth: 2.5,
                            pointRadius: 7,
                            pointBackgroundColor: '#009ee3',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2.5,
                            pointHoverRadius: 9,
                            fill: true,
                            tension: 0.3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'top',
                                align: 'end',
                                labels: {{ font: {{ family: 'Inter', size: 12 }}, usePointStyle: true }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                titleFont: {{ family: 'Inter', size: 13 }},
                                bodyFont: {{ family: 'Inter', size: 12 }},
                                padding: 12,
                                cornerRadius: 8,
                                callbacks: {{
                                    label: function(ctx) {{ return 'NPS: ' + ctx.parsed.y.toFixed(1); }}
                                }}
                            }},
                            datalabels: undefined
                        }},
                        scales: {{
                            y: {{
                                min: Math.floor(minVal - 5),
                                max: Math.ceil(maxVal + 5),
                                grid: {{ display: false }},
                                ticks: {{ font: {{ family: 'Inter', size: 11 }}, color: '#666' }},
                                border: {{ display: false }}
                            }},
                            x: {{
                                grid: {{ display: false }},
                                ticks: {{ font: {{ family: 'Inter', size: 11 }}, color: '#666' }},
                                border: {{ color: '#e0e0e0' }}
                            }}
                        }},
                        animation: {{
                            duration: 800,
                            easing: 'easeOutQuart'
                        }}
                    }},
                    plugins: [{{
                        afterDatasetsDraw: function(chart) {{
                            const ctx2 = chart.ctx;
                            chart.data.datasets.forEach(function(dataset, i) {{
                                const meta = chart.getDatasetMeta(i);
                                meta.data.forEach(function(point, index) {{
                                    const value = dataset.data[index];
                                    ctx2.fillStyle = '#333';
                                    ctx2.font = 'bold 12px Inter';
                                    ctx2.textAlign = 'center';
                                    ctx2.fillText(value.toFixed(1), point.x, point.y - 14);
                                }});
                            }});
                        }}
                    }}]
                }});
            }})();
            </script>
        '''
    else:
        grafico_evolucion_html = f'<div class="grafico-box"><div class="grafico-box-titulo">{TXT["evolucion_nps"]}</div><p style="color:#999;text-align:center;">Gráfico no disponible - datos insuficientes para generar evolución NPS</p></div>'
    
    # ==========================================================================
    # DIAGNÓSTICO PRINCIPAL (html_diagnostico_principal del notebook)
    # ==========================================================================
    if diagnostico_gpt:
        html_diagnostico_principal = f"""
            <div class="diagnostico-principal-box">
                <div class="diagnostico-principal-titulo">📋 {TXT['diagnostico_principal']}</div>
                <div class="diagnostico-principal-texto" style="line-height: 1.8;">{diagnostico_gpt}</div>
            </div>
        """
    else:
        html_diagnostico_principal = _generar_diagnostico_principal(resultados, TXT, q_ant, q_act, _causas_semanticas)
    
    # ==========================================================================
    # ANÁLISIS DE QUEJAS (html_quejas_box del notebook)
    # ==========================================================================
    html_quejas_box = _generar_quejas_box(resultados, TXT, q_ant, q_act)
    
    # ==========================================================================
    # html_conclusion (estructura EXACTA del notebook)
    # ==========================================================================
    html_conclusion = f"""
    <div class="content-main">
        <div class="titulo-principal">
            <span class="bandera">{BANDERA}</span>
            <h1>{TXT['titulo_resumen']} {player} - {q_act}</h1>
        </div>

        <div class="nps-resumen-box">
            <div class="nps-resumen-valor">
                <span class="nps-antes">{nps_q1:.0f}</span>
                <span class="nps-flecha">→</span>
                <span class="nps-actual">{nps_q2:.0f}</span>
                <span class="nps-delta {delta_clase}">{nps_delta:+.0f}pp</span>
                {alerta_tendencia}
            </div>
            <div class="nps-resumen-texto">
                En {q_act}, el NPS de <strong>{player}</strong> alcanzó <strong>{nps_q2:.0f}</strong>, {tendencia} respecto al período anterior.
            </div>
        </div>

        <!-- DIAGNÓSTICO PRINCIPAL - Arriba del gráfico -->
        <div class="diagnostico-principal-section" style="margin-top: 25px;">
            {html_diagnostico_principal}
        </div>

        <!-- GRÁFICO NPS - Debajo del diagnóstico -->
        <div class="seccion-titulo-simple" style="margin-top: 25px;">
            <span class="icono">📈</span> {TXT['evolucion_nps']}
        </div>
        {grafico_evolucion_html}
    </div>
    """
    
    # ==========================================================================
    # SECCIÓN QUEJAS - Chart.js interactivo (stacked bar)
    # ==========================================================================
    import json as _json
    
    evolucion_quejas_df = wf_data.get('evolucion_quejas_data')
    
    if evolucion_quejas_df is not None and len(evolucion_quejas_df) > 0:
        # df_evolucion: index = quarter labels, columns = motive categories, values = impact
        quejas_labels = evolucion_quejas_df.index.tolist()
        quejas_motivos = evolucion_quejas_df.columns.tolist()
        
        # COLORES mapping for JS
        COLORES_JS = {
            'Financiamiento': '#6bcb77', 'Rendimientos': '#e63946', 'Atención': '#c8b6ff',
            'Seguridad': '#2d6a4f', 'Funcionalidades': '#5f6c7b', 'Promociones': '#7c3aed',
            'Complejidad': '#ff9f43', 'Tasas': '#778ca3', 'Inversiones': '#0984e3',
            'Tarifas': '#fd79a8', 'Dificultad': '#fdcb6e',
            'Sin opinión': '#d1d8e0', 'Otro': '#95a5a6', 'Outros': '#95a5a6',
            'Otros': '#95a5a6', 'Não uso ou sem opinião': '#d1d8e0',
            'No uso o sin opinión': '#d1d8e0', 'Sin desglose': '#bdc3c7'
        }
        
        # Build datasets for Chart.js
        chart_datasets = []
        for mot in quejas_motivos:
            vals = [round(float(v), 1) for v in evolucion_quejas_df[mot].values]
            color = COLORES_JS.get(mot, '#a5b1c2')
            chart_datasets.append({
                'label': mot,
                'data': vals,
                'backgroundColor': color,
                'borderColor': 'white',
                'borderWidth': 1.5,
                'borderRadius': 2
            })
        
        grafico_quejas_html = f'''
            <div style="position: relative; height: 380px;">
                <canvas id="chartQuejasEvolucion"></canvas>
            </div>
            <script>
            (function() {{
                const ctx = document.getElementById('chartQuejasEvolucion').getContext('2d');
                const labels = {_json.dumps(quejas_labels)};
                const datasets = {_json.dumps(chart_datasets)};
                
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: labels,
                        datasets: datasets
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'right',
                                labels: {{
                                    font: {{ family: 'Inter', size: 11 }},
                                    usePointStyle: true,
                                    pointStyle: 'rectRounded',
                                    padding: 12
                                }}
                            }},
                            tooltip: {{
                                backgroundColor: 'rgba(15, 23, 42, 0.92)',
                                titleFont: {{ family: 'Inter', size: 13, weight: 'bold' }},
                                bodyFont: {{ family: 'Inter', size: 12 }},
                                padding: 12,
                                cornerRadius: 8,
                                mode: 'index',
                                intersect: false,
                                callbacks: {{
                                    label: function(ctx) {{
                                        if (ctx.parsed.y > 0) {{
                                            return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(1) + '%';
                                        }}
                                        return null;
                                    }},
                                    footer: function(tooltipItems) {{
                                        let total = 0;
                                        tooltipItems.forEach(function(item) {{ total += item.parsed.y; }});
                                        return 'Total: ' + total.toFixed(0) + '%';
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                stacked: true,
                                grid: {{ display: false }},
                                ticks: {{ font: {{ family: 'Inter', size: 12, weight: '600' }}, color: '#334155' }},
                                border: {{ display: false }}
                            }},
                            y: {{
                                stacked: true,
                                title: {{
                                    display: true,
                                    text: 'Impacto (pp)',
                                    font: {{ family: 'Inter', size: 11 }},
                                    color: '#64748b'
                                }},
                                grid: {{ color: 'rgba(0,0,0,0.04)' }},
                                ticks: {{ font: {{ family: 'Inter', size: 10 }}, color: '#64748b' }},
                                border: {{ display: false }}
                            }}
                        }},
                        animation: {{
                            duration: 800,
                            easing: 'easeOutQuart'
                        }}
                    }},
                    plugins: [{{
                        // Plugin: total label on top of each stacked bar
                        afterDatasetsDraw: function(chart) {{
                            const ctx2 = chart.ctx;
                            const meta = chart.getDatasetMeta(chart.data.datasets.length - 1);
                            
                            meta.data.forEach(function(bar, index) {{
                                // Calculate total for this bar
                                let total = 0;
                                chart.data.datasets.forEach(function(ds) {{ total += ds.data[index] || 0; }});
                                
                                ctx2.fillStyle = '#2d3436';
                                ctx2.font = 'bold 12px Inter';
                                ctx2.textAlign = 'center';
                                ctx2.fillText(total.toFixed(0) + '%', bar.x, bar.y - 8);
                            }});
                        }},
                        // Plugin: percentage labels inside bars (only if >= 3%)
                        afterDraw: function(chart) {{
                            const ctx2 = chart.ctx;
                            chart.data.datasets.forEach(function(dataset, datasetIndex) {{
                                const meta = chart.getDatasetMeta(datasetIndex);
                                meta.data.forEach(function(bar, index) {{
                                    const value = dataset.data[index];
                                    if (value >= 3) {{
                                        const {{ x, y, base }} = bar.getProps(['x', 'y', 'base']);
                                        const midY = (y + base) / 2;
                                        const label = dataset.label;
                                        const lightLabels = ['Sin opinión', 'Otro', 'Sin desglose', 'Não uso ou sem opinião'];
                                        ctx2.fillStyle = lightLabels.includes(label) ? '#333' : '#fff';
                                        ctx2.font = '600 10px Inter';
                                        ctx2.textAlign = 'center';
                                        ctx2.textBaseline = 'middle';
                                        ctx2.fillText(value.toFixed(0) + '%', x, midY);
                                    }}
                                }});
                            }});
                        }}
                    }}]
                }});
            }})();
            </script>
        '''
    else:
        grafico_quejas_html = '<p style="color:#999;">Gráfico no disponible</p>'
    
    # Waterfall con acordeones enriquecidos (ahora con causas semánticas)
    html_waterfall = _generar_waterfall_html(causas_waterfall, TXT, q_ant, q_act, _causas_semanticas)
    
    # Promotores resumen
    html_promotores_resumen = _generar_promotores_resumen(resultados, TXT, q_ant, q_act)
    
    seccion_quejas = f"""
    <div class="content-main" style="padding-top: 0; border-top: 1px solid #e8ecf0; margin-top: 30px;">
        <div class="seccion-titulo-simple">
            <span class="icono">📢</span> Análisis de Quejas
        </div>
        
        <!-- Gráfico Evolución de Quejas -->
        <div class="grafico-box" style="margin-bottom: 20px;">
            <div class="grafico-box-titulo">📈 Evolución de Quejas por Quarter</div>
            <div style="padding: 15px;">
                {grafico_quejas_html}
            </div>
        </div>
        
        <!-- Detalle por motivo con causas raíz -->
        {html_waterfall}
    </div>
    """
    
    # ==========================================================================
    # SECCIÓN PRODUCTOS (tabla + deep dive top 3)
    # ==========================================================================
    html_productos = _generar_tabla_productos(productos_todos, TXT)
    html_causas_deepdive = _generar_causas_deepdive(resultados, TXT, q_ant, q_act)
    
    seccion_productos = f"""
    <div class="content-main" style="padding-top: 0; border-top: 1px solid #e8ecf0; margin-top: 30px;">
        <div class="seccion-titulo-simple">
            <span class="icono">📦</span> Productos
        </div>
        
        <!-- Tabla detallada de productos -->
        {html_productos}
        
        <!-- Productos Clave: Top 3 con métricas y comentarios -->
        {html_causas_deepdive}
    </div>
    """
    
    # ==========================================================================
    # SECCIÓN TRIANGULACIÓN (unificada)
    # ==========================================================================
    seccion_triangulacion = _generar_seccion_triangulacion(resultados, TXT, q_ant, q_act)
    
    # ==========================================================================
    # SECCIÓN NOTICIAS (solo grid de noticias, sin triangulación)
    # ==========================================================================
    seccion_noticias_grid = _generar_noticias_grid(resultados, TXT, q_act)
    
    # Mantener seccion_noticias original para uso en otros contextos (sin cambiar API)
    seccion_noticias = _generar_seccion_noticias(resultados, TXT, q_ant, q_act)
    
    # ==========================================================================
    # SECCIÓN EVOLUCIÓN HISTÓRICA (contexto Q anterior - se mueve a anexos)
    # ==========================================================================
    seccion_evolucion = _generar_seccion_evolucion(resultados)
    
    # ==========================================================================
    # TAB RESUMEN - ESTRUCTURA
    # ==========================================================================
    # 1. DIAGNÓSTICO PRINCIPAL (narrativa arriba + gráfico NPS debajo)
    # 2. QUEJAS (gráfico evolución + cajas por motivo con causas raíz)
    # 3. PRODUCTOS (tabla + top 3 deep dive)
    # 4. TRIANGULACIÓN (unificada: Producto↔Queja↔Noticia + Motivo↔Noticia + Métricas)
    # 5. NOTICIAS (todas, agrupadas por tema)
    # ==========================================================================
    html_tab_resumen = f"""
    <div id="resumen" class="tab-content" style="display: block;">
        <!-- 1. DIAGNÓSTICO PRINCIPAL + GRÁFICO NPS -->
        {html_conclusion}
        
        <!-- 2. QUEJAS + CAUSAS RAÍZ por motivo -->
        {seccion_quejas}
        
        <!-- 3. PRODUCTOS (tabla + productos clave) -->
        {seccion_productos}
        
        <!-- 4. TRIANGULACIÓN (unificada) -->
        {seccion_triangulacion}
        
        <!-- 5. NOTICIAS DEL MERCADO (todas, por tema) -->
        {seccion_noticias_grid}
    </div>
    """
    
    # ==========================================================================
    # ANEXOS
    # ==========================================================================
    html_anexos = _generar_anexos(resultados, TXT, BANDERA, player, q_ant, q_act,
                                   grafico_wf_b64, grafico_quejas_b64,
                                   grafico_seg_b64, grafico_mot_inseg_b64,
                                   grafico_princ_b64, grafico_mot_princ_b64)
    
    # ==========================================================================
    # FOOTER
    # ==========================================================================
    html_footer = f"""
    <div class="footer-v3" style="background: #f8f9fa; padding: 15px 30px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e8ecf0;">
        Generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')} | 
        Modelo NPS v3.0 | {player} - {NOMBRE_PAIS}
    </div>
    """
    
    # ==========================================================================
    # ENSAMBLAJE FINAL (estructura EXACTA del notebook)
    # ==========================================================================
    html_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TXT['titulo_resumen']} - {player}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
</head>
<body style="margin: 0; padding: 20px; background: #f0f2f5;">
    
<style>
{CSS}
</style>

    <div class="resumen-v3">
        {html_header}
        {html_tab_resumen}
        {html_anexos}
        {html_footer}
    </div>

</body>
</html>
"""
    
    return html_completo


# ==============================================================================
# FUNCIONES AUXILIARES (copiadas EXACTAMENTE del notebook)
# ==============================================================================

def _generar_resumen_narrativo(player, nps_delta, quejas_deterioro, quejas_mejora, 
                                productos_sorted, delta_princ, delta_seg, noticias, q_ant, q_act,
                                triangulacion_motivos=None, causas_semanticas=None,
                                todos_los_productos=None):
    """
    Genera un resumen narrativo al estilo de las presentaciones del equipo.
    
    Umbrales (basados en metodología CX):
    - UMBRAL_PRINCIPAL = 0.5p.p. (motivos en dirección del NPS)
    - UMBRAL_COMPENSACION = 0.9p.p. (motivos opuestos, compensaciones)
    - UMBRAL_NPS_ESTABLE = 1.0p.p. (±1p.p. para considerar NPS "sin cambio")
    
    Si hay causas semánticas, las usa para enriquecer el texto.
    Si una noticia triangula bien con una causa raíz, se menciona en el diagnóstico.
    """
    if causas_semanticas is None:
        causas_semanticas = {}
    
    def _obtener_causa_raiz_top(motivo):
        """Devuelve el título de la causa raíz top para un motivo, o ''."""
        sem = causas_semanticas.get(motivo, {})
        causas = sem.get('causas_raiz', []) if sem else []
        if causas:
            return causas[0].get('titulo', '').lower()
        return ''
    # UMBRALES CONFIGURABLES
    UMBRAL_PRINCIPAL = 0.5
    UMBRAL_COMPENSACION = 0.9
    UMBRAL_NPS_ESTABLE = 1.0
    
    if triangulacion_motivos is None:
        triangulacion_motivos = []
    
    # MAPEO MOTIVO → PRODUCTO (asociación para el diagnóstico)
    MAPEO_MOTIVO_PRODUCTO = {
        'financiamiento': ['Crédito', 'Tarjeta de Crédito', 'Préstamo', 'Empréstimo'],
        'rendimientos': ['Rendimientos', 'Cuenta Remunerada', 'Inversiones'],
        'seguridad': ['Pix', 'Transferencias'],
        'complejidad': ['App', 'Pagos', 'Transferencias'],
        'promociones': ['Cashback', 'Beneficios'],
    }
    
    def buscar_producto_asociado(motivo, productos):
        """Busca producto relacionado al motivo de queja."""
        motivo_lower = motivo.lower()
        for key, productos_relacionados in MAPEO_MOTIVO_PRODUCTO.items():
            if key in motivo_lower:
                for prod in productos:
                    nombre = prod.get('nombre_display', prod.get('nombre_original', '')).lower()
                    for pr in productos_relacionados:
                        if pr.lower() in nombre:
                            return prod
        return None
    
    def buscar_noticia_triangulada(motivo, delta_queja=0):
        """
        Busca noticia que triangule bien con un motivo de queja.
        Solo incluye si la triangulación es coherente (no incoherente).
        Muestra resumen completo de la noticia con link clickeable.
        """
        noticia = _buscar_noticia_para_motivo(motivo, triangulacion_motivos, noticias)
        if noticia and noticia.get('titulo'):
            # Verificar coherencia: si es incoherente, no mencionar
            impacto = noticia.get('impacto_esperado', 'neutro')
            coherencia = _evaluar_coherencia_noticia(delta_queja, impacto)
            if 'Incoherente' in coherencia:
                return ''
            
            fuente = noticia.get('fuente', 'web')
            url = noticia.get('url', '')
            # Usar resumen completo; fallback a título si no hay resumen
            texto_noticia = noticia.get('resumen', '') or noticia.get('titulo', '')
            # Link clickeable separado
            if url:
                link = f' (<a href="{url}" target="_blank" style="color: #0369a1; text-decoration: underline;">ver noticia</a>)'
            else:
                link = f' ({fuente})'
            return f', consistente con {texto_noticia}{link}'
        return ''
    
    partes = []
    causas_principales = []
    causas_compensan = []
    
    # Clasificar productos por impacto
    productos_positivos = [p for p in productos_sorted if p.get('total_effect', 0) > UMBRAL_PRODUCTO_RELEVANTE]
    productos_negativos = [p for p in productos_sorted if p.get('total_effect', 0) < -UMBRAL_PRODUCTO_RELEVANTE]
    
    # 1. DETERMINAR DIRECCIÓN DEL NPS Y APLICAR UMBRALES
    nps_sube = nps_delta >= UMBRAL_NPS_ESTABLE
    nps_baja = nps_delta <= -UMBRAL_NPS_ESTABLE
    nps_estable = not nps_sube and not nps_baja
    
    # 2. HEADLINE - Player + NPS delta (con texto adecuado según dirección)
    signo = "+" if nps_delta >= 0 else ""
    if nps_estable:
        partes.append(f"<strong>{player}: NPS estable ({signo}{nps_delta:.0f}p.p.)</strong>")
    else:
        partes.append(f"<strong>{player}: NPS {signo}{nps_delta:.0f}p.p.</strong>")
    
    # MOTIVOS GENÉRICOS A EXCLUIR DEL DIAGNÓSTICO (no son informativos)
    MOTIVOS_EXCLUIR = {'otro', 'otros', 'other', 'outros', 'otra', 'otras', 'n/a', 'sin categoría'}
    
    def es_motivo_generico(motivo):
        """Retorna True si el motivo es genérico y debe excluirse del diagnóstico."""
        return motivo.lower().strip() in MOTIVOS_EXCLUIR
    
    def es_tema_valido(tema):
        """
        Valida que el tema sea descriptivo y tenga sentido en el diagnóstico.
        
        CRITERIO: Aceptar temas específicos extraídos del análisis de comentarios.
        Estos incluyen:
        - Menciones de competencia: "usuarios mencionan que Nubank ofrece mejor rendimiento"
        - Problemas concretos: "tasa de rendimiento baja", "app con errores"
        - Frases descriptivas: "cashback no acreditado o demorado"
        """
        if not tema:
            return False
        tema_limpio = tema.strip().lower()
        
        # PRIORIDAD 1: Temas que empiezan con "usuarios mencionan" son SIEMPRE válidos
        # Estos vienen del análisis profundo de comentarios
        if tema_limpio.startswith('usuarios mencionan') or tema_limpio.startswith('usuarios comparan'):
            return True
        
        # PRIORIDAD 2: Temas específicos conocidos (lista blanca - ES + PT)
        TEMAS_ESPECIFICOS_VALIDOS = {
            # Español
            'cashback no acreditado', 'cashback no acreditado o demorado',
            'tasa de rendimiento baja', 'rendimiento bajo',
            'app con errores o lentitud', 'app con errores',
            'atención al cliente deficiente', 'atención deficiente',
            'incidentes de fraude o hackeo', 'incidentes de fraude reportados',
            'cuenta bloqueada sin explicación', 'cuenta bloqueada',
            'límite de crédito insuficiente', 'límite insuficiente',
            'tasas o intereses altos', 'tasas altas', 'intereses altos',
            'difícil contactar soporte', 'soporte lento',
            'proceso de solicitud difícil', 'errores técnicos en la app',
            'demora en atención al cliente',
            # Português
            'cashback não creditado', 'cashback não creditado ou atrasado',
            'taxa de rendimento baixa', 'rendimento baixo',
            'app com erros ou lentidão', 'app com erros',
            'atendimento ao cliente deficiente', 'atendimento deficiente',
            'incidentes de fraude ou invasão', 'incidentes de fraude reportados',
            'conta bloqueada sem explicação', 'conta bloqueada',
            'limite de crédito insuficiente', 'limite insuficiente',
            'taxas ou juros altos', 'taxas altas', 'juros altos',
            'difícil contatar suporte', 'suporte lento',
            'processo de solicitação difícil', 'erros técnicos no app',
            'demora no atendimento ao cliente',
        }
        if tema_limpio in TEMAS_ESPECIFICOS_VALIDOS:
            return True
        
        # PRIORIDAD 3: Temas descriptivos (3+ palabras, 15+ caracteres)
        if len(tema_limpio) >= 15:
            palabras = tema_limpio.split()
            if len(palabras) >= 3:
                # Excluir frases genéricas
                FRASES_GENERICAS = {
                    'necesita mejoras', 'mejor en competencia', 'competencia mejor',
                    'falta de opciones', 'problemas varios', 'experiencia negativa',
                    'experiencia muy negativa', 'necesidades no cubiertas',
                    'expectativas no cumplidas', 'ofertas/beneficios insuficientes'
                }
                if tema_limpio not in FRASES_GENERICAS:
                    return True
        
        return False
    
    # Helper: obtener texto descriptivo de causa (semántica > tema > nada)
    def _texto_causa(motivo, tema=''):
        """Devuelve texto descriptivo: prioriza causa semántica, luego tema, luego vacío."""
        cr = _obtener_causa_raiz_top(motivo)
        if cr:
            return f" por {cr}"
        if es_tema_valido(tema) and 'diversas' not in tema.lower():
            return f" por {tema.lower()}"
        return ''
    
    # 3. CAUSAS PRINCIPALES (filtradas por umbral)
    if nps_estable:
        # NPS ESTABLE: mostrar movimientos significativos
        for q in quejas_deterioro:
            delta = q.get('delta', 0)
            motivo = q.get('motivo', 'N/A')
            if delta >= UMBRAL_PRINCIPAL and not es_motivo_generico(motivo):
                tema = q.get('tema_principal', '')
                texto = f"aumento de quejas de <strong>{motivo}</strong> (+{delta:.0f}p.p.)"
                texto += _texto_causa(motivo, tema)
                texto += buscar_noticia_triangulada(motivo, delta)
                causas_principales.append(texto)
        
        for q in quejas_mejora:
            delta_raw = q.get('delta', 0)
            delta = abs(delta_raw)
            motivo = q.get('motivo', 'N/A')
            if delta >= UMBRAL_COMPENSACION and not es_motivo_generico(motivo):
                texto = f"reducción de quejas de {motivo} (-{delta:.0f}p.p.)"
                texto += buscar_noticia_triangulada(motivo, delta_raw)
                causas_compensan.append(texto)
    
    elif nps_sube:
        for q in quejas_mejora:
            delta_raw = q.get('delta', 0)
            delta = abs(delta_raw)
            motivo = q.get('motivo', 'N/A')
            if delta >= UMBRAL_PRINCIPAL and not es_motivo_generico(motivo):
                texto = f"reducción de quejas de <strong>{motivo}</strong> (-{delta:.0f}p.p.)"
                texto += _texto_causa(motivo)
                texto += buscar_noticia_triangulada(motivo, delta_raw)
                causas_principales.append(texto)
        
        for q in quejas_deterioro:
            delta = q.get('delta', 0)
            motivo = q.get('motivo', 'N/A')
            if delta >= UMBRAL_COMPENSACION and not es_motivo_generico(motivo):
                tema = q.get('tema_principal', '')
                texto = f"incremento en quejas de {motivo} (+{delta:.0f}p.p.)"
                texto += _texto_causa(motivo, tema)
                texto += buscar_noticia_triangulada(motivo, delta)
                causas_compensan.append(texto)
    
    elif nps_baja:
        for q in quejas_deterioro:
            delta = q.get('delta', 0)
            motivo = q.get('motivo', 'N/A')
            if delta >= UMBRAL_PRINCIPAL and not es_motivo_generico(motivo):
                tema = q.get('tema_principal', '')
                texto = f"incremento en quejas de <strong>{motivo}</strong> (+{delta:.0f}p.p.)"
                texto += _texto_causa(motivo, tema)
                texto += buscar_noticia_triangulada(motivo, delta)
                causas_principales.append(texto)
        
        for q in quejas_mejora:
            delta_raw = q.get('delta', 0)
            delta = abs(delta_raw)
            motivo = q.get('motivo', 'N/A')
            if delta >= UMBRAL_COMPENSACION and not es_motivo_generico(motivo):
                texto = f"reducción de quejas de {motivo} (-{delta:.0f}p.p.)"
                texto += _texto_causa(motivo)
                texto += buscar_noticia_triangulada(motivo, delta_raw)
                causas_compensan.append(texto)
    
    # 4. ARMAR TEXTO CON FORMATO (I), (II)
    if causas_principales:
        if nps_estable:
            partes.append(", con movimientos en quejas: ")
        else:
            partes.append(", ")
        for i, causa in enumerate(causas_principales[:3]):
            if i == 0:
                partes.append(f"(I) {causa}")
            elif i == 1:
                partes.append(f" (II) {causa}")
            else:
                partes.append(f" (III) {causa}")
    
    # 5. COMPENSACIONES (si las hay y son significativas)
    if causas_compensan:
        if nps_estable:
            partes.append(f". Esto se compensa con {causas_compensan[0]}")
        else:
            partes.append(f". Sin embargo, compensa parcialmente {causas_compensan[0]}")
    
    # 6. CIERRE
    # (Principalidad y Seguridad se muestran aparte en las métricas headline, no en el texto narrativo)
    
    texto_quejas = ''.join(partes)
    
    # 7. PÁRRAFO PRODUCTOS CLAVE (separado, con quejas y noticias asociadas)
    # Mapeo inverso: producto → motivo de queja asociado
    MAPEO_PRODUCTO_QUEJA = {}
    for motivo_key, prods_relacionados in MAPEO_MOTIVO_PRODUCTO.items():
        for prod_name in prods_relacionados:
            MAPEO_PRODUCTO_QUEJA[prod_name.lower()] = motivo_key
    
    def _buscar_queja_asociada(nombre_producto):
        """Busca la queja asociada a un producto y devuelve texto descriptivo."""
        nombre_lower = nombre_producto.lower()
        for prod_key, motivo_key in MAPEO_PRODUCTO_QUEJA.items():
            if prod_key in nombre_lower or nombre_lower in prod_key:
                # Buscar en quejas_deterioro y quejas_mejora
                for q in quejas_deterioro + quejas_mejora:
                    motivo = q.get('motivo', '').lower()
                    if motivo_key in motivo:
                        delta = q.get('delta', 0)
                        causa = _obtener_causa_raiz_top(q.get('motivo', ''))
                        signo = "+" if delta > 0 else ""
                        texto = f"quejas de {q.get('motivo', '')} {signo}{delta:.0f}p.p."
                        if causa:
                            texto += f" por {causa}"
                        return texto, q.get('motivo', '')
        return '', ''
    
    partes_prod = []
    todos_productos = []
    for p in productos_negativos[:3]:
        todos_productos.append((p, 'deterioro'))
    for p in productos_positivos[:3]:
        todos_productos.append((p, 'mejora'))
    
    # GARANTÍA: Rendimientos SIEMPRE debe aparecer en el diagnóstico de productos
    # Buscar si algún producto de Rendimientos ya está incluido
    NOMBRES_RENDIMIENTOS = ['rendimiento', 'cuenta remunerada', 'inversiones', 'inversión', 'ahorro']
    ya_tiene_rendimientos = any(
        any(rend in p.get('nombre_display', p.get('nombre_original', '')).lower() 
            for rend in NOMBRES_RENDIMIENTOS)
        for p, _ in todos_productos
    )
    
    if not ya_tiene_rendimientos:
        # Buscar producto de Rendimientos en la lista COMPLETA de productos
        lista_busqueda = (todos_los_productos or []) + productos_sorted
        prod_rendimientos = None
        for p in lista_busqueda:
            nombre = p.get('nombre_display', p.get('nombre_original', '')).lower()
            if any(rend in nombre for rend in NOMBRES_RENDIMIENTOS):
                prod_rendimientos = p
                break
        
        if prod_rendimientos:
            efecto = prod_rendimientos.get('total_effect', 0)
            ctx = 'deterioro' if efecto < 0 else 'mejora'
            todos_productos.append((prod_rendimientos, ctx))
    
    if todos_productos:
        items_prod = []
        for p, contexto in todos_productos:
            nombre = p.get('nombre_display', p.get('nombre_original', ''))
            desc = _describir_producto(p, contexto=contexto)
            metricas = desc.replace(f'el producto {nombre} (', '').rstrip(')')
            
            # Buscar queja asociada
            queja_texto, motivo_queja = _buscar_queja_asociada(nombre)
            
            # Buscar noticia triangulada para el motivo asociado
            noticia_texto = ''
            delta_q = 0
            if motivo_queja:
                delta_q = next((q.get('delta', 0) for q in quejas_deterioro + quejas_mejora 
                               if q.get('motivo', '').lower() == motivo_queja.lower()), 0)
                noticia_texto = buscar_noticia_triangulada(motivo_queja, delta_q)
            
            # Descripción inteligente: si el efecto total es ~0 pero hay quejas asociadas,
            # explicar que no varió a pesar de las quejas
            total_eff = p.get('total_effect', 0)
            delta_nps_u = p.get('delta_nps_usuario', 0)
            delta_share = p.get('delta_share', 0)
            
            if abs(total_eff) < 0.3 and abs(delta_nps_u) < 2 and abs(delta_share) < 2:
                # Producto estable - describir en contexto de quejas
                if delta_q > 0 and queja_texto:
                    item = f"<strong>{nombre}</strong> sin variación significativa en uso ni NPS pese a {queja_texto}"
                elif delta_q < 0 and queja_texto:
                    item = f"<strong>{nombre}</strong> estable en uso y NPS, beneficiado por {queja_texto}"
                else:
                    item = f"<strong>{nombre}</strong> estable (sin cambios significativos en uso ni NPS)"
            else:
                # Producto con variación - describir normalmente
                item = f"<strong>{nombre}</strong> ({metricas})"
                if queja_texto:
                    item += f", asociado a {queja_texto}"
            
            if noticia_texto:
                item += noticia_texto
            items_prod.append(item)
        
        if items_prod:
            partes_prod.append("En productos, los movimientos más relevantes son: ")
            partes_prod.append(". ".join(items_prod))
            partes_prod.append(".")
    
    texto_productos = ''.join(partes_prod)
    
    return texto_quejas, texto_productos


def _generar_diagnostico_principal(resultados, TXT, q_ant, q_act, causas_semanticas=None):
    """
    Genera el diagnóstico principal con estructura PYRAMID PRINCIPLE.
    
    Incluye:
    - Resumen narrativo automático (copiable para presentaciones)
    - Métricas headline (NPS, Principalidad, Seguridad)
    - TOP Quejas (deterioros y mejoras) con causa raíz semántica
    - TOP Productos por impacto
    """
    if causas_semanticas is None:
        causas_semanticas = {}
    config = resultados['config']
    player = config['player']
    
    nps_data = resultados.get('nps', {})
    nps_q1 = nps_data.get('nps_q1', 0)
    nps_q2 = nps_data.get('nps_q2', 0)
    nps_delta = nps_q2 - nps_q1
    
    prod_data = resultados.get('productos', {})
    productos = prod_data.get('productos_clave', [])
    
    # Buscar causas/quejas en múltiples ubicaciones
    wf_data = resultados.get('waterfall', {})
    causas = resultados.get('causas_waterfall', [])
    if not causas:
        causas = wf_data.get('causas_waterfall', [])
    
    # Métricas de Seguridad y Principalidad (estructura anidada)
    seg_data = resultados.get('seguridad', {})
    princ_data = resultados.get('principalidad', {})
    
    # Extraer datos del player específico
    player_seg = seg_data.get('player_seguridad', {})
    player_princ = princ_data.get('player_principalidad', {})
    
    # Detectar si hay datos reales vs defaults a 0
    _seg_q1_raw = player_seg.get('seg_q1')
    _seg_q2_raw = player_seg.get('seg_q2')
    seg_datos_faltantes = (_seg_q1_raw is None and _seg_q2_raw is None) and not player_seg
    seg_q1 = (_seg_q1_raw or 0)
    seg_q2 = (_seg_q2_raw or 0)
    delta_seg = player_seg.get('delta', seg_q2 - seg_q1) or 0
    
    _princ_q1_raw = player_princ.get('princ_q1')
    _princ_q2_raw = player_princ.get('princ_q2')
    princ_datos_faltantes = (_princ_q1_raw is None and _princ_q2_raw is None) and not player_princ
    princ_q1 = (_princ_q1_raw or 0)
    princ_q2 = (_princ_q2_raw or 0)
    delta_princ = player_princ.get('delta', princ_q2 - princ_q1) or 0
    
    # =========================================================================
    # SEPARAR QUEJAS: Deterioros vs Mejoras
    # =========================================================================
    quejas_deterioro = sorted(
        [c for c in causas if c.get('delta', 0) > UMBRAL_PRODUCTO_RELEVANTE],  # Delta > 0 = más quejas = peor
        key=lambda x: x.get('delta', 0),
        reverse=True
    )[:3]
    
    quejas_mejora = sorted(
        [c for c in causas if c.get('delta', 0) < -UMBRAL_PRODUCTO_RELEVANTE],  # Delta < 0 = menos quejas = mejor
        key=lambda x: x.get('delta', 0)
    )[:3]
    
    # Top productos por impacto absoluto
    productos_sorted = sorted(productos, key=lambda x: abs(x.get('total_effect', 0)), reverse=True)[:3]
    todos_los_productos = sorted(productos, key=lambda x: abs(x.get('total_effect', 0)), reverse=True)
    
    # Noticias y triangulaciones para contexto
    noticias = resultados.get('noticias', [])
    triangulacion_motivos = resultados.get('triangulacion_motivos', [])
    
    # =========================================================================
    # GENERAR RESUMEN NARRATIVO AUTOMÁTICO
    # =========================================================================
    texto_quejas, texto_productos = _generar_resumen_narrativo(
        player=player,
        nps_delta=nps_delta,
        quejas_deterioro=quejas_deterioro,
        quejas_mejora=quejas_mejora,
        productos_sorted=productos_sorted,
        delta_princ=delta_princ,
        delta_seg=delta_seg,
        noticias=noticias,
        q_ant=q_ant,
        q_act=q_act,
        triangulacion_motivos=triangulacion_motivos,
        causas_semanticas=causas_semanticas,
        todos_los_productos=todos_los_productos
    )
    
    # =========================================================================
    # CONSTRUIR HTML DEL DIAGNÓSTICO
    # =========================================================================
    html_parts = []
    
    # HEADLINE
    emoji_tendencia = "📈" if nps_delta > 0 else "📉" if nps_delta < 0 else "➡️"
    html_parts.append(f"""
        <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 15px;">
            {emoji_tendencia} <strong>{player}</strong> {nps_delta:+.0f}pp NPS ({q_ant} → {q_act})
        </div>
    """)
    
    # PÁRRAFO QUEJAS
    html_parts.append(f"""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 18px 22px; border-radius: 10px; margin-bottom: 12px; border-left: 4px solid #0284c7; line-height: 1.7;">
            <div style="font-size: 11px; color: #0369a1; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">📢 Quejas</div>
            <div style="font-size: 14px; color: #1e293b;">{texto_quejas}</div>
        </div>
    """)
    
    # PÁRRAFO PRODUCTOS CLAVE (solo si hay contenido)
    if texto_productos:
        html_parts.append(f"""
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 18px 22px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #16a34a; line-height: 1.7;">
            <div style="font-size: 11px; color: #15803d; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">📦 Productos Clave</div>
            <div style="font-size: 14px; color: #1e293b;">{texto_productos}</div>
        </div>
        """)
    
    diagnostico_html = ''.join(html_parts)
    
    return f"""
        <div class="diagnostico-principal-box" style="background: linear-gradient(to bottom, #ffffff, #f8fafc); padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div class="diagnostico-principal-titulo" style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0;">
                📋 {TXT['diagnostico_principal']}
            </div>
            <div class="diagnostico-principal-texto">{diagnostico_html}</div>
        </div>
    """


def _buscar_noticia_para_motivo(motivo: str, triangulacion_motivos: list, noticias: list) -> dict:
    """
    Busca una noticia relacionada con un motivo del waterfall.
    Primero busca en triangulaciones ya hechas, luego en noticias directamente.
    """
    motivo_lower = motivo.lower()
    
    # 1. Buscar en triangulaciones ya calculadas
    for tri in triangulacion_motivos:
        tri_motivo = tri.get('motivo', '').lower()
        if tri_motivo in motivo_lower or motivo_lower in tri_motivo:
            return tri.get('noticia', {})
    
    # 2. Búsqueda directa en noticias por categoría
    MAPEO_MOTIVO_CATEGORIA = {
        'financiamiento': ['financiamiento', 'crédito', 'credito', 'préstamo', 'emprestimo'],
        'financiamento': ['financiamiento', 'crédito', 'credito', 'préstamo', 'emprestimo'],
        'rendimiento': ['rendimientos', 'rendimentos', 'cdi', 'inversión', 'ahorro'],
        'rendimentos': ['rendimientos', 'rendimentos', 'cdi', 'inversión', 'ahorro'],
        'seguridad': ['seguridad', 'segurança', 'fraude', 'robo'],
        'segurança': ['seguridad', 'segurança', 'fraude', 'robo'],
        'atención': ['atención', 'atendimento', 'soporte', 'sac'],
        'atendimento': ['atención', 'atendimento', 'soporte', 'sac'],
        'funcionalidad': ['funcionalidades', 'app', 'tecnología', 'feature'],
        'promociones': ['promociones', 'promoções', 'beneficios', 'cashback'],
        'beneficios': ['promociones', 'promoções', 'beneficios', 'cashback'],
    }
    
    categorias_buscar = []
    for key, cats in MAPEO_MOTIVO_CATEGORIA.items():
        if key in motivo_lower:
            categorias_buscar.extend(cats)
            break
    
    if not categorias_buscar:
        categorias_buscar = [motivo_lower]
    
    for noticia in noticias:
        cat_noticia = noticia.get('categoria_relacionada', '').lower()
        for cat in categorias_buscar:
            if cat in cat_noticia or cat_noticia in cat:
                return noticia
    
    return {}


def _evaluar_coherencia_noticia(delta_queja: float, impacto_noticia: str) -> str:
    """
    Evalúa coherencia entre cambio de queja y impacto de noticia.
    """
    if impacto_noticia == 'positivo' and delta_queja < 0:
        return "✓ Coherente"
    elif impacto_noticia == 'negativo' and delta_queja > 0:
        return "✓ Coherente"
    elif impacto_noticia == 'positivo' and delta_queja > 0:
        return "? Incoherente"
    elif impacto_noticia == 'negativo' and delta_queja < 0:
        return "? Incoherente"
    else:
        return "Neutro"


def _mapear_queja_a_producto(motivo, productos):
    """
    Mapea una queja a un producto relacionado usando keywords inteligentes.
    Retorna (producto_nombre, delta_uso, producto_dict, explicacion)
    
    producto_dict contiene: total_effect, nps_effect, mix_effect,
    delta_nps_usuario, delta_share, etc.
    
    Mapeo basado en la lógica del notebook:
    - Quejas de Financiamiento/Crédito → productos tipo 'credito'
    - Quejas de Rendimientos → productos tipo 'ahorro'
    - Quejas operativas (Atención, Complejidad, Seguridad) → sin producto
    """
    # Mapeo queja -> tipo de producto
    MAPEO_QUEJA_TIPO = {
        # Quejas relacionadas con CRÉDITO
        'financiamento': 'credito',
        'financiamiento': 'credito',
        'crédito': 'credito',
        'credito': 'credito',
        'empréstimo': 'credito',
        'emprestimo': 'credito',
        'préstamo': 'credito',
        'prestamo': 'credito',
        'cartão': 'credito',
        'cartao': 'credito',
        'tarjeta': 'credito',
        
        # Quejas relacionadas con AHORRO/RENDIMIENTOS
        'rendimento': 'ahorro',
        'rendimientos': 'ahorro',
        'investimento': 'ahorro',
        'inversión': 'ahorro',
        'inversion': 'ahorro',
        'poupança': 'ahorro',
        'poupanca': 'ahorro',
        'ahorro': 'ahorro',
        
        # Quejas OPERATIVAS (sin producto)
        'atención': None,
        'atencion': None,
        'atendimento': None,
        'complejidad': None,
        'complexidade': None,
        'seguridad': None,
        'segurança': None,
        'seguranca': None,
        'funcionalidades': None,
        'funcionalidad': None,
        'promociones': None,
        'promoções': None,
        'otro': None,
        'outros': None,
        'otros': None,
    }
    
    motivo_lower = motivo.lower()
    
    # Determinar tipo de producto a buscar
    tipo_producto = None
    for queja_key, tipo in MAPEO_QUEJA_TIPO.items():
        if queja_key in motivo_lower:
            tipo_producto = tipo
            break
    
    # Si es queja operativa, no hay producto asociado
    if tipo_producto is None:
        return None, 0, None, "— Operativo"
    
    # Buscar producto del tipo correcto
    producto_relacionado = None
    for p in productos:
        if p.get('tipo') == tipo_producto:
            # Preferir el de mayor impacto absoluto
            if producto_relacionado is None:
                producto_relacionado = p
            elif abs(p.get('total_effect', 0)) > abs(producto_relacionado.get('total_effect', 0)):
                producto_relacionado = p
    
    if not producto_relacionado:
        return None, 0, None, "— Operativo"
    
    # Retornar datos del producto (dict completo para descomponer NPS vs share)
    nombre = producto_relacionado.get('nombre_display', producto_relacionado.get('nombre_original', ''))
    delta_uso = producto_relacionado.get('delta_share', 0)
    
    return nombre, delta_uso, producto_relacionado, None


def _describir_producto(prod_dict, contexto='deterioro'):
    """
    Genera frase descriptiva de un producto descomponiendo NPS vs share.
    
    En vez de mostrar total_effect (que puede ser ~0 cuando se netean),
    explica por separado:
    - delta_nps_usuario: cómo cambió el NPS de los que usan el producto
    - delta_share: cómo cambió la penetración del producto
    
    Args:
        prod_dict: dict del producto con nps_effect, mix_effect, delta_nps_usuario, delta_share, etc.
        contexto: 'deterioro' o 'mejora' para ajustar el fraseo
    Returns:
        str: frase descriptiva (ej: "NPS usuarios -3pp, share +2pp")
    """
    if not isinstance(prod_dict, dict):
        return ""
    
    nombre = prod_dict.get('nombre_display', prod_dict.get('nombre_original', ''))
    delta_nps_u = prod_dict.get('delta_nps_usuario', 0)
    delta_share = prod_dict.get('delta_share', 0)
    
    partes = []
    
    # NPS de usuarios del producto
    if abs(delta_nps_u) >= UMBRAL_NPS_PRODUCTO_RELEVANTE:
        if delta_nps_u > 0:
            partes.append(f"NPS usuarios +{delta_nps_u:.0f}pp")
        else:
            partes.append(f"NPS usuarios {delta_nps_u:.0f}pp")
    
    # Share / penetración
    if abs(delta_share) >= UMBRAL_SHARE_RELEVANTE:
        if delta_share > 0:
            partes.append(f"share +{delta_share:.0f}pp")
        else:
            partes.append(f"share {delta_share:.0f}pp")
    
    if partes:
        return f"el producto {nombre} ({', '.join(partes)})"
    else:
        total = prod_dict.get('total_effect', 0)
        return f"el producto {nombre} ({total:+.0f}p.p.)"


def _evaluar_triangulacion(queja_delta, prod_dict_or_effect, producto_nombre):
    """
    Evalúa la coherencia entre queja y producto.
    queja_delta > 0 = más quejas (deterioro)
    queja_delta < 0 = menos quejas (mejora)
    
    Acepta tanto un dict de producto como un número (total_effect) por compatibilidad.
    Usa delta_nps_usuario como señal principal si está disponible (más informativo
    que total_effect que netea NPS y share).
    """
    if producto_nombre is None:
        return "", "— Operativo"
    
    # Extraer el efecto relevante
    if isinstance(prod_dict_or_effect, dict):
        # Usar delta_nps_usuario como señal principal
        delta_nps_u = prod_dict_or_effect.get('delta_nps_usuario', 0)
        producto_effect = prod_dict_or_effect.get('total_effect', 0)
        # Si hay un cambio claro en NPS usuario, usar eso para coherencia
        if abs(delta_nps_u) >= 1:
            señal = delta_nps_u
        else:
            señal = producto_effect
    else:
        señal = prod_dict_or_effect if prod_dict_or_effect is not None else 0
    
    if señal > 0 and queja_delta < 0:
        return "triangulacion-coherente", "✓ Coherente: mejora en producto = menos quejas"
    elif señal > 0 and queja_delta > 0:
        return "triangulacion-incoherente", "✗ Incoherente: producto mejora pero quejas suben"
    elif señal < 0 and queja_delta > 0:
        return "triangulacion-coherente", "✓ Coherente: deterioro producto = más quejas"
    elif señal < 0 and queja_delta < 0:
        return "triangulacion-incoherente", "✗ Incoherente: producto empeora pero quejas bajan"
    else:
        return "", "— Sin cambio significativo"


def _generar_quejas_box(resultados, TXT, q_ant, q_act):
    """
    Genera el análisis de quejas EXACTAMENTE como en el notebook.
    Sección diagnostico-quejas-box con deterioros, mejoras, productos asociados y tags de coherencia.
    """
    wf_data = resultados.get('waterfall', {})
    
    # Obtener causas waterfall (transformar si es DataFrame)
    wf_df = wf_data.get('waterfall_data_comparativo', None)
    causas_waterfall = []
    if wf_df is not None:
        try:
            if hasattr(wf_df, 'to_dict'):
                for _, row in wf_df.iterrows():
                    causas_waterfall.append({
                        'motivo': row.get('Motivo', ''),
                        'delta': row.get('Delta', 0) if 'Delta' in row.index else 0,
                        'pct_q1': row.get('Impacto_Anterior', 0) if 'Impacto_Anterior' in row.index else 0,
                        'pct_q2': row.get('Impacto_Actual', 0),
                    })
        except Exception:
            pass
    
    # Obtener productos para triangulación
    prod_data = resultados.get('productos', {})
    productos = prod_data.get('productos_clave', [])
    
    if not causas_waterfall:
        return ''
    
    # Separar deterioros y mejoras (delta > 0 = más quejas = deterioro)
    deterioros = [c for c in causas_waterfall if c.get('delta', 0) > 0]
    mejoras = [c for c in causas_waterfall if c.get('delta', 0) < 0]
    
    total_balance = sum(c.get('delta', 0) for c in causas_waterfall)
    balance_texto = "mejora neta" if total_balance < -0.1 else ("deterioro neto" if total_balance > 0.1 else "sin cambio neto")
    
    html = f"""
        <div class="diagnostico-quejas-box">
            <div class="diagnostico-quejas-titulo">📢 {TXT['analisis_quejas']}</div>
            <div class="diagnostico-quejas-texto">
        <div style="background: #f8fafc; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #e2e8f0;">
            <strong style="color: #0f172a;">📊 Las quejas explican <strong>{total_balance:+.0f}pp</strong> del cambio en NPS ({balance_texto}).</strong>
        </div>
    """
    
    # Deterioros (delta > 0 = más quejas)
    if deterioros:
        html += f"""
            <div class="quejas-deterioros">
                <div style="font-weight: 700; color: #dc2626; margin-bottom: 10px; font-size: 13px;">⚠️ {TXT['deterioros']}</div>
        """
        for c in sorted(deterioros, key=lambda x: x.get('delta', 0), reverse=True)[:5]:
            motivo = c.get('motivo', 'N/A')
            delta = c.get('delta', 0)
            
            # Buscar producto asociado y evaluar coherencia
            prod_nombre, prod_delta_uso, prod_dict, _ = _mapear_queja_a_producto(motivo, productos)
            
            if prod_nombre:
                triangulacion_class, coherencia_texto = _evaluar_triangulacion(delta, prod_dict, prod_nombre)
                producto_texto = _describir_producto(prod_dict, contexto='deterioro')
            else:
                triangulacion_class = ""
                coherencia_texto = "— Operativo"
                producto_texto = "Sin producto asociado"
            
            html += f"""
            <div style="margin: 8px 0; padding: 10px 14px; background: rgba(255,255,255,0.6); border-radius: 6px; border-left: 3px solid #dc2626;">
                <strong style="color: #1e293b;">{motivo}</strong>
                <span style="font-weight: 700; color: #dc2626; margin-left: 8px;">{delta:+.0f}pp</span>
                <br><span style="font-size: 12px; color: #64748b;">→ {producto_texto} <span class="triangulacion-tag {triangulacion_class}" style="margin-left: 4px;">{coherencia_texto}</span></span>
            </div>
            """
        html += "</div>"
    
    # Mejoras (delta < 0 = menos quejas)
    if mejoras:
        html += f"""
            <div class="quejas-mejoras">
                <div style="font-weight: 700; color: #16a34a; margin-bottom: 10px; font-size: 13px;">✅ {TXT['mejoras']}</div>
        """
        for c in sorted(mejoras, key=lambda x: x.get('delta', 0))[:5]:
            motivo = c.get('motivo', 'N/A')
            delta = c.get('delta', 0)
            
            # Buscar producto asociado y evaluar coherencia
            prod_nombre, prod_delta_uso, prod_dict, _ = _mapear_queja_a_producto(motivo, productos)
            
            if prod_nombre:
                triangulacion_class, coherencia_texto = _evaluar_triangulacion(delta, prod_dict, prod_nombre)
                producto_texto = _describir_producto(prod_dict, contexto='mejora')
            else:
                triangulacion_class = ""
                coherencia_texto = "— Operativo"
                producto_texto = "Sin producto asociado"
            
            html += f"""
            <div style="margin: 8px 0; padding: 10px 14px; background: rgba(255,255,255,0.6); border-radius: 6px; border-left: 3px solid #16a34a;">
                <strong style="color: #1e293b;">{motivo}</strong>
                <span style="font-weight: 700; color: #16a34a; margin-left: 8px;">{delta:+.0f}pp</span>
                <br><span style="font-size: 12px; color: #64748b;">→ {producto_texto} <span class="triangulacion-tag {triangulacion_class}" style="margin-left: 4px;">{coherencia_texto}</span></span>
            </div>
            """
        html += "</div>"
    
    # Total
    color_balance = "#16a34a" if total_balance < 0 else "#dc2626"
    html += f"""
            <div class="quejas-total" style="border-left: 3px solid {color_balance}; background: #f0f7ff; padding: 15px 20px; border-radius: 8px; margin-top: 20px;">
                📊 <strong>Balance neto:</strong> {total_balance:+.0f}pp ({balance_texto})
            </div>
            </div>
        </div>
    """
    
    return html


def _generar_causas_deepdive(resultados, TXT, q_ant, q_act):
    """
    Deep Dive de Productos Clave (top 3 por impacto absoluto).
    
    Para cada producto muestra:
    1. Header con nombre + total effect + badge
    2. Tabla histórica (últimos 5Q): Share y NPS Usuario
    3. Descomposición del impacto: Mix Effect vs NPS Effect
    4. Queja conectada con coherencia
    5. Causas raíz semánticas del motivo asociado
    6. Noticia triangulada (si existe)
    7. Comentarios representativos
    """
    prod_data = resultados.get('productos', {})
    productos = prod_data.get('productos_clave', [])
    
    wf_data = resultados.get('waterfall', {})
    causas = wf_data.get('causas_waterfall', [])
    causas_enriquecidas = resultados.get('causas_waterfall', causas)
    
    # Triangulaciones y causas semánticas
    triangulaciones = resultados.get('triangulaciones', [])
    causas_semanticas = resultados.get('causas_semanticas', {})
    
    if not productos:
        return ''
    
    # Top 3 productos por impacto absoluto
    top = sorted(productos, key=lambda x: abs(x.get('total_effect', 0)), reverse=True)[:3]
    
    html = """
    <div class="seccion-diagnostico">
        <div class="seccion-titulo-simple">
            <span class="icono">🎯</span> Productos Clave
        </div>
        <div class="diagnostico-contenido">
    """
    
    for i, p in enumerate(top, 1):
        nombre = p.get('nombre_display', p.get('nombre_original', 'N/A'))
        nombre_orig = p.get('nombre_original', nombre)
        total = p.get('total_effect', 0)
        share_q1 = p.get('share_q1', 0)
        share_q2 = p.get('share_q2', 0)
        delta_share = p.get('delta_share', share_q2 - share_q1)
        nps_u_q1 = p.get('nps_usuario_q1', 0)
        nps_u_q2 = p.get('nps_usuario_q2', 0)
        delta_nps_u = p.get('delta_nps_usuario', nps_u_q2 - nps_u_q1)
        mix_eff = p.get('mix_effect', 0)
        nps_eff = p.get('nps_effect', 0)
        lift_q2 = p.get('lift_q2', 0)
        historico = p.get('historico', {})
        
        # Detect "new to tracking" products (share went from ~0 to significant)
        es_nuevo_tracking = share_q1 < 2 and share_q2 >= 10
        
        # For new-to-tracking products, use last 2 available quarters for trend instead
        hist_q = historico.get('quarters', [])
        hist_s = historico.get('share', [])
        hist_n = historico.get('nps_usuario', [])
        
        if es_nuevo_tracking and len(hist_s) >= 2:
            # Find last 2 quarters with actual data (share > 2%)
            datos_reales = [(q, s, n) for q, s, n in zip(hist_q, hist_s, hist_n) if s >= 2]
            if len(datos_reales) >= 2:
                q_prev, s_prev, n_prev = datos_reales[-2]
                q_curr, s_curr, n_curr = datos_reales[-1]
                delta_share_reciente = s_curr - s_prev
                delta_nps_reciente = n_curr - n_prev
            else:
                delta_share_reciente = delta_share
                delta_nps_reciente = delta_nps_u
        else:
            delta_share_reciente = delta_share
            delta_nps_reciente = delta_nps_u
        
        # Color según impacto
        es_positivo = total > 0
        color_borde = "#22c55e" if es_positivo else "#ef4444"
        badge_bg = "#ecfdf5" if es_positivo else "#fef2f2"
        badge_text = "#16a34a" if es_positivo else "#dc2626"
        
        # Badge principal: si es nuevo en tracking, mostrar "Nuevo en tracking" + tendencia reciente
        if es_nuevo_tracking:
            # Use recent trend for the badge
            tendencia_reciente = delta_share_reciente + delta_nps_reciente / 10  # simplified
            badge_html = f"""
                            <span style="background: #dbeafe; color: #1d4ed8; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 11px; border: 1px solid #93c5fd;">Nuevo en tracking</span>
                            <span style="background: {badge_bg}; color: {badge_text}; padding: 4px 10px; border-radius: 20px; font-weight: 700; font-size: 12px; border: 1px solid {color_borde}40;">Impacto: {total:+.1f}pp</span>
            """
        else:
            badge_html = f"""
                            <span style="background: {badge_bg}; color: {badge_text}; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 13px; border: 1px solid {color_borde}40;">{total:+.1f}pp</span>
            """
        
        # ── 1. HEADER ──
        html += f"""
            <div style="background: white; border: 1px solid #e2e8f0; border-left: 4px solid {color_borde}; border-radius: 10px; margin-bottom: 20px; overflow: hidden;">
                <div style="padding: 16px 20px; background: linear-gradient(to right, {badge_bg}, white); border-bottom: 1px solid #f1f5f9;">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="font-weight: 700; color: #0f172a; font-size: 16px;">{nombre}</span>
                            {badge_html}
                        </div>
                        <div style="display: flex; gap: 16px; font-size: 12px; color: #64748b;">
                            <span>Mix: <strong style="color: {'#16a34a' if mix_eff > 0 else '#dc2626' if mix_eff < 0 else '#64748b'};">{mix_eff:+.2f}pp</strong></span>
                            <span>NPS Eff: <strong style="color: {'#16a34a' if nps_eff > 0 else '#dc2626' if nps_eff < 0 else '#64748b'};">{nps_eff:+.2f}pp</strong></span>
                            <span>Lift: <strong>{lift_q2:+.0f}</strong></span>
                        </div>
                    </div>
                </div>
                
                <div style="padding: 16px 20px;">
        """
        
        # Nota explicativa para productos nuevos en tracking
        if es_nuevo_tracking:
            html += f"""
                    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; font-size: 12px; color: #1e40af; display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 16px;">ℹ️</span>
                        <span>Este producto no tenía adopción significativa en {q_ant} ({share_q1:.0f}%) y creció a {share_q2:.0f}% en {q_act}. El impacto de <strong>{total:+.1f}pp</strong> refleja principalmente el <em>efecto de entrada</em> al tracking, no necesariamente una mejora QoQ. Consultá la tabla histórica para ver la tendencia real.</span>
                    </div>
            """
        
        # ── 2. TABLA HISTÓRICA ──
        hist_quarters = historico.get('quarters', [])
        hist_share = historico.get('share', [])
        hist_nps = historico.get('nps_usuario', [])
        
        if hist_quarters and len(hist_quarters) >= 2:
            # Build table headers
            th_cells = ""
            for qi, q_label in enumerate(hist_quarters):
                is_last = (qi == len(hist_quarters) - 1)
                bg = "background: #eff6ff;" if is_last else ""
                fw = "font-weight: 700;" if is_last else "font-weight: 600;"
                th_cells += f'<th style="padding: 6px 10px; text-align: center; font-size: 11px; color: #475569; {bg} {fw} border-bottom: 2px solid #e2e8f0;">{q_label}</th>'
            
            # Share row
            share_cells = ""
            for qi, val in enumerate(hist_share):
                is_last = (qi == len(hist_share) - 1)
                bg = "background: #eff6ff;" if is_last else ""
                fw = "font-weight: 700;" if is_last else ""
                # Delta arrow for non-first values
                arrow = ""
                if qi > 0:
                    diff = val - hist_share[qi - 1]
                    if abs(diff) >= 0.5:
                        arrow_color = "#16a34a" if diff > 0 else "#dc2626"
                        arrow = f' <span style="color: {arrow_color}; font-size: 9px;">{"▲" if diff > 0 else "▼"}</span>'
                share_cells += f'<td style="padding: 6px 10px; text-align: center; font-size: 12px; {bg} {fw}">{val:.0f}%{arrow}</td>'
            
            # NPS row
            nps_cells = ""
            for qi, val in enumerate(hist_nps):
                is_last = (qi == len(hist_nps) - 1)
                bg = "background: #eff6ff;" if is_last else ""
                fw = "font-weight: 700;" if is_last else ""
                arrow = ""
                if qi > 0:
                    diff = val - hist_nps[qi - 1]
                    if abs(diff) >= 1:
                        arrow_color = "#16a34a" if diff > 0 else "#dc2626"
                        arrow = f' <span style="color: {arrow_color}; font-size: 9px;">{"▲" if diff > 0 else "▼"}</span>'
                nps_cells += f'<td style="padding: 6px 10px; text-align: center; font-size: 12px; {bg} {fw}">{val:.0f}{arrow}</td>'
            
            html += f"""
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 14px; border: 1px solid #e2e8f0; border-radius: 8px;">
                        <thead>
                            <tr style="background: #f8fafc;">
                                <th style="padding: 6px 10px; text-align: left; font-size: 11px; color: #64748b; border-bottom: 2px solid #e2e8f0; min-width: 80px;"></th>
                                {th_cells}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 6px 10px; font-size: 11px; font-weight: 600; color: #475569;">Adopción</td>
                                {share_cells}
                            </tr>
                            <tr style="border-top: 1px solid #f1f5f9;">
                                <td style="padding: 6px 10px; font-size: 11px; font-weight: 600; color: #475569;">NPS Usu.</td>
                                {nps_cells}
                            </tr>
                        </tbody>
                    </table>
            """
        
        # ── 3. QUEJA CONECTADA + COHERENCIA ──
        queja_rel = _buscar_queja_relacionada(nombre, causas_enriquecidas)
        
        # Also try to find from triangulaciones for noticia
        tri_match = None
        nombre_lower = nombre.lower()
        for tri in triangulaciones:
            tri_prod = tri.get('producto', '').lower()
            if tri_prod and (tri_prod in nombre_lower or nombre_lower in tri_prod):
                tri_match = tri
                break
        
        if queja_rel:
            motivo_queja = queja_rel.get('motivo', '')
            delta_queja = queja_rel.get('delta', 0)
            coherencia = _evaluar_coherencia_texto(total, delta_queja)
            
            if 'COHERENTE' in coherencia.upper() and 'INCOHERENTE' not in coherencia.upper():
                coh_color = '#10b981'
                coh_bg = '#ecfdf5'
            elif 'INCOHERENTE' in coherencia.upper():
                coh_color = '#f59e0b'
                coh_bg = '#fffbeb'
            else:
                coh_color = '#6b7280'
                coh_bg = '#f9fafb'
            
            html += f"""
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap;">
                        <div style="background: #f8fafc; padding: 6px 12px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 12px;">
                            <span style="color: #64748b;">Queja:</span>
                            <strong style="color: #1e293b; margin-left: 4px;">{motivo_queja}</strong>
                            <span style="color: {'#ef4444' if delta_queja > 0 else '#10b981'}; font-weight: 600; margin-left: 4px;">{delta_queja:+.0f}pp</span>
                        </div>
                        <span style="background: {coh_bg}; color: {coh_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; border: 1px solid {coh_color}40;">{coherencia}</span>
                    </div>
            """
            
            # ── 4. CAUSAS RAÍZ SEMÁNTICAS ──
            motivo_sem = motivo_queja
            causas_motivo = causas_semanticas.get(motivo_sem, {})
            causas_raiz_list = causas_motivo.get('causas_raiz', [])
            
            if causas_raiz_list:
                html += '<div style="margin-bottom: 12px;">'
                html += '<div style="font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 6px; text-transform: uppercase;">Causas raíz identificadas:</div>'
                html += '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'
                for cr in causas_raiz_list[:3]:
                    titulo_cr = cr.get('titulo', '')
                    freq = cr.get('frecuencia_pct', 0)
                    html += f"""
                        <div style="background: #fef3c7; border: 1px solid #fbbf2440; border-radius: 8px; padding: 8px 12px; flex: 1; min-width: 180px;">
                            <div style="font-size: 12px; font-weight: 600; color: #92400e; line-height: 1.3;">{html_module.escape(titulo_cr[:80])}</div>
                            <div style="font-size: 11px; color: #b45309; margin-top: 3px;">{freq:.0f}% de menciones</div>
                        </div>
                    """
                html += '</div></div>'
        
        # ── 5. NOTICIA ──
        noticia = None
        if tri_match and tri_match.get('noticia'):
            noticia = tri_match['noticia']
        elif queja_rel:
            triang = queja_rel.get('triangulacion')
            if triang and isinstance(triang, dict) and triang.get('noticia_titulo'):
                noticia = triang
        
        if noticia:
            n_titulo = noticia.get('titulo', noticia.get('noticia_titulo', ''))
            n_url = noticia.get('url', '#')
            n_fuente = noticia.get('fuente', '')
            if n_titulo:
                html += f"""
                    <div style="background: #f0fdf4; border: 1px solid #bbf7d040; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 16px;">📰</span>
                        <div>
                            <a href="{n_url}" target="_blank" style="font-size: 12px; color: #047857; font-weight: 600; text-decoration: none; line-height: 1.3;">{html_module.escape(n_titulo[:90])}</a>
                            {'<div style="font-size: 10px; color: #6b7280; margin-top: 2px;">' + html_module.escape(n_fuente) + '</div>' if n_fuente else ''}
                        </div>
                    </div>
                """
        
        # ── 6. COMENTARIOS ──
        comentarios_encontrados = []
        if queja_rel:
            comentarios_encontrados = queja_rel.get('ejemplos_comentarios', queja_rel.get('comentarios', []))
        
        if comentarios_encontrados:
            muestra = comentarios_encontrados[:3]
            comms_items = ""
            for c in muestra:
                c_str = str(c)
                c_texto = html_module.escape(c_str[:150])
                ellipsis = "..." if len(c_str) > 150 else ""
                comms_items += f'<div style="margin-top: 4px; font-style: italic; color: #64748b; font-size: 11px;">"{c_texto}{ellipsis}"</div>'
            html += f"""
                    <div style="background: #fafafa; border-radius: 8px; padding: 10px 14px; border: 1px solid #f1f5f9;">
                        <div style="font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 4px;">💬 Usuarios dicen:</div>
                        {comms_items}
                    </div>
            """
        
        # Close product card
        html += """
                </div>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html


def _generar_acordeon_waterfall(motivo_data, es_mejora=True, q_ant='Q1', q_act='Q2', causas_semanticas=None):
    """
    Genera un acordeón enriquecido para un motivo de queja.
    Si hay causas semánticas disponibles para este motivo, las usa.
    Si no, muestra las subcausas keyword como fallback.
    """
    if causas_semanticas is None:
        causas_semanticas = {}
    
    motivo = motivo_data.get('motivo', 'Sin motivo')
    delta = motivo_data.get('delta', 0)
    pct_q1 = motivo_data.get('pct_q1', 0)
    pct_q2 = motivo_data.get('pct_q2', 0)
    
    # Colores según tipo
    color_bg = "#e8f5e9" if es_mejora else "#ffebee"
    color_tag = "#c8e6c9" if es_mejora else "#ffcdd2"
    color_tag_text = "#2e7d32" if es_mejora else "#c62828"
    color_borde = "#10b981" if es_mejora else "#ef4444"
    
    n_comentarios = motivo_data.get('num_comentarios_q2', 0)
    
    # ==================================================================
    # Buscar causas semánticas para este motivo
    # ==================================================================
    causas_sem = causas_semanticas.get(motivo, {})
    causas_raiz = causas_sem.get('causas_raiz', []) if causas_sem else []
    
    subcausas_html = ""
    
    if causas_raiz:
        # USAR CAUSAS SEMÁNTICAS (del análisis LLM)
        total_comms = causas_sem.get('total_comentarios_analizados', n_comentarios)
        subcausas_html = f'''
        <div style="margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <strong style="font-size: 12px; color: #1a5276;">🔍 Causas raíz identificadas ({total_comms} comentarios analizados)</strong>
                <span style="font-size: 10px; color: #6366f1; background: #eef2ff; padding: 2px 8px; border-radius: 10px;">análisis semántico</span>
            </div>
        '''
        
        colors = ['#2563eb', '#7c3aed', '#0891b2', '#c2410c']
        
        for i, causa in enumerate(causas_raiz):
            titulo = html_module.escape(causa.get('titulo', ''))
            desc = html_module.escape(causa.get('descripcion', ''))
            freq_pct = causa.get('frecuencia_pct', 0)
            freq_abs = causa.get('frecuencia_abs', 0)
            ejemplos = causa.get('ejemplos', [])
            bar_color = colors[i % len(colors)]
            
            # Ejemplos HTML
            ejemplos_html = ""
            if ejemplos:
                ejemplos_items = ""
                for ej in ejemplos[:3]:
                    ej_limpio = html_module.escape(str(ej)[:200])
                    ellipsis = "..." if len(str(ej)) > 200 else ""
                    ejemplos_items += f'''
                        <div style="padding: 8px 12px; background: white; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid {bar_color};">
                            <span style="font-size: 11px; color: #555; font-style: italic;">"{ej_limpio}{ellipsis}"</span>
                        </div>'''
                
                ejemplos_html = f'''
                <details style="margin-top: 6px;">
                    <summary style="font-size: 10px; color: #0369a1; cursor: pointer; user-select: none;">
                        💬 Ver comentarios representativos
                    </summary>
                    <div style="margin-top: 8px; padding-left: 4px;">
                        {ejemplos_items}
                    </div>
                </details>'''
            
            subcausas_html += f'''
            <div style="margin-bottom: 14px; padding: 12px 14px; background: #f9fafb; border-radius: 8px; border-left: 4px solid {bar_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                    <span style="font-size: 12px; font-weight: 700; color: #1f2937; flex: 1;">{titulo}</span>
                    <span style="background: {bar_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; white-space: nowrap; margin-left: 10px;">
                        {freq_pct}% ({freq_abs})
                    </span>
                </div>
                <div style="background: #e5e7eb; border-radius: 4px; height: 6px; overflow: hidden; margin-bottom: 6px;">
                    <div style="background: {bar_color}; width: {min(freq_pct, 100)}%; height: 100%; border-radius: 4px;"></div>
                </div>
                <div style="font-size: 11px; color: #6b7280; line-height: 1.4;">{desc}</div>
                {ejemplos_html}
            </div>'''
        
        subcausas_html += '</div>'
    else:
        # FALLBACK: subcausas keyword (comportamiento original)
        subcausas = motivo_data.get('subcausas', [])
        
        if subcausas:
            subcausas_html = f'''
            <div style="margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <strong style="font-size: 12px; color: #1a5276;">🎯 ¿Qué dicen los usuarios? (análisis de {n_comentarios} comentarios)</strong>
                    <span style="font-size: 10px; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 10px;">≈100%</span>
                </div>
            '''
            
            for sc in subcausas[:6]:
                sc_nombre = str(sc.get('subcausa', sc.get('nombre', '')))[:50]
                sc_pct = sc.get('porcentaje', 0)
                sc_menciones = sc.get('menciones', 0)
                bar_color = color_tag_text if sc_pct >= 40 else "#666" if sc_pct >= 20 else "#999"
                
                subcausas_html += f'''
                <div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #eee;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-size: 12px; color: #333;">{sc_nombre}</span>
                        <span style="font-size: 12px; font-weight: 700; color: {bar_color};">{sc_pct:.0f}%</span>
                    </div>
                    <div style="background: #e8e8e8; border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: {bar_color}; width: {min(sc_pct, 100)}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                    <span style="font-size: 10px; color: #888;">({sc_menciones} menciones)</span>
                </div>'''
            
            subcausas_html += '</div>'
        else:
            if n_comentarios == 0:
                subcausas_html = f'''
                <div style="margin-bottom: 15px; padding: 12px 15px; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #ddd;">
                    <span style="font-size: 12px; color: #666; font-style: italic;">
                        📊 Sin comentarios suficientes para análisis detallado.
                    </span>
                </div>'''
            else:
                subcausas_html = f'''
                <div style="margin-bottom: 15px; padding: 12px 15px; background: #fff8e6; border-radius: 8px; border-left: 3px solid #f59e0b;">
                    <span style="font-size: 12px; color: #92400e;">
                        🔍 {n_comentarios} comentarios disponibles en esta categoría
                    </span>
                </div>'''
    
    # Métricas Q1 vs Q2
    metricas_html = ""
    if pct_q1 > 0 or pct_q2 > 0:
        delta_emoji = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
        metricas_html = f'''
        <div style="padding: 12px 0; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; border-bottom: 1px dashed #ddd; margin-bottom: 12px;">
            <span style="font-size: 12px; color: #555;">📊 {q_ant}: <strong>{pct_q1:.0f}%</strong></span>
            <span style="font-size: 12px; color: #555;">→ {q_act}: <strong>{pct_q2:.0f}%</strong></span>
            <span style="font-size: 12px; color: {color_tag_text}; font-weight: 600;">
                {delta_emoji} {delta:+.0f}pp
            </span>
        </div>'''
    
    return f'''
    <details style="margin-bottom: 12px; background: {color_bg}; border-radius: 10px; border-left: 5px solid {color_borde}; overflow: hidden;">
        <summary style="padding: 14px 18px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; list-style: none;">
            <span style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 14px;">▸</span>
                <strong style="font-size: 13px; color: #1f2937;">{motivo}</strong>
            </span>
            <span style="background: {color_tag}; color: {color_tag_text}; padding: 5px 14px; border-radius: 15px; font-size: 13px; font-weight: 700;">
                {delta:+.0f}pp
            </span>
        </summary>
        <div style="padding: 0 18px 18px 18px; border-top: 1px solid {color_tag};">
            {metricas_html}
            {subcausas_html}
        </div>
    </details>
    '''


def _generar_waterfall_html(causas_waterfall, TXT, q_ant='Q1', q_act='Q2', causas_semanticas=None):
    """
    Genera HTML del waterfall con ACORDEONES ENRIQUECIDOS.
    Si hay causas semánticas disponibles, las usa en vez de subcausas por keywords.
    """
    if causas_semanticas is None:
        causas_semanticas = {}
    
    if not causas_waterfall:
        return ''
    
    mejoras = [c for c in causas_waterfall if c.get('delta', 0) < 0]
    deterioros = [c for c in causas_waterfall if c.get('delta', 0) > 0]
    
    html = f"""
    <div class="seccion-soporte" style="background: white; padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 25px;">
        <div class="seccion-titulo-soporte" style="font-weight: 700; font-size: 16px; margin-bottom: 20px; border-bottom: 2px solid #009ee3; padding-bottom: 10px;">
            📉 Impacto por Motivo de Queja (Waterfall)
        </div>
        <p style="color: #888; font-size: 12px; margin-bottom: 15px;">👆 Click en cada motivo para ver causas raíz</p>
    """
    
    if mejoras:
        html += f'<div style="margin-bottom: 20px;"><strong style="color: #00c853;">✅ {TXT["mejoras"]}</strong></div>'
        for c in sorted(mejoras, key=lambda x: x.get('delta', 0))[:5]:
            html += _generar_acordeon_waterfall(c, es_mejora=True, q_ant=q_ant, q_act=q_act, causas_semanticas=causas_semanticas)
    
    if deterioros:
        html += f'<div style="margin: 25px 0 20px 0;"><strong style="color: #ff5252;">⚠️ {TXT["deterioros"]}</strong></div>'
        for c in sorted(deterioros, key=lambda x: x.get('delta', 0), reverse=True)[:5]:
            html += _generar_acordeon_waterfall(c, es_mejora=False, q_ant=q_ant, q_act=q_act, causas_semanticas=causas_semanticas)
    
    total_wf = sum(c.get('delta', 0) for c in causas_waterfall)
    color_total = "#16a34a" if total_wf < 0 else "#dc2626"
    
    html += f"""
        <div style="background: #f0f7ff; padding: 15px 20px; border-radius: 8px; margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
            <strong>TOTAL WATERFALL</strong>
            <span style="font-size: 18px; font-weight: 700; color: {color_total};">{total_wf:+.0f}pp</span>
        </div>
    </div>
    """
    
    return html


def _generar_acordeon_promotor(motivo_data, q_ant, q_act, comentarios_promotores=None):
    """
    Genera un acordeón para un motivo de promotor.
    EXACTAMENTE como en el notebook original.
    """
    motivo = motivo_data.get('motivo', 'Sin motivo')
    pct_q1 = motivo_data.get('pct_q1', 0)
    pct_q2 = motivo_data.get('pct_q2', 0)
    delta = motivo_data.get('delta', 0)
    
    # Colores según delta (verde = mejora en satisfacción)
    es_mejora = delta > 0
    color_bg = "#e8f5e9" if es_mejora else "#fff3e0" if delta < 0 else "#f5f5f5"
    color_tag = "#c8e6c9" if es_mejora else "#ffe0b2" if delta < 0 else "#e0e0e0"
    color_tag_text = "#2e7d32" if es_mejora else "#e65100" if delta < 0 else "#616161"
    color_borde = "#10b981" if es_mejora else "#f59e0b" if delta < 0 else "#9e9e9e"
    
    # Métricas Q1 vs Q2
    delta_emoji = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
    
    # Obtener comentarios del motivo desde comentarios_promotores
    ejemplos = motivo_data.get('ejemplos_comentarios', motivo_data.get('comentarios', []))
    if not ejemplos and comentarios_promotores:
        # Buscar comentarios para este motivo
        for key in comentarios_promotores:
            if motivo.lower() in key.lower() or key.lower() in motivo.lower():
                comms = comentarios_promotores[key]
                if isinstance(comms, dict):
                    ejemplos = comms.get('q2', comms.get('comentarios', []))
                elif isinstance(comms, list):
                    ejemplos = comms
                break
    
    # Subcausas (si existen)
    subcausas = motivo_data.get('subcausas', [])
    subcausas_html = ""
    if subcausas:
        subcausas_html = '<div style="margin-bottom: 15px;"><strong style="font-size: 12px; color: #065f46;">🎯 ¿Por qué lo valoran?</strong>'
        subcausas_html += '<div style="margin-top: 10px;">'
        for sc in subcausas[:4]:
            sc_nombre = str(sc.get('subcausa', sc.get('nombre', '')))[:70]
            sc_pct = sc.get('pct_q2', sc.get('porcentaje', 0)) or 0
            subcausas_html += f'''
            <div style="margin-bottom: 10px; padding: 10px 14px; background: white; border-radius: 8px; border-left: 4px solid {color_borde};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #333;">{sc_nombre}</span>
                    <span style="font-size: 11px; font-weight: 600; color: {color_tag_text}; background: {color_tag}; padding: 2px 8px; border-radius: 10px;">{sc_pct:.0f}%</span>
                </div>
            </div>'''
        subcausas_html += '</div></div>'
    
    # Comentarios de ejemplo
    comentarios_html = ""
    if ejemplos:
        comentarios_html = '<div style="margin-bottom: 15px;"><strong style="font-size: 12px; color: #065f46;">💬 Lo que dicen los promotores:</strong>'
        comentarios_html += '<div style="margin-top: 8px;">'
        sample = ejemplos[:3]
        for ej in sample:
            if ej and len(str(ej)) > 5:
                ej_str = str(ej)
                ej_texto = html_module.escape(ej_str[:150])
                ellipsis = "..." if len(ej_str) > 150 else ""
                comentarios_html += f'''
                <div style="padding: 8px 12px; background: white; border-radius: 8px; margin-bottom: 6px; font-size: 11px; color: #555; font-style: italic; border-left: 3px solid #10b981;">
                    "{ej_texto}{ellipsis}"
                </div>'''
        comentarios_html += '</div></div>'
    
    # Keywords
    keywords = motivo_data.get('keywords', [])
    keywords_html = ""
    if keywords:
        keywords_html = '<div><strong style="font-size: 12px; color: #065f46;">🔑 Keywords:</strong>'
        keywords_html += '<div style="margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px;">'
        kw_list = list(keywords.keys())[:6] if isinstance(keywords, dict) else keywords[:6]
        for kw in kw_list:
            keywords_html += f'<span style="background: #d1fae5; color: #065f46; padding: 3px 10px; border-radius: 12px; font-size: 10px;">{kw}</span>'
        keywords_html += '</div></div>'
    
    return f'''
    <details style="margin-bottom: 12px; background: {color_bg}; border-radius: 10px; border-left: 5px solid {color_borde}; overflow: hidden;">
        <summary style="padding: 14px 18px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; list-style: none;">
            <span style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 14px;">▸</span>
                <strong style="font-size: 13px; color: #1f2937;">{motivo}</strong>
            </span>
            <span style="background: {color_tag}; color: {color_tag_text}; padding: 5px 14px; border-radius: 15px; font-size: 13px; font-weight: 700;">
                {pct_q2:.0f}%
            </span>
        </summary>
        <div style="padding: 0 18px 18px 18px; border-top: 1px solid {color_tag};">
            <div style="padding: 12px 0; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; border-bottom: 1px dashed #ddd; margin-bottom: 12px;">
                <span style="font-size: 12px; color: #555;">📊 {q_ant}: <strong>{pct_q1:.0f}%</strong></span>
                <span style="font-size: 12px; color: #555;">→ {q_act}: <strong>{pct_q2:.0f}%</strong></span>
                <span style="font-size: 12px; color: {color_tag_text}; font-weight: 600;">
                    {delta_emoji} {delta:+.0f}pp
                </span>
            </div>
            {subcausas_html}
            {comentarios_html}
            {keywords_html}
        </div>
    </details>
    '''


def _generar_promotores_resumen(resultados, TXT, q_ant, q_act):
    """
    Genera resumen de promotores CON ACORDEONES DETALLADOS.
    EXACTAMENTE como en el notebook original.
    """
    prom_data = resultados.get('promotores', {})
    
    # Datos de porcentaje de promotores
    pct_prom_q1 = prom_data.get('pct_prom_q1', prom_data.get('pct_promotores_q1', 0))
    pct_prom_q2 = prom_data.get('pct_prom_q2', prom_data.get('pct_promotores_q2', 0))
    delta_prom = prom_data.get('delta_prom', prom_data.get('delta_promotores', pct_prom_q2 - pct_prom_q1))
    
    # Lista de motivos de satisfacción
    motivos_lista = prom_data.get('promotores_data', [])
    
    # Comentarios de promotores
    comentarios_promotores = prom_data.get('comentarios_promotores', {})
    
    delta_color = '#10b981' if delta_prom > 0 else '#ef4444' if delta_prom < 0 else '#6b7280'
    delta_bg = '#d1fae5' if delta_prom > 0 else '#fee2e2' if delta_prom < 0 else '#f3f4f6'
    
    html = f"""
    <div class="seccion-soporte" style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 25px; border-radius: 12px; margin-top: 25px;">
        <div class="seccion-titulo-soporte" style="font-weight: 700; font-size: 16px; margin-bottom: 20px; border-bottom: 2px solid #10b981; padding-bottom: 10px;">
            🌟 {TXT['porque_recomiendan']}
        </div>
        <p style="color: #888; font-size: 12px; margin-bottom: 15px;">👆 Click en cada motivo para ver detalles</p>
        
        <div style="display: flex; align-items: flex-start; gap: 30px; flex-wrap: wrap;">
            <div style="background: white; padding: 20px 30px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); min-width: 150px;">
                <div style="font-size: 11px; color: #666; text-transform: uppercase;">Promotores</div>
                <div style="font-size: 28px; font-weight: 700; color: #10b981;">{pct_prom_q2:.0f}%</div>
                <div style="font-size: 12px; color: {delta_color}; font-weight: 600; background: {delta_bg}; padding: 3px 10px; border-radius: 12px; margin-top: 5px;">
                    {delta_prom:+.0f}pp vs {q_ant}
                </div>
            </div>
            
            <div style="flex: 1; min-width: 400px;">
    """
    
    # Generar acordeones si hay motivos
    if motivos_lista:
        # Separar en mejoras y deterioros
        mejoras_prom = [m for m in motivos_lista if m.get('delta', 0) > UMBRAL_PRODUCTO_RELEVANTE]
        deterioros_prom = [m for m in motivos_lista if m.get('delta', 0) < -UMBRAL_PRODUCTO_RELEVANTE]
        estables_prom = [m for m in motivos_lista if -UMBRAL_PRODUCTO_RELEVANTE <= m.get('delta', 0) <= UMBRAL_PRODUCTO_RELEVANTE]
        
        # Mostrar mejoras primero
        if mejoras_prom:
            html += '<div style="margin-bottom: 15px;"><strong style="color: #10b981;">📈 Creciendo</strong></div>'
            for m in sorted(mejoras_prom, key=lambda x: x.get('delta', 0), reverse=True)[:3]:
                html += _generar_acordeon_promotor(m, q_ant, q_act, comentarios_promotores)
        
        # Mostrar deterioros
        if deterioros_prom:
            html += '<div style="margin: 20px 0 15px 0;"><strong style="color: #f59e0b;">📉 Perdiendo peso</strong></div>'
            for m in sorted(deterioros_prom, key=lambda x: x.get('delta', 0))[:3]:
                html += _generar_acordeon_promotor(m, q_ant, q_act, comentarios_promotores)
        
        # Si no hay mejoras ni deterioros, mostrar top 5 estables
        if not mejoras_prom and not deterioros_prom:
            html += '<div style="margin-bottom: 15px;"><strong style="color: #10b981;">🌟 Top Motivos</strong></div>'
            for m in sorted(estables_prom, key=lambda x: x.get('pct_q2', 0), reverse=True)[:5]:
                html += _generar_acordeon_promotor(m, q_ant, q_act, comentarios_promotores)
    else:
        html += '<p style="color: #888; font-style: italic;">Sin datos de motivos de satisfacción</p>'
    
    html += f"""
            </div>
        </div>
        <div style="text-align: right; margin-top: 15px;">
            <a href="#" onclick="document.querySelectorAll('.tab-btn')[5].click(); return false;" style="font-size: 12px; color: #10b981; text-decoration: none; font-weight: 600;">
                Ver análisis completo →
            </a>
        </div>
    </div>
    """
    
    return html


def _generar_triangulacion_metricas(resultados, noticias, q_ant, q_act):
    """
    Genera la triangulación de métricas de Seguridad y Principalidad con noticias.
    
    Ejemplo de triangulación:
    - Noticia de seguridad → Quejas de Seguridad (waterfall) + Valoración Seguridad
    - Noticia de TC/crédito → Motivo Principalidad "Tarjeta de crédito" + Queja "Financiamiento"
    """
    html = ""
    
    # Obtener datos de seguridad
    seg_data = resultados.get('seguridad', {})
    ps = seg_data.get('player_seguridad', {})
    seg_q1 = ps.get('seg_q1', 0)
    seg_q2 = ps.get('seg_q2', 0)
    delta_seg = ps.get('delta', 0)
    
    # Obtener datos de principalidad
    princ_data = resultados.get('principalidad', {})
    pp = princ_data.get('player_principalidad', {})
    princ_q1 = pp.get('princ_q1', 0)
    princ_q2 = pp.get('princ_q2', 0)
    delta_princ = pp.get('delta', 0)
    
    # Obtener quejas del waterfall relacionadas
    wf_data = resultados.get('waterfall', {})
    causas = wf_data.get('causas', [])
    
    # Buscar queja de seguridad y financiamiento
    queja_seg = None
    queja_financ = None
    for c in causas:
        nombre = c.get('nombre', '').lower()
        if 'segur' in nombre and not queja_seg:
            queja_seg = c
        if 'financ' in nombre or 'credito' in nombre or 'crédito' in nombre:
            if not queja_financ:
                queja_financ = c
    
    delta_queja_seg = queja_seg.get('delta', 0) if queja_seg else 0
    delta_queja_financ = queja_financ.get('delta', 0) if queja_financ else 0
    
    # Buscar noticias relacionadas a seguridad y principalidad/TC
    noticia_seg = None
    noticia_princ = None
    keywords_seg = ['segur', 'fraude', 'robo', 'hack', 'protec', 'verifica']
    keywords_princ = ['tarjeta', 'credito', 'crédito', 'tc', 'cartao', 'cartão', 'card', 'principal', 'banco principal']
    
    for n in noticias:
        titulo_lower = n.get('titulo', '').lower()
        cat_lower = n.get('categoria_relacionada', '').lower()
        
        # Buscar noticia de seguridad
        if not noticia_seg:
            if any(kw in titulo_lower or kw in cat_lower for kw in keywords_seg):
                noticia_seg = n
        
        # Buscar noticia de principalidad/TC
        if not noticia_princ:
            if any(kw in titulo_lower or kw in cat_lower for kw in keywords_princ):
                noticia_princ = n
    
    # Solo mostrar si hay algo relevante
    if delta_seg != 0 or delta_princ != 0:
        html += """
        <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #16a34a;">
            <div style="font-weight: 700; color: #166534; margin-bottom: 15px; font-size: 15px;">
                📊 Triangulación: Métricas de Percepción ↔ Quejas ↔ Noticias
            </div>
            <div style="font-size: 12px; color: #15803d; margin-bottom: 15px;">
                Conexión entre métricas de percepción (Seguridad, Principalidad), quejas del waterfall y noticias del mercado.
            </div>
        """
        
        # ══════════════════════════════════════════════════════════════════════
        # SEGURIDAD: Valoración ↔ Quejas ↔ Noticia
        # ══════════════════════════════════════════════════════════════════════
        if delta_seg != 0 or delta_queja_seg != 0:
            # Determinar coherencia
            if delta_queja_seg != 0 and delta_seg != 0:
                # Quejas bajan + Valoración sube = coherente
                if (delta_queja_seg < 0 and delta_seg > 0) or (delta_queja_seg > 0 and delta_seg < 0):
                    coherencia = "coherente"
                    coherencia_color = "#10b981"
                    coherencia_icon = "✓"
                else:
                    coherencia = "observar"
                    coherencia_color = "#f59e0b"
                    coherencia_icon = "⚠"
            else:
                coherencia = "neutro"
                coherencia_color = "#6b7280"
                coherencia_icon = "—"
            
            html += f"""
            <div style="background: white; border: 1px solid {coherencia_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🔒</span>
                    <span style="font-weight: 700; color: #1e293b; font-size: 14px;">SEGURIDAD</span>
                    <span style="background: {coherencia_color}15; color: {coherencia_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{coherencia_icon} {coherencia.upper()}</span>
                </div>
                
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <!-- Valoración Seguridad -->
                    <div style="background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 120px; text-align: center;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Valoración</span>
                        <span style="font-weight: 700; color: {'#10b981' if delta_seg > 0 else '#ef4444' if delta_seg < 0 else '#6b7280'}; font-size: 16px;">{delta_seg:+.0f}pp</span>
                        <span style="font-size: 10px; color: #64748b; display: block;">{seg_q1:.0f}% → {seg_q2:.0f}%</span>
                    </div>
                    
                    <span style="font-size: 18px; color: #94a3b8;">↔</span>
                    
                    <!-- Quejas Seguridad (Waterfall) -->
                    <div style="background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 120px; text-align: center;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Quejas NPS</span>
                        <span style="font-weight: 700; color: {'#10b981' if delta_queja_seg < 0 else '#ef4444' if delta_queja_seg > 0 else '#6b7280'}; font-size: 16px;">{delta_queja_seg:+.0f}pp</span>
                        <span style="font-size: 10px; color: #64748b; display: block;">{"↓ Menos quejas" if delta_queja_seg < 0 else "↑ Más quejas" if delta_queja_seg > 0 else "Sin cambio"}</span>
                    </div>
            """
            
            if noticia_seg:
                noticia_titulo = noticia_seg.get('titulo', '')[:60] + '...' if len(noticia_seg.get('titulo', '')) > 60 else noticia_seg.get('titulo', '')
                noticia_url = noticia_seg.get('url', '#')
                impacto = noticia_seg.get('impacto_esperado', 'neutro')
                impacto_emoji = '📈' if impacto == 'positivo' else ('📉' if impacto == 'negativo' else '➡️')
                
                html += f"""
                    <span style="font-size: 18px; color: #94a3b8;">↔</span>
                    
                    <!-- Noticia Relacionada -->
                    <div style="background: #eff6ff; padding: 10px 14px; border-radius: 8px; border: 1px solid #bfdbfe; flex: 1; min-width: 200px;">
                        <span style="font-size: 10px; color: #1e40af; display: block;">📰 NOTICIA {impacto_emoji}</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #1d4ed8; text-decoration: none; font-size: 12px; line-height: 1.3;">{noticia_titulo}</a>
                    </div>
                """
            else:
                html += """
                    <div style="background: #f9fafb; padding: 10px 14px; border-radius: 8px; border: 1px dashed #d1d5db; flex: 1; min-width: 200px; text-align: center;">
                        <span style="font-size: 11px; color: #9ca3af;">Sin noticia relacionada a seguridad</span>
                    </div>
                """
            
            html += """
                </div>
            </div>
            """
        
        # ══════════════════════════════════════════════════════════════════════
        # PRINCIPALIDAD: % Principal ↔ Quejas Financiamiento ↔ Noticia TC
        # ══════════════════════════════════════════════════════════════════════
        if delta_princ != 0:
            # Obtener top motivo de principalidad
            motivos_princ = princ_data.get('motivos_principalidad', None)
            top_motivo = "N/A"
            try:
                import pandas as pd
                if motivos_princ is not None:
                    if isinstance(motivos_princ, pd.DataFrame) and not motivos_princ.empty:
                        col_motivo = None
                        for col in motivos_princ.columns:
                            if 'motivo' in col.lower():
                                col_motivo = col
                                break
                        if col_motivo:
                            top_motivo = str(motivos_princ.iloc[0][col_motivo])[:25]
            except:
                pass
            
            # Color según delta
            if delta_princ > 1:
                princ_color = "#10b981"
                princ_estado = "GANANDO"
            elif delta_princ < -1:
                princ_color = "#ef4444"
                princ_estado = "OBSERVAR"
            else:
                princ_color = "#6b7280"
                princ_estado = "ESTABLE"
            
            html += f"""
            <div style="background: white; border: 1px solid {princ_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🏠</span>
                    <span style="font-weight: 700; color: #1e293b; font-size: 14px;">PRINCIPALIDAD</span>
                    <span style="background: {princ_color}15; color: {princ_color}; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;">{princ_estado}</span>
                </div>
                
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <!-- % Principalidad -->
                    <div style="background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 120px; text-align: center;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">% Principal</span>
                        <span style="font-weight: 700; color: {princ_color}; font-size: 16px;">{delta_princ:+.0f}pp</span>
                        <span style="font-size: 10px; color: #64748b; display: block;">{princ_q1:.0f}% → {princ_q2:.0f}%</span>
                    </div>
                    
                    <span style="font-size: 18px; color: #94a3b8;">↔</span>
                    
                    <!-- Top Motivo -->
                    <div style="background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 140px; text-align: center;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Top Motivo</span>
                        <span style="font-weight: 600; color: #1e293b; font-size: 12px;">{top_motivo}</span>
                    </div>
            """
            
            # Agregar queja de financiamiento si existe
            if queja_financ and abs(delta_queja_financ) > 0.1:
                html += f"""
                    <span style="font-size: 18px; color: #94a3b8;">↔</span>
                    
                    <!-- Quejas Financiamiento -->
                    <div style="background: #f8fafc; padding: 10px 14px; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 120px; text-align: center;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Quejas Financ.</span>
                        <span style="font-weight: 700; color: {'#10b981' if delta_queja_financ < 0 else '#ef4444' if delta_queja_financ > 0 else '#6b7280'}; font-size: 16px;">{delta_queja_financ:+.0f}pp</span>
                    </div>
                """
            
            if noticia_princ:
                noticia_titulo = noticia_princ.get('titulo', '')[:60] + '...' if len(noticia_princ.get('titulo', '')) > 60 else noticia_princ.get('titulo', '')
                noticia_url = noticia_princ.get('url', '#')
                impacto = noticia_princ.get('impacto_esperado', 'neutro')
                impacto_emoji = '📈' if impacto == 'positivo' else ('📉' if impacto == 'negativo' else '➡️')
                
                html += f"""
                    <span style="font-size: 18px; color: #94a3b8;">↔</span>
                    
                    <!-- Noticia Relacionada -->
                    <div style="background: #eff6ff; padding: 10px 14px; border-radius: 8px; border: 1px solid #bfdbfe; flex: 1; min-width: 200px;">
                        <span style="font-size: 10px; color: #1e40af; display: block;">📰 NOTICIA {impacto_emoji}</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #1d4ed8; text-decoration: none; font-size: 12px; line-height: 1.3;">{noticia_titulo}</a>
                    </div>
                """
            else:
                html += """
                    <div style="background: #f9fafb; padding: 10px 14px; border-radius: 8px; border: 1px dashed #d1d5db; flex: 1; min-width: 200px; text-align: center;">
                        <span style="font-size: 11px; color: #9ca3af;">Sin noticia relacionada a TC/crédito</span>
                    </div>
                """
            
            html += """
                </div>
            </div>
            """
        
        html += "</div>"
    
    return html


def _generar_seccion_noticias(resultados, TXT, q_ant, q_act):
    """
    Genera la sección de Noticias / Contexto del Mercado con TRIANGULACIÓN.
    Muestra noticias REALES obtenidas de búsquedas web y su relación con NPS.
    
    ⚠️ IMPORTANTE: Las noticias son 100% REALES, nunca inventadas.
    
    TRIANGULACIÓN: Producto ↔ Queja ↔ Noticia
    """
    deep_research = resultados.get('deep_research', {})
    noticias = resultados.get('noticias', [])  # Noticias reales del cache
    triangulaciones = resultados.get('triangulaciones', [])  # Triangulaciones Producto-Queja-Noticia
    
    # Datos del deep research
    queries = deep_research.get('queries', [])
    cambios_quejas = deep_research.get('cambios_quejas', [])
    cambios_productos = deep_research.get('cambios_productos', [])
    rango_fechas = deep_research.get('rango_fechas', q_act)
    dominios = deep_research.get('dominios_confiables', [])
    
    html = f"""
    <div class="content-main" style="padding-top: 0; border-top: 1px solid #e8ecf0; margin-top: 30px;">
        <div class="seccion-titulo-simple">
            <span class="icono">📰</span> {TXT.get('contexto_mercado', 'Contexto del Mercado')} &amp; Triangulación
        </div>
    """
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE TRIANGULACIÓN MOTIVO ↔ NOTICIA (PRINCIPAL)
    # ═══════════════════════════════════════════════════════════════════════════
    
    triangulacion_motivos = resultados.get('triangulacion_motivos', [])
    
    if triangulacion_motivos:
        html += """
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #2563eb;">
            <div style="font-weight: 700; color: #1e40af; margin-bottom: 15px; font-size: 15px;">
                📰 Triangulación: Motivo de Variación ↔ Noticia
            </div>
            <div style="font-size: 12px; color: #1e3a8a; margin-bottom: 15px;">
                Conexión directa entre los cambios en quejas del NPS y noticias del mercado que podrían explicarlos.
            </div>
        """
        
        for tri in triangulacion_motivos[:5]:
            motivo = tri.get('motivo', 'N/A')
            delta = tri.get('delta', 0)
            coherencia = tri.get('coherencia', 'neutro')
            explicacion = tri.get('explicacion', '')
            noticia = tri.get('noticia', {})
            
            # Colores según coherencia
            if coherencia == 'coherente':
                border_color = '#10b981'
                bg_color = '#ecfdf5'
                icon = '✓'
            elif coherencia == 'incoherente':
                border_color = '#f59e0b'
                bg_color = '#fffbeb'
                icon = '?'
            else:
                border_color = '#6b7280'
                bg_color = '#f9fafb'
                icon = '—'
            
            noticia_titulo = noticia.get('titulo', '')[:70] + '...' if len(noticia.get('titulo', '')) > 70 else noticia.get('titulo', '')
            noticia_url = noticia.get('url', '#')
            noticia_impacto = noticia.get('impacto_esperado', 'neutro')
            
            # Emoji según impacto de la noticia
            impacto_emoji = '📈' if noticia_impacto == 'positivo' else ('📉' if noticia_impacto == 'negativo' else '➡️')
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <!-- Motivo del Waterfall -->
                    <div style="background: white; padding: 10px 16px; border-radius: 8px; border: 1px solid #e8ecf0; min-width: 140px;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Motivo NPS</span>
                        <span style="font-weight: 700; color: #1e293b; font-size: 14px;">{motivo}</span>
                        <span style="color: {'#ef4444' if delta > 0 else '#10b981'}; font-size: 13px; font-weight: 600; margin-left: 8px;">{delta:+.0f}pp</span>
                    </div>
                    
                    <span style="font-size: 24px; color: {border_color};">↔</span>
                    
                    <!-- Noticia Relacionada -->
                    <div style="background: white; padding: 10px 16px; border-radius: 8px; border: 1px solid #e8ecf0; flex: 1; min-width: 250px;">
                        <span style="font-size: 10px; color: #64748b; display: block;">NOTICIA {impacto_emoji} {noticia_impacto.upper()}</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #0369a1; text-decoration: none; font-size: 13px; line-height: 1.4;">{noticia_titulo}</a>
                    </div>
                    
                    <!-- Coherencia -->
                    <div style="background: {border_color}15; padding: 8px 14px; border-radius: 20px; border: 1px solid {border_color}40; text-align: center;">
                        <span style="font-weight: 700; color: {border_color}; font-size: 12px; display: block;">{icon} {coherencia.upper()}</span>
                        <span style="font-size: 10px; color: {border_color}90; display: block; margin-top: 2px;">{explicacion[:40]}...</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE TRIANGULACIÓN MÉTRICAS: Seguridad & Principalidad ↔ Noticias
    # ═══════════════════════════════════════════════════════════════════════════
    
    html += _generar_triangulacion_metricas(resultados, noticias, q_ant, q_act)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE TRIANGULACIÓN (Producto ↔ Queja ↔ Noticia) - SECUNDARIA
    # ═══════════════════════════════════════════════════════════════════════════
    
    triangulaciones_con_noticia = [t for t in triangulaciones if t.get('noticia')]
    
    if triangulaciones_con_noticia and not triangulacion_motivos:
        html += """
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #f59e0b;">
            <div style="font-weight: 700; color: #92400e; margin-bottom: 15px; font-size: 15px;">
                🔗 Triangulación: Producto ↔ Queja ↔ Noticia
            </div>
            <div style="font-size: 12px; color: #78350f; margin-bottom: 15px;">
                Conexiones detectadas entre cambios en productos, quejas de usuarios y noticias del mercado.
            </div>
        """
        
        for tri in triangulaciones_con_noticia[:4]:
            producto = tri.get('producto', 'N/A')
            efecto = tri.get('efecto_nps', 0)
            queja = tri.get('queja_relacionada', '')
            delta_queja = tri.get('delta_queja', 0)
            coherencia = tri.get('coherencia', 'neutro')
            noticia = tri.get('noticia', {})
            
            # Colores según coherencia
            if coherencia == 'coherente':
                border_color = '#10b981'
                bg_color = '#ecfdf5'
                icon = '✓'
            elif coherencia == 'incoherente':
                border_color = '#ef4444'
                bg_color = '#fef2f2'
                icon = '!'
            else:
                border_color = '#6b7280'
                bg_color = '#f9fafb'
                icon = '—'
            
            noticia_titulo = noticia.get('titulo', 'Sin noticia')[:60] + '...' if len(noticia.get('titulo', '')) > 60 else noticia.get('titulo', 'Sin noticia')
            noticia_url = noticia.get('url', '#')
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <!-- Producto -->
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0;">
                        <span style="font-size: 10px; color: #64748b; display: block;">PRODUCTO</span>
                        <span style="font-weight: 600; color: #1e293b;">{producto}</span>
                        <span style="color: {'#10b981' if efecto > 0 else '#ef4444'}; font-size: 12px; margin-left: 5px;">{efecto:+.0f}pp</span>
                    </div>
                    
                    <span style="font-size: 18px; color: {border_color};">↔</span>
                    
                    <!-- Queja -->
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0;">
                        <span style="font-size: 10px; color: #64748b; display: block;">QUEJA</span>
                        <span style="font-weight: 600; color: #1e293b;">{queja if queja else 'N/A'}</span>
                        <span style="color: {'#ef4444' if delta_queja > 0 else '#10b981'}; font-size: 12px; margin-left: 5px;">{delta_queja:+.0f}pp</span>
                    </div>
                    
                    <span style="font-size: 18px; color: {border_color};">↔</span>
                    
                    <!-- Noticia -->
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0; flex: 1; min-width: 200px;">
                        <span style="font-size: 10px; color: #64748b; display: block;">NOTICIA</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #0369a1; text-decoration: none; font-size: 12px;">{noticia_titulo}</a>
                    </div>
                    
                    <!-- Coherencia -->
                    <div style="background: {border_color}20; padding: 6px 12px; border-radius: 20px; border: 1px solid {border_color};">
                        <span style="font-weight: 600; color: {border_color}; font-size: 11px;">{icon} {coherencia.upper()}</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SECCIÓN DE NOTICIAS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Si hay noticias ya encontradas, mostrarlas con detalle
    if noticias:
        # Header con estadísticas
        noticias_con_correlacion = len([n for n in noticias if n.get('tiene_correlacion', False) or n.get('queja_relacionada')])
        html += f"""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; border-left: 4px solid #009ee3;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 600; color: #0369a1;">📊 {len(noticias)} noticias relevantes</span>
                    <span style="font-size: 12px; color: #64748b; margin-left: 10px;">Período: {rango_fechas}</span>
                </div>
                <div style="font-size: 11px; color: #64748b;">
                    🔗 {noticias_con_correlacion} relacionadas con cambios NPS
                </div>
            </div>
        </div>
        """
        
        html += '<div class="noticias-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">'
        for n in noticias[:6]:
            categoria = n.get('categoria_relacionada', n.get('categoria', '📰 Noticia'))
            titulo = n.get('titulo', 'Sin título')
            titulo_display = titulo[:80] + '...' if len(titulo) > 80 else titulo
            url = n.get('url', n.get('link', '#'))
            fuente = n.get('fuente', '')
            fecha = n.get('fecha', '')
            resumen = n.get('resumen', '')[:120] + '...' if len(n.get('resumen', '')) > 120 else n.get('resumen', '')
            impacto = n.get('impacto_esperado', 'neutro')
            queja_rel = n.get('queja_relacionada', '')
            delta_queja = n.get('delta_queja', 0)
            
            # Colores según impacto
            if impacto == 'positivo':
                impacto_color = '#10b981'
                impacto_bg = '#ecfdf5'
                impacto_icon = '📈'
            elif impacto == 'negativo':
                impacto_color = '#ef4444'
                impacto_bg = '#fef2f2'
                impacto_icon = '📉'
            else:
                impacto_color = '#6b7280'
                impacto_bg = '#f9fafb'
                impacto_icon = '➡️'
            
            # Badge de correlación si hay
            correlacion_badge = ''
            if queja_rel:
                delta_color = '#ef4444' if delta_queja > 0 else '#10b981'
                correlacion_badge = f"""
                <div style="background: {delta_color}15; border: 1px solid {delta_color}40; color: {delta_color}; padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; margin-top: 8px;">
                    🔗 Relacionado: {queja_rel} ({delta_queja:+.0f}pp)
                </div>
                """
            
            html += f"""
            <div class="noticia-card" style="background: white; border: 1px solid #e8ecf0; border-radius: 12px; padding: 18px; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <span style="font-size: 10px; color: #009ee3; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">{categoria}</span>
                    <span style="background: {impacto_bg}; color: {impacto_color}; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 500;">{impacto_icon} {impacto.capitalize()}</span>
                </div>
                <div style="font-size: 13px; color: #1f2937; margin-bottom: 8px; font-weight: 600; line-height: 1.4;">{titulo_display}</div>
                <div style="font-size: 11px; color: #64748b; line-height: 1.5; margin-bottom: 10px;">{resumen}</div>
                {correlacion_badge}
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9;">
                    <span style="font-size: 10px; color: #888;">📅 {fecha} • {fuente}</span>
                    <a href="{url}" target="_blank" style="font-size: 11px; color: #009ee3; text-decoration: none; font-weight: 600;">Ver noticia →</a>
                </div>
            </div>
            """
        html += '</div>'
    
    # Si no hay noticias pero hay queries, mostrar resumen de búsqueda sugerida
    elif queries or cambios_quejas:
        html += f"""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 20px; border-radius: 12px; border-left: 4px solid #009ee3;">
            <div style="font-weight: 600; color: #0369a1; margin-bottom: 15px;">
                🔍 Deep Research - Período: {rango_fechas}
            </div>
        """
        
        # Mostrar cambios que requieren investigación
        if cambios_quejas:
            html += '<div style="margin-bottom: 15px;"><strong style="font-size: 12px; color: #334155;">Cambios a investigar:</strong></div>'
            html += '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">'
            for c in cambios_quejas[:5]:
                emoji = "📈" if c.get('delta', 0) > 0 else "📉"
                color = "#ef4444" if c.get('delta', 0) > 0 else "#10b981"
                html += f"""
                <span style="background: white; padding: 6px 12px; border-radius: 20px; font-size: 11px; border: 1px solid {color};">
                    {emoji} {c.get('categoria', 'N/A')}: <strong style="color: {color};">{c.get('delta', 0):+.0f}pp</strong>
                </span>
                """
            html += '</div>'
        
        # Mostrar queries sugeridas
        if queries:
            html += '<div style="margin-bottom: 15px;"><strong style="font-size: 12px; color: #334155;">Búsquedas sugeridas:</strong></div>'
            html += '<div style="background: white; padding: 12px 15px; border-radius: 8px; font-size: 11px; color: #555;">'
            for i, q in enumerate(queries[:5], 1):
                html += f'<div style="margin-bottom: 5px;">🔎 {q}</div>'
            html += '</div>'
        
        # Dominios confiables
        if dominios:
            html += f"""
            <div style="margin-top: 15px; font-size: 10px; color: #64748b;">
                <strong>Fuentes sugeridas:</strong> {', '.join(dominios[:5])}...
            </div>
            """
        
        html += """
            <div style="margin-top: 15px; padding: 10px; background: #fef3c7; border-radius: 8px; font-size: 11px; color: #92400e;">
                💡 <strong>Tip:</strong> Ejecuta Deep Research (WebSearch) con las queries sugeridas para obtener contexto de mercado.
            </div>
        </div>
        """
    
    # Si no hay datos de deep research
    else:
        html += f"""
        <div style="background: #f8fafc; padding: 40px; text-align: center; border-radius: 12px;">
            <div style="font-size: 48px; margin-bottom: 15px;">📰</div>
            <div style="color: #64748b; font-size: 13px;">
                No se encontraron noticias de mercado para este player/período
            </div>
        </div>
        """
    
    html += "</div>"
    
    # =========================================================================
    # PANEL DE GAPS: Drivers sin cobertura de noticias + sugerencias de busqueda
    # =========================================================================
    sugerencias = resultados.get('sugerencias_busqueda', {})
    gaps = sugerencias.get('gaps_sin_noticia', [])
    busquedas = sugerencias.get('busquedas_sugeridas', [])
    drivers_detectados = sugerencias.get('drivers_detectados', [])
    
    if gaps and drivers_detectados:
        total_drivers = len(drivers_detectados)
        cubiertos = total_drivers - len(gaps)
        pct = int(cubiertos / total_drivers * 100) if total_drivers > 0 else 0
        
        # Color del indicador
        if pct >= 80:
            barra_color = '#10b981'
        elif pct >= 50:
            barra_color = '#f59e0b'
        else:
            barra_color = '#ef4444'
        
        html += f"""
        <div style="background: #fffbeb; border: 1px solid #fbbf24; border-radius: 12px; padding: 18px 22px; margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-weight: 700; font-size: 14px; color: #92400e;">
                    Cobertura de noticias por driver
                </span>
                <span style="font-size: 13px; color: #b45309; font-weight: 600;">
                    {cubiertos} de {total_drivers} drivers con noticias ({pct}%)
                </span>
            </div>
            <div style="background: #fef3c7; border-radius: 6px; height: 8px; overflow: hidden; margin-bottom: 15px;">
                <div style="width: {pct}%; background: {barra_color}; height: 100%; border-radius: 6px;"></div>
            </div>
        """
        
        # Listar gaps
        html += '<div style="margin-bottom: 12px;">'
        html += '<div style="font-size: 12px; font-weight: 600; color: #92400e; margin-bottom: 8px;">Drivers sin cobertura:</div>'
        for gap in gaps[:5]:
            motivo = gap.get('motivo', '')
            delta = gap.get('delta', 0)
            signo = '+' if delta > 0 else ''
            color = '#ef4444' if delta > 0 else '#10b981'
            html += f"""
            <div style="display: inline-block; background: white; padding: 4px 10px; border-radius: 16px; 
                        margin: 3px 4px; font-size: 12px; border: 1px solid #e5e7eb;">
                <strong>{motivo}</strong> <span style="color: {color};">{signo}{delta:.1f}pp</span>
            </div>"""
        html += '</div>'
        
        # Sugerencias de busqueda (copiables)
        if busquedas:
            html += '<div style="font-size: 12px; font-weight: 600; color: #92400e; margin-bottom: 6px;">Busquedas sugeridas:</div>'
            html += '<div style="background: white; padding: 10px 14px; border-radius: 8px; font-family: monospace; font-size: 11px;">'
            for b in busquedas[:5]:
                query_text = b.get('query', '')
                html += f'<div style="margin-bottom: 4px; color: #475569;">{query_text}</div>'
            html += '</div>'
        
        html += '</div>'
    
    return html


def _generar_seccion_triangulacion(resultados, TXT, q_ant, q_act):
    """
    Genera sección unificada de Triangulación con TODAS las triangulaciones:
    1. Producto ↔ Queja ↔ Noticia
    2. Motivo ↔ Noticia
    3. Métricas (Seguridad/Principalidad) ↔ Quejas ↔ Noticias
    """
    noticias = resultados.get('noticias', [])
    triangulaciones = resultados.get('triangulaciones', [])
    triangulacion_motivos = resultados.get('triangulacion_motivos', [])
    
    # Check if there's anything to show
    seg_data = resultados.get('seguridad', {})
    delta_seg = seg_data.get('player_seguridad', {}).get('delta', 0)
    princ_data = resultados.get('principalidad', {})
    delta_princ = princ_data.get('player_principalidad', {}).get('delta', 0)
    
    has_content = triangulaciones or triangulacion_motivos or delta_seg != 0 or delta_princ != 0
    if not has_content:
        return ''
    
    html = f"""
    <div class="content-main" style="padding-top: 0; border-top: 1px solid #e8ecf0; margin-top: 30px;">
        <div class="seccion-titulo-simple">
            <span class="icono">🔗</span> Triangulación
        </div>
        <div style="font-size: 12px; color: #64748b; margin-bottom: 20px; padding: 0 5px;">
            Conexiones detectadas entre productos, quejas, métricas de percepción y noticias del mercado.
        </div>
    """
    
    # ──────────────────────────────────────────────────────────────────────
    # 1. Producto ↔ Queja ↔ Noticia (ALL, not just those with news)
    # ──────────────────────────────────────────────────────────────────────
    if triangulaciones:
        for tri in triangulaciones:
            producto = tri.get('producto', 'N/A')
            efecto = tri.get('efecto_nps', 0)
            queja = tri.get('queja_relacionada', '')
            delta_queja = tri.get('delta_queja', 0)
            coherencia = tri.get('coherencia', 'neutro')
            noticia = tri.get('noticia', {})
            
            if coherencia == 'coherente':
                border_color = '#10b981'
                bg_color = '#ecfdf5'
                icon = '✓'
            elif coherencia == 'incoherente':
                border_color = '#ef4444'
                bg_color = '#fef2f2'
                icon = '!'
            else:
                border_color = '#6b7280'
                bg_color = '#f9fafb'
                icon = '—'
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0;">
                        <span style="font-size: 10px; color: #64748b; display: block;">PRODUCTO</span>
                        <span style="font-weight: 600; color: #1e293b;">{producto}</span>
                        <span style="color: {'#10b981' if efecto > 0 else '#ef4444'}; font-size: 12px; margin-left: 5px;">{efecto:+.0f}pp</span>
                    </div>
                    <span style="font-size: 18px; color: {border_color};">↔</span>
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0;">
                        <span style="font-size: 10px; color: #64748b; display: block;">QUEJA</span>
                        <span style="font-weight: 600; color: #1e293b;">{queja if queja else 'N/A'}</span>
                        <span style="color: {'#ef4444' if delta_queja > 0 else '#10b981'}; font-size: 12px; margin-left: 5px;">{delta_queja:+.0f}pp</span>
                    </div>
            """
            
            if noticia and isinstance(noticia, dict) and noticia.get('titulo'):
                noticia_titulo = noticia.get('titulo', '')[:60] + '...' if len(noticia.get('titulo', '')) > 60 else noticia.get('titulo', '')
                noticia_url = noticia.get('url', '#')
                html += f"""
                    <span style="font-size: 18px; color: {border_color};">↔</span>
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0; flex: 1; min-width: 200px;">
                        <span style="font-size: 10px; color: #64748b; display: block;">NOTICIA</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #0369a1; text-decoration: none; font-size: 12px;">{noticia_titulo}</a>
                    </div>
                """
            
            html += f"""
                    <div style="background: {border_color}20; padding: 6px 12px; border-radius: 20px; border: 1px solid {border_color};">
                        <span style="font-weight: 600; color: {border_color}; font-size: 11px;">{icon} {coherencia.upper()}</span>
                    </div>
                </div>
            </div>
            """
    
    # ──────────────────────────────────────────────────────────────────────
    # 2. Motivo ↔ Noticia (solo motivos NO ya cubiertos en Producto ↔ Queja ↔ Noticia)
    # ──────────────────────────────────────────────────────────────────────
    # Recopilar motivos que ya aparecen triangulados con producto
    motivos_ya_triangulados = set()
    if triangulaciones:
        for tri in triangulaciones:
            queja = (tri.get('queja_relacionada', '') or '').strip().lower()
            if queja:
                motivos_ya_triangulados.add(queja)
    
    if triangulacion_motivos:
        # Filtrar motivos que ya aparecieron arriba en la triangulación con productos
        motivos_filtrados = [
            tri for tri in triangulacion_motivos
            if (tri.get('motivo', '') or '').strip().lower() not in motivos_ya_triangulados
        ]
        for tri in motivos_filtrados:
            motivo = tri.get('motivo', 'N/A')
            delta = tri.get('delta', 0)
            coherencia = tri.get('coherencia', 'neutro')
            noticia = tri.get('noticia', {})
            
            if coherencia == 'coherente':
                border_color = '#10b981'
                bg_color = '#ecfdf5'
                icon = '✓'
            elif coherencia == 'incoherente':
                border_color = '#f59e0b'
                bg_color = '#fffbeb'
                icon = '?'
            else:
                border_color = '#6b7280'
                bg_color = '#f9fafb'
                icon = '—'
            
            noticia_titulo = noticia.get('titulo', '')[:70] + '...' if len(noticia.get('titulo', '')) > 70 else noticia.get('titulo', '')
            noticia_url = noticia.get('url', '#')
            noticia_impacto = noticia.get('impacto_esperado', 'neutro')
            impacto_emoji = '📈' if noticia_impacto == 'positivo' else ('📉' if noticia_impacto == 'negativo' else '➡️')
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="background: white; padding: 10px 16px; border-radius: 8px; border: 1px solid #e8ecf0; min-width: 140px;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Motivo NPS</span>
                        <span style="font-weight: 700; color: #1e293b; font-size: 14px;">{motivo}</span>
                        <span style="color: {'#ef4444' if delta > 0 else '#10b981'}; font-size: 13px; font-weight: 600; margin-left: 8px;">{delta:+.0f}pp</span>
                    </div>
                    <span style="font-size: 24px; color: {border_color};">↔</span>
                    <div style="background: white; padding: 10px 16px; border-radius: 8px; border: 1px solid #e8ecf0; flex: 1; min-width: 250px;">
                        <span style="font-size: 10px; color: #64748b; display: block;">NOTICIA {impacto_emoji} {noticia_impacto.upper()}</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #0369a1; text-decoration: none; font-size: 13px; line-height: 1.4;">{noticia_titulo}</a>
                    </div>
                    <div style="background: {border_color}15; padding: 8px 14px; border-radius: 20px; border: 1px solid {border_color}40; text-align: center;">
                        <span style="font-weight: 700; color: {border_color}; font-size: 12px;">{icon} {coherencia.upper()}</span>
                    </div>
                </div>
            </div>
            """
    
    html += "</div>"
    return html


def _generar_triangulacion_productos(resultados, TXT, q_ant, q_act):
    """
    LEGACY: Genera HTML de triangulación (Motivo↔Noticia + Producto↔Queja↔Noticia + Métricas).
    Kept for backward compatibility. Use _generar_seccion_triangulacion() instead.
    """
    noticias = resultados.get('noticias', [])
    triangulaciones = resultados.get('triangulaciones', [])
    triangulacion_motivos = resultados.get('triangulacion_motivos', [])
    
    html = ''
    
    # Triangulación Motivo ↔ Noticia
    if triangulacion_motivos:
        html += """
        <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #2563eb;">
            <div style="font-weight: 700; color: #1e40af; margin-bottom: 15px; font-size: 15px;">
                📰 Triangulación: Motivo de Variación ↔ Noticia
            </div>
            <div style="font-size: 12px; color: #1e3a8a; margin-bottom: 15px;">
                Conexión directa entre los cambios en quejas del NPS y noticias del mercado que podrían explicarlos.
            </div>
        """
        
        for tri in triangulacion_motivos[:5]:
            motivo = tri.get('motivo', 'N/A')
            delta = tri.get('delta', 0)
            coherencia = tri.get('coherencia', 'neutro')
            explicacion = tri.get('explicacion', '')
            noticia = tri.get('noticia', {})
            
            if coherencia == 'coherente':
                border_color = '#10b981'
                bg_color = '#ecfdf5'
                icon = '✓'
            elif coherencia == 'incoherente':
                border_color = '#f59e0b'
                bg_color = '#fffbeb'
                icon = '?'
            else:
                border_color = '#6b7280'
                bg_color = '#f9fafb'
                icon = '—'
            
            noticia_titulo = noticia.get('titulo', '')[:70] + '...' if len(noticia.get('titulo', '')) > 70 else noticia.get('titulo', '')
            noticia_url = noticia.get('url', '#')
            noticia_impacto = noticia.get('impacto_esperado', 'neutro')
            impacto_emoji = '📈' if noticia_impacto == 'positivo' else ('📉' if noticia_impacto == 'negativo' else '➡️')
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="background: white; padding: 10px 16px; border-radius: 8px; border: 1px solid #e8ecf0; min-width: 140px;">
                        <span style="font-size: 10px; color: #64748b; display: block; text-transform: uppercase;">Motivo NPS</span>
                        <span style="font-weight: 700; color: #1e293b; font-size: 14px;">{motivo}</span>
                        <span style="color: {'#ef4444' if delta > 0 else '#10b981'}; font-size: 13px; font-weight: 600; margin-left: 8px;">{delta:+.0f}pp</span>
                    </div>
                    <span style="font-size: 24px; color: {border_color};">↔</span>
                    <div style="background: white; padding: 10px 16px; border-radius: 8px; border: 1px solid #e8ecf0; flex: 1; min-width: 250px;">
                        <span style="font-size: 10px; color: #64748b; display: block;">NOTICIA {impacto_emoji} {noticia_impacto.upper()}</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #0369a1; text-decoration: none; font-size: 13px; line-height: 1.4;">{noticia_titulo}</a>
                    </div>
                    <div style="background: {border_color}15; padding: 8px 14px; border-radius: 20px; border: 1px solid {border_color}40; text-align: center;">
                        <span style="font-weight: 700; color: {border_color}; font-size: 12px; display: block;">{icon} {coherencia.upper()}</span>
                        <span style="font-size: 10px; color: {border_color}90; display: block; margin-top: 2px;">{explicacion[:40]}...</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    # Triangulación Métricas
    html += _generar_triangulacion_metricas(resultados, noticias, q_ant, q_act)
    
    # Triangulación Producto ↔ Queja ↔ Noticia
    triangulaciones_con_noticia = [t for t in triangulaciones if t.get('noticia')]
    
    if triangulaciones_con_noticia:
        html += """
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #f59e0b;">
            <div style="font-weight: 700; color: #92400e; margin-bottom: 15px; font-size: 15px;">
                🔗 Triangulación: Producto ↔ Queja ↔ Noticia
            </div>
            <div style="font-size: 12px; color: #78350f; margin-bottom: 15px;">
                Conexiones detectadas entre cambios en productos, quejas de usuarios y noticias del mercado.
            </div>
        """
        
        for tri in triangulaciones_con_noticia[:4]:
            producto = tri.get('producto', 'N/A')
            efecto = tri.get('efecto_nps', 0)
            queja = tri.get('queja_relacionada', '')
            delta_queja = tri.get('delta_queja', 0)
            coherencia = tri.get('coherencia', 'neutro')
            noticia = tri.get('noticia', {})
            
            if coherencia == 'coherente':
                border_color = '#10b981'
                bg_color = '#ecfdf5'
                icon = '✓'
            elif coherencia == 'incoherente':
                border_color = '#ef4444'
                bg_color = '#fef2f2'
                icon = '!'
            else:
                border_color = '#6b7280'
                bg_color = '#f9fafb'
                icon = '—'
            
            noticia_titulo = noticia.get('titulo', 'Sin noticia')[:60] + '...' if len(noticia.get('titulo', '')) > 60 else noticia.get('titulo', 'Sin noticia')
            noticia_url = noticia.get('url', '#')
            
            html += f"""
            <div style="background: {bg_color}; border: 1px solid {border_color}40; border-radius: 10px; padding: 15px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0;">
                        <span style="font-size: 10px; color: #64748b; display: block;">PRODUCTO</span>
                        <span style="font-weight: 600; color: #1e293b;">{producto}</span>
                        <span style="color: {'#10b981' if efecto > 0 else '#ef4444'}; font-size: 12px; margin-left: 5px;">{efecto:+.0f}pp</span>
                    </div>
                    <span style="font-size: 18px; color: {border_color};">↔</span>
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0;">
                        <span style="font-size: 10px; color: #64748b; display: block;">QUEJA</span>
                        <span style="font-weight: 600; color: #1e293b;">{queja if queja else 'N/A'}</span>
                        <span style="color: {'#ef4444' if delta_queja > 0 else '#10b981'}; font-size: 12px; margin-left: 5px;">{delta_queja:+.0f}pp</span>
                    </div>
                    <span style="font-size: 18px; color: {border_color};">↔</span>
                    <div style="background: white; padding: 8px 14px; border-radius: 8px; border: 1px solid #e8ecf0; flex: 1; min-width: 200px;">
                        <span style="font-size: 10px; color: #64748b; display: block;">NOTICIA</span>
                        <a href="{noticia_url}" target="_blank" style="font-weight: 500; color: #0369a1; text-decoration: none; font-size: 12px;">{noticia_titulo}</a>
                    </div>
                    <div style="background: {border_color}20; padding: 6px 12px; border-radius: 20px; border: 1px solid {border_color};">
                        <span style="font-weight: 600; color: {border_color}; font-size: 11px;">{icon} {coherencia.upper()}</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
    
    return html


def _generar_noticias_grid(resultados, TXT, q_act):
    """
    Genera sección de noticias agrupadas por tema/categoría.
    Muestra TODAS las noticias (sin límite), organizadas por categoria_relacionada.
    """
    deep_research = resultados.get('deep_research', {})
    noticias = resultados.get('noticias', [])
    rango_fechas = deep_research.get('rango_fechas', q_act)
    
    html = f"""
    <div class="content-main" style="padding-top: 0; border-top: 1px solid #e8ecf0; margin-top: 30px;">
        <div class="seccion-titulo-simple">
            <span class="icono">📰</span> Noticias del Mercado
        </div>
    """
    
    if noticias:
        noticias_con_correlacion = len([n for n in noticias if n.get('tiene_correlacion', False) or n.get('queja_relacionada')])
        html += f"""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; border-left: 4px solid #009ee3;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 600; color: #0369a1;">{len(noticias)} noticias relevantes</span>
                    <span style="font-size: 12px; color: #64748b; margin-left: 10px;">Período: {rango_fechas}</span>
                </div>
                <div style="font-size: 11px; color: #64748b;">
                    🔗 {noticias_con_correlacion} relacionadas con cambios NPS
                </div>
            </div>
        </div>
        """
        
        # ── Group news by categoria_relacionada ──
        from collections import defaultdict
        grupos = defaultdict(list)
        for n in noticias:
            cat = n.get('categoria_relacionada', n.get('categoria', '')).strip()
            if not cat or cat.lower() in ['general', 'otros', 'otro', 'noticia']:
                cat = 'Otros'
            grupos[cat].append(n)
        
        # Sort groups: most news first, "Otros" always last
        grupos_ordenados = sorted(
            grupos.items(),
            key=lambda x: (x[0] == 'Otros', -len(x[1]))
        )
        
        # Theme icons
        TEMA_ICONOS = {
            'rendimientos': '💰', 'financiamiento': '💳', 'atención': '🎧',
            'atencion': '🎧', 'seguridad': '🔒', 'complejidad': '⚙️',
            'funcionalidades': '🔧', 'promociones': '🎁', 'tarifas': '💲',
            'otros': '📰', 'principalidad': '🏠',
        }
        
        for tema, noticias_grupo in grupos_ordenados:
            icono = TEMA_ICONOS.get(tema.lower(), '📰')
            html += f"""
            <div style="margin-bottom: 25px;">
                <div style="font-weight: 700; color: #334155; font-size: 14px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0;">
                    {icono} {tema} <span style="font-weight: 400; color: #94a3b8; font-size: 12px;">({len(noticias_grupo)})</span>
                </div>
                <div class="noticias-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
            """
            
            for n in noticias_grupo:
                titulo = n.get('titulo', 'Sin título')
                titulo_display = titulo[:80] + '...' if len(titulo) > 80 else titulo
                url = n.get('url', n.get('link', '#'))
                fuente = n.get('fuente', '')
                fecha = n.get('fecha', '')
                resumen = n.get('resumen', '')[:120] + '...' if len(n.get('resumen', '')) > 120 else n.get('resumen', '')
                impacto = n.get('impacto_esperado', 'neutro')
                queja_rel = n.get('queja_relacionada', '')
                delta_queja = n.get('delta_queja', 0)
                
                if impacto == 'positivo':
                    impacto_color = '#10b981'
                    impacto_bg = '#ecfdf5'
                    impacto_icon = '📈'
                elif impacto == 'negativo':
                    impacto_color = '#ef4444'
                    impacto_bg = '#fef2f2'
                    impacto_icon = '📉'
                else:
                    impacto_color = '#6b7280'
                    impacto_bg = '#f9fafb'
                    impacto_icon = '➡️'
                
                correlacion_badge = ''
                if queja_rel:
                    delta_color = '#ef4444' if delta_queja > 0 else '#10b981'
                    correlacion_badge = f"""
                    <div style="background: {delta_color}15; border: 1px solid {delta_color}40; color: {delta_color}; padding: 4px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; margin-top: 8px;">
                        🔗 Relacionado: {queja_rel} ({delta_queja:+.0f}pp)
                    </div>
                    """
                
                html += f"""
                <div class="noticia-card" style="background: white; border: 1px solid #e8ecf0; border-radius: 12px; padding: 18px; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <span style="background: {impacto_bg}; color: {impacto_color}; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 500;">{impacto_icon} {impacto.capitalize()}</span>
                    </div>
                    <div style="font-size: 13px; color: #1f2937; margin-bottom: 8px; font-weight: 600; line-height: 1.4;">{titulo_display}</div>
                    <div style="font-size: 11px; color: #64748b; line-height: 1.5; margin-bottom: 10px;">{resumen}</div>
                    {correlacion_badge}
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px; padding-top: 10px; border-top: 1px solid #f1f5f9;">
                        <span style="font-size: 10px; color: #888;">📅 {fecha} • {fuente}</span>
                        <a href="{url}" target="_blank" style="font-size: 11px; color: #009ee3; text-decoration: none; font-weight: 600;">Ver noticia →</a>
                    </div>
                </div>
                """
            
            html += '</div></div>'
    
    else:
        html += f"""
        <div style="background: #f8fafc; padding: 40px; text-align: center; border-radius: 12px;">
            <div style="font-size: 48px; margin-bottom: 15px;">📰</div>
            <div style="color: #64748b; font-size: 13px;">
                No se encontraron noticias de mercado para este player/período
            </div>
        </div>
        """
    
    html += "</div>"
    
    return html


def _generar_seccion_consistencia_metricas(resultados, TXT, q_ant, q_act):
    """
    Genera sección de Consistencia de Métricas que triangula:
    - Quejas de Seguridad (waterfall) ↔ Valoración de Seguridad
    - Principalidad y sus motivos
    - Noticias relacionadas
    
    Esto cierra el círculo de triangulación completo.
    """
    # Obtener datos de seguridad
    seg_data = resultados.get('seguridad', {})
    ps = seg_data.get('player_seguridad', {})
    seg_q1 = ps.get('seg_q1', 0)
    seg_q2 = ps.get('seg_q2', 0)
    delta_seg = ps.get('delta', 0)
    
    # Obtener datos de principalidad
    princ_data = resultados.get('principalidad', {})
    pp = princ_data.get('player_principalidad', {})
    princ_q1 = pp.get('princ_q1', 0)
    princ_q2 = pp.get('princ_q2', 0)
    delta_princ = pp.get('delta', 0)
    
    # Obtener quejas de seguridad del waterfall
    wf_data = resultados.get('waterfall', {})
    causas = wf_data.get('causas', [])
    queja_seguridad = None
    for c in causas:
        nombre = c.get('nombre', '').lower()
        if 'segur' in nombre:
            queja_seguridad = c
            break
    
    delta_queja_seg = queja_seguridad.get('delta', 0) if queja_seguridad else 0
    
    # Obtener noticias relacionadas
    noticias = resultados.get('noticias', [])
    noticia_seg = None
    noticia_princ = None
    for n in noticias:
        cat = n.get('categoria_relacionada', '').lower()
        if 'segur' in cat and not noticia_seg:
            noticia_seg = n
        if 'princip' in cat or 'confianza' in cat or 'funcional' in cat:
            if not noticia_princ:
                noticia_princ = n
    
    # Determinar consistencia de seguridad
    # Quejas bajan (delta negativo) + Valoración sube (delta positivo) = CONSISTENTE
    # Quejas suben (delta positivo) + Valoración baja (delta negativo) = CONSISTENTE
    if delta_queja_seg != 0 and delta_seg != 0:
        if (delta_queja_seg < 0 and delta_seg > 0) or (delta_queja_seg > 0 and delta_seg < 0):
            seg_consistencia = "consistente"
            seg_icon = "✓"
            seg_color = "#10b981"
            seg_bg = "#ecfdf5"
            seg_texto = "Quejas y percepción alineadas"
        else:
            seg_consistencia = "observar"
            seg_icon = "⚠"
            seg_color = "#f59e0b"
            seg_bg = "#fffbeb"
            seg_texto = "Quejas y percepción divergen - investigar"
    else:
        seg_consistencia = "neutro"
        seg_icon = "—"
        seg_color = "#6b7280"
        seg_bg = "#f9fafb"
        seg_texto = "Sin cambio significativo"
    
    # Determinar estado de principalidad
    if delta_princ > 1:
        princ_icon = "📈"
        princ_color = "#10b981"
        princ_bg = "#ecfdf5"
        princ_texto = "Ganando usuarios principales"
    elif delta_princ < -1:
        princ_icon = "📉"
        princ_color = "#ef4444"
        princ_bg = "#fef2f2"
        princ_texto = "Perdiendo usuarios principales - observar"
    else:
        princ_icon = "➡️"
        princ_color = "#6b7280"
        princ_bg = "#f9fafb"
        princ_texto = "Estable"
    
    # Obtener top motivos de principalidad
    motivos_princ = princ_data.get('motivos_principalidad', None)
    top_motivo_princ = ""
    try:
        # Puede ser DataFrame o lista
        import pandas as pd
        if motivos_princ is not None:
            if isinstance(motivos_princ, pd.DataFrame) and not motivos_princ.empty:
                # Buscar columna de motivo
                col_motivo = None
                for col in motivos_princ.columns:
                    if 'motivo' in col.lower():
                        col_motivo = col
                        break
                if col_motivo and len(motivos_princ) > 0:
                    top_motivo_princ = str(motivos_princ.iloc[0][col_motivo])[:30]
            elif isinstance(motivos_princ, list) and len(motivos_princ) > 0:
                if hasattr(motivos_princ[0], 'get'):
                    top_motivo_princ = motivos_princ[0].get('motivo', '')[:30]
    except Exception:
        pass
    
    html = f"""
    <div class="content-main" style="padding-top: 0; border-top: 1px solid #e8ecf0; margin-top: 30px;">
        <div class="seccion-titulo-simple">
            <span class="icono">📊</span> Consistencia de Métricas
        </div>
        
        <div style="font-size: 12px; color: #64748b; margin-bottom: 20px; padding: 0 5px;">
            Triangulación entre quejas (waterfall), métricas de percepción y contexto de mercado.
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            
            <!-- SEGURIDAD -->
            <div style="background: {seg_bg}; border: 1px solid {seg_color}40; border-radius: 12px; padding: 20px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                    <span style="font-size: 24px;">🔒</span>
                    <div>
                        <div style="font-weight: 700; color: #1e293b; font-size: 14px;">SEGURIDAD</div>
                        <div style="font-size: 11px; color: {seg_color}; font-weight: 600;">{seg_icon} {seg_consistencia.upper()}</div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                    <div style="background: white; padding: 10px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Quejas</div>
                        <div style="font-weight: 700; color: {'#10b981' if delta_queja_seg < 0 else '#ef4444' if delta_queja_seg > 0 else '#6b7280'}; font-size: 16px;">{delta_queja_seg:+.0f}pp</div>
                    </div>
                    <div style="background: white; padding: 10px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Valoración</div>
                        <div style="font-weight: 700; color: {'#10b981' if delta_seg > 0 else '#ef4444' if delta_seg < 0 else '#6b7280'}; font-size: 16px;">{delta_seg:+.0f}pp</div>
                        <div style="font-size: 10px; color: #64748b;">{seg_q1:.0f}% → {seg_q2:.0f}%</div>
                    </div>
                </div>
                
                <div style="font-size: 12px; color: #475569; margin-bottom: 10px;">
                    {seg_texto}
                </div>
                
                {"" if not noticia_seg else f'''
                <div style="background: white; padding: 10px; border-radius: 8px; border-left: 3px solid #0369a1; margin-top: 10px;">
                    <div style="font-size: 10px; color: #64748b;">📰 Noticia relacionada:</div>
                    <a href="{noticia_seg.get('url', '#')}" target="_blank" style="font-size: 11px; color: #0369a1; text-decoration: none;">{noticia_seg.get('titulo', '')[:50]}...</a>
                </div>
                '''}
            </div>
            
            <!-- PRINCIPALIDAD -->
            <div style="background: {princ_bg}; border: 1px solid {princ_color}40; border-radius: 12px; padding: 20px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                    <span style="font-size: 24px;">🏠</span>
                    <div>
                        <div style="font-weight: 700; color: #1e293b; font-size: 14px;">PRINCIPALIDAD</div>
                        <div style="font-size: 11px; color: {princ_color}; font-weight: 600;">{princ_icon} {princ_texto[:20]}</div>
                    </div>
                </div>
                
                <div style="background: white; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">% Principal</div>
                            <div style="font-size: 11px; color: #475569;">{q_ant}: {princ_q1:.0f}% → {q_act}: {princ_q2:.0f}%</div>
                        </div>
                        <div style="font-weight: 700; color: {princ_color}; font-size: 18px;">{delta_princ:+.0f}pp</div>
                    </div>
                </div>
                
                <div style="font-size: 12px; color: #475569;">
                    {princ_texto}
                </div>
                
                {"" if not top_motivo_princ else f'''
                <div style="margin-top: 10px; font-size: 11px; color: #64748b;">
                    <strong>Top motivo:</strong> {top_motivo_princ}
                </div>
                '''}
                
                {"" if not noticia_princ else f'''
                <div style="background: white; padding: 10px; border-radius: 8px; border-left: 3px solid #0369a1; margin-top: 10px;">
                    <div style="font-size: 10px; color: #64748b;">📰 Noticia relacionada:</div>
                    <a href="{noticia_princ.get('url', '#')}" target="_blank" style="font-size: 11px; color: #0369a1; text-decoration: none;">{noticia_princ.get('titulo', '')[:50]}...</a>
                </div>
                '''}
            </div>
            
        </div>
    </div>
    """
    
    return html


def _generar_tabla_productos(productos, TXT):
    """Genera tabla de TODOS los productos (no solo los clave)."""
    if not productos:
        return '<p style="color:#999;">Sin datos de productos</p>'
    
    # Ordenar por impacto total (absoluto)
    productos_ordenados = sorted(productos, key=lambda x: abs(x.get('total_effect', 0)), reverse=True)
    
    total_mix = sum(p.get('mix_effect', 0) for p in productos_ordenados)
    total_nps_eff = sum(p.get('nps_effect', 0) for p in productos_ordenados)
    total_total = sum(p.get('total_effect', 0) for p in productos_ordenados)
    
    html = f"""
    <div class="seccion-soporte" style="background: white; padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb;">
        <div class="seccion-titulo-soporte" style="font-weight: 700; font-size: 16px; margin-bottom: 15px; border-bottom: 2px solid #009ee3; padding-bottom: 10px;">
            📈 {TXT['impacto_productos']} ({len(productos_ordenados)} productos)
        </div>
        
        <!-- Explicación de métricas -->
        <div style="background: #f8fafc; border-radius: 8px; padding: 15px; margin-bottom: 20px; font-size: 12px; color: #475569; border-left: 4px solid #009ee3;">
            <div style="font-weight: 600; margin-bottom: 8px; color: #1e293b;">📐 ¿Cómo se calculan los efectos?</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <strong style="color: #0369a1;">Mix Effect</strong> = ΔShare × Lift<sub>Q2</sub> / 100<br>
                    <span style="font-size: 11px; color: #64748b;">Impacto por cambio en penetración. Si más usuarios adoptan un producto con Lift positivo, el NPS sube.</span>
                </div>
                <div>
                    <strong style="color: #0369a1;">NPS Effect</strong> = Share<sub>Q2</sub> × Δ NPS Usuario / 100<br>
                    <span style="font-size: 11px; color: #64748b;">Impacto por cambio en satisfacción. Si los usuarios de un producto están más satisfechos, el NPS sube.</span>
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 11px; color: #64748b;">
                <strong>Lift</strong> = NPS usuarios del producto - NPS usuarios sin el producto. <strong>NPS Usuario</strong> = NPS promedio de quienes usan el producto.
            </div>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead>
                <tr style="background: #f8fafc;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e0e0e0;">Producto</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">Share</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">NPS Usu</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">Lift</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">Mix Eff</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">NPS Eff</th>
                    <th style="padding: 10px; text-align: center; border-bottom: 2px solid #e0e0e0;">Total</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Mostrar TODOS los productos
    for p in productos_ordenados:
        total = p.get('total_effect', 0)
        nombre = p.get('nombre_display', p.get('nombre_original', 'N/A'))
        nps_usuario = p.get('nps_usuario_q2', 0)
        delta_nps_usuario = p.get('delta_nps_usuario', 0)
        lift = p.get('lift_q2', 0)
        delta_lift = p.get('delta_lift', 0)
        
        # Colores
        color_total = "#16a34a" if total > 0.1 else "#dc2626" if total < -0.1 else "#6b7280"
        color_share = "#16a34a" if p.get('delta_share', 0) > 0 else "#dc2626" if p.get('delta_share', 0) < 0 else "#6b7280"
        color_nps = "#16a34a" if delta_nps_usuario > 0 else "#dc2626" if delta_nps_usuario < 0 else "#6b7280"
        color_lift = "#16a34a" if delta_lift > 0 else "#dc2626" if delta_lift < 0 else "#6b7280"
        
        # Destacar productos con alto impacto
        row_bg = "#fff9e6" if abs(total) > UMBRAL_PRODUCTO_DESTACAR else "white"
        
        html += f"""
        <tr style="background: {row_bg};">
            <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{nombre}</strong></td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee;">{p.get('share_q2', 0):.0f}% <span style="color: {color_share}; font-size: 11px;">({p.get('delta_share', 0):+.0f})</span></td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee;">{nps_usuario:.0f} <span style="color: {color_nps}; font-size: 11px;">({delta_nps_usuario:+.0f})</span></td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee;">{lift:.0f} <span style="color: {color_lift}; font-size: 11px;">({delta_lift:+.0f})</span></td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee; color: {'#16a34a' if p.get('mix_effect', 0) > 0 else '#dc2626' if p.get('mix_effect', 0) < 0 else '#6b7280'};">{p.get('mix_effect', 0):+.0f}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee; color: {'#16a34a' if p.get('nps_effect', 0) > 0 else '#dc2626' if p.get('nps_effect', 0) < 0 else '#6b7280'};">{p.get('nps_effect', 0):+.0f}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #eee; color: {color_total};"><strong>{total:+.0f}pp</strong></td>
        </tr>
        """
    
    color_total_all = "#16a34a" if total_total > 0 else "#dc2626" if total_total < 0 else "#6b7280"
    
    html += f"""
        <tr style="background: #f0f7ff; font-weight: 700;">
            <td colspan="4" style="padding: 12px; border-top: 2px solid #e0e0e0;"><strong>TOTAL PRODUCTOS</strong></td>
            <td style="padding: 12px; text-align: center; border-top: 2px solid #e0e0e0; color: {'#16a34a' if total_mix > 0 else '#dc2626'};">{total_mix:+.0f}</td>
            <td style="padding: 12px; text-align: center; border-top: 2px solid #e0e0e0; color: {'#16a34a' if total_nps_eff > 0 else '#dc2626'};">{total_nps_eff:+.0f}</td>
            <td style="padding: 12px; text-align: center; border-top: 2px solid #e0e0e0; color: {color_total_all};"><strong>{total_total:+.0f}pp</strong></td>
        </tr>
    </tbody></table>
    </div>
    """
    
    return html


def _buscar_queja_relacionada(producto, causas):
    """Busca queja relacionada con un producto - mapeo expandido."""
    # Mapeo Producto → Motivos de queja relacionados (waterfall)
    mapeo = {
        # Productos de CRÉDITO → Queja Financiamiento
        'crédito': ['Financiamiento', 'Financiamento', 'Crédito', 'Credito'],
        'credito': ['Financiamiento', 'Financiamento', 'Crédito', 'Credito'],
        'tarjeta': ['Financiamiento', 'Financiamento', 'Tarjeta'],
        'cartão': ['Financiamiento', 'Financiamento', 'Cartão'],
        'cartao': ['Financiamiento', 'Financiamento', 'Cartão'],
        'empréstimo': ['Financiamiento', 'Financiamento', 'Préstamo'],
        'préstamo': ['Financiamiento', 'Financiamento', 'Préstamo'],
        
        # Productos de RENDIMIENTOS → Queja Rendimientos
        'rendimento': ['Rendimientos', 'Rendimentos'],
        'rendimientos': ['Rendimientos', 'Rendimentos'],
        'rendimentos': ['Rendimientos', 'Rendimentos'],
        'cdi': ['Rendimientos', 'Rendimentos'],
        'inversión': ['Rendimientos', 'Rendimentos', 'Inversiones'],
        'investimento': ['Rendimientos', 'Rendimentos', 'Inversiones'],
        
        # Productos de PAGOS
        'pago': ['Pagos', 'Pagamentos', 'Complejidad'],
        'pagamento': ['Pagos', 'Pagamentos', 'Complejidad'],
        'qr': ['Funcionalidades', 'Complejidad'],
        'billetera': ['Funcionalidades', 'Complejidad'],
        'wallet': ['Funcionalidades', 'Complejidad'],
        
        # Transferencias
        'transferencia': ['Funcionalidades', 'Complejidad'],
        'transferência': ['Funcionalidades', 'Complejidad'],
        'pix': ['Funcionalidades', 'Complejidad'],
    }
    
    producto_lower = producto.lower()
    
    # Buscar por keywords en el nombre del producto
    for key, quejas_rel in mapeo.items():
        if key in producto_lower:
            for c in causas:
                motivo = c.get('motivo', '').lower()
                for q in quejas_rel:
                    if q.lower() in motivo or motivo in q.lower():
                        return c
    
    # Fallback: buscar coincidencia directa
    for c in causas:
        motivo = c.get('motivo', '').lower()
        if any(word in motivo for word in producto_lower.split()):
            return c
    
    return None


    # _evaluar_coherencia eliminada (dead code, reemplazada por _evaluar_coherencia_texto)


def _evaluar_coherencia_texto(producto_effect, queja_delta):
    """Evalúa coherencia - retorna texto descriptivo."""
    if producto_effect > 0 and queja_delta < 0:
        return "COHERENTE ✓ (mejor producto = menos quejas)"
    elif producto_effect < 0 and queja_delta > 0:
        return "COHERENTE ✓ (peor producto = más quejas)"
    elif producto_effect > 0 and queja_delta > 0:
        return "INCOHERENTE ✗ (producto mejora pero quejas suben)"
    elif producto_effect < 0 and queja_delta < 0:
        return "REVISAR (producto empeora pero quejas bajan)"
    return "Sin triangulación"


def _generar_alertas(resultados):
    """Genera alertas basadas en los datos."""
    alertas = []
    
    seg_data = resultados.get('seguridad', {})
    ps = seg_data.get('player_seguridad', {})
    delta_seg = ps.get('delta', 0)
    if delta_seg < -2:
        alertas.append(f"La percepción de seguridad cayó {abs(delta_seg):.0f}pp. Posible riesgo reputacional.")
    
    princ_data = resultados.get('principalidad', {})
    pp = princ_data.get('player_principalidad', {})
    delta_princ = pp.get('delta', 0)
    if delta_princ < -3:
        alertas.append(f"La principalidad cayó {abs(delta_princ):.0f}pp. Riesgo de pérdida de usuarios principales.")
    
    wf_data = resultados.get('waterfall', {})
    causas = wf_data.get('causas_waterfall', [])
    for c in causas:
        if c.get('delta', 0) > 2:
            alertas.append(f"Queja \"{c.get('motivo', '')}\" subió {c.get('delta', 0):+.0f}pp. Requiere atención.")
            break
    
    return alertas


def _generar_anexos(resultados, TXT, bandera, player, q_ant, q_act, g_wf, g_quejas, g_seg, g_mot_inseg, g_princ, g_mot_princ):
    """Genera los tabs de anexos."""
    
    prod_data = resultados.get('productos', {})
    productos = prod_data.get('productos_todos', prod_data.get('productos_clave', []))
    
    prom_data = resultados.get('promotores', {})
    pct_prom = prom_data.get('pct_promotores_q2', 0)
    delta_prom = prom_data.get('delta_promotores', 0)
    
    # Anexo 1: Quejas
    html_anexo1 = f"""
    <div id="anexo1" class="tab-content" style="display: none;">
        <div class="content-main">
            <div class="titulo-principal">
                <span class="bandera">{bandera}</span>
                <h1>{TXT['evolucion_quejas']} - {player}</h1>
            </div>
            <div class="grafico-box">
                <div class="grafico-box-titulo">📉 Waterfall NPS</div>
                {f'<img src="data:image/png;base64,{g_wf}" style="max-width:100%;">' if g_wf else '<p style="color:#999;">Gráfico no disponible</p>'}
            </div>
            <div class="grafico-box">
                <div class="grafico-box-titulo">📈 Evolución de Quejas</div>
                {f'<img src="data:image/png;base64,{g_quejas}" style="max-width:100%;">' if g_quejas else '<p style="color:#999;">Gráfico no disponible</p>'}
            </div>
        </div>
    </div>
    """
    
    # Anexo 2: Seguridad - CON GRÁFICO DE MOTIVOS PONDERADOS
    html_anexo2 = f"""
    <div id="anexo2" class="tab-content" style="display: none;">
        <div class="content-main">
            <div class="titulo-principal">
                <span class="bandera">{bandera}</span>
                <h1>{TXT['seguridad']} - {player}</h1>
            </div>
            <div class="grafico-box">
                <div class="grafico-box-titulo">📊 Evolución de {TXT['seguridad']}</div>
                {f'<img src="data:image/png;base64,{g_seg}" style="max-width:100%;">' if g_seg else '<p style="color:#999;">Gráfico no disponible</p>'}
            </div>
            <div class="grafico-box" style="margin-top: 25px;">
                <div class="grafico-box-titulo">📉 Motivos de Inseguridad (Ponderado sobre Base Total)</div>
                <div style="font-size: 12px; color: #64748b; margin-bottom: 15px; padding: 0 10px;">
                    % Ponderado = % Motivo × % Inseguridad de la marca. Muestra la proporción de usuarios inseguros por cada motivo respecto a la base total.
                </div>
                {f'<img src="data:image/png;base64,{g_mot_inseg}" style="max-width:100%;">' if g_mot_inseg else '<p style="color:#999;">Gráfico de motivos no disponible</p>'}
            </div>
        </div>
    </div>
    """
    
    # Anexo 3: Principalidad - CON GRÁFICO DE MOTIVOS PONDERADOS
    html_anexo3 = f"""
    <div id="anexo3" class="tab-content" style="display: none;">
        <div class="content-main">
            <div class="titulo-principal">
                <span class="bandera">{bandera}</span>
                <h1>{TXT['principalidad']} - {player}</h1>
            </div>
            <div class="grafico-box">
                <div class="grafico-box-titulo">📊 Evolución de {TXT['principalidad']}</div>
                {f'<img src="data:image/png;base64,{g_princ}" style="max-width:100%;">' if g_princ else '<p style="color:#999;">Gráfico no disponible</p>'}
            </div>
            <div class="grafico-box" style="margin-top: 25px;">
                <div class="grafico-box-titulo">🏆 Motivos de Principalidad (Ponderado sobre Base Total)</div>
                <div style="font-size: 12px; color: #64748b; margin-bottom: 15px; padding: 0 10px;">
                    % Ponderado = % Motivo × % Principalidad de la marca. Muestra la proporción de usuarios principales por cada motivo respecto a la base total.
                </div>
                {f'<img src="data:image/png;base64,{g_mot_princ}" style="max-width:100%;">' if g_mot_princ else '<p style="color:#999;">Gráfico de motivos no disponible</p>'}
            </div>
        </div>
    </div>
    """
    
    # Anexo 4: Productos
    html_anexo4 = f"""
    <div id="anexo4" class="tab-content" style="display: none;">
        <div class="content-main">
            <div class="titulo-principal">
                <span class="bandera">{bandera}</span>
                <h1>{TXT['productos']} - {player}</h1>
            </div>
            {_generar_tabla_productos(productos, TXT)}
        </div>
    </div>
    """
    
    # Anexo 5: Promotores - COMPLETO como en el notebook
    prom_data = resultados.get('promotores', {})
    pct_prom_q1 = prom_data.get('pct_prom_q1', 0)
    pct_prom_q2 = prom_data.get('pct_prom_q2', pct_prom)
    delta_prom_calc = prom_data.get('delta_prom', delta_prom)
    motivos_lista = prom_data.get('promotores_data', [])
    comentarios_promotores = prom_data.get('comentarios_promotores', {})
    
    html_anexo5 = f"""
    <div id="anexo5" class="tab-content" style="display: none;">
        <div class="content-main">
            <!-- Header Verde con Métricas -->
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">🌟 {TXT['porque_recomiendan']}</div>
                <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 36px; font-weight: 300; opacity: 0.8;">{pct_prom_q1:.0f}%</span>
                        <span style="font-size: 24px; opacity: 0.5; margin: 0 10px;">→</span>
                        <span style="font-size: 48px; font-weight: 700;">{pct_prom_q2:.0f}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 8px; font-size: 20px; font-weight: 600;">
                        {delta_prom_calc:+.0f}pp
                    </div>
                </div>
                <div style="margin-top: 10px; opacity: 0.9; font-size: 13px;">Promotores (NPS 9-10) de {q_ant} a {q_act}</div>
            </div>
    """
    
    # Distribución de motivos con barras
    if motivos_lista:
        html_anexo5 += f'''
            <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; border: 1px solid #e5e7eb;">
                <h3 style="color: #065f46; margin-bottom: 20px; font-size: 16px;">📊 {TXT.get('motivos_satisfaccion', 'Motivos de Satisfacción')}</h3>
                <div style="display: grid; gap: 12px;">
        '''
        
        # Ordenar por Q2 descendente
        motivos_ordenados = sorted(motivos_lista, key=lambda x: x.get('pct_q2', 0), reverse=True)
        
        for m in motivos_ordenados[:8]:
            motivo_nombre = m.get('motivo', 'Otro')[:50]
            q1_val = m.get('pct_q1', 0)
            q2_val = m.get('pct_q2', 0)
            delta_mot = m.get('delta', 0)
            
            # Color según delta
            if delta_mot > 1:
                delta_color_m = '#10b981'
                delta_bg_m = '#d1fae5'
                emoji_m = '📈'
            elif delta_mot < -1:
                delta_color_m = '#ef4444'
                delta_bg_m = '#fee2e2'
                emoji_m = '📉'
            else:
                delta_color_m = '#6b7280'
                delta_bg_m = '#f3f4f6'
                emoji_m = '➡️'
            
            bar_width = min(q2_val * 2, 100)
            
            html_anexo5 += f'''
                <div style="background: #f9fafb; padding: 14px 18px; border-radius: 10px; border-left: 4px solid #10b981;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 600; color: #1f2937; font-size: 13px;">{motivo_nombre}</span>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 12px; color: #6b7280;">{q1_val:.0f}% → {q2_val:.0f}%</span>
                            <span style="background: {delta_bg_m}; color: {delta_color_m}; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">
                                {emoji_m} {delta_mot:+.0f}pp
                            </span>
                        </div>
                    </div>
                    <div style="background: #e5e7eb; border-radius: 4px; height: 6px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #10b981, #34d399); width: {bar_width}%; height: 100%; border-radius: 4px;"></div>
                    </div>
                </div>
            '''
        
        html_anexo5 += '</div></div>'
        
        # Deep Dive - Acordeones para cada motivo
        html_anexo5 += f'''
            <div style="background: white; padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <h3 style="color: #065f46; margin-bottom: 20px; font-size: 16px;">🔬 Deep Dive - ¿Por qué nos recomiendan?</h3>
                <p style="color: #888; font-size: 12px; margin-bottom: 15px;">👆 Click en cada motivo para ver comentarios de promotores</p>
        '''
        
        for m in motivos_ordenados[:6]:
            html_anexo5 += _generar_acordeon_promotor(m, q_ant, q_act, comentarios_promotores)
        
        html_anexo5 += '</div>'
    
    html_anexo5 += """
        </div>
    </div>
    """
    
    # ==========================================================================
    # ANEXO 6: CAUSAS RAÍZ SEMÁNTICAS
    # ==========================================================================
    
    html_anexo6 = _generar_tab_causas_raiz(resultados, q_ant, q_act, player)
    
    return html_anexo1 + html_anexo2 + html_anexo3 + html_anexo4 + html_anexo5 + html_anexo6


# ==============================================================================
# TAB CAUSAS RAÍZ SEMÁNTICAS
# ==============================================================================

def _generar_tab_causas_raiz(resultados, q_ant, q_act, player):
    """Genera el tab de Causas Raíz semánticas a partir del JSON generado por LLM."""
    import json
    from pathlib import Path
    
    # Intentar cargar JSON de causas raíz
    data_dir = Path(__file__).parent.parent / 'data'
    causas_data = None
    
    json_filename = f'causas_raiz_semantico_{player}_{q_act}.json'
    json_path = data_dir / json_filename
    
    if json_path.exists():
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                causas_data = json.load(f)
        except Exception:
            pass
    
    # Fallback: buscar cualquier JSON de causas raíz para este player
    if not causas_data:
        for f in sorted(data_dir.glob(f'causas_raiz_semantico_{player}_*.json'), reverse=True):
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    causas_data = json.load(fh)
                break
            except Exception:
                continue
    
    if not causas_data or not causas_data.get('causas_por_motivo'):
        return f"""
    <div id="anexo6" class="tab-content" style="display: none;">
        <div class="content-main">
            <div style="background: white; padding: 40px; border-radius: 12px; text-align: center; border: 1px solid #e5e7eb;">
                <div style="font-size: 48px; margin-bottom: 15px;">🔍</div>
                <h3 style="color: #6b7280;">Análisis de Causas Raíz no disponible</h3>
                <p style="color: #9ca3af;">No se encontró el archivo de causas raíz semánticas para este período.</p>
            </div>
        </div>
    </div>
    """
    
    causas_por_motivo = causas_data['causas_por_motivo']
    
    # Ordenar motivos por delta (más empeorados primero)
    motivos_ordenados = sorted(
        causas_por_motivo.items(),
        key=lambda x: x[1].get('delta_pp', 0),
        reverse=True
    )
    
    # Header
    html = f"""
    <div id="anexo6" class="tab-content" style="display: none;">
        <div class="content-main">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); padding: 25px; border-radius: 12px; color: white; margin-bottom: 25px;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">🔍 Análisis Semántico de Causas Raíz</div>
                <div style="font-size: 24px; font-weight: 700; margin-bottom: 5px;">{player} - {q_ant} → {q_act}</div>
                <div style="opacity: 0.85; font-size: 13px;">{len(causas_por_motivo)} motivos analizados · Basado en comentarios reales de detractores y neutros</div>
            </div>
    """
    
    # Cada motivo como un card con acordeón
    for motivo, datos in motivos_ordenados:
        delta = datos.get('delta_pp', 0)
        total_comms = datos.get('total_comentarios_analizados', 0)
        causas = datos.get('causas_raiz', [])
        
        if not causas:
            continue
        
        # Color del header según delta
        if delta > 1:
            header_bg = 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)'
            delta_label = f'🔥 +{delta:.1f}pp (empeoró)'
        elif delta > 0:
            header_bg = 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
            delta_label = f'⚠️ +{delta:.1f}pp'
        elif delta > -1:
            header_bg = 'linear-gradient(135deg, #6b7280 0%, #9ca3af 100%)'
            delta_label = f'➡️ {delta:.1f}pp (estable)'
        else:
            header_bg = 'linear-gradient(135deg, #059669 0%, #10b981 100%)'
            delta_label = f'✅ {delta:.1f}pp (mejoró)'
        
        motivo_id = motivo.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        
        html += f"""
            <div style="background: white; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e5e7eb; overflow: hidden;">
                <!-- Header del motivo -->
                <div onclick="document.getElementById('causas_{motivo_id}').style.display = document.getElementById('causas_{motivo_id}').style.display === 'none' ? 'block' : 'none'; this.querySelector('.chevron').textContent = document.getElementById('causas_{motivo_id}').style.display === 'none' ? '▶' : '▼';"
                     style="background: {header_bg}; padding: 18px 22px; cursor: pointer; color: white; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 17px; font-weight: 700;">{motivo}</div>
                        <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">{delta_label} · {total_comms} comentarios · {len(causas)} causas identificadas</div>
                    </div>
                    <span class="chevron" style="font-size: 16px; opacity: 0.8;">▶</span>
                </div>
                
                <!-- Contenido expandible -->
                <div id="causas_{motivo_id}" style="display: none; padding: 20px;">
        """
        
        # Cada causa raíz
        for i, causa in enumerate(causas):
            titulo = html_module.escape(causa.get('titulo', ''))
            desc = html_module.escape(causa.get('descripcion', ''))
            freq_pct = causa.get('frecuencia_pct', 0)
            freq_abs = causa.get('frecuencia_abs', 0)
            ejemplos = causa.get('ejemplos', [])
            
            # Color de la barra según posición
            colors = ['#2563eb', '#7c3aed', '#0891b2', '#c2410c']
            bar_color = colors[i % len(colors)]
            
            html += f"""
                    <div style="margin-bottom: 20px; padding: 16px; background: #f9fafb; border-radius: 10px; border-left: 4px solid {bar_color};">
                        <!-- Título + frecuencia -->
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <div style="font-weight: 700; font-size: 14px; color: #1f2937; flex: 1;">{titulo}</div>
                            <div style="background: {bar_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; white-space: nowrap; margin-left: 12px;">
                                {freq_pct}% ({freq_abs})
                            </div>
                        </div>
                        
                        <!-- Barra de frecuencia -->
                        <div style="background: #e5e7eb; border-radius: 4px; height: 6px; margin-bottom: 10px; overflow: hidden;">
                            <div style="background: {bar_color}; width: {min(freq_pct, 100)}%; height: 100%; border-radius: 4px;"></div>
                        </div>
                        
                        <!-- Descripción -->
                        <div style="color: #4b5563; font-size: 13px; line-height: 1.5; margin-bottom: 10px;">{desc}</div>
                        
                        <!-- Ejemplos -->
                        <div style="margin-top: 8px;">
                            <div style="font-size: 11px; color: #9ca3af; font-weight: 600; margin-bottom: 6px; text-transform: uppercase;">Comentarios representativos</div>
            """
            
            for ej in ejemplos[:3]:
                ej_escaped = html_module.escape(str(ej))
                html += f"""
                            <div style="background: white; border: 1px solid #e5e7eb; padding: 10px 14px; border-radius: 8px; margin-bottom: 6px; font-style: italic; color: #374151; font-size: 12px; line-height: 1.4;">
                                "{ej_escaped}"
                            </div>
                """
            
            html += """
                        </div>
                    </div>
            """
        
        html += """
                </div>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html


# ==============================================================================
# EXPORTACIÓN
# ==============================================================================

def guardar_html(html, player, periodo, output_dir=None):
    """Guarda el HTML en un archivo."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'outputs'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"Resumen_NPS_{player.replace(' ', '_')}_{periodo}.html"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Print suprimido - se muestra en resultado final de correr_modelo.py
    pass
    return str(filepath)


# ==============================================================================
# EJECUCIÓN DIRECTA
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from ejecutar_modelo import ejecutar_modelo_completo
    
    print("Ejecutando modelo...")
    resultados = ejecutar_modelo_completo(verbose=False)
    
    print("\nGenerando HTML...")
    html = generar_html_completo(resultados)
    
    filepath = guardar_html(html, resultados['config']['player'], resultados['config']['periodo_2'])
    print(f"📄 HTML: {len(html):,} caracteres")
