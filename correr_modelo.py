# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
CORRER MODELO NPS - PUNTO DE ENTRADA PRINCIPAL
═══════════════════════════════════════════════════════════════════════════════

Este es el script principal para ejecutar el modelo NPS desde Cursor.

USO DESDE CURSOR:
    El analista dice: "Quiero ver variaciones de Mercado Pago Argentina 25Q3 vs 25Q4"
    Cursor ejecuta: python correr_modelo.py --site MLA --player "Mercado Pago" --q1 25Q3 --q2 25Q4

USO DIRECTO:
    python correr_modelo.py --site MLB --player "Mercado Pago" --q1 25Q3 --q2 25Q4
    python correr_modelo.py --site MLA --player "Ualá" --q1 25Q3 --q2 25Q4
    python correr_modelo.py  # Usa valores del config.yaml

SITES DISPONIBLES:
    - MLB: Brasil 🇧🇷
    - MLA: Argentina 🇦🇷  
    - MLM: México 🇲🇽
    - MLC: Chile 🇨🇱

PLAYERS POR SITE:
    MLB: Mercado Pago, Nubank, PicPay, Banco Inter, C6 Bank, Itaú, Bradesco, PagBank
    MLA: Mercado Pago, Ualá, Naranja X, Brubank, Personal Pay, MODO
    MLM: Mercado Pago, Nubank, BBVA, Banamex, Santander, Hey Banco, Stori, Klar, Didi
    MLC: Mercado Pago, Tenpo, MACH, Banco Estado
"""

import sys
import io
import argparse
from pathlib import Path
import yaml

# Windows: evitar UnicodeEncodeError en consola (cp1252)
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configurar paths
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

from scripts.ejecutar_modelo import ejecutar_modelo_completo
from scripts.generar_html import generar_html_completo, guardar_html


def actualizar_config_silent(site=None, player=None, q1=None, q2=None):
    """Actualiza config.yaml con los parámetros especificados (sin output)."""
    config_path = SCRIPT_DIR / "config" / "config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if site:
        config['site'] = site
    if player:
        config['player_analizar'] = player
    if q1:
        config['periodo_1'] = q1
    if q2:
        config['periodo_2'] = q2
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    return config


def main():
    """Punto de entrada principal."""
    
    parser = argparse.ArgumentParser(
        description='Ejecutar Modelo NPS Fintech',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python correr_modelo.py --site MLB --player "Mercado Pago" --q1 25Q3 --q2 25Q4
  python correr_modelo.py --site MLA --player "Ualá"
  python correr_modelo.py  # Usa config.yaml actual
        """
    )
    
    parser.add_argument('--site', type=str, choices=['MLB', 'MLA', 'MLM', 'MLC'],
                        help='Site a analizar (MLB=Brasil, MLA=Argentina, MLM=México, MLC=Chile)')
    parser.add_argument('--player', type=str,
                        help='Player/marca a analizar (ej: "Mercado Pago", "Nubank")')
    parser.add_argument('--q1', type=str,
                        help='Período anterior (ej: 25Q3)')
    parser.add_argument('--q2', type=str,
                        help='Período actual (ej: 25Q4)')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help='Mostrar detalles de ejecución (por defecto: silencioso)')
    parser.add_argument('--no-browser', action='store_true',
                        help='No abrir HTML en navegador al finalizar')
    
    args = parser.parse_args()
    
    # Modo silencioso: solo muestra inicio y resultado final
    if args.verbose:
        print("\n" + "-" * 80)
        print("🎯 MODELO NPS FINTECH - CURSOR EDITION")
        print("-" * 80)
    
    # Ejecutar modelo completo pasando parámetros directamente (sin mutar config.yaml)
    if args.verbose:
        print("\n🚀 Ejecutando modelo...")
    resultados = ejecutar_modelo_completo(
        verbose=args.verbose,
        site=args.site,
        player=args.player,
        q1=args.q1,
        q2=args.q2
    )
    
    # ══════════════════════════════════════════════════════════════════════
    # CHECKPOINT: Verificar si faltan causas raíz semánticas
    # ══════════════════════════════════════════════════════════════════════
    if resultados.get('necesita_causas_raiz'):
        prompt_path = resultados.get('prompt_causas_raiz', '')
        json_destino = resultados.get('json_destino_causas_raiz', '')
        player = resultados['config']['player']
        periodo = resultados['config']['periodo_2']
        site = resultados['config']['site']
        
        print("\n" + "=" * 80)
        print("PAUSA: ANALISIS SEMANTICO DE CAUSAS RAIZ REQUERIDO")
        print("=" * 80)
        print(f"")
        print(f"   El modelo necesita analisis semantico antes de generar el HTML.")
        print(f"   Esto asegura que las causas raiz sean de alta calidad.")
        print(f"")
        print(f"   PROMPT: {prompt_path}")
        print(f"   JSON DESTINO: {json_destino}")
        print(f"")
        print(f"   INSTRUCCIONES PARA EL AGENTE:")
        print(f"   1. Leer el prompt: {prompt_path}")
        print(f"   2. Analizar semanticamente los comentarios de cada motivo")
        print(f"   3. Guardar el JSON en: {json_destino}")
        print(f"   4. Re-ejecutar: python correr_modelo.py (mismos args)")
        print(f"")
        print("=" * 80)
        
        # Salir con código 42 = "necesita causas raíz"
        sys.exit(42)
    
    # ══════════════════════════════════════════════════════════════════════
    # SAFEGUARD: Verificar que TODOS los componentes críticos existen
    # ══════════════════════════════════════════════════════════════════════
    causas_ok = bool(resultados.get('causas_semanticas'))
    noticias_ok = 'noticias' in resultados
    waterfall_ok = 'waterfall' in resultados
    
    if not causas_ok:
        print("\n⛔ ERROR: No se encontraron causas raíz semánticas en los resultados.")
        print("   Esto no debería pasar. Re-ejecutá el modelo.")
        sys.exit(42)
    
    if not waterfall_ok:
        print("\n⛔ ERROR: No se encontró el waterfall de quejas.")
        sys.exit(1)
    
    # Generar HTML
    if args.verbose:
        print("\n📄 Generando HTML...")
    html = generar_html_completo(resultados)
    
    player = resultados['config']['player']
    periodo = resultados['config']['periodo_2']
    site = resultados['config']['site']
    
    filepath = guardar_html(html, player, periodo)
    
    # Abrir en navegador
    if not args.no_browser:
        import subprocess
        try:
            subprocess.Popen(['start', '', filepath], shell=True)
        except:
            pass
    
    # Resultado final (siempre se muestra)
    print("\n" + "-" * 80)
    print(f"✅ MODELO NPS COMPLETADO")
    print(f"   📊 {player} ({site})")
    print(f"   📅 {resultados['config']['periodo_1']} → {periodo}")
    nps_q1 = resultados.get('nps', {}).get('nps_q1', 0)
    nps_q2 = resultados.get('nps', {}).get('nps_q2', 0)
    delta = nps_q2 - nps_q1
    print(f"   📈 NPS: {nps_q1:.1f} → {nps_q2:.1f} ({delta:+.1f}pp)")
    print(f"   📄 {filepath}")
    print("-" * 80 + "\n")
    
    # Retornar para uso programático
    return {
        'resultados': resultados,
        'html_path': filepath
    }


if __name__ == "__main__":
    main()
