#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para aplicar el patch de checkpoint automático de noticias.
"""

import re

# ═══════════════════════════════════════════════════════════════════════
# PATCH 1: ejecutar_modelo.py - Agregar checkpoint de noticias
# ═══════════════════════════════════════════════════════════════════════

def patch_ejecutar_modelo():
    file_path = "scripts/ejecutar_modelo.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar la sección a reemplazar (usando regex flexible)
    pattern = r"(resultados\['sugerencias_busqueda'\] = sugerencias\s*\n\s*\n)"
    pattern += r"(.*?)"  # Todo entre sugerencias y return
    pattern += r"(\s*return resultados)"

    new_code = r"""\1
    # ══════════════════════════════════════════════════════════════════════
    # CHECKPOINT CRÍTICO: BÚSQUEDA DE NOTICIAS (igual que causas raíz)
    # ══════════════════════════════════════════════════════════════════════
    # Si hay drivers significativos SIN noticias, el modelo se DETIENE
    # para que el agente ejecute búsquedas con WebSearch automáticamente.
    # Esto garantiza triangulación completa antes de generar el HTML.

    if sugerencias['gaps_sin_noticia']:
        gaps_count = len(sugerencias['gaps_sin_noticia'])
        _print(mostrar_sugerencias_busqueda(sugerencias))

        _print("\n" + "═" * 80)
        _print("⚠️  CHECKPOINT: BÚSQUEDA DE NOTICIAS REQUERIDA")
        _print("═" * 80)
        _print(f"")
        _print(f"   El modelo necesita noticias para {gaps_count} drivers significativos.")
        _print(f"   Esto asegura triangulación completa en el reporte.")
        _print(f"")
        _print(f"   DRIVERS SIN NOTICIAS:")
        for gap in sugerencias['gaps_sin_noticia']:
            _print(f"   • {gap['driver']} ({gap['delta']:+.1f}pp)")
        _print(f"")
        _print(f"   INSTRUCCIONES PARA EL AGENTE:")
        _print(f"   1. Ejecutar búsquedas con WebSearch para cada driver")
        _print(f"   2. Las queries están en resultados['sugerencias_busqueda']")
        _print(f"   3. Guardar noticias en: data/noticias_cursor_batch.json")
        _print(f"   4. Inyectar al cache: python scripts/agregar_noticias_cursor.py")
        _print(f"   5. Re-ejecutar: python correr_modelo.py (mismos args)")
        _print(f"")
        _print("═" * 80)

        # Guardar sugerencias para que el agente las use
        resultados['necesita_noticias'] = True
        resultados['queries_busqueda'] = sugerencias['queries']
        resultados['gaps_sin_noticia'] = sugerencias['gaps_sin_noticia']

        # Salir con código 43 = "necesita noticias"
\3"""

    content_modified = re.sub(pattern, new_code, content, flags=re.DOTALL)

    if content != content_modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_modified)
        print(f"✅ {file_path} - Checkpoint de noticias agregado")
        return True
    else:
        print(f"⚠️  {file_path} - No se encontró la sección a modificar")
        return False


# ═══════════════════════════════════════════════════════════════════════
# PATCH 2: correr_modelo.py - Manejar exit code 43
# ═══════════════════════════════════════════════════════════════════════

def patch_correr_modelo():
    file_path = "correr_modelo.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar dónde insertar el nuevo checkpoint (después del checkpoint de causas raíz)
    pattern = r"(if not waterfall_ok:.*?sys\.exit\(1\))"

    new_code = r"""\1

    # ══════════════════════════════════════════════════════════════════════
    # CHECKPOINT: BÚSQUEDA DE NOTICIAS REQUERIDA
    # ══════════════════════════════════════════════════════════════════════
    if resultados.get('necesita_noticias'):
        print("\n" + "=" * 80)
        print("PAUSA: BÚSQUEDA DE NOTICIAS REQUERIDA")
        print("=" * 80)
        print(f"")
        print(f"   El modelo necesita noticias para drivers significativos.")
        print(f"")

        # Mostrar queries a buscar
        if resultados.get('queries_busqueda'):
            print(f"   QUERIES DE BÚSQUEDA:")
            for query in resultados['queries_busqueda'][:5]:  # Mostrar max 5
                print(f"   • {query.get('query_principal', 'N/A')}")
            print(f"")

        print(f"   INSTRUCCIONES PARA EL AGENTE:")
        print(f"   1. Usar WebSearch para buscar noticias")
        print(f"   2. Guardar en: data/noticias_cursor_batch.json")
        print(f"   3. Ejecutar: python scripts/agregar_noticias_cursor.py")
        print(f"   4. Re-ejecutar: python correr_modelo.py (mismos args)")
        print(f"")
        print("=" * 80)

        # Salir con código 43 = "necesita noticias"
        sys.exit(43)"""

    content_modified = re.sub(pattern, new_code, content, flags=re.DOTALL)

    if content != content_modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_modified)
        print(f"✅ {file_path} - Manejo de exit code 43 agregado")
        return True
    else:
        print(f"⚠️  {file_path} - No se encontró la sección a modificar")
        return False


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*80)
    print("APLICANDO PATCH: CHECKPOINT AUTOMATICO DE NOTICIAS")
    print("="*80 + "\n")

    success = []
    success.append(patch_ejecutar_modelo())
    success.append(patch_correr_modelo())

    print("\n" + "="*80)
    if all(success):
        print("✅ PATCH APLICADO EXITOSAMENTE")
        print("\nEl modelo ahora:")
        print("  1. Se pausará automáticamente si faltan noticias")
        print("  2. Generará queries de búsqueda")
        print("  3. Esperará a que el agente busque noticias")
        print("  4. Continuará automáticamente después")
    else:
        print("⚠️  PATCH PARCIALMENTE APLICADO")
        print("\nRevisar CHECKPOINT_NOTICIAS_PATCH.md para aplicar manualmente")
    print("="*80 + "\n")
