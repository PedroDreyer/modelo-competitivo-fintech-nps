#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para aplicar el patch de checkpoint automático de noticias.
"""

import re
import sys

def patch_ejecutar_modelo():
    file_path = "scripts/ejecutar_modelo.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Buscar la línea que contiene "resultados['sugerencias_busqueda'] = sugerencias"
    insert_idx = None
    for i, line in enumerate(lines):
        if "resultados['sugerencias_busqueda'] = sugerencias" in line:
            insert_idx = i + 1
            break

    if insert_idx is None:
        print(f"ERROR: No se encontro la linea en {file_path}")
        return False

    # Buscar donde termina el bloque actual (return resultados)
    end_idx = None
    for i in range(insert_idx, len(lines)):
        if lines[i].strip() == "return resultados" and lines[i][0] != ' ':
            end_idx = i
            break

    if end_idx is None:
        print(f"ERROR: No se encontro el return en {file_path}")
        return False

    # Nuevo código a insertar
    new_code = '''
    # CHECKPOINT CRITICO: BUSQUEDA DE NOTICIAS
    if sugerencias['gaps_sin_noticia']:
        gaps_count = len(sugerencias['gaps_sin_noticia'])
        _print(mostrar_sugerencias_busqueda(sugerencias))

        _print("\\n" + "=" * 80)
        _print("CHECKPOINT: BUSQUEDA DE NOTICIAS REQUERIDA")
        _print("=" * 80)
        _print(f"")
        _print(f"   El modelo necesita noticias para {gaps_count} drivers significativos.")
        _print(f"")
        _print(f"   DRIVERS SIN NOTICIAS:")
        for gap in sugerencias['gaps_sin_noticia']:
            _print(f"   - {gap['driver']} ({gap['delta']:+.1f}pp)")
        _print(f"")
        _print(f"   INSTRUCCIONES PARA EL AGENTE:")
        _print(f"   1. Ejecutar busquedas con WebSearch para cada driver")
        _print(f"   2. Guardar noticias en: data/noticias_cursor_batch.json")
        _print(f"   3. Inyectar: python scripts/agregar_noticias_cursor.py")
        _print(f"   4. Re-ejecutar: python correr_modelo.py")
        _print(f"")
        _print("=" * 80)

        # Guardar para que el agente las use
        resultados['necesita_noticias'] = True
        resultados['queries_busqueda'] = sugerencias['queries']
        resultados['gaps_sin_noticia'] = sugerencias['gaps_sin_noticia']

        return resultados
    else:
        _print("   OK: Todos los drivers tienen noticias asociadas")

'''

    # Reemplazar el bloque
    new_lines = lines[:insert_idx + 1] + [new_code] + [lines[end_idx]]

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"OK: {file_path} - Checkpoint de noticias agregado")
    return True


def patch_correr_modelo():
    file_path = "correr_modelo.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar donde está el checkpoint de waterfall
    if "if not waterfall_ok:" not in content:
        print(f"ERROR: No se encontro waterfall_ok en {file_path}")
        return False

    # Buscar el sys.exit(1) después de waterfall_ok
    pattern = r"(if not waterfall_ok:.*?sys\.exit\(1\))"

    new_code = r'''\1

    # CHECKPOINT: BUSQUEDA DE NOTICIAS REQUERIDA
    if resultados.get('necesita_noticias'):
        print("\\n" + "=" * 80)
        print("PAUSA: BUSQUEDA DE NOTICIAS REQUERIDA")
        print("=" * 80)
        print("")
        print("   El modelo necesita noticias para drivers significativos.")
        print("")

        if resultados.get('queries_busqueda'):
            print("   QUERIES DE BUSQUEDA:")
            for query in resultados['queries_busqueda'][:5]:
                print(f"   - {query.get('query_principal', 'N/A')}")
            print("")

        print("   INSTRUCCIONES:")
        print("   1. Usar WebSearch para buscar noticias")
        print("   2. Guardar en: data/noticias_cursor_batch.json")
        print("   3. Ejecutar: python scripts/agregar_noticias_cursor.py")
        print("   4. Re-ejecutar: python correr_modelo.py")
        print("")
        print("=" * 80)

        sys.exit(43)'''

    content_modified = re.sub(pattern, new_code, content, flags=re.DOTALL)

    if content != content_modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_modified)
        print(f"OK: {file_path} - Manejo de exit code 43 agregado")
        return True
    else:
        print(f"ERROR: No se pudo modificar {file_path}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("APLICANDO PATCH: CHECKPOINT AUTOMATICO DE NOTICIAS")
    print("="*80 + "\n")

    success = []
    success.append(patch_ejecutar_modelo())
    success.append(patch_correr_modelo())

    print("\n" + "="*80)
    if all(success):
        print("PATCH APLICADO EXITOSAMENTE")
        print("\nEl modelo ahora:")
        print("  1. Se pausara automaticamente si faltan noticias")
        print("  2. Generara queries de busqueda")
        print("  3. Esperara a que el agente busque noticias")
        print("  4. Continuara automaticamente despues")
    else:
        print("PATCH PARCIALMENTE APLICADO")
        print("\nRevisar errores arriba")
    print("="*80 + "\n")
