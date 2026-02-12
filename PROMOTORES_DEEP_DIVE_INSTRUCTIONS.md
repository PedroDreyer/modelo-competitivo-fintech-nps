# 🌟 Deep Dive para Promotores - Instrucciones de Implementación

## ✅ Completado

### 1. Función de Carga de Causas Raíz Semánticas para Promotores
**Archivo**: `scripts/analisis_automatico.py`
**Status**: ✅ COMPLETADO

Se agregó la función `cargar_causas_raiz_semanticas_promotores()` que carga el JSON con análisis semántico de promotores:
- Formato del archivo: `causas_raiz_semantico_promotores_{player}_{site}_{q_act}.json`
- Validación estricta de metadata (player, site, quarter)
- Retorna dict con estructura `{motivo: [causas_raiz]}`

### 2. Import en Ejecutar Modelo
**Archivo**: `scripts/ejecutar_modelo.py` (línea 73)
**Status**: ✅ COMPLETADO

Se agregó el import:
```python
from analisis_automatico import (
    ...
    cargar_causas_raiz_semanticas,
    cargar_causas_raiz_semanticas_promotores  # ← NUEVO
)
```

---

## ⏳ Pendiente de Implementación Manual

### 3. Checkpoint para Causas Raíz Semánticas de Promotores
**Archivo**: `scripts/ejecutar_modelo.py`
**Ubicación**: Después de línea 274 (después de preparar análisis semántico promotores)

**Código a agregar**:
```python
    # =========================================================================
    # CHECKPOINT: CAUSAS RAIZ SEMANTICAS PROMOTORES (opcional pero recomendado)
    # =========================================================================
    _print("\n🧠 CHECKPOINT: Verificando causas raiz semanticas promotores...")

    causas_semanticas_promotores = cargar_causas_raiz_semanticas_promotores(player, q_act, site=site)
    if causas_semanticas_promotores:
        _print(f"   ✅ Causas raiz semanticas promotores OK: {len(causas_semanticas_promotores)} motivos")
        _print(f"       Archivo: causas_raiz_semantico_promotores_{player}_{site}_{q_act}.json")
        resultados['causas_semanticas_promotores'] = causas_semanticas_promotores
    else:
        # NOTA: Para promotores es opcional - el modelo continúa sin deep dive semántico
        _print(f"   ⚠️  Causas raiz semanticas promotores no encontradas (opcional)")
        _print(f"       Para deep dive completo, generar: data/causas_raiz_semantico_promotores_{player}_{site}_{q_act}.json")
        _print(f"       Prompt disponible en: {resultado_semantico_prom.get('prompt_path', 'N/A')}")
        resultados['causas_semanticas_promotores'] = {}
```

---

## 🎯 Siguiente Fase: Visualización en HTML

### 4. Función para Obtener Causas Raíz de Promotor
**Archivo**: `scripts/generar_html.py`
**Ubicación**: Cerca de `_obtener_causa_raiz_top()` (línea ~1090)

**Código a agregar**:
```python
def _obtener_causa_raiz_top_promotor(motivo: str, causas_semanticas_promotores: dict = None) -> str:
    """
    Obtiene la causa raíz #1 para un motivo POSITIVO de promotor.

    Similar a _obtener_causa_raiz_top() pero para satisfacción.

    Args:
        motivo: Motivo de satisfacción (ej: "Facilidad de uso")
        causas_semanticas_promotores: Dict {motivo: [causas]}

    Returns:
        str: Título de la causa raíz principal o '' si no hay
    """
    if not causas_semanticas_promotores or not motivo:
        return ''

    motivo_norm = motivo.lower().strip()

    # Buscar match exacto o parcial
    for motivo_key, causas in causas_semanticas_promotores.items():
        motivo_key_norm = motivo_key.lower().strip()

        if motivo_norm in motivo_key_norm or motivo_key_norm in motivo_norm:
            if causas and len(causas) > 0:
                # Retornar la causa #1
                causa_top = causas[0]
                return causa_top.get('titulo', '')

    return ''
```

### 5. Enhancing el Acordeón de Promotores
**Archivo**: `scripts/generar_html.py`
**Función**: `_generar_acordeon_promotor()` (línea ~2493)

**Modificación necesaria**: Agregar sección de "Causas Raíz Semánticas" similar a los detractores:

