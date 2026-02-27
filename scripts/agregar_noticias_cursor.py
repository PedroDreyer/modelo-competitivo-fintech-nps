#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper script para que Cursor inyecte noticias al cache en batch.

Uso:
    python scripts/agregar_noticias_cursor.py --file data/noticias_cursor_batch.json

El archivo JSON de batch debe tener la estructura:
{
    "site": "MLM",
    "player": "Nubank",
    "noticias": [
        {
            "titulo": "Nubank lanza nueva tarjeta en México",
            "fuente": "El Economista",
            "url": "https://...",
            "resumen": "Nubank anunció el lanzamiento...",
            "categoria_relacionada": "Financiamiento",
            "impacto_esperado": "positivo",
            "fecha": "2025-04"
        },
        ...
    ]
}
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.analisis_automatico import agregar_noticia_a_cache


def main():
    parser = argparse.ArgumentParser(
        description='Inyectar noticias de Cursor al cache del modelo NPS'
    )
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Ruta al archivo JSON con las noticias (formato batch)'
    )
    args = parser.parse_args()

    # Leer archivo batch
    batch_path = Path(args.file)
    if not batch_path.exists():
        print(f"[ERROR] Archivo no encontrado: {batch_path}")
        sys.exit(1)

    with open(batch_path, 'r', encoding='utf-8') as f:
        batch = json.load(f)

    site = batch.get('site', '')
    player = batch.get('player', '')
    noticias = batch.get('noticias', [])

    if not site or not player:
        print("[ERROR] El archivo batch debe incluir 'site' y 'player'")
        sys.exit(1)

    if not noticias:
        print("[WARN] No hay noticias en el archivo batch")
        sys.exit(0)

    print(f"[CURSOR NEWS] Inyectando {len(noticias)} noticias para {player} ({site})...")

    exitos = 0
    errores = 0

    for i, noticia in enumerate(noticias, 1):
        titulo = noticia.get('titulo', '')
        if not titulo:
            print(f"  [{i}] SKIP: sin titulo")
            continue

        ok = agregar_noticia_a_cache(
            site=site,
            player=player,
            titulo=titulo,
            fuente=noticia.get('fuente', 'web'),
            url=noticia.get('url', ''),
            resumen=noticia.get('resumen', ''),
            categoria_relacionada=noticia.get('categoria_relacionada', 'General'),
            impacto_esperado=noticia.get('impacto_esperado', 'neutro'),
            fecha=noticia.get('fecha', '')
        )

        if ok:
            exitos += 1
            print(f"  [{i}] OK: {titulo[:70]}...")
        else:
            errores += 1
            print(f"  [{i}] ERROR: {titulo[:70]}...")

    print(f"\n[RESULTADO] {exitos} noticias agregadas, {errores} errores")

    # Limpiar archivo batch temporal
    try:
        batch_path.unlink()
        print(f"[CLEANUP] Archivo batch eliminado: {batch_path}")
    except Exception:
        pass


if __name__ == '__main__':
    main()
