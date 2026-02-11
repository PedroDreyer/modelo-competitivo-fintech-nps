# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
PARTE 12: SENIOR ANALYST - RESUMEN EJECUTIVO FINAL
═══════════════════════════════════════════════════════════════════════════════

Esta parte genera el resumen ejecutivo final donde Cursor actúa como
Senior Analyst, triangulando datos de Producto ↔ Queja ↔ Noticia.

Uso:
    from scripts.parte12_senior_analyst import generar_resumen_ejecutivo
    resumen = generar_resumen_ejecutivo(resultados, config)
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# ==============================================================================
# PROMPT PARA CURSOR COMO SENIOR ANALYST
# ==============================================================================

PROMPT_SENIOR_ANALYST = """
═══════════════════════════════════════════════════════════════════════════════
🎯 ROL: SENIOR ANALYST - DIAGNÓSTICO DE VARIACIONES DE NPS
═══════════════════════════════════════════════════════════════════════════════

Eres un Senior Analyst experto en Customer Experience (CX) y análisis competitivo 
del sector Fintech. Tu tarea es generar un diagnóstico ejecutivo de las variaciones 
de NPS observadas.

═══════════════════════════════════════════════════════════════════════════════
📋 DATOS DISPONIBLES
═══════════════════════════════════════════════════════════════════════════════

{datos_resumen}

═══════════════════════════════════════════════════════════════════════════════
📝 INSTRUCCIONES DE ANÁLISIS
═══════════════════════════════════════════════════════════════════════════════

1. **DIAGNÓSTICO GENERAL** (2-3 párrafos):
   - Interpretar la variación del NPS ({nps_q1} → {nps_q2}, Δ {delta_nps:+.1f}pp)
   - Identificar los principales drivers (positivos y negativos)
   - Contextualizar con el mercado/competencia

2. **TRIANGULACIÓN** (Producto ↔ Queja ↔ Contexto):
   - Relacionar cambios en productos con cambios en quejas
   - Identificar patrones causa-efecto
   - Señalar si las noticias/contexto explican los cambios

3. **ALERTAS** (máximo 3):
   - ⚠️ Alertas críticas que requieren acción inmediata
   - 📉 Tendencias preocupantes
   - 🔍 Inconsistencias en los datos

4. **OPORTUNIDADES** (máximo 3):
   - 🌟 Bright spots a capitalizar
   - 📈 Tendencias positivas a reforzar
   - 💡 Quick wins identificados

5. **RECOMENDACIONES** (3-5 acciones concretas):
   - Acciones específicas y medibles
   - Priorizadas por impacto esperado

═══════════════════════════════════════════════════════════════════════════════
📊 FORMATO DE RESPUESTA
═══════════════════════════════════════════════════════════════════════════════

{{
    "diagnostico_general": "...",
    "triangulacion": [
        {{"producto": "...", "queja_relacionada": "...", "relacion": "..."}},
        ...
    ],
    "alertas": [
        {{"tipo": "critica|preocupante|inconsistencia", "descripcion": "..."}},
        ...
    ],
    "oportunidades": [
        {{"tipo": "bright_spot|tendencia|quick_win", "descripcion": "..."}},
        ...
    ],
    "recomendaciones": [
        {{"prioridad": 1, "accion": "...", "impacto_esperado": "..."}},
        ...
    ],
    "conclusion": "..."
}}
"""


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def generar_resumen_ejecutivo(resultados, config, verbose=True):
    """
    Genera el resumen ejecutivo consolidando todos los análisis.
    
    Args:
        resultados: Dict con resultados de todas las partes
        config: Diccionario de configuración
        
    Returns:
        dict: Resumen ejecutivo estructurado
    """
    
    site = config['site']
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    if verbose:
        print("=" * 80)
        print(f"🎯 PARTE 12: SENIOR ANALYST - RESUMEN EJECUTIVO")
        print(f"   {BANDERA} {player} | {q_ant} vs {q_act}")
        print("=" * 80)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSOLIDAR MÉTRICAS PRINCIPALES
    # ═══════════════════════════════════════════════════════════════════════════
    
    metricas = {
        'player': player,
        'site': site,
        'pais': NOMBRE_PAIS,
        'q_ant': q_ant,
        'q_act': q_act
    }
    
    # NPS
    if 'nps' in resultados:
        metricas['nps_q1'] = resultados['nps'].get('nps_q1', 0)
        metricas['nps_q2'] = resultados['nps'].get('nps_q2', 0)
        metricas['delta_nps'] = resultados['nps'].get('delta_nps', 0)
    
    # Promotores
    if 'promotores' in resultados:
        metricas['pct_prom_q1'] = resultados['promotores'].get('pct_prom_q1', 0)
        metricas['pct_prom_q2'] = resultados['promotores'].get('pct_prom_q2', 0)
    
    # Principalidad
    if 'principalidad' in resultados:
        pp = resultados['principalidad'].get('player_principalidad', {})
        metricas['princ_q1'] = pp.get('princ_q1', 0)
        metricas['princ_q2'] = pp.get('princ_q2', 0)
        metricas['delta_princ'] = pp.get('delta', 0)
    
    # Seguridad
    if 'seguridad' in resultados:
        ps = resultados['seguridad'].get('player_seguridad', {})
        metricas['seg_q1'] = ps.get('seg_q1', 0)
        metricas['seg_q2'] = ps.get('seg_q2', 0)
        metricas['delta_seg'] = ps.get('delta', 0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSOLIDAR DRIVERS (con temas principales de subcausas)
    # ═══════════════════════════════════════════════════════════════════════════
    
    drivers_positivos = []
    drivers_negativos = []
    
    # Usar causas_waterfall enriquecidas (tienen tema_principal)
    # Si no existe, fallback a causas_raiz['waterfall_data']
    causas_data = resultados.get('causas_waterfall', [])
    if not causas_data and 'causas_raiz' in resultados:
        causas_data = resultados['causas_raiz'].get('waterfall_data', [])
    
    for item in causas_data:
        delta = item.get('delta', 0)
        motivo = item.get('motivo', '')
        tema_principal = item.get('tema_principal', '')
        temas = item.get('temas_principales', [])
        
        # Construir descripción con tema principal si existe
        if delta < -1:  # Quejas que bajaron = positivo
            desc = f"Quejas de {motivo} bajaron {abs(delta):.1f}pp"
            if tema_principal:
                desc += f" (principalmente '{tema_principal}')"
            drivers_positivos.append({
                'tipo': 'queja',
                'nombre': motivo,
                'delta': delta,
                'tema_principal': tema_principal,
                'temas': temas,
                'descripcion': desc
            })
        elif delta > 1:  # Quejas que subieron = negativo
            desc = f"Quejas de {motivo} subieron {delta:.1f}pp"
            if tema_principal:
                desc += f" (principalmente '{tema_principal}')"
            drivers_negativos.append({
                'tipo': 'queja',
                'nombre': motivo,
                'delta': delta,
                'tema_principal': tema_principal,
                'temas': temas,
                'descripcion': desc
            })
    
    # Desde productos
    if 'productos' in resultados and 'productos_clave' in resultados['productos']:
        for prod in resultados['productos']['productos_clave']:
            effect = prod.get('total_effect', 0)
            if effect > 0.3:
                drivers_positivos.append({
                    'tipo': 'producto',
                    'nombre': prod.get('nombre_original', ''),
                    'delta': effect,
                    'descripcion': f"{prod.get('nombre_original', '')} aporta {effect:+.2f}pp al NPS"
                })
            elif effect < -0.3:
                drivers_negativos.append({
                    'tipo': 'producto',
                    'nombre': prod.get('nombre_original', ''),
                    'delta': effect,
                    'descripcion': f"{prod.get('nombre_original', '')} resta {abs(effect):.2f}pp al NPS"
                })
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GENERAR DATOS PARA PROMPT
    # ═══════════════════════════════════════════════════════════════════════════
    
    datos_resumen = f"""
MÉTRICAS PRINCIPALES:
- NPS: {metricas.get('nps_q1', 0):.1f} → {metricas.get('nps_q2', 0):.1f} (Δ {metricas.get('delta_nps', 0):+.1f}pp)
- Promotores: {metricas.get('pct_prom_q1', 0):.1f}% → {metricas.get('pct_prom_q2', 0):.1f}%
- Principalidad: {metricas.get('princ_q1', 0):.1f}% → {metricas.get('princ_q2', 0):.1f}% (Δ {metricas.get('delta_princ', 0):+.1f}pp)
- Seguridad: {metricas.get('seg_q1', 0):.1f}% → {metricas.get('seg_q2', 0):.1f}% (Δ {metricas.get('delta_seg', 0):+.1f}pp)

DRIVERS POSITIVOS:
{chr(10).join(['• ' + d['descripcion'] for d in drivers_positivos[:5]]) if drivers_positivos else '• Sin drivers positivos significativos'}

DRIVERS NEGATIVOS:
{chr(10).join(['• ' + d['descripcion'] for d in drivers_negativos[:5]]) if drivers_negativos else '• Sin drivers negativos significativos'}
"""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # GENERAR PROMPT COMPLETO
    # ═══════════════════════════════════════════════════════════════════════════
    
    prompt_final = PROMPT_SENIOR_ANALYST.format(
        datos_resumen=datos_resumen,
        nps_q1=metricas.get('nps_q1', 0),
        nps_q2=metricas.get('nps_q2', 0),
        delta_nps=metricas.get('delta_nps', 0)
    )
    
    if verbose:
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE MÉTRICAS")
        print("=" * 80)
        print(datos_resumen)
        
        print("\n" + "=" * 80)
        print("📝 PROMPT PARA CURSOR (SENIOR ANALYST)")
        print("=" * 80)
        print(prompt_final[:2000] + "..." if len(prompt_final) > 2000 else prompt_final)
        
        print("\n" + "=" * 80)
        print("✅ PARTE 12 OK - Datos preparados para análisis de Senior Analyst")
        print("=" * 80)
        print("\n⚠️  ACCIÓN REQUERIDA: Cursor debe actuar como Senior Analyst")
        print("    y generar el diagnóstico ejecutivo siguiendo el prompt.")
    
    return {
        'metricas': metricas,
        'drivers_positivos': drivers_positivos,
        'drivers_negativos': drivers_negativos,
        'prompt_senior_analyst': prompt_final,
        'datos_resumen': datos_resumen
    }


def consolidar_para_html(resultados, resumen_ejecutivo, config):
    """
    Consolida todos los datos para generación del HTML final.
    
    Args:
        resultados: Dict con resultados de todas las partes
        resumen_ejecutivo: Resultado de generar_resumen_ejecutivo
        config: Diccionario de configuración
        
    Returns:
        dict: Datos consolidados para HTML
    """
    
    player = config['player']
    BANDERA = config['site_bandera']
    NOMBRE_PAIS = config['site_nombre']
    q_ant = config['periodo_1']
    q_act = config['periodo_2']
    
    html_data = {
        'titulo': f"Resumen NPS {player} {q_act}",
        'subtitulo': f"{BANDERA} {NOMBRE_PAIS} | {q_ant} vs {q_act}",
        'fecha_generacion': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'metricas': resumen_ejecutivo['metricas'],
        'drivers_positivos': resumen_ejecutivo['drivers_positivos'][:5],
        'drivers_negativos': resumen_ejecutivo['drivers_negativos'][:5],
        'secciones': {}
    }
    
    # Agregar secciones si existen
    if 'causas_raiz' in resultados:
        html_data['secciones']['causas_raiz'] = resultados['causas_raiz']
    
    if 'promotores' in resultados:
        html_data['secciones']['promotores'] = resultados['promotores']
    
    if 'productos' in resultados:
        html_data['secciones']['productos'] = resultados['productos']
    
    if 'principalidad' in resultados:
        html_data['secciones']['principalidad'] = resultados['principalidad']
    
    if 'seguridad' in resultados:
        html_data['secciones']['seguridad'] = resultados['seguridad']
    
    return html_data


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    
    from parte1_carga_datos import cargar_datos
    
    print("\n" + "=" * 70)
    print("🧪 PRUEBA PARTE 12: SENIOR ANALYST")
    print("=" * 70)
    
    try:
        resultado_carga = cargar_datos(verbose=False)
        config = resultado_carga['config']
        
        # Simular resultados de partes anteriores
        resultados = {
            'nps': {
                'nps_q1': 61.2,
                'nps_q2': 61.6,
                'delta_nps': 0.4
            },
            'promotores': {
                'pct_prom_q1': 69.5,
                'pct_prom_q2': 70.4
            },
            'causas_raiz': {
                'waterfall_data': [
                    {'motivo': 'Financiamiento', 'delta': 2.5, 'pct_q2': 15.0},
                    {'motivo': 'Rendimientos', 'delta': -1.8, 'pct_q2': 12.0},
                    {'motivo': 'Seguridad', 'delta': 1.2, 'pct_q2': 5.0}
                ]
            },
            'productos': {
                'productos_clave': [
                    {'nombre_original': 'Rendimentos', 'total_effect': -0.91},
                    {'nombre_original': 'Cartão de crédito', 'total_effect': 0.98}
                ]
            },
            'principalidad': {
                'player_principalidad': {
                    'princ_q1': 30.2,
                    'princ_q2': 27.6,
                    'delta': -2.6
                }
            },
            'seguridad': {
                'player_seguridad': {
                    'seg_q1': 89.5,
                    'seg_q2': 88.6,
                    'delta': -0.9
                }
            }
        }
        
        resumen = generar_resumen_ejecutivo(resultados, config, verbose=True)
        
        print("\n📋 Variables exportadas:")
        print(f"   metricas: {len(resumen['metricas'])} campos")
        print(f"   drivers_positivos: {len(resumen['drivers_positivos'])}")
        print(f"   drivers_negativos: {len(resumen['drivers_negativos'])}")
        
        print("\n✅ Prueba PARTE 12 completada")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