```python
def _generar_acordeon_promotor(motivo_data, q_ant, q_act, comentarios_promotores=None, causas_semanticas=None):
    """
    Genera un acordeón con deep dive de un motivo de promotor.

    Args:
        ...
        causas_semanticas: Dict con causas raíz semánticas de promotores (NUEVO)
    """
    # ... código existente ...

    # NUEVA SECCIÓN: Causas Raíz Semánticas (si existen)
    if causas_semanticas:
        motivo_norm = motivo_data.get('motivo', '').lower().strip()
        causas = None

        # Buscar causas para este motivo
        for motivo_key, causas_list in causas_semanticas.items():
            if motivo_norm in motivo_key.lower() or motivo_key.lower() in motivo_norm:
                causas = causas_list
                break

        if causas:
            html += f'''
            <div style="margin-top: 20px; padding: 15px; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 8px; border-left: 4px solid #10b981;">
                <div style="font-weight: 600; font-size: 13px; color: #065f46; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                    <span>🔍</span>
                    <span>¿Por qué nos recomiendan en "{motivo_data.get('motivo', '')}"?</span>
                </div>
            '''

            for i, causa in enumerate(causas[:3], 1):  # Top 3 causas
                titulo = causa.get('titulo', '')
                descripcion = causa.get('descripcion', '')
                ejemplos = causa.get('ejemplos', [])

                html += f'''
                <div style="margin-bottom: 12px; padding: 10px; background: white; border-radius: 6px;">
                    <div style="font-weight: 600; font-size: 12px; color: #047857; margin-bottom: 4px;">
                        {i}. {titulo}
                    </div>
                '''

                if descripcion:
                    html += f'<div style="font-size: 11px; color: #064e3b; margin-bottom: 6px;">{descripcion}</div>'

                if ejemplos:
                    html += '<div style="font-size: 10px; color: #065f46; font-style: italic; margin-top: 4px;">'
                    for ej in ejemplos[:2]:  # Max 2 ejemplos
                        html += f'<div style="margin-bottom: 2px;">💬 "{ej}"</div>'
                    html += '</div>'

                html += '</div>'

            html += '</div>'

    # ... resto del código existente ...
```

### 6. Modificar la Llamada al Acordeón
**Archivo**: `scripts/generar_html.py`
**Función**: `_generar_promotores_resumen()` (línea ~2599)

**Modificación**:
```python
def _generar_promotores_resumen(resultados, TXT, q_ant, q_act):
    # ... código existente ...

    # NUEVO: Obtener causas semánticas de promotores
    causas_semanticas_promotores = resultados.get('causas_semanticas_promotores', {})

    # Generar acordeones
    for motivo_data in motivos_lista:
        acordeon_html = _generar_acordeon_promotor(
            motivo_data,
            q_ant,
            q_act,
            comentarios_promotores=comentarios_prom,
            causas_semanticas=causas_semanticas_promotores  # ← NUEVO parámetro
        )
        acordeones += acordeon_html

    # ... resto del código ...
```

---

## 📋 Checklist de Implementación

- [x] Función `cargar_causas_raiz_semanticas_promotores()` en analisis_automatico.py
- [x] Import en ejecutar_modelo.py
- [ ] Checkpoint en ejecutar_modelo.py (línea 274)
- [ ] Función `_obtener_causa_raiz_top_promotor()` en generar_html.py
- [ ] Modificar `_generar_acordeon_promotor()` para incluir causas semánticas
- [ ] Modificar `_generar_promotores_resumen()` para pasar causas semánticas
- [ ] Testing con archivo de ejemplo `causas_raiz_semantico_promotores_{player}_{site}_{q}.json`

---

## 🧪 Testing

### Crear archivo de prueba:
```json
{
  "metadata": {
    "player": "Nubank",
    "site": "MLM",
    "quarter": "25Q4",
    "fecha_generacion": "2025-01-15",
    "tipo": "promotores"
  },
  "causas_por_motivo": {
    "Facilidad de uso": [
      {
        "titulo": "App intuitiva y rápida",
        "descripcion": "Los usuarios destacan la interfaz limpia y la velocidad de la aplicación",
        "ejemplos": [
          "La app es super fácil de usar",
          "Todo es muy intuitivo y rápido"
        ]
      },
      {
        "titulo": "Proceso de registro simple",
        "descripcion": "Apertura de cuenta sin complicaciones",
        "ejemplos": [
          "Me dieron la tarjeta en 5 minutos",
          "Registro muy fácil"
        ]
      }
    ],
    "Rendimientos": [
      {
        "titulo": "Rendimientos competitivos vs bancos tradicionales",
        "descripcion": "Ofrece mejores tasas que la competencia",
        "ejemplos": [
          "Rinde mejor que otros bancos",
          "Los intereses son buenos"
        ]
      }
    ]
  }
}
```

**Ubicación**: `data/causas_raiz_semantico_promotores_Nubank_MLM_25Q4.json`

---

## 🎯 Beneficios del Deep Dive de Promotores

1. **Simetría con Detractores**: Misma metodología para ambos extremos del NPS
2. **Insights Accionables**: Entender qué hacer MÁS (no solo qué arreglar)
3. **Triangulación Completa**: Combinar satisfacción con noticias positivas
4. **Storytelling Robusto**: Narrativa balanceada (no solo problemas)
5. **Benchmarking Competitivo**: Identificar fortalezas para defender vs competencia

---

## 📞 Soporte

Para dudas sobre la implementación:
- Revisar implementación análoga para detractores en `_generar_acordeon_causa_raiz()`
- Verificar estructura del JSON semántico en `parte7_causas_raiz.py`
- Testing con diferentes players y sites antes de producción
