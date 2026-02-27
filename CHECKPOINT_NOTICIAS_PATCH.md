# PATCH: Agregar Checkpoint Automático de Noticias

## Ubicación: scripts/ejecutar_modelo.py

### Líneas 450-467: REEMPLAZAR ESTA SECCIÓN

**CÓDIGO ACTUAL** (líneas 450-467):
```python
    resultados['sugerencias_busqueda'] = sugerencias

    # Mostrar sugerencias si hay gaps
    if sugerencias['gaps_sin_noticia']:
        _print(mostrar_sugerencias_busqueda(sugerencias))
    else:
        _print("   ✅ Todos los drivers principales tienen noticias asociadas")

    _print("\n" + "═" * 80)
    _print("⚠️  PRÓXIMOS PASOS:")
    _print("   1. Revisar las SUGERENCIAS DE BÚSQUEDA arriba (si las hay)")
    _print("   2. Usar Cursor WebSearch para buscar noticias de los gaps")
    _print("   3. Agregar noticias con: agregar_noticia_a_cache(site, player, ...)")
    _print("   4. Re-ejecutar modelo para incluir nuevas noticias")
    _print("   5. Generar HTML final con generar_html()")
    _print("═" * 80)

    return resultados
```

**CÓDIGO NUEVO** (reemplazar todo lo anterior con esto):
```python
    resultados['sugerencias_busqueda'] = sugerencias

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
        return resultados
    else:
        _print("   ✅ Todos los drivers principales tienen noticias asociadas")

    return resultados
```

---

## Paso 2: Modificar `correr_modelo.py` para manejar exit code 43

### Ubicación: correr_modelo.py (después de la línea 150)

**Buscar esta sección** (alrededor de línea 150-162):
```python
    if not causas_ok:
        print("\n⛔ ERROR: No se encontraron causas raíz semánticas en los resultados.")
        print("   Esto no debería pasar. Re-ejecutá el modelo.")
        sys.exit(42)
```

**AGREGAR DESPUÉS** de ese bloque:
```python
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
        sys.exit(43)
```

---

## Paso 3: Actualizar `.cursor/rules/modelo_nps.mdc`

### Agregar al final del archivo:

```markdown
## CHECKPOINT AUTOMÁTICO: BÚSQUEDA DE NOTICIAS

Si el modelo se detiene con exit code 43 (necesita noticias):

1. **Extraer queries** de los resultados
2. **Ejecutar búsquedas** con WebSearch para CADA driver sin noticia
3. **Formato de búsqueda**:
   ```
   site:{site_confiable} "{player}" "{país}" "{motivo}" 2025
   ```
4. **Guardar en JSON batch**:
   ```json
   {
     "noticias": [
       {
         "titulo": "título real de la noticia",
         "url": "URL completa",
         "fecha": "YYYY-MM-DD",
         "resumen": "resumen breve (1-2 frases)",
         "categorias": ["Seguridad"],
         "site": "MLM",
         "player": "BBVA"
       }
     ]
   }
   ```
5. **Inyectar al cache**: `python scripts/agregar_noticias_cursor.py --file data/noticias_cursor_batch.json`
6. **Re-ejecutar modelo**: El modelo continuará automáticamente

## DOMINIOS CONFIABLES POR PAÍS

- **México (MLM)**: elfinanciero.com.mx, expansion.mx, eleconomista.com.mx, forbes.com.mx
- **Brasil (MLB)**: infomoney.com.br, valor.globo.com, exame.com, moneytimes.com.br
- **Argentina (MLA)**: ambito.com, infobae.com, cronista.com, iprofesional.com

## IMPORTANTE

- NUNCA inventar noticias
- Siempre usar URLs reales de las búsquedas
- Fecha en formato YYYY-MM-DD
- Incluir solo noticias relevantes al driver identificado
```

