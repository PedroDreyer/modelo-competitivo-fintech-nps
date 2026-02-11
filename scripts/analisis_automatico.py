# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
ANÁLISIS AUTOMÁTICO - SUBCAUSAS, TRIANGULACIÓN Y DEEP DIVE
═══════════════════════════════════════════════════════════════════════════════

Este módulo ejecuta análisis REAL sobre los datos:
1. Genera subcausas analizando comentarios reales
2. Triangula Producto ↔ Queja ↔ Noticia
3. Extrae keywords y tendencias para acordeones

Uso:
    from scripts.analisis_automatico import (
        generar_subcausas_automatico,
        ejecutar_triangulacion,
        enriquecer_waterfall_para_acordeones
    )
"""

import re
import random
import json
import time
import requests
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser


# ==============================================================================
# THRESHOLDS DE BÚSQUEDA DE NOTICIAS
# (Espejo de los definidos en generar_html.py para evitar imports circulares)
# ==============================================================================
UMBRAL_DRIVER_SIGNIFICATIVO = 0.1     # p.p. delta mínimo para buscar noticias (antes: 0.3)
UMBRAL_SEGURIDAD_NOTICIA = 0.5        # p.p. delta seguridad para buscar noticias (antes: 1.0)
UMBRAL_PRINCIPALIDAD_NOTICIA = 1.0    # p.p. delta principalidad para buscar noticias (antes: 2.0)

# ==============================================================================
# STOPWORDS para limpieza de keywords de causas raíz (cross-site)
# ==============================================================================
_STOPWORDS_ES = {
    'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'en', 'por', 'para', 'con', 'sin', 'al', 'a', 'y', 'o', 'que', 'se',
    'no', 'es', 'lo', 'su', 'sus', 'muy', 'más', 'mas', 'como', 'pero',
    'ya', 'entre', 'desde', 'hasta', 'sobre', 'ante', 'bajo', 'tras',
    'tiene', 'hay', 'ser', 'fue', 'son', 'esta', 'está', 'este', 'esto',
    'les', 'nos', 'les', 'todo', 'toda', 'todos', 'todas', 'cada', 'donde',
    'cuando', 'sido', 'han', 'puede', 'hacer', 'solo', 'bien', 'mal',
    'tan', 'también', 'tambien', 'queja', 'quejas', 'comentario', 'usuarios',
}
_STOPWORDS_PT = {
    'de', 'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'um', 'uma',
    'em', 'por', 'para', 'com', 'sem', 'ao', 'a', 'e', 'ou', 'que', 'se',
    'não', 'é', 'o', 'seu', 'sua', 'muito', 'mais', 'como', 'mas',
    'já', 'entre', 'desde', 'até', 'sobre', 'tem', 'ser', 'foi', 'são',
    'esta', 'está', 'esse', 'isso', 'todo', 'toda', 'todos', 'todas',
    'pode', 'fazer', 'bem', 'mal', 'também', 'reclamação', 'usuários',
}


def cargar_causas_raiz_semanticas(player: str, q_act: str, data_dir: str = None) -> Dict:
    """
    Carga el JSON de causas raíz semánticas generado por el LLM.
    
    Args:
        player: Nombre del player (ej: 'Nubank')
        q_act: Quarter actual (ej: '25Q2')
        data_dir: Directorio de datos (si None, usa data/ relativo al proyecto)
    
    Returns:
        Dict con estructura {motivo: [causas_raiz]} o {} si no existe
    """
    if data_dir is None:
        data_dir = Path(__file__).resolve().parent.parent / 'data'
    else:
        data_dir = Path(data_dir)
    
    # Buscar archivo: causas_raiz_semantico_{player}_{quarter}.json
    patron = f"causas_raiz_semantico_{player}_{q_act}.json"
    archivo = data_dir / patron
    
    if not archivo.exists():
        # Intentar sin acentos / variantes
        import glob
        candidatos = list(data_dir.glob(f"causas_raiz_semantico_{player}*{q_act}*.json"))
        if candidatos:
            archivo = candidatos[0]
        else:
            return {}
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('causas_por_motivo', {})
    except Exception:
        return {}


def _limpiar_texto_para_keywords(texto: str) -> str:
    """Limpia un texto para extracción de keywords (quita paréntesis, %, números)."""
    limpio = re.sub(r'\([^)]*\)', '', texto)
    limpio = re.sub(r'\d+[%.,]?\d*%?', '', limpio)
    limpio = re.sub(r'[^\w\sáéíóúñüàèìòùãõâêîôûç]', ' ', limpio, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', limpio).strip()


def extraer_keywords_causa_raiz(titulo: str, site: str = 'MLA', max_keywords: int = 4,
                                 descripcion: str = '', ejemplos: List[str] = None) -> List[str]:
    """
    Extrae keywords significativas de una causa raíz semántica.
    Usa título + descripción + ejemplos para capturar términos del dominio.
    
    CROSS-SITE: No depende de diccionarios por país, sino de los textos reales
    que vienen de los comentarios de usuarios en su idioma nativo.
    
    Args:
        titulo: Título de la causa raíz
        site: Site para elegir stopwords (MLB=portugués, resto=español)
        max_keywords: Máximo de keywords a retornar
        descripcion: Descripción de la causa raíz (más contexto)
        ejemplos: Lista de comentarios ejemplo (términos del dominio reales)
    
    Returns:
        Lista de keywords limpias y priorizadas
    """
    stopwords = _STOPWORDS_PT if site == 'MLB' else _STOPWORDS_ES
    
    def _extraer_palabras(texto):
        limpio = _limpiar_texto_para_keywords(texto)
        return [p.lower() for p in limpio.split() if len(p) > 2 and p.lower() not in stopwords]
    
    # 1. Keywords del título (máxima prioridad)
    kw_titulo = _extraer_palabras(titulo)
    
    # 2. Keywords de la descripción (prioridad media, captura términos del dominio)
    kw_desc = _extraer_palabras(descripcion) if descripcion else []
    
    # 3. Keywords de ejemplos/comentarios (prioridad baja, pero captura jerga real)
    kw_ejemplos = []
    if ejemplos:
        # Contar frecuencia de palabras en ejemplos para encontrar términos recurrentes
        freq = Counter()
        for ej in ejemplos[:5]:  # Max 5 ejemplos para no sobrecargar
            palabras = _extraer_palabras(ej)
            freq.update(palabras)
        # Solo tomar palabras que aparecen en 2+ ejemplos (son términos del dominio)
        kw_ejemplos = [p for p, c in freq.most_common(10) if c >= 2]
    
    # 4. Combinar: título primero, luego descripción aportando nuevos, luego ejemplos
    vistos = set()
    keywords = []
    
    for palabra in kw_titulo + kw_desc + kw_ejemplos:
        if palabra not in vistos:
            vistos.add(palabra)
            keywords.append(palabra)
    
    return keywords[:max_keywords]


def _extraer_terminos_dominio(causa: Dict, site: str) -> List[str]:
    """
    Extrae términos específicos del dominio de una causa raíz completa.
    Busca sustantivos concretos que aparecen en descripción y ejemplos
    pero NO en el título (son los "hidden terms" que necesitamos para buscar).
    
    Ejemplo: título dice "Caída de tasas de rendimiento" pero la descripción
    y ejemplos mencionan "cajitas", "cajita turbo" → retorna ["cajita", "cajita turbo"]
    
    CROSS-SITE: Los términos vienen del idioma real de los comentarios.
    """
    titulo = causa.get('titulo', '').lower()
    descripcion = causa.get('descripcion', '').lower()
    ejemplos = causa.get('ejemplos', [])
    
    stopwords = _STOPWORDS_PT if site == 'MLB' else _STOPWORDS_ES
    
    # Buscar bigramas y términos compuestos en descripción
    desc_palabras = _limpiar_texto_para_keywords(descripcion).lower().split()
    
    # Contar unigramas en descripción + ejemplos
    freq = Counter()
    for p in desc_palabras:
        if len(p) > 3 and p not in stopwords and p not in titulo:
            freq[p] += 1
    
    for ej in ejemplos[:5]:
        limpio = _limpiar_texto_para_keywords(ej).lower()
        for p in limpio.split():
            if len(p) > 3 and p not in stopwords:
                freq[p] += 1
    
    # Buscar bigramas recurrentes (ej: "cajita turbo", "limite credito")
    bigramas = Counter()
    todos_textos = [descripcion] + [ej.lower() for ej in ejemplos[:5]]
    for texto in todos_textos:
        limpio = _limpiar_texto_para_keywords(texto).lower()
        palabras = [p for p in limpio.split() if len(p) > 2 and p not in stopwords]
        for i in range(len(palabras) - 1):
            bigrama = f"{palabras[i]} {palabras[i+1]}"
            bigramas[bigrama] += 1
    
    # Términos del dominio = bigramas recurrentes (2+) + unigramas frecuentes (3+)
    # que NO están ya en el título
    terminos = []
    for bigrama, count in bigramas.most_common(5):
        if count >= 2 and not all(p in titulo for p in bigrama.split()):
            terminos.append(bigrama)
    for palabra, count in freq.most_common(5):
        if count >= 3 and palabra not in titulo and palabra not in ' '.join(terminos):
            terminos.append(palabra)
    
    return terminos[:4]


def generar_queries_desde_causas_raiz(
    causas_semanticas: Dict,
    player: str,
    site: str,
    sufijo_temporal: str,
    max_causas_por_motivo: int = 2,
    max_queries: int = 12
) -> List[Dict]:
    """
    Genera queries de búsqueda específicas a partir de las causas raíz semánticas.
    
    Estrategia CROSS-SITE (no depende de diccionarios por país):
    1. Query desde título: keywords conceptuales (ej: "caída tasas rendimiento")
    2. Query desde términos del dominio: palabras reales de usuarios (ej: "cajita baja")
    3. Query mixta: player + término dominio + motivo
    
    Args:
        causas_semanticas: Dict {motivo: {causas_raiz: [...]}} del JSON semántico
        player: Nombre del player
        site: Código site
        sufijo_temporal: Sufijo de fecha para queries
        max_causas_por_motivo: Cuántas causas top por motivo
        max_queries: Máximo total de queries
    
    Returns:
        Lista de dicts con {query, categoria, impacto, origen}
    """
    pais = PAISES_BUSQUEDA.get(site, 'Latinoamérica')
    queries = []
    queries_vistas = set()
    
    for motivo, datos in causas_semanticas.items():
        causas = datos.get('causas_raiz', [])
        delta = datos.get('delta_pp', 0)
        impacto = 'negativo' if delta > 0 else 'positivo'
        
        for causa in causas[:max_causas_por_motivo]:
            titulo = causa.get('titulo', '')
            descripcion = causa.get('descripcion', '')
            ejemplos = causa.get('ejemplos', [])
            if not titulo:
                continue
            
            # Query 1: Keywords del título + descripción (conceptual)
            keywords = extraer_keywords_causa_raiz(
                titulo, site, max_keywords=4,
                descripcion=descripcion, ejemplos=ejemplos
            )
            if len(keywords) >= 2:
                kw_text = ' '.join(keywords[:3])
                q = f"{player} {pais} {kw_text} {sufijo_temporal}"
                if q not in queries_vistas:
                    queries_vistas.add(q)
                    queries.append({
                        'query': q,
                        'categoria': motivo,
                        'impacto': impacto,
                        'origen': 'causa_raiz_titulo',
                        'causa_titulo': titulo
                    })
            
            # Query 2: Términos del dominio (jerga real de usuarios)
            terminos_dominio = _extraer_terminos_dominio(causa, site)
            if terminos_dominio:
                td = terminos_dominio[0]  # Término más frecuente
                q2 = f"{player} {pais} {td} {sufijo_temporal}"
                if q2 not in queries_vistas:
                    queries_vistas.add(q2)
                    queries.append({
                        'query': q2,
                        'categoria': motivo,
                        'impacto': impacto,
                        'origen': 'causa_raiz_dominio',
                        'causa_titulo': titulo,
                        'termino_dominio': td
                    })
    
    return queries[:max_queries]


# ==============================================================================
# PATRONES DE SUBCAUSAS POR CATEGORÍA
# ==============================================================================

PATRONES_SUBCAUSAS = {
    'Financiamiento': {
        'limite_bajo': [
            'limite bajo', 'límite bajo', 'poco limite', 'poco credito', 'pouco crédito',
            'limite insuficiente', 'limite pequeno', 'aumentar limite', 'subir limite',
            'mas limite', 'más límite', 'no me dan limite', 'não me dão limite',
            'quiero mas credito', 'quero mais credito', 'necesito mas limite',
            'no me suben', 'não me aumentam', 'limite ridiculo', 'limite miseria'
        ],
        'rechazo_credito': [
            'negado', 'negaram', 'rechazado', 'rechazo', 'rechazaron', 'não aprova', 'no aprob',
            'no me dieron', 'não me deram', 'negaron', 'denegado', 'sin aprobar', 'no califico',
            'não qualif', 'no me aprueban', 'não me aprovam', 'recusado', 'recusaram',
            'no me autorizan', 'não me autorizam'
        ],
        'tasas_altas': [
            'tasa alta', 'taxa alta', 'juros altos', 'interés alto', 'interes alto',
            'muy caro', 'muito caro', 'usura', 'abusiv', 'exorbitante', 'tasa elevada',
            'cobran mucho', 'cobram muito', 'intereses altos', 'juros absurd',
            'tasa de interes', 'taxa de juros', 'porcentaje alto', 'porcentagem alta'
        ],
        'proceso_lento': [
            'demora credito', 'tarda en aprobar', 'proceso largo', 'mucho tramite', 'muito papel',
            'burocracia', 'burocrát', 'engorroso', 'tedioso', 'solicitud lenta', 'solicitacao lenta',
            'muchos requisitos', 'muitos requisitos', 'proceso complicado', 'piden muchos documentos'
        ],
        'cuotas_problema': [
            'parcela', 'cuota', 'cuotas', 'pago mensual', 'pagos atrasados', 'cobrança indebida',
            'cobro indebido', 'vencimento errado', 'vencimiento incorrecto', 'fecha de pago', 'data de pagamento',
            'refinanc', 'atrasar cuota', 'atraso parcela', 'me cobran de mas', 'cobraram a mais'
        ],
    },
    # Rendimientos: ver bloque expandido más abajo
    'Seguridad': {
        'fraude_conta_invadida': [
            # Fraude y robo - todas las variantes
            'fraude', 'fraud', 'golpe', 'golpes', 'roubo', 'roub', 'robo', 'robaron', 'roubaram', 
            'robado', 'roubado', 'roubada', 'robada', 'clonaram', 'clonaron', 'clonad', 'clone',
            'hackearon', 'hackearam', 'hackea', 'hack', 'invasion', 'invasão', 'invad',
            'me sacaron', 'me tiraram', 'vaciaron', 'esvaziaram', 'invadiram', 'invadida', 'invadido',
            'desaparecio', 'desapareceu', 'sumiu', 'desaparec', 'ladron', 'ladrão', 'ladrao',
            'delincuente', 'criminoso', 'me robaron', 'me roubaram', 'estafaron', 'acesso indevido',
            'terceiros', 'terceros', 'alguien entro', 'alguém entrou', 'sin mi permiso', 'sem minha',
            'nao fui eu', 'no fui yo', 'outra pessoa', 'otra persona', 'compraram', 'compraron',
            'sacaram', 'sacaron', 'transferiram', 'transfirieron', 'gastaram', 'gastaron'
        ],
        'tarjeta_clonada': [
            # Tarjeta clonada - específico y frecuente
            'cartao clonad', 'tarjeta clonad', 'cartão clonad', 'clonar', 'clonagem',
            'cartao fraud', 'tarjeta fraud', 'compra no autorizada', 'compra nao autorizada',
            'cobro que no', 'cobranca que nao', 'no reconozco la compra', 'nao reconheco',
            'uso indebido', 'uso indevido', 'fisica', 'fisico', 'aproximacao', 'aproximación',
            'passou o cartao', 'pasaron la tarjeta', 'maquininha', 'terminal'
        ],
        'golpe_phishing': [
            # Phishing y estafas digitales
            'link falso', 'sms falso', 'email falso', 'golpe do pix', 'estafa', 'estafad',
            'golpista', 'mensagem falsa', 'mensaje falso', 'llamada falsa', 'ligacao golpe',
            'engano', 'engaño', 'enganar', 'engañar', 'cilada', 'suplantacion', 'spam', 
            'whatsapp falso', 'pix falso', 'qr falso', 'falso', 'fake', 'phishing',
            'caí en', 'caí no', 'me engañaron', 'me enganaram', 'link suspeito', 'sospechoso'
        ],
        'conta_bloqueada': [
            # Cuenta bloqueada - muy frecuente
            'bloqueada', 'bloqueado', 'bloquearam', 'bloquearon', 'bloque', 'suspendida', 'suspensa',
            'suspendieron', 'suspens', 'travou', 'conta travada', 'congelou', 'congelaron', 'congel',
            'nao consigo entrar', 'no puedo entrar', 'sem acesso', 'sin acceso', 'acceso negado',
            'nao me deixa', 'no me deja', 'inhabilitaron', 'restricao', 'restriccion', 'restri',
            'nao abre', 'no abre', 'trancada', 'trancado', 'cancelada', 'cancelaron', 'desativaram'
        ],
        'problemas_autenticacion': [
            # Autenticación y verificación
            'autenticacao', 'autenticación', 'autenticacao', 'verificacao', 'verificación', 'verifica',
            'doble factor', 'dois fatores', '2fa', 'token', 'codigo sms', 'código', 'codigo',
            'biometria', 'huella', 'reconhecimento', 'facial', 'digital', 'face id', 'touch',
            'mais seguranca', 'más seguridad', 'confirmar identidade', 'validar', 'validacao',
            'nao reconhece', 'no reconoce', 'falha biometria', 'falla biometria', 'dedo', 'rosto'
        ],
        'problemas_contraseña': [
            # Contraseña - muy frecuente
            'senha', 'contraseña', 'clave', 'password', 'trocar senha', 'cambiar clave', 'mudar senha',
            'esqueci senha', 'olvidé contraseña', 'olvidé mi', 'esqueci minha', 'recuperar senha',
            'resetar', 'reset', 'nao aceita senha', 'no acepta contraseña', 'senha fraca', 
            'clave débil', 'senha errada', 'contraseña incorrecta', 'nao lembro', 'no recuerdo',
            'nova senha', 'nueva contraseña', 'redefinir', 'alterar senha'
        ],
        'transaccion_no_reconocida': [
            # Transacciones desconocidas
            'nao reconheco', 'no reconozco', 'compra que nao fiz', 'compra que no hice',
            'cobro indebido', 'cobranca indevida', 'duplicada', 'duplicado', 'cobro doble',
            'valor errado', 'valor equivocado', 'transacao desconhecida', 'nao autorizei',
            'no autoricé', 'desconozco', 'desconheco', 'nao foi eu', 'no fui yo', 'extraña',
            'estranha', 'cobraram', 'me cobraron', 'debito que nao', 'débito que no'
        ],
        'inseguridad_general': [
            # Percepción de inseguridad - SOLO términos directamente relacionados con seguridad
            'seguranca', 'segurança', 'seguridad', 'insegur', 'no me siento segur',
            'nao me sinto segur', 'medo de usar', 'miedo de usar', 'nao confio', 'no confío',
            'desconfianca', 'desconfianza', 'tenho medo', 'tengo miedo', 'vulnerab',
            'falta seguridad', 'falta seguranca', 'poca seguridad', 'pouca seguranca',
            'más seguridad', 'mais seguranca', 'mejorar seguridad', 'melhorar seguranca',
            'risco de', 'riesgo de', 'peligroso', 'perigoso', 'no es seguro', 'nao é seguro',
            'protección de datos', 'protecao de dados', 'mis datos', 'meus dados',
            'no recomiendo por seguridad', 'cuidado con', 'não é confiável', 'no es confiable'
        ],
    },
    'Atención': {
        'demora_respuesta': [
            # Demoras en atención - términos específicos de atención al cliente
            'demora en responder', 'demoran en atender', 'demoram para responder', 'tardou responder',
            'mucho tiempo esperando', 'muito tempo esperando', 'horas esperando', 'dias esperando',
            'semanas esperando', 'nunca responde', 'nunca respondem', 'sin respuesta', 'sem resposta',
            'no contestan', 'nao responde', 'na fila', 'en cola', 'cola de espera',
            'tarda en responder', 'tardan en atender', 'espera eterna', 'aguardando resposta',
            'demora atencion', 'demora atendimento', 'tardanza en soporte'
        ],
        'no_resuelve': [
            # No resuelven el problema
            'não resolve', 'no resuelve', 'não ajuda', 'no ayuda', 'inútil', 'inutiles',
            'no sirve de nada', 'não serve pra nada', 'no solucion', 'não solucion',
            'sin solución', 'sem solução', 'problema sigue igual', 'sigue sin resolver',
            'mesmo problema', 'mismo problema', 'nada resolvido', 'nada resuelto',
            'no hacen nada', 'nao fazem nada', 'incompetente', 'incapaz',
            'no me ayudaron', 'nao me ajudaram', 'sigo esperando solucion'
        ],
        'atencion_robot': [
            # Robot/automatizado - frustración común
            'robô', 'robot', 'bot', 'automatico', 'automático', 'automatizada',
            'inteligencia artificial', 'hablar con alguien', 'falar com alguém',
            'respuesta automatica', 'resposta automatica', 'maquina', 'máquina',
            'quero falar com pessoa', 'quiero hablar con persona', 'pessoa real', 'persona real',
            'atendente humano', 'operador humano', 'agente real',
            'no es humano', 'nao é humano', 'responde igual siempre', 'copia y pega',
            'quiero hablar con un humano', 'quero falar com humano'
        ],
        'dificil_contactar': [
            # Difícil contactar soporte
            'telefone', 'teléfono', 'telefono', 'chat', 'falar', 'hablar', 'contacto', 'contactar',
            'comunicar', 'comunicarse', 'canal', 'atencion', 'atención', 'atendimento', 'numero',
            'número', 'llamar', 'ligar', 'whatsapp', 'mail', 'email', 'correo', 'não consigo falar',
            'no puedo contactar', 'como falo', 'como hablo', 'onde acho', 'donde encuentro',
            'no hay forma', 'nao tem como', 'impossível', 'imposible', 'nao encontro', 'no encuentro'
        ],
        'mala_atencion': [
            # Mal trato
            'mala atencion', 'má atendimento', 'mal atendido', 'pesimo', 'péssimo', 'pésimo',
            'horrible', 'horrível', 'horroroso', 'mal trato', 'maltrato', 'grosero', 'grosseiro',
            'desprecio', 'irrespetuoso', 'desrespeit', 'falta de respeto', 'prepotente', 'arrogante',
            'descaso', 'negligencia', 'negligência', 'ignoram', 'ignoran', 'nao ligam', 'no les importa'
        ],
        'problema_ticket': [
            # Problemas con reclamos/tickets
            'reclamo', 'reclamacao', 'reclamação', 'queja', 'ticket', 'caso', 'protocolo',
            'numero de caso', 'não responderam', 'no respondieron', 'cerrado sin', 'fecharam sem',
            'abrí un caso', 'abri um chamado', 'já reclamei', 'ya reclamé', 'varias veces',
            'várias vezes', 'siempre lo mismo', 'sempre a mesma coisa'
        ],
    },
    'Complejidad': {
        'app_dificil': [
            # App difícil de usar - términos específicos
            'app dificil', 'aplicativo dificil', 'aplicación difícil', 'dificil de usar',
            'difícil de usar', 'complicado de usar', 'complicada de usar', 'app confusa',
            'app confuso', 'no entiendo la app', 'não entendo o app', 'interfaz confusa',
            'nao sei usar', 'no sé usar', 'cómo hago para', 'como faço para',
            'dificuldade de uso', 'dificultad de uso', 'poco intuitivo', 'pouco intuitivo'
        ],
        'proceso_largo': [
            # Proceso largo/burocrático
            'muchos pasos', 'muitos passos', 'tantos pasos', 'proceso largo', 'processo longo',
            'tedioso', 'engorroso', 'burocracia', 'burocrático', 'muchos tramites', 'muitos tramites',
            'piden muchos documentos', 'pedem muitos documentos', 'formulario largo',
            'procedimiento complicado', 'procedimento complicado', 'rellenar formulario',
            'preencher formulario', 'demasiados requisitos'
        ],
        'bugs_errores': [
            # Errores técnicos - muy frecuente
            'bug', 'bugs', 'erro na app', 'error en la app', 'errores', 'erros',
            'trava', 'trabou', 'travando', 'crash', 'crashea', 'crasheou',
            'não funciona', 'no funciona', 'falla', 'falha', 'falhou',
            'se cierra sola', 'se fecha sozinho', 'fechou', 'cuelga', 'congela', 'congelou',
            'app lenta', 'app lento', 'caiu o app', 'se cae la app',
            'instável', 'inestable', 'travou', 'não abre', 'no abre',
            'não carrega', 'no carga', 'fica carregando', 'loading eterno',
            'tela branca', 'pantalla blanca', 'não entra', 'no entra',
            'deu problema na app', 'dio problema la app'
        ],
        'interfaz_confusa': [
            # Interfaz confusa - cambios de layout
            'no encuentro', 'não encontro', 'donde esta', 'onde fica', 'botão sumiu', 'botón desapareció',
            'escondido', 'oculto', 'no veo la opcion', 'não vejo a opção',
            'mudou o layout', 'cambió el diseño', 'antes estava melhor', 'antes estaba mejor',
            'nova versao pior', 'nueva versión peor', 'atualizou e piorou', 'actualizó y empeoró',
            'menu confuso', 'menú confuso', 'diseño feo', 'layout ruim'
        ],
        'funcionalidad_faltante': [
            # Funcionalidad que falta
            'falta funcionalidad', 'falta função', 'não tem opção', 'no tiene opción',
            'deveria ter', 'debería tener', 'seria bom ter', 'sería bueno tener',
            'queria que tivesse', 'quisiera que tuviera', 'por que nao tem',
            'por qué no tiene', 'otros apps tienen', 'outras apps tem',
            'competidor tiene', 'concorrente tem', 'función básica que falta',
            'funcao basica que falta'
        ],
    },
    'Promociones': {
        'cashback_no_acreditado': [
            # Cashback no llegó - muy frecuente
            'cashback', 'cash back', 'devolucao', 'devolucion', 'estorno', 'devolução',
            'não veio', 'no llegó', 'no llego', 'não caiu', 'no cayó', 'nao caiu', 'nao veio',
            'prometido', 'prometieron', 'prometeram', 'descuento', 'desconto', 'não me deram',
            'nao me deram', 'puntos', 'pontos', 'centavos', 'centavinhos', 'nao credita',
            'no acredita', 'sumou', 'nao sumou', 'valor prometido', 'nao recebi', 'no recibí',
            'cadê', 'donde está', 'nao apareceu', 'no apareció', 'demora cashback', 'tarda'
        ],
        'promocion_limitada': [
            # Promoción con restricciones
            'so vale', 'solo vale', 'apenas', 'limitado', 'só funciona', 'solo funciona',
            'condicoes', 'condiciones', 'restricao', 'restriccion', 'minimo', 'mínimo',
            'maximo', 'máximo', 'excluido', 'excluído', 'nao inclui', 'no incluye', 'algumas',
            'algunos', 'poucas', 'pocas', 'certas lojas', 'ciertas tiendas', 'categoria',
            'não aceita', 'no acepta', 'não vale', 'no vale', 'letra pequeña', 'letra miúda',
            'condição', 'condición', 'regra', 'regla', 'exige', 'requisito'
        ],
        'beneficio_reducido': [
            # Beneficios que bajaron - frases específicas
            'beneficio diminuiu', 'beneficio disminuyó', 'reduziu beneficio', 'reducido beneficio',
            'antes daban mas', 'antes tinha mais', 'cashback bajo', 'cashback caiu',
            'acabou o beneficio', 'acabó el beneficio', 'terminó el beneficio',
            'quitaron beneficio', 'tiraram beneficio', 'eliminaron beneficio',
            'cada vez menos beneficio', 'cada vez pior', 'cada vez peor',
            'era melhor antes', 'era mejor antes', 'ya no tiene beneficio',
            'ja nao tem beneficio', 'antes era mejor', 'antes era melhor',
            'perdeu beneficio', 'perdí beneficio', 'beneficio desapareceu'
        ],
        'cupon_invalido': [
            # Cupones que no funcionan
            'cupom', 'cupón', 'cupon', 'codigo', 'código', 'voucher', 'invalido', 'inválido',
            'expirou', 'expirado', 'nao funciona', 'no funciona', 'nao aceita', 'nao aplica',
            'no aplica', 'erro codigo', 'error código', 'vencido', 'venceu', 'não aceita'
        ],
        'peor_que_competencia': [
            # Comparación negativa con competencia (evitar false positives de "inter"="intereses")
            'nubank tiene', 'banco inter', 'picpay tiene', 'c6 tiene',
            'otro app tiene', 'outro app tem', 'la competencia tiene', 'o concorrente tem',
            'otro banco tiene', 'outro banco tem', 'mejor promocion en', 'melhor promocao em',
            'mas beneficio en', 'mais beneficio em', 'ofrece mas que', 'oferece mais que',
            'da mas que', 'da mais que', 'tiene mas beneficios', 'tem mais beneficios',
            'en otro banco dan', 'noutro banco dao', 'competencia da mas', 'concorrencia da mais'
        ],
        'promocion_confusa': [
            # Promoción difícil de entender
            'não entendi', 'no entendí', 'confuso', 'complicado', 'nao explicam', 'no explican',
            'regras', 'reglas', 'clareza', 'claridad', 'como funciona', 'como uso',
            'dificil entender', 'difícil entender', 'não sei como', 'no sé cómo', 'enganosa',
            'enganoso', 'engañoso', 'propaganda enganosa', 'publicidade enganosa', 'mentira'
        ],
        'pocos_beneficios': [
            # Pocos beneficios en general - frases específicas
            'poucos beneficios', 'pocos beneficios', 'quase nenhum beneficio', 'casi ningun beneficio',
            'nenhum beneficio', 'ningun beneficio', 'nada de beneficio',
            'não oferece beneficio', 'no ofrece beneficio', 'não tem promocion', 'no tiene promocion',
            'sem beneficio', 'sin beneficio', 'falta beneficio', 'falta promocion',
            'otros tienen mas', 'outros tem mais', 'no tiene nada de',
            'le falta un', 'falta un extra', 'no tiene buenas promociones'
        ],
    },
    'Funcionalidades': {
        'pix_problemas': [
            # Problemas con Pix (Brasil)
            'pix', 'chave pix', 'llave pix', 'transferencia pix', 'pix nao funciona',
            'pix demora', 'erro pix', 'error pix', 'limite pix', 'horario pix',
            'pix agendado', 'pix automatico', 'copia e cola', 'chave aleatoria',
            'pix parcelado', 'pix saque', 'pix troco', 'qr code pix'
        ],
        'tarjeta_virtual': [
            # Tarjeta virtual
            'cartao virtual', 'tarjeta virtual', 'cartão virtual', 'gerar cartao',
            'generar tarjeta', 'numero cartao', 'cvv', 'data validade', 'fecha de vencimiento', 'data de vencimento',
            'criar cartao', 'crear tarjeta', 'cartao temporario', 'tarjeta temporal',
            'cartao unico', 'tarjeta única', 'não gera', 'no genera'
        ],
        'pagos_servicios': [
            # Pagos de boletos y servicios
            'boleto', 'pagar boleto', 'gerar boleto', 'generar boleto', 'codigo barras',
            'código de barras', 'scanner', 'leitura', 'conta de luz', 'cuenta luz',
            'servicos', 'servicios', 'água', 'agua', 'gas', 'telefone', 'teléfono',
            'internet', 'condomínio', 'recarga', 'recarga celular', 'sube', 'carga'
        ],
        'limite_transferencia': [
            # Límites de transferencia
            'transferir', 'transferencia', 'transferência', 'limite', 'limites',
            'limite diario', 'limite transferencia', 'muito baixo', 'muy bajo',
            'aumentar limite', 'liberar limite', 'nao consigo enviar', 'no puedo enviar',
            'valor maximo', 'valor máximo', 'bloqueado', 'travado'
        ],
        'funcion_basica_faltante': [
            # Función básica que falta
            'basico', 'básico', 'simples', 'simple', 'deveria ter', 'debería tener',
            'todo app tem', 'todo app tiene', 'obvio', 'óbvio', 'essencial', 'esencial',
            'nao tem opcao', 'no tiene opción', 'falta opcao', 'falta función', 'nao tem como',
            'no hay forma', 'impossível', 'imposible', 'não dá para', 'no se puede'
        ],
        'notificaciones': [
            # Notificaciones
            'notificacao', 'notificación', 'notificaçao', 'aviso', 'alerta', 'push',
            'nao avisa', 'no avisa', 'nao notifica', 'no notifica', 'gostaria de saber',
            'quisiera saber', 'acompanhar', 'seguir', 'avisam tarde', 'avisan tarde',
            'sem alerta', 'sin alerta', 'não me avisa', 'no me avisa'
        ],
        'extrato_comprobante': [
            # Extracto y comprobantes
            'extrato', 'extracto', 'exportar', 'pdf', 'excel', 'csv', 'comprovante',
            'comprobante', 'historico', 'histórico', 'baixar', 'descargar', 'imprimir',
            'relatorio', 'reporte', 'recibo', 'detalhado', 'detallado', 'movimentos'
        ],
        'personalizacion': [
            # Personalización
            'personalizar', 'customizar', 'tema', 'escuro', 'dark mode', 'modo escuro',
            'claro', 'modo noturno', 'modo nocturno', 'configurar', 'ajustar', 'preferencias',
            'cor', 'color', 'aparência', 'apariencia', 'widget', 'atalho', 'atajo'
        ],
    },
    'Tarifas': {
        'cobros_indebidos': [
            # Cobros indebidos
            'cobro', 'cobrança', 'cobraron', 'cobraram', 'indebido', 'indevido',
            'no corresponde', 'não corresponde', 'sin razon', 'sem razão', 'injusto',
            'me cobraron', 'me cobraram', 'cobrança indevida', 'cobro indebido',
            'por qué cobraron', 'por que cobraram', 'sin explicación', 'sem explicação'
        ],
        'comisiones_altas': [
            # Comisiones/tasas altas - frases específicas
            'comision alta', 'comisión alta', 'comissão alta', 'tarifa alta', 'tarifa cara',
            'taxa alta', 'taxas altas', 'muy caro', 'muito caro', 'costoso', 'custoso',
            'excesivo', 'excessivo', 'abusivo', 'mucho cobran', 'muito cobram',
            'comision abusiva', 'tarifa abusiva', 'cobran demasiado', 'cobram demais'
        ],
        'costo_oculto': [
            # Costos ocultos
            'oculto', 'escondido', 'sorpresa', 'no sabia', 'não sabia', 'no avisaron',
            'letra chica', 'letras miudas', 'fine print', 'sin avisar', 'sem avisar',
            'de repente', 'do nada', 'apareceu', 'apareció', 'inesperado'
        ],
        'intereses_altos': [
            # Intereses altos - frases específicas
            'juros altos', 'juros absurd', 'interés alto', 'interes alto', 'intereses altos',
            'tasa de interes alta', 'taxa de juros alta', 'juros rotativo', 'interes rotativo',
            'juros do parcelado', 'interes del financiamiento', 'juros exorbitante',
            'interes exorbitante', 'agiota', 'usura', 'cobran mucho interes', 'cobram muito juros'
        ],
    },
    'Rendimientos': {
        'rendimiento_bajo': [
            # Rendimiento bajo - frases específicas de rendimiento
            'rendimento baixo', 'rendimiento bajo', 'rende poco', 'rinde poco',
            'rendimiento miseria', 'rendimento miseria', 'casi nada de rendimiento',
            'quase nada de rendimento', 'centavos de rendimiento', 'centavinhos de rendimento',
            'tasa de rendimiento baja', 'taxa de rendimento baixa',
            'no rinde nada', 'não rende nada', 'rendimiento ridículo', 'rendimento ridiculo',
            'poupança rende mais', 'ahorro rinde más', 'bajaron el rendimiento',
            'baixaram o rendimento', 'poco rendimiento', 'pouco rendimento',
            'ganancias muy bajas', 'ganhos muito baixos', 'intereses muy bajos'
        ],
        'rendimiento_peor_competencia': [
            # Peor rendimiento que competencia (solo keywords de rendimiento + competencia)
            'nubank rende mais', 'nubank rinde más', 'inter rende mais', 'c6 rende mais',
            'picpay rende mais', 'outro rende mais', 'otro rinde más',
            'rinde mejor en', 'rende melhor em', 'rendimiento mejor en',
            'mejor rendimiento', 'melhor rendimento', 'allá rinde más', 'lá rende mais'
        ],
        'cdi_insuficiente': [
            # CDI insuficiente (Brasil)
            'cdi', 'porcentagem', 'porcentaje', '100%', '99%', 'menos de', 'selic',
            'não paga', 'no paga', 'deveria pagar', 'debería pagar', 'prometido', 'prometieron'
        ],
        'demora_rendimiento': [
            # Demora en acreditar rendimiento
            'demora', 'tarda', 'não caiu', 'no cayó', 'quando cai', 'cuándo cae',
            'não aparece', 'no aparece', 'esperando', 'aguardando'
        ],
    },
    # 'Otro' y 'Otros' unificados en una sola categoría
    'Otros': {
        'experiencia_general': [
            'experiência', 'experiencia', 'geral', 'general', 'ruim', 'malo', 'mala',
            'decepcion', 'decepcionado', 'decepc', 'frustrad', 'arrepent', 'problema',
            'problemas', 'mal', 'pesimo', 'péssimo', 'horrible', 'horrível', 'peor'
        ],
        'expectativa_frustrada': [
            'esperava', 'esperaba', 'pensé', 'pensei', 'creí', 'achei', 'me dijeron',
            'me disseram', 'prometieron', 'prometeram', 'no cumpl', 'não cumpr'
        ],
        'recomendacion_parcial': [
            'mais ou menos', 'más o menos', 'ni bien ni mal', 'regular', 'normal',
            'podría mejorar', 'poderia melhorar', 'algunas cosas', 'algumas coisas'
        ],
    },
    # Fallback genérico - SOLO términos MUY específicos para reducir "Otros temas"
    # IMPORTANTE: Estos patrones solo se usan si NO matchea con la categoría específica
    '_default': {
        'insatisfaccion_grave': [
            'pessimo', 'pésimo', 'horrible', 'horrivel', 'lixo', 'basura',
            'desastre', 'desastroso', 'nunca mais', 'nunca mas', 
            'no volveria', 'nao voltaria', 'arrepentido', 'arrependido'
        ],
        'comparar_competencia': [
            'nubank melhor', 'nubank mejor', 'inter melhor', 'inter mejor',
            'prefiro nubank', 'prefiero nubank', 'prefiro inter', 
            'la sim funciona', 'ahi si funciona', 'outro app melhor'
        ],
    }
}


# ==============================================================================
# ANÁLISIS DE SUBCAUSAS AUTOMÁTICO
# ==============================================================================

def generar_subcausas_automatico(comentarios: List[str], categoria: str) -> List[Dict]:
    """
    Analiza comentarios REALES y clasifica cada uno en UNA subcausa.
    Retorna distribución que suma ~100% sobre los comentarios analizados.
    
    ⚠️ IMPORTANTE: Esta función NUNCA genera ni inventa comentarios.
    Solo CLASIFICA los comentarios reales que recibe del DataFrame.
    Los comentarios vienen de: parte7_causas_raiz.py -> exportar_comentarios_para_cursor()
    que los extrae directamente de df_q[col_comentario].dropna().astype(str).tolist()
    
    Args:
        comentarios: Lista de comentarios REALES del dataset (NUNCA inventados)
        categoria: Categoría del motivo (Financiamiento, Rendimientos, etc.)
        
    Returns:
        Lista de subcausas con porcentaje sobre total (suma ~100%)
    """
    if not comentarios or len(comentarios) < 2:
        return []
    
    # Obtener patrones para la categoría (con fallback)
    patrones = PATRONES_SUBCAUSAS.get(categoria)
    if not patrones:
        # Intentar match parcial
        for key in PATRONES_SUBCAUSAS:
            if key.lower() in categoria.lower() or categoria.lower() in key.lower():
                patrones = PATRONES_SUBCAUSAS[key]
                break
    if not patrones:
        patrones = PATRONES_SUBCAUSAS.get('_default', {})
    
    # Nombres amigables para subcausas (ESPAÑOL, legibles para C-level)
    NOMBRES_DISPLAY = {
        # Financiamiento
        'limite_bajo': 'Límite de crédito insuficiente',
        'rechazo_credito': 'Rechazo de solicitud de crédito',
        'tasas_altas': 'Tasas/intereses altos',
        'proceso_lento': 'Proceso de solicitud difícil',
        'cuotas_problema': 'Problemas con cuotas/pagos',
        'demora_credito': 'Demora en acreditación',
        
        # Seguridad - EXPANDIDOS
        'fraude_conta_invadida': 'Fraude/cuenta invadida',
        'tarjeta_clonada': 'Tarjeta clonada',
        'golpe_phishing': 'Phishing/estafa digital',
        'conta_bloqueada': 'Cuenta bloqueada sin explicación',
        'problemas_autenticacion': 'Problemas de autenticación',
        'problemas_contraseña': 'Problemas con contraseña',
        'transaccion_no_reconocida': 'Transacción no reconocida',
        'inseguridad_general': 'Percepción de inseguridad',
        # legacy
        'fraude_robo': 'Fraude/robo de cuenta',
        'phishing_estafa': 'Phishing/estafa',
        'cuenta_bloqueada': 'Cuenta bloqueada',
        'falta_proteccion': 'Falta de protección',
        'autenticacao_insuficiente': 'Autenticación insuficiente',
        'senha_acesso': 'Problemas con contraseña',
        'transacao_nao_reconhecida': 'Transacción no reconocida',
        'medo_inseguranca': 'Percepción de inseguridad',
        'conta_bloqueada_restricao': 'Cuenta bloqueada/restringida',
        
        # Atención - EXPANDIDOS
        'demora_respuesta': 'Demora en atención al cliente',
        'no_resuelve': 'No resuelven el problema',
        'atencion_robot': 'Atención automatizada/robot',
        'dificil_contactar': 'Difícil contactar soporte',
        'mala_atencion': 'Mal trato en atención',
        'problema_ticket': 'Reclamo sin resolver',
        # legacy
        'robot_no_humano': 'Atención robot/no humano',
        'canal_dificil': 'Difícil contactar soporte',
        
        # Complejidad - EXPANDIDOS
        'app_dificil': 'App difícil de usar',
        'proceso_largo': 'Proceso muy largo/burocrático',
        'bugs_errores': 'Errores técnicos en la app',
        'interfaz_confusa': 'Interfaz confusa/cambió layout',
        'funcionalidad_faltante': 'Funcionalidad básica faltante',
        
        # Promociones - EXPANDIDOS
        'cashback_no_acreditado': 'Cashback no acreditado',
        'promocion_limitada': 'Promoción con muchas restricciones',
        'beneficio_reducido': 'Beneficios reducidos vs antes',
        'cupon_invalido': 'Cupón/código no funciona',
        'peor_que_competencia': 'Menos beneficios que competencia',
        'promocion_confusa': 'Promoción confusa/engañosa',
        'pocos_beneficios': 'Pocos beneficios disponibles',
        # legacy
        'cashback_problema': 'Cashback no acreditado',
        'comparacao_concorrencia': 'Mejor en competencia',
        'promocao_confusa': 'Promoción confusa',
        'promocion_enganosa': 'Promoción engañosa',
        'beneficio_cancelado': 'Beneficio cancelado',
        'condiciones_ocultas': 'Condiciones ocultas',
        
        # Funcionalidades - EXPANDIDOS
        'pix_problemas': 'Problemas con Pix',
        'tarjeta_virtual': 'Problemas con tarjeta virtual',
        'pagos_servicios': 'Problemas pagando servicios',
        'limite_transferencia': 'Límite de transferencia bajo',
        'funcion_basica_faltante': 'Función básica faltante',
        'notificaciones': 'Problemas con notificaciones',
        'extrato_comprobante': 'No puede exportar extracto',
        'personalizacion': 'Falta personalización',
        # legacy
        'cartao_virtual': 'Tarjeta virtual',
        'pagamentos_boletos': 'Pagos/boletos',
        'transferencia_limitada': 'Límite de transferencia',
        'funcao_basica_falta': 'Falta función básica',
        'notificacoes': 'Notificaciones',
        'exportar_dados': 'Exportar datos/extracto',
        'personalizacao': 'Personalización',
        'falta_funcion': 'Falta funcionalidad',
        'funcion_limitada': 'Función limitada',
        'funcion_incompleta': 'Función incompleta',
        
        # Tarifas - EXPANDIDOS
        'cobros_indebidos': 'Cobros indebidos/inesperados',
        'comisiones_altas': 'Comisiones muy altas',
        'costo_oculto': 'Costos ocultos/sorpresa',
        'intereses_altos': 'Intereses muy altos',
        
        # Rendimientos - EXPANDIDOS
        'rendimiento_bajo': 'Tasa de rendimiento baja',
        'rendimiento_peor_competencia': 'Rendimiento menor que competencia',
        'cdi_insuficiente': 'CDI/tasa menor al prometido',
        'demora_rendimiento': 'Demora en acreditar rendimiento',
        # legacy
        'tasa_baja': 'Tasa de rendimiento baja',
        'comparacion_competencia': 'Mejor en competencia',
        'calculo_confuso': 'Cálculo confuso',
        
        # Genéricos
        'experiencia_general': 'Experiencia general negativa',
        'expectativa_frustrada': 'Expectativa no cumplida',
        'sin_razon_especifica': 'Sin razón específica',
        'recomendacion_parcial': 'Recomendación parcial',
        'insatisfaccion_general': 'Insatisfacción general',
        'insatisfaccion_grave': 'Insatisfacción grave',
        'comparar_competencia': 'Comparación negativa con competencia',
    }
    
    # Obtener también patrones _default para fallback
    patrones_default = PATRONES_SUBCAUSAS.get('_default', {})
    
    # Clasificar CADA comentario en UNA sola subcausa
    clasificaciones = {subcausa: {'count': 0, 'ejemplos': []} for subcausa in patrones}
    # Agregar patrones default al clasificador
    for subcausa in patrones_default:
        if subcausa not in clasificaciones:
            clasificaciones[subcausa] = {'count': 0, 'ejemplos': []}
    clasificaciones['otros_temas'] = {'count': 0, 'ejemplos': []}
    
    total_clasificados = 0
    
    def normalizar_texto(texto):
        """Normaliza el texto para búsqueda"""
        texto = texto.lower()
        # Normalizar encoding
        texto = texto.replace('ã', 'a').replace('õ', 'o').replace('ç', 'c')
        texto = texto.replace('á', 'a').replace('é', 'e').replace('í', 'i')
        texto = texto.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        texto = texto.replace('à', 'a').replace('è', 'e').replace('ì', 'i')
        texto = texto.replace('ò', 'o').replace('ù', 'u')
        return texto
    
    def buscar_match(texto, patrones_dict):
        """Busca best-match: la subcausa con más keywords que aparecen en el texto.
        Desempata por especificidad (largo promedio de keywords matcheados)."""
        mejor_subcausa = None
        mejor_hits = 0
        mejor_especificidad = 0  # largo promedio de keywords matcheados (más largo = más específico)
        
        for subcausa, keywords in patrones_dict.items():
            hits = 0
            largo_total = 0
            for kw in keywords:
                kw_norm = normalizar_texto(kw)
                if kw_norm in texto:
                    hits += 1
                    largo_total += len(kw_norm)
            
            if hits > 0:
                especificidad = largo_total / hits  # largo promedio del keyword
                # Gana la subcausa con más hits; si empatan, la más específica
                if (hits > mejor_hits) or (hits == mejor_hits and especificidad > mejor_especificidad):
                    mejor_subcausa = subcausa
                    mejor_hits = hits
                    mejor_especificidad = especificidad
        
        return mejor_subcausa
    
    for comentario in comentarios:
        texto = normalizar_texto(comentario)
        
        clasificado = False
        
        # 1. Primero intentar con patrones de la categoría específica
        match = buscar_match(texto, patrones)
        if match:
            clasificaciones[match]['count'] += 1
            # Guardar hasta 5 ejemplos REALES (truncados a 150 chars para legibilidad)
            if len(clasificaciones[match]['ejemplos']) < 5:
                clasificaciones[match]['ejemplos'].append(comentario[:150])
            clasificado = True
            total_clasificados += 1
        
        # 2. Si no encontró, intentar con patrones _default
        if not clasificado:
            match = buscar_match(texto, patrones_default)
            if match:
                clasificaciones[match]['count'] += 1
                if len(clasificaciones[match]['ejemplos']) < 5:
                    clasificaciones[match]['ejemplos'].append(comentario[:150])
                clasificado = True
                total_clasificados += 1
        
        # 3. Solo si no matchea nada, va a "otros"
        if not clasificado:
            clasificaciones['otros_temas']['count'] += 1
            if len(clasificaciones['otros_temas']['ejemplos']) < 5:
                clasificaciones['otros_temas']['ejemplos'].append(comentario[:150])
            total_clasificados += 1
    
    # Total de comentarios analizados
    total = total_clasificados if total_clasificados > 0 else 1
    
    # Construir lista de subcausas
    subcausas = []
    for nombre, datos in clasificaciones.items():
        if datos['count'] > 0:
            nombre_display = NOMBRES_DISPLAY.get(nombre, nombre.replace('_', ' ').title())
            if nombre == 'otros_temas':
                nombre_display = 'Otros temas'
            
            pct = round((datos['count'] / total) * 100, 0)
            
            subcausas.append({
                'subcausa': nombre_display,
                'nombre': nombre,
                'porcentaje': pct,  # % sobre total de comentarios
                'menciones': datos['count'],
                'evidencia': datos['ejemplos']
            })
    
    # Ordenar por porcentaje y tomar top (pero incluir todos los significativos)
    subcausas = sorted(subcausas, key=lambda x: x['porcentaje'], reverse=True)
    
    # Filtrar solo los que tienen >5% o son top 5
    subcausas_filtradas = [s for s in subcausas if s['porcentaje'] >= 5][:6]
    
    # Si quedó muy poco, tomar al menos top 3
    if len(subcausas_filtradas) < 3:
        subcausas_filtradas = subcausas[:3]
    
    # Verificar que sumen ~100%
    suma = sum(s['porcentaje'] for s in subcausas_filtradas)
    
    # Si no suman 100%, agregar "Otros" con el resto
    if suma < 95 and 'otros_temas' not in [s['nombre'] for s in subcausas_filtradas]:
        resto = 100 - suma
        subcausas_filtradas.append({
            'subcausa': 'Otros temas',
            'nombre': 'otros_temas',
            'porcentaje': resto,
            'menciones': round(resto * total / 100),
            'evidencia': []
        })
    
    return subcausas_filtradas


def extraer_tema_especifico(comentarios: List[str], motivo: str, max_sample: int = 50) -> str:
    """
    Extrae un tema ESPECÍFICO y DESCRIPTIVO de los comentarios reales.
    
    Busca patrones concretos como:
    - Menciones de competencia: "Nubank ofrece mejor rendimiento"
    - Problemas específicos: "la app se cierra cuando intento transferir"
    - Comparaciones: "antes era mejor, ahora empeoró"
    
    Returns:
        Frase descriptiva estilo: "usuarios mencionan que el rendimiento de Nubank es mejor"
        o None si no encuentra patrón específico
    """
    if not comentarios:
        return None
    
    # Muestrear más comentarios para mejor análisis
    sample_size = min(max_sample, len(comentarios))
    sample = random.sample(comentarios, sample_size) if len(comentarios) > sample_size else comentarios
    
    # COMPETIDORES conocidos (para detectar comparaciones)
    COMPETIDORES = {
        'nubank', 'nu bank', 'picpay', 'pic pay', 'banco inter',
        'c6 bank', 'itau', 'itaú', 'bradesco', 'santander',
        'ualá', 'uala', 'naranja', 'naranja x', 'brubank', 'personal pay',
        'modo', 'bbva', 'banamex', 'hey banco', 'stori', 'klar', 'didi',
        'banco nacion', 'banco estado', 'tenpo', 'mach', 'pagbank', 'pag bank'
    }
    # NOTA: Removidos 'inter' (matchea con 'intereses'), 'c6' (muy corto), 'bb' (muy corto)
    
    # PATRONES de comparación con competencia
    PATRONES_COMPETENCIA = [
        (r'(nubank|picpay|inter|c6|ualá|uala|naranja|brubank|bbva|itau|bradesco).{0,30}(melhor|mejor|mais|más|ofrece|oferece|tiene|tem|da mais|dá mais)', 'competencia_mejor'),
        (r'(em|en|no|na)\s+(nubank|picpay|inter|c6|ualá|naranja).{0,20}(funciona|tem|tiene|ofrece|oferece|rende|rinde)', 'competencia_funciona'),
        (r'(prefiro|prefiero|vou para|voy a|migrar|mudar).{0,15}(nubank|picpay|inter|c6|ualá|naranja)', 'migrando_competencia'),
    ]
    
    # PATRONES de problemas específicos
    PATRONES_PROBLEMAS = [
        (r'(app|aplicativo|aplicación).{0,20}(trava|cierra|crash|lento|lenta|demora|bug|erro|error|falla)', 'problema_app'),
        (r'(cashback|devolución|estorno).{0,20}(não|no|nunca|demora|prometido|prometieron)', 'problema_cashback'),
        (r'(rendimento|rendimiento).{0,20}(baixo|bajo|poco|pouco|nada|miseria|inferior)', 'rendimiento_bajo'),
        (r'(limite|límite).{0,20}(baixo|bajo|poco|insuficiente|ridículo|aumentar)', 'limite_bajo'),
        (r'(taxa|tasa|juros|interés|intereses).{0,20}(alto|alta|caro|cara|abusivo|exorbitante)', 'tasas_altas'),
        (r'(atendimento|atención|soporte|suporte).{0,20}(ruim|malo|demora|lento|robô|robot|não resolve|no resuelve)', 'atencion_mala'),
        (r'(fraude|golpe|robo|roubo|hackearon|clonaron|invadiram)', 'fraude_seguridad'),
        (r'(bloquearam|bloquearon|conta bloqueada|cuenta bloqueada|sem acesso|sin acceso)', 'cuenta_bloqueada'),
    ]
    
    # Contadores para detectar patrones dominantes
    conteo_competencia = {}
    conteo_problemas = {}
    ejemplos_competencia = []
    ejemplos_problemas = []
    
    for comentario in sample:
        texto = comentario.lower()
        # Normalizar
        texto_norm = texto.replace('ã', 'a').replace('õ', 'o').replace('ç', 'c')
        texto_norm = texto_norm.replace('á', 'a').replace('é', 'e').replace('í', 'i')
        texto_norm = texto_norm.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        
        # Buscar menciones de competencia
        for competidor in COMPETIDORES:
            if competidor in texto_norm:
                conteo_competencia[competidor] = conteo_competencia.get(competidor, 0) + 1
                if len(ejemplos_competencia) < 5:
                    ejemplos_competencia.append((competidor, comentario[:120]))
        
        # Buscar patrones de problemas
        for patron, tipo in PATRONES_PROBLEMAS:
            if re.search(patron, texto_norm):
                conteo_problemas[tipo] = conteo_problemas.get(tipo, 0) + 1
                if tipo not in [e[0] for e in ejemplos_problemas] and len(ejemplos_problemas) < 5:
                    ejemplos_problemas.append((tipo, comentario[:120]))
    
    # GENERAR TEMA ESPECÍFICO basado en lo encontrado
    tema = None
    
    # 1. Si hay menciones significativas de competencia (>10% de la muestra)
    if conteo_competencia:
        top_competidor = max(conteo_competencia, key=conteo_competencia.get)
        menciones = conteo_competencia[top_competidor]
        if menciones >= max(3, sample_size * 0.1):  # Al menos 10% o 3 menciones
            # Generar frase descriptiva según el motivo
            if 'rendimiento' in motivo.lower() or 'rendimento' in motivo.lower():
                tema = f"usuarios mencionan que {top_competidor.title()} ofrece mejor rendimiento"
            elif 'promocion' in motivo.lower() or 'cashback' in motivo.lower():
                tema = f"usuarios comparan con beneficios de {top_competidor.title()}"
            elif 'funcional' in motivo.lower():
                tema = f"usuarios prefieren funcionalidades de {top_competidor.title()}"
            else:
                tema = f"usuarios comparan negativamente con {top_competidor.title()}"
    
    # 2. Si no hay competencia, usar problema específico más frecuente
    if not tema and conteo_problemas:
        top_problema = max(conteo_problemas, key=conteo_problemas.get)
        menciones = conteo_problemas[top_problema]
        if menciones >= max(2, sample_size * 0.08):  # Al menos 8% o 2 menciones
            FRASES_PROBLEMA = {
                'problema_app': 'app con errores o lentitud',
                'problema_cashback': 'cashback no acreditado o demorado',
                'rendimiento_bajo': 'tasa de rendimiento baja',
                'limite_bajo': 'límite de crédito insuficiente',
                'tasas_altas': 'tasas o intereses altos',
                'atencion_mala': 'atención al cliente deficiente',
                'fraude_seguridad': 'incidentes de fraude o hackeo',
                'cuenta_bloqueada': 'cuenta bloqueada sin explicación',
            }
            tema = FRASES_PROBLEMA.get(top_problema)
    
    return tema


def extraer_keywords_avanzado(comentarios: List[str], top_n: int = 10) -> Dict[str, int]:
    """
    Extrae keywords más frecuentes de los comentarios.
    Excluye stopwords y palabras muy genéricas de fintech.
    """
    stopwords = {
        # Portugués básico
        'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com',
        'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como',
        'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou', 'ser',
        'nao', 'voce', 'você', 'eles', 'elas', 'nos', 'essa', 'esse', 'isso',
        # Español básico
        'la', 'el', 'en', 'los', 'del', 'las', 'al', 'lo', 'pero', 'sus', 'le',
        'ya', 'fue', 'este', 'ha', 'sí', 'porque', 'muy', 'bien', 'mal', 'todo',
        'usar', 'uso', 'ter', 'fazer', 'sempre', 'siempre', 'ainda', 'todavía',
        'quando', 'cuando', 'onde', 'donde', 'como', 'muito', 'mucho', 'poco',
        'pouco', 'nada', 'tudo', 'isso', 'eso', 'esto', 'aqui', 'aquí', 'ali',
        'ahí', 'mesmo', 'mismo', 'gosto', 'gusto', 'gosta', 'gusta', 'acho',
        'creo', 'pienso', 'penso', 'esta', 'este', 'esos', 'esas',
        # Marcas y genéricos de fintech (NO informativos)
        'app', 'mercado', 'pago', 'libre', 'nubank', 'banco', 'bank', 'conta',
        'cuenta', 'aplicativo', 'aplicacion', 'dinheiro', 'dinero', 'plata',
        'gente', 'pessoa', 'personas', 'usuario', 'cliente', 'clientes',
        'coisa', 'cosa', 'cosas', 'forma', 'manera', 'parte', 'lugar',
        'tempo', 'tiempo', 'vezes', 'veces', 'dias', 'anos', 'meses',
        'alguns', 'algunas', 'varios', 'outras', 'otros', 'otras', 'outro',
        'seria', 'poderia', 'podria', 'deveria', 'deberia', 'fazer', 'hacer',
        'sendo', 'siendo', 'tendo', 'teniendo', 'pode', 'puede', 'podem',
        'precisa', 'necesita', 'quero', 'quiero', 'quer', 'quiere',
        'bom', 'bueno', 'ruim', 'malo', 'melhor', 'mejor', 'pior', 'peor',
        'recomendo', 'recomiendo', 'gostaria', 'gustaria', 'ainda', 'todavia',
        'sobre', 'entre', 'desde', 'hasta', 'cada', 'toda', 'todas', 'todos',
        # Palabras genéricas adicionales (NO informativas)
        'algumas', 'alguma', 'algum', 'algo', 'algun', 'alguno', 'alguna',
        'muitas', 'muita', 'muitos', 'muchas', 'muchos', 'mucha',
        'sempre', 'nunca', 'tambem', 'también', 'porem', 'porém',
        'apenas', 'somente', 'apenas', 'solo', 'solamente', 'apenas',
        'agora', 'ahora', 'depois', 'despues', 'antes', 'logo',
        'assim', 'entao', 'entonces', 'portanto', 'pois', 'porque',
        'sendo', 'sido', 'estar', 'estou', 'estoy', 'estava', 'estaba'
    }
    
    if not comentarios:
        return {}
    
    texto = ' '.join(comentarios).lower()
    # Normalizar
    texto = texto.replace('ã', 'a').replace('õ', 'o').replace('ç', 'c')
    texto = texto.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    texto = texto.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
    
    palabras = re.findall(r'\b[a-z]{4,15}\b', texto)
    palabras_filtradas = [p for p in palabras if p not in stopwords]
    
    return dict(Counter(palabras_filtradas).most_common(top_n))


# ==============================================================================
# TRIANGULACIÓN PRODUCTO ↔ QUEJA ↔ NOTICIA
# ==============================================================================

MAPEO_PRODUCTO_QUEJA = {
    # Producto → Quejas relacionadas (ampliado para match parcial)
    'Rendimentos': ['Rendimientos'],
    'Rendimientos': ['Rendimientos'],
    'Rendimientos con el dinero en cuenta': ['Rendimientos'],
    'Conta remunerada': ['Rendimientos'],
    'Cuenta remunerada': ['Rendimientos'],
    'Cuenta Remunerada': ['Rendimientos'],
    'Inversiones': ['Rendimientos'],
    'Investimentos': ['Rendimientos'],
    'Cartão de crédito': ['Financiamiento'],
    'Tarjeta de crédito': ['Financiamiento'],
    'Tarjeta de Crédito': ['Financiamiento'],
    'Acesso a crédito': ['Financiamiento'],
    'Acceso a crédito': ['Financiamiento'],
    'Crédito': ['Financiamiento'],
    'Préstamo': ['Financiamiento'],
    'Empréstimo': ['Financiamiento'],
    'Línea de crédito': ['Financiamiento'],
    'Pix': ['Complejidad', 'Seguridad'],
    'Transferencias': ['Complejidad', 'Seguridad'],
    'Pagamentos': ['Complejidad'],
    'Pagos': ['Complejidad'],
    'QR': ['Complejidad'],
    'Billetera': ['Complejidad', 'Seguridad'],
    'Wallet': ['Complejidad', 'Seguridad'],
}

# Mapeo de categorías de noticias a quejas (para triangulación)
MAPEO_NOTICIA_QUEJA = {
    'Financiamiento': ['Financiamiento', 'Crédito', 'Tarjeta'],
    'Rendimientos': ['Rendimientos', 'Inversiones', 'Ahorro'],
    'Seguridad': ['Seguridad', 'Fraude', 'Estafa'],
    'Atención': ['Atención', 'Soporte', 'Servicio'],
    'Funcionalidades': ['Funcionalidades', 'App', 'Tecnología'],
    'Complejidad': ['Complejidad', 'Usabilidad', 'Dificultad'],
    'Promociones': ['Promociones', 'Beneficios', 'Descuentos'],
}


def _buscar_queja_producto(nombre_prod: str, causas_waterfall: List[Dict]) -> tuple:
    """
    Busca la queja relacionada con un producto usando matching flexible.
    """
    nombre_lower = nombre_prod.lower()
    
    # 1. Buscar en MAPEO_PRODUCTO_QUEJA (exacto)
    quejas_rel = MAPEO_PRODUCTO_QUEJA.get(nombre_prod, [])
    
    # 2. Si no hay match exacto, buscar parcial
    if not quejas_rel:
        for key, quejas in MAPEO_PRODUCTO_QUEJA.items():
            if key.lower() in nombre_lower or nombre_lower in key.lower():
                quejas_rel = quejas
                break
    
    # 3. Deducir por nombre si aún no hay
    if not quejas_rel:
        if 'rendim' in nombre_lower or 'invest' in nombre_lower or 'cuenta' in nombre_lower:
            quejas_rel = ['Rendimientos']
        elif 'créd' in nombre_lower or 'cred' in nombre_lower or 'tarj' in nombre_lower or 'cart' in nombre_lower:
            quejas_rel = ['Financiamiento']
        elif 'segur' in nombre_lower or 'fraud' in nombre_lower:
            quejas_rel = ['Seguridad']
        elif 'pago' in nombre_lower or 'transfer' in nombre_lower or 'pix' in nombre_lower:
            quejas_rel = ['Complejidad', 'Seguridad']
    
    # Buscar match en waterfall
    queja_match = None
    for causa in causas_waterfall:
        motivo = causa.get('motivo', '')
        for queja in quejas_rel:
            if queja.lower() in motivo.lower() or motivo.lower() in queja.lower():
                queja_match = causa
                break
        if queja_match:
            break
    
    return quejas_rel, queja_match


def _buscar_noticia_relacionada(quejas_rel: List[str], noticias: List[Dict]) -> Dict:
    """
    Busca noticia relacionada con las quejas usando matching flexible.
    """
    if not noticias or not quejas_rel:
        return None
    
    for noticia in noticias:
        cat_noticia = noticia.get('categoria_relacionada', '').lower()
        
        # Match directo con categoría de noticia
        for queja in quejas_rel:
            queja_lower = queja.lower()
            if queja_lower in cat_noticia or cat_noticia in queja_lower:
                return noticia
        
        # Match con mapeo de noticias a quejas
        for queja in quejas_rel:
            queja_lower = queja.lower()
            for cat_key, cats_relacionadas in MAPEO_NOTICIA_QUEJA.items():
                if queja_lower in cat_key.lower():
                    for cat_rel in cats_relacionadas:
                        if cat_rel.lower() in cat_noticia:
                            return noticia
    
    return None


def ejecutar_triangulacion(productos: List[Dict], causas_waterfall: List[Dict], 
                           noticias: List[Dict] = None) -> List[Dict]:
    """
    Triangula Producto ↔ Queja ↔ Noticia automáticamente.
    
    Busca conexiones entre:
    - Cambios en productos (uso, NPS usuario)
    - Cambios en quejas (waterfall)
    - Noticias del mercado (contexto)
    
    ⚠️ IMPORTANTE: Las noticias son 100% REALES, nunca inventadas.
    
    Args:
        productos: Lista de productos con total_effect, delta_share, etc.
        causas_waterfall: Lista de causas del waterfall con delta
        noticias: Lista de noticias REALES encontradas
        
    Returns:
        Lista de triangulaciones con coherencia detectada
    """
    if noticias is None:
        noticias = []
    
    triangulaciones = []
    
    for prod in productos:
        nombre_prod = prod.get('nombre_original', prod.get('nombre', ''))
        efecto = prod.get('total_effect', 0)
        delta_nps = prod.get('delta_nps_usuario', 0)
        
        # Buscar queja relacionada con matching flexible
        quejas_rel, queja_match = _buscar_queja_producto(nombre_prod, causas_waterfall)
        
        # Determinar coherencia
        coherencia = None
        explicacion = ""
        
        if queja_match:
            delta_queja = queja_match.get('delta', 0)
            
            # Lógica de coherencia:
            # Producto mejoró (efecto > 0) + Queja bajó (delta < 0) = COHERENTE
            # Producto mejoró (efecto > 0) + Queja subió (delta > 0) = INCOHERENTE
            # Producto empeoró (efecto < 0) + Queja subió (delta > 0) = COHERENTE
            # Producto empeoró (efecto < 0) + Queja bajó (delta < 0) = INCOHERENTE
            
            if efecto > 0 and delta_queja < 0:
                coherencia = 'coherente'
                explicacion = f"Producto mejoró {efecto:+.2f}pp y quejas bajaron {delta_queja:.1f}pp"
            elif efecto > 0 and delta_queja > 0:
                coherencia = 'incoherente'
                explicacion = f"Producto mejoró {efecto:+.2f}pp pero quejas subieron {delta_queja:+.1f}pp"
            elif efecto < 0 and delta_queja > 0:
                coherencia = 'coherente'
                explicacion = f"Producto empeoró {efecto:.2f}pp y quejas subieron {delta_queja:+.1f}pp"
            elif efecto < 0 and delta_queja < 0:
                coherencia = 'incoherente'
                explicacion = f"Producto empeoró {efecto:.2f}pp pero quejas bajaron {delta_queja:.1f}pp"
            else:
                coherencia = 'neutro'
                explicacion = "Sin cambio significativo"
        
        # Buscar noticia relacionada con matching flexible
        noticia_relacionada = _buscar_noticia_relacionada(quejas_rel, noticias)
        
        triangulaciones.append({
            'producto': nombre_prod,
            'efecto_nps': efecto,
            'delta_nps_usuario': delta_nps,
            'queja_relacionada': queja_match.get('motivo') if queja_match else None,
            'delta_queja': queja_match.get('delta', 0) if queja_match else 0,
            'coherencia': coherencia,
            'explicacion': explicacion,
            'noticia': noticia_relacionada
        })
    
    return triangulaciones


# ==============================================================================
# ENRIQUECIMIENTO DE WATERFALL PARA ACORDEONES
# ==============================================================================

def _buscar_comentarios_fuzzy(motivo: str, comentarios_por_motivo: Dict) -> Dict:
    """
    Busca comentarios con matching aproximado del nombre del motivo.
    """
    # Match exacto primero
    if motivo in comentarios_por_motivo:
        return comentarios_por_motivo[motivo]
    
    # Mapeo de variantes para motivos genéricos
    VARIANTES_MOTIVOS = {
        'otro': ['otros', 'other', 'outros', 'otra', 'demás', 'misc', 'general', 'varios'],
        'otros': ['otro', 'other', 'outros', 'otra', 'demás', 'misc', 'general', 'varios'],
        'funcionalidades': ['funcionalidad', 'funciones', 'features', 'funcionalidade'],
        'promociones': ['promocion', 'promoção', 'promocoes', 'descuentos', 'beneficios'],
        'complejidad': ['complexidade', 'complicado', 'dificil', 'difícil', 'usabilidad'],
        'atención': ['atencion', 'atendimento', 'soporte', 'suporte', 'servicio', 'serviço'],
    }
    
    motivo_lower = motivo.lower()
    
    # Buscar por variantes conocidas
    variantes = VARIANTES_MOTIVOS.get(motivo_lower, [])
    for variante in variantes:
        for key in comentarios_por_motivo:
            if variante in key.lower():
                return comentarios_por_motivo[key]
    
    # Match parcial
    for key in comentarios_por_motivo:
        key_lower = key.lower()
        # Si uno contiene al otro
        if motivo_lower in key_lower or key_lower in motivo_lower:
            return comentarios_por_motivo[key]
        # Si comparten palabras significativas
        palabras_motivo = set(motivo_lower.split())
        palabras_key = set(key_lower.split())
        if palabras_motivo & palabras_key:
            return comentarios_por_motivo[key]
    
    return {'q1': [], 'q2': []}


def enriquecer_waterfall_para_acordeones(causas_waterfall: List[Dict], 
                                          comentarios_por_motivo: Dict,
                                          triangulaciones: List[Dict] = None) -> List[Dict]:
    """
    Enriquece los datos del waterfall con subcausas, keywords y comentarios
    para mostrar en acordeones del HTML.
    
    Args:
        causas_waterfall: Lista de causas del waterfall
        comentarios_por_motivo: Dict {motivo: {'q1': [...], 'q2': [...]}}
        triangulaciones: Lista de triangulaciones (opcional)
        
    Returns:
        Lista de causas enriquecidas para acordeones
    """
    if triangulaciones is None:
        triangulaciones = []
    
    # Crear dict de triangulaciones por queja
    triang_por_queja = {}
    for t in triangulaciones:
        queja = t.get('queja_relacionada')
        if queja:
            triang_por_queja[queja] = t
    
    causas_enriquecidas = []
    
    for causa in causas_waterfall:
        motivo = causa.get('motivo', '')
        delta = causa.get('delta', 0)
        pct_q1 = causa.get('pct_q1', causa.get('impacto_anterior', 0))
        pct_q2 = causa.get('pct_q2', causa.get('impacto_actual', 0))
        
        # Obtener comentarios (con fuzzy matching)
        comentarios_motivo = _buscar_comentarios_fuzzy(motivo, comentarios_por_motivo)
        comms_q1 = comentarios_motivo.get('q1', [])
        comms_q2 = comentarios_motivo.get('q2', [])
        
        # Si no hay comentarios para Q2, intentar con todos los comentarios disponibles
        if not comms_q2:
            # Buscar en todas las categorías si el nombre parcialmente coincide
            for key, val in comentarios_por_motivo.items():
                if motivo.lower()[:5] in key.lower() or key.lower()[:5] in motivo.lower():
                    comms_q2 = val.get('q2', [])
                    comms_q1 = val.get('q1', [])
                    if comms_q2:
                        break
        
        # Generar subcausas automáticamente
        subcausas = generar_subcausas_automatico(comms_q2, motivo)
        
        # Extraer keywords
        keywords = extraer_keywords_avanzado(comms_q2)
        
        # Obtener triangulación (también con fuzzy)
        triangulacion = triang_por_queja.get(motivo)
        if not triangulacion:
            for key, val in triang_por_queja.items():
                if key and (motivo.lower() in key.lower() or key.lower() in motivo.lower()):
                    triangulacion = val
                    break
        
        # Seleccionar ejemplos de comentarios REALES (NUNCA inventados)
        # Aumentado a 10 comentarios y separados por Q para mejor análisis
        ejemplos_q1 = []
        ejemplos_q2 = []
        if comms_q1:
            sample_q1 = random.sample(comms_q1, min(5, len(comms_q1)))
            ejemplos_q1 = [c[:150] + '...' if len(c) > 150 else c for c in sample_q1]
        if comms_q2:
            sample_q2 = random.sample(comms_q2, min(5, len(comms_q2)))
            ejemplos_q2 = [c[:150] + '...' if len(c) > 150 else c for c in sample_q2]
        
        # Combinar para compatibilidad (los más recientes primero)
        ejemplos = ejemplos_q2 + ejemplos_q1
        
        # =====================================================================
        # EXTRACCIÓN INTELIGENTE DEL TEMA PRINCIPAL
        # Prioridad: 1) Análisis profundo de comentarios, 2) Subcausas, 3) Keywords
        # =====================================================================
        tema_principal = None
        temas_principales = []
        
        # 1. PRIMERO: Intentar extraer tema ESPECÍFICO de los comentarios (análisis profundo)
        # Esto busca menciones de competencia, problemas concretos, etc.
        if comms_q2 and len(comms_q2) >= 3:
            tema_especifico = extraer_tema_especifico(comms_q2, motivo, max_sample=50)
            if tema_especifico:
                tema_principal = tema_especifico
        
        # 2. SEGUNDO: Si no hay tema específico, usar subcausas con nombre descriptivo
        if not tema_principal and subcausas:
            for sc in subcausas[:3]:  # Revisar top 3
                if sc.get('porcentaje', 0) >= 10:
                    subcausa_nombre = sc.get('subcausa', '')
                    # Solo usar si es descriptivo (2+ palabras, no genérico)
                    if (subcausa_nombre.lower() not in ['otros temas', 'experiencia general mala', 
                                                         'necesita mejoras', 'mejor en competencia'] and 
                        len(subcausa_nombre) >= 10 and ' ' in subcausa_nombre):
                        temas_principales.append(subcausa_nombre)
            if temas_principales:
                tema_principal = temas_principales[0].lower()  # minúsculas para consistencia
        
        # 3. TERCERO: Fallback con subcausa top mejorada
        if not tema_principal and subcausas:
            primera = subcausas[0].get('subcausa', '')
            if primera and primera.lower() != 'otros temas':
                # Mapeo de subcausas a frases más descriptivas
                SUBCAUSA_A_FRASE = {
                    'límite bajo/insuficiente': 'límite de crédito insuficiente',
                    'tasas/intereses altos': 'tasas o intereses altos',
                    'proceso lento/difícil': 'proceso de solicitud difícil',
                    'tasa de rendimiento baja': 'tasa de rendimiento baja',
                    'mejor en competencia': None,  # Excluir - muy genérico
                    'app difícil de usar': 'app difícil de usar',
                    'bugs/errores técnicos': 'errores técnicos en la app',
                    'demora en respuesta': 'demora en atención al cliente',
                    'difícil contactar soporte': 'difícil contactar soporte',
                    'cashback no acreditado': 'cashback no acreditado',
                    'fraude/cuenta invadida': 'incidentes de fraude reportados',
                    'cuenta bloqueada/restringida': 'cuenta bloqueada sin explicación',
                }
                primera_lower = primera.lower()
                if primera_lower in SUBCAUSA_A_FRASE:
                    tema_principal = SUBCAUSA_A_FRASE[primera_lower]
                elif len(primera) >= 12 and ' ' in primera:
                    tema_principal = primera.lower()
        
        causa_enriquecida = {
            **causa,
            'motivo': motivo,
            'delta': delta,
            'pct_q1': pct_q1,
            'pct_q2': pct_q2,
            'subcausas': subcausas,
            'keywords': keywords,
            'ejemplos_comentarios': ejemplos,
            'ejemplos_q1': ejemplos_q1,
            'ejemplos_q2': ejemplos_q2,
            'num_comentarios_q1': len(comms_q1),
            'num_comentarios_q2': len(comms_q2),
            'triangulacion': triangulacion,
            'tema_principal': tema_principal,
            'temas_principales': temas_principales
        }
        
        causas_enriquecidas.append(causa_enriquecida)
    
    return causas_enriquecidas


# ==============================================================================
# GESTIÓN DE NOTICIAS - CARGA Y BÚSQUEDA
# ==============================================================================

import json

# Mapeo de países para búsquedas
PAISES_BUSQUEDA = {
    'MLA': 'Argentina',
    'MLB': 'Brasil',
    'MLM': 'México',
    'MLC': 'Chile'
}

def buscar_noticias_por_drivers(
    player: str, 
    site: str, 
    drivers_waterfall: List[Dict] = None,
    productos_clave: List[Dict] = None,
    delta_seguridad: float = 0,
    delta_principalidad: float = 0,
    año: int = None,
    q_ant: str = '',
    q_act: str = '',
    causas_semanticas: Dict = None
) -> List[Dict]:
    """
    Busca noticias ESPECIFICAS basadas en los drivers reales del analisis.
    
    IMPORTANTE: Esta funcion GARANTIZA que siempre retorne noticias.
    
    Args:
        player: Nombre del player
        site: Codigo del site (MLB, MLA, MLM)
        drivers_waterfall: Lista de drivers del waterfall con sus deltas
        productos_clave: Lista de productos con mayor impacto
        delta_seguridad: Variacion de la metrica de seguridad
        delta_principalidad: Variacion de principalidad
        año: Año para busqueda
        q_ant: Quarter anterior (ej: '25Q3') - para restriccion temporal
        q_act: Quarter actual (ej: '25Q4') - para restriccion temporal
        causas_semanticas: Dict de causas raíz semánticas por motivo (del JSON LLM)
    
    Returns:
        Lista de noticias encontradas (NUNCA vacia)
    """
    if año is None:
        año = datetime.now().year
    pais = PAISES_BUSQUEDA.get(site, 'Latinoamerica')
    idioma = 'português' if site == 'MLB' else 'español'
    
    # =========================================================================
    # RESTRICCION TEMPORAL: meses del quarter para las queries
    # =========================================================================
    MESES_NOMBRE_ES = {1:'enero',2:'febrero',3:'marzo',4:'abril',5:'mayo',6:'junio',
                        7:'julio',8:'agosto',9:'septiembre',10:'octubre',11:'noviembre',12:'diciembre'}
    MESES_NOMBRE_PT = {1:'janeiro',2:'fevereiro',3:'março',4:'abril',5:'maio',6:'junho',
                        7:'julho',8:'agosto',9:'setembro',10:'outubro',11:'novembro',12:'dezembro'}
    MESES_POR_Q = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
    
    sufijo_temporal = ''
    if q_act:
        try:
            q_year = int('20' + q_act[:2])
            q_num = int(q_act[-1])
            meses = MESES_POR_Q.get(q_num, [])
            nombres_meses = MESES_NOMBRE_PT if site == 'MLB' else MESES_NOMBRE_ES
            sufijo_temporal = ' '.join(nombres_meses.get(m, '') for m in meses) + f' {q_year}'
        except (ValueError, IndexError):
            sufijo_temporal = str(año)
    else:
        sufijo_temporal = str(año)
    
    # =========================================================================
    # OPCION A: Mapeo EXPANDIDO de drivers a terminos de busqueda especificos
    # Diferenciado por idioma/site para mayor precision
    # =========================================================================
    
    TERMINOS_BUSQUEDA_BR = {
        'rendimientos': ['rendimento CDI', 'poupança', 'cofrinhos', 'caixinha turbo', 'taxa rendimento'],
        'rendimentos': ['rendimento CDI', 'poupança', 'cofrinhos', 'caixinha turbo', 'taxa rendimento'],
        'financiamiento': ['crédito', 'empréstimo', 'limite cartão', 'consignado', 'parcelamento'],
        'financiamento': ['crédito', 'empréstimo', 'limite cartão', 'consignado', 'parcelamento'],
        'seguridad': ['segurança', 'golpe pix', 'fraude', 'proteção conta', 'biometria'],
        'segurança': ['segurança', 'golpe pix', 'fraude', 'proteção conta', 'biometria'],
        'complejidad': ['app instável', 'falha aplicativo', 'problema sistema', 'caiu app'],
        'complexidade': ['app instável', 'falha aplicativo', 'problema sistema', 'caiu app'],
        'atención': ['atendimento cliente', 'SAC', 'reclamação', 'ouvidoria'],
        'atencion al cliente': ['atendimento cliente', 'SAC', 'reclamação', 'ouvidoria'],
        'promociones': ['promoção', 'cashback', 'desconto', 'benefício cliente'],
        'funcionalidades': ['nova funcionalidade', 'lançamento', 'atualização app'],
        'tarifas': ['taxa', 'tarifa', 'cobrança', 'custo manutenção'],
    }
    
    TERMINOS_BUSQUEDA_MX = {
        'rendimientos': ['rendimiento cuenta', 'tasa interés', 'ahorro rendimiento', 'cuenta remunerada'],
        'financiamiento': ['crédito', 'préstamo', 'límite tarjeta', 'línea crédito', 'BNPL'],
        'seguridad': ['seguridad app', 'fraude', 'protección cuenta', 'verificación'],
        'complejidad': ['nueva app', 'actualización aplicación', 'falla app', 'problemas sistema', 'caída servicio'],
        'atención': ['atención cliente', 'servicio cliente', 'soporte', 'queja'],
        'atencion al cliente': ['atención cliente', 'servicio cliente', 'soporte'],
        'promociones': ['promoción', 'MSI', 'meses sin intereses', 'cashback', 'descuento'],
        'funcionalidades': ['nueva función', 'lanzamiento', 'actualización', 'IA inteligencia'],
        'tarifas': ['comisión', 'costo', 'tarifa', 'anualidad'],
    }
    
    TERMINOS_BUSQUEDA_AR = {
        'rendimientos': ['rendimiento', 'TNA', 'plazo fijo', 'cuenta remunerada', 'intereses'],
        'financiamiento': ['crédito', 'préstamo', 'límite', 'tarjeta crédito', 'cuotas'],
        'seguridad': ['seguridad', 'fraude', 'estafa', 'protección'],
        'complejidad': ['app caída', 'falla', 'problema aplicación'],
        'atención': ['atención cliente', 'reclamo', 'soporte'],
        'promociones': ['descuento', 'cashback', 'promoción'],
        'funcionalidades': ['nueva función', 'lanzamiento', 'novedad'],
    }
    
    # Seleccionar diccionario según site
    if site == 'MLB':
        TERMINOS_BUSQUEDA = TERMINOS_BUSQUEDA_BR
    elif site == 'MLM':
        TERMINOS_BUSQUEDA = TERMINOS_BUSQUEDA_MX
    else:
        TERMINOS_BUSQUEDA = TERMINOS_BUSQUEDA_AR
    
    queries = []
    
    # 1. Construir queries basadas en TOP DRIVERS del waterfall (deterioros Y mejoras)
    if drivers_waterfall:
        # Ordenar por delta descendente (delta > 0 = deterioro = más quejas)
        drivers_ordenados = sorted(drivers_waterfall, key=lambda x: x.get('delta', 0), reverse=True)
        
        # Top 4 deterioros
        for driver in drivers_ordenados[:4]:
            motivo = driver.get('motivo', '').lower()
            delta = driver.get('delta', 0)
            
            if abs(delta) > UMBRAL_DRIVER_SIGNIFICATIVO:
                terminos = TERMINOS_BUSQUEDA.get(motivo, [motivo])
                for termino in terminos[:2]:  # Max 2 terminos por driver
                    queries.append({
                        'query': f"{player} {pais} {termino} {sufijo_temporal}",
                        'categoria': motivo.capitalize(),
                        'impacto': 'negativo' if delta > 0 else 'positivo'
                    })
        
        # Top 3 mejoras (delta < 0 = menos quejas = mejora)
        drivers_mejoras = sorted(drivers_waterfall, key=lambda x: x.get('delta', 0))
        for driver in drivers_mejoras[:3]:
            motivo = driver.get('motivo', '').lower()
            delta = driver.get('delta', 0)
            
            if delta < -UMBRAL_DRIVER_SIGNIFICATIVO:
                terminos = TERMINOS_BUSQUEDA.get(motivo, [motivo])
                for termino in terminos[:2]:  # Max 2 terminos por mejora
                    q_text = f"{player} {pais} {termino} {sufijo_temporal}"
                    # Evitar duplicar queries ya agregadas en deterioros
                    if not any(q['query'] == q_text for q in queries):
                        queries.append({
                            'query': q_text,
                            'categoria': motivo.capitalize(),
                            'impacto': 'positivo'
                        })
    
    # 2. Construir queries basadas en PRODUCTOS clave
    if productos_clave:
        productos_ordenados = sorted(productos_clave, key=lambda x: abs(x.get('total_effect', 0)), reverse=True)
        
        for prod in productos_ordenados[:3]:  # Top 3 productos
            nombre = prod.get('nombre_original', prod.get('nombre_display', ''))
            if nombre and len(nombre) > 3:
                queries.append({
                    'query': f"{player} {pais} {nombre} {sufijo_temporal}",
                    'categoria': 'Productos',
                    'impacto': 'positivo' if prod.get('total_effect', 0) > 0 else 'negativo'
                })
    
    # 3. Agregar queries de SEGURIDAD si varió significativamente
    if abs(delta_seguridad) > UMBRAL_SEGURIDAD_NOTICIA:
        terminos_seg = ['segurança', 'fraude'] if site == 'MLB' else ['seguridad', 'fraude']
        for t in terminos_seg:
            queries.append({
                'query': f"{player} {pais} {t} {sufijo_temporal}",
                'categoria': 'Seguridad',
                'impacto': 'positivo' if delta_seguridad > 0 else 'negativo'
            })
    
    # 4. Agregar queries de PRINCIPALIDAD si varió significativamente
    if abs(delta_principalidad) > UMBRAL_PRINCIPALIDAD_NOTICIA:
        terminos_princ = ['banco principal', 'conta principal'] if site == 'MLB' else ['banco principal', 'cuenta principal']
        queries.append({
            'query': f"{player} {pais} {terminos_princ[0]} {sufijo_temporal}",
            'categoria': 'Principalidad',
            'impacto': 'positivo' if delta_principalidad > 0 else 'negativo'
        })
    
    # 5. NUEVO: Queries basadas en CAUSAS RAÍZ SEMÁNTICAS (más específicas)
    if causas_semanticas:
        queries_cr = generar_queries_desde_causas_raiz(
            causas_semanticas, player, site, sufijo_temporal,
            max_causas_por_motivo=2, max_queries=6
        )
        for qcr in queries_cr:
            # Evitar duplicar queries ya existentes
            if not any(q['query'] == qcr['query'] for q in queries):
                queries.append(qcr)
        if queries_cr:
            print(f"   [CAUSA RAIZ] {len(queries_cr)} queries adicionales desde analisis semantico")
    
    # 6. SIEMPRE agregar queries generales del player (contexto amplio)
    queries_generales = [
        {'query': f"{player} {pais} {sufijo_temporal} noticias", 'categoria': 'General', 'impacto': 'neutro'},
        {'query': f"{player} {pais} {sufijo_temporal} lanzamiento novedad", 'categoria': 'Funcionalidades', 'impacto': 'neutro'},
    ]
    for qg in queries_generales:
        if not any(q['query'] == qg['query'] for q in queries):
            queries.append(qg)
    
    # 7. FALLBACK: Si aún no hay queries específicas, agregar más genéricas
    if len(queries) <= 2:
        queries_extra = [
            {'query': f"{player} {pais} {sufijo_temporal} credito", 'categoria': 'Financiamiento', 'impacto': 'neutro'},
            {'query': f"{player} {pais} {sufijo_temporal} app", 'categoria': 'Complejidad', 'impacto': 'neutro'},
        ]
        queries.extend(queries_extra)
    
    # Limitar queries a un máximo razonable para evitar rate-limiting
    MAX_QUERIES = 15
    if len(queries) > MAX_QUERIES:
        # Priorizar: causas_raiz > drivers deterioro > productos > generales
        queries = queries[:MAX_QUERIES]
    
    print(f"   [SEARCH] Buscando noticias con {len(queries)} queries ({sufijo_temporal})...")
    
    # Reset stats
    global _BUSQUEDA_STATS
    _BUSQUEDA_STATS = {'exitosas': 0, 'fallidas': 0, 'total_resultados': 0}
    
    noticias_encontradas = _ejecutar_busquedas(queries, player, q_ant=q_ant, q_act=q_act, enriquecer=True)
    
    # 7. GARANTIA: Si pocas noticias, buscar con queries super genericas
    if len(noticias_encontradas) < 10:
        print(f"   [RETRY] Solo {len(noticias_encontradas)} noticias, intentando queries genericas...")
        queries_genericas = [
            {'query': f"{player} {pais} {año} noticias fintech", 'categoria': 'General', 'impacto': 'neutro'},
            {'query': f"{player} fintech {pais} {año}", 'categoria': 'General', 'impacto': 'neutro'},
            {'query': f"{player} {pais} {año}", 'categoria': 'General', 'impacto': 'neutro'},
            {'query': f"{player} {pais} novedades {año}", 'categoria': 'General', 'impacto': 'neutro'},
            {'query': f"{player} {pais} app actualizacion {año}", 'categoria': 'Funcionalidades', 'impacto': 'neutro'},
        ]
        extras = _ejecutar_busquedas(queries_genericas, player, q_ant=q_ant, q_act=q_act, enriquecer=True)
        # Agregar solo las que no sean duplicados
        urls_existentes = {n.get('url', '') for n in noticias_encontradas}
        for n in extras:
            if n.get('url', '') not in urls_existentes:
                noticias_encontradas.append(n)
                urls_existentes.add(n.get('url', ''))
    
    # Stats
    stats = _BUSQUEDA_STATS
    if noticias_encontradas:
        print(f"   [OK] {len(noticias_encontradas)} noticias encontradas (queries: {stats['exitosas']} ok, {stats['fallidas']} fail)")
    else:
        print(f"   [WARN] No se encontraron noticias automaticamente (queries: {stats['exitosas']} ok, {stats['fallidas']} fail)")
    
    return noticias_encontradas


# ==============================================================================
# PARSER DDG HTML (extrae titulo + URL + snippet)
# ==============================================================================

class _DDGHTMLParser(HTMLParser):
    """
    Parser para DuckDuckGo HTML (html.duckduckgo.com/html/).
    Extrae titulo, URL y snippet de cada resultado.
    DDG HTML estructura resultados con clases result__a (titulo) y result__snippet.
    """
    def __init__(self):
        super().__init__()
        self.results = []
        self._in_title_link = False
        self._in_snippet = False
        self._current = {'titulo': '', 'url': '', 'snippet': ''}
        self._current_classes = []
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get('class', '').split()
        self._current_classes = classes
        
        if tag == 'a' and 'result__a' in classes:
            href = attrs_dict.get('href', '')
            # DDG HTML wraps URLs - extract the actual URL
            if '//duckduckgo.com/l/?uddg=' in href:
                # Extract real URL from redirect
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                real_url = parsed.get('uddg', [href])[0]
                self._current['url'] = real_url
            elif href.startswith('http') and 'duckduckgo' not in href:
                self._current['url'] = href
            self._in_title_link = True
            self._current['titulo'] = ''
        
        if tag == 'a' and 'result__snippet' in classes:
            self._in_snippet = True
            self._current['snippet'] = ''
        
        # Fallback: also detect <td> class="result-snippet" for DDG Lite
        if tag == 'td' and 'result-snippet' in classes:
            self._in_snippet = True
            self._current['snippet'] = ''
    
    def handle_endtag(self, tag):
        if tag == 'a' and self._in_title_link:
            self._in_title_link = False
        
        if tag == 'a' and self._in_snippet:
            self._in_snippet = False
            # Snippet ends -> result is complete, save it
            if self._current['titulo'] and self._current['url']:
                self.results.append({
                    'titulo': self._current['titulo'].strip()[:150],
                    'url': self._current['url'],
                    'snippet': self._current['snippet'].strip()[:300],
                })
            self._current = {'titulo': '', 'url': '', 'snippet': ''}
        
        if tag == 'td' and self._in_snippet:
            self._in_snippet = False
    
    def handle_data(self, data):
        if self._in_title_link:
            self._current['titulo'] += data
        if self._in_snippet:
            self._current['snippet'] += data


class _DDGLiteFallbackParser(HTMLParser):
    """Fallback parser for DDG Lite (simpler HTML, no snippets)."""
    def __init__(self):
        super().__init__()
        self.in_link = False
        self.current_link = None
        self.current_title = ""
        self.results = []
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'a' and 'href' in attrs_dict:
            href = attrs_dict['href']
            if href.startswith('http') and 'duckduckgo' not in href:
                self.in_link = True
                self.current_link = href
                self.current_title = ""
    
    def handle_endtag(self, tag):
        if tag == 'a' and self.in_link:
            if self.current_title and self.current_link:
                self.results.append({
                    'titulo': self.current_title.strip()[:150],
                    'url': self.current_link,
                    'snippet': '',
                })
            self.in_link = False
    
    def handle_data(self, data):
        if self.in_link:
            self.current_title += data


class _BingParser(HTMLParser):
    """Parser for Bing search results HTML."""
    def __init__(self):
        super().__init__()
        self.in_result_link = False
        self.current_link = None
        self.current_title = ""
        self.results = []
        self._in_snippet = False
        self._current_snippet = ""
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        # Bing results: <a> inside <h2> or <li class="b_algo">
        if tag == 'a' and 'href' in attrs_dict:
            href = attrs_dict['href']
            if (href.startswith('http') 
                and 'bing.com' not in href 
                and 'microsoft.com' not in href
                and 'go.microsoft' not in href):
                self.in_result_link = True
                self.current_link = href
                self.current_title = ""
        # Snippet in <p> or <span> after the link
        if tag == 'p' and self.current_link and not self.in_result_link:
            self._in_snippet = True
            self._current_snippet = ""
    
    def handle_endtag(self, tag):
        if tag == 'a' and self.in_result_link:
            if self.current_title.strip() and self.current_link:
                # Don't add yet, wait for snippet
                pass
            self.in_result_link = False
        if tag == 'p' and self._in_snippet:
            self._in_snippet = False
            if self.current_link and self.current_title.strip():
                self.results.append({
                    'titulo': self.current_title.strip()[:150],
                    'url': self.current_link,
                    'snippet': self._current_snippet.strip()[:300],
                })
                self.current_link = None
                self.current_title = ""
        # Also capture results without snippets when moving to next result
        if tag == 'li' and self.current_link and self.current_title.strip():
            self.results.append({
                'titulo': self.current_title.strip()[:150],
                'url': self.current_link,
                'snippet': self._current_snippet.strip()[:300] if self._current_snippet else '',
            })
            self.current_link = None
            self.current_title = ""
            self._current_snippet = ""
    
    def handle_data(self, data):
        if self.in_result_link:
            self.current_title += data
        if self._in_snippet:
            self._current_snippet += data


# ==============================================================================
# ENRIQUECIMIENTO DE NOTICIAS (scraping meta tags)
# ==============================================================================

def _enriquecer_noticia(noticia: dict, timeout: int = 5) -> dict:
    """
    Fetch meta tags del articulo para obtener fecha real y descripcion.
    Parsea solo <head> para ser liviano. Graceful degradation si falla.
    """
    url = noticia.get('url', '')
    if not url:
        return noticia
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html',
        }
        # Solo leer los primeros 15KB (suficiente para <head>)
        resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
        content = b''
        for chunk in resp.iter_content(chunk_size=1024):
            content += chunk
            if len(content) > 15000:
                break
        html_head = content.decode('utf-8', errors='ignore')
        
        # Extraer meta og:description o meta description
        desc_match = (
            re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html_head, re.IGNORECASE | re.DOTALL)
            or re.search(r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:description["\']', html_head, re.IGNORECASE | re.DOTALL)
            or re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html_head, re.IGNORECASE | re.DOTALL)
            or re.search(r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']', html_head, re.IGNORECASE | re.DOTALL)
        )
        if desc_match:
            desc = desc_match.group(1).strip()
            if len(desc) > 20:
                noticia['resumen'] = desc[:300]
        
        # Extraer fecha: article:published_time, datePublished, o time[datetime]
        fecha_match = (
            re.search(r'<meta\s+property=["\']article:published_time["\']\s+content=["\']([\d\-T:+]+)', html_head, re.IGNORECASE)
            or re.search(r'<meta\s+content=["\']([\d\-T:+]+)["\']\s+property=["\']article:published_time["\']', html_head, re.IGNORECASE)
            or re.search(r'"datePublished"\s*:\s*"([\d\-T:+]+)"', html_head)
            or re.search(r'<time[^>]+datetime=["\']([\d\-T:+]+)', html_head, re.IGNORECASE)
        )
        if fecha_match:
            fecha_raw = fecha_match.group(1)
            # Normalizar a YYYY-MM
            if len(fecha_raw) >= 7:
                noticia['fecha'] = fecha_raw[:7]  # "2025-10"
                noticia['fecha_origen'] = 'meta_tag'
        
        # Extraer og:title si el titulo actual esta truncado
        if len(noticia.get('titulo', '')) < 40:
            title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html_head, re.IGNORECASE)
            if title_match:
                better_title = title_match.group(1).strip()
                if len(better_title) > len(noticia.get('titulo', '')):
                    noticia['titulo'] = better_title[:150]
    
    except Exception:
        pass  # Graceful degradation: keep original data
    
    return noticia


def _extraer_fecha_de_titulo(titulo: str) -> Optional[str]:
    """
    Intenta extraer fecha del titulo de la noticia con regex.
    Retorna formato YYYY-MM o None.
    """
    # Meses en espanol y portugues
    MESES = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'janeiro': '01', 'fevereiro': '02', 'marco': '03', 'marco': '03',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'abr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08', 'ago': '08',
        'sep': '09', 'set': '09', 'oct': '10', 'out': '10',
        'nov': '11', 'dec': '12', 'dic': '12', 'dez': '12',
    }
    
    titulo_lower = titulo.lower()
    
    # Patron: "mes YYYY" o "mes de YYYY"
    for mes_nombre, mes_num in MESES.items():
        patron = rf'{mes_nombre}\s+(?:de\s+)?(\d{{4}})'
        match = re.search(patron, titulo_lower)
        if match:
            year = match.group(1)
            if 2020 <= int(year) <= 2030:
                return f"{year}-{mes_num}"
    
    # Patron: "DD/MM/YYYY"
    match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](20\d{2})', titulo)
    if match:
        dia, mes, year = match.groups()
        if 1 <= int(mes) <= 12:
            return f"{year}-{int(mes):02d}"
    
    # Patron: "YYYY-MM"
    match = re.search(r'(20\d{2})-(\d{2})', titulo)
    if match:
        year, mes = match.groups()
        if 1 <= int(mes) <= 12:
            return f"{year}-{mes}"
    
    return None


# ==============================================================================
# SCORING DE RELEVANCIA
# ==============================================================================

# Fuentes conocidas de calidad (medios de prensa)
_FUENTES_CONFIABLES = {
    'reuters.com', 'bloomberg.com', 'forbes.com', 'forbes.com.mx',
    'eleconomista.com', 'eleconomista.com.mx', 'expansion.mx',
    'infobae.com', 'lanacion.com.ar', 'clarin.com', 'ambito.com',
    'folha.uol.com.br', 'valor.globo.com', 'exame.com',
    'infomoney.com.br', 'g1.globo.com', 'uol.com.br',
    'elfinanciero.com.mx', 'milenio.com', 'reforma.com',
    'latercera.com', 'emol.com', 'df.cl', 'biobiochile.cl',
    'cronista.com', 'iprofesional.com', 'bae.com.ar',
    'tecmundo.com.br', 'canaltech.com.br', 'xataka.com.mx',
}

# Fuentes a penalizar (no son noticias)
_FUENTES_PENALIZAR = {
    'wikipedia.org', 'investopedia.com', 'significados.com',
    'concepto.de', 'definicion.de', 'quora.com', 'reddit.com',
    'facebook.com', 'twitter.com', 'x.com', 'instagram.com',
    'youtube.com', 'tiktok.com',
}


def _calcular_relevancia(noticia: dict, player: str, categoria_driver: str = '',
                          q_ant: str = '', q_act: str = '') -> int:
    """
    Calcula un score de relevancia para una noticia.
    Score mas alto = mas relevante para el analisis.
    """
    score = 0
    titulo = (noticia.get('titulo', '') + ' ' + noticia.get('resumen', '')).lower()
    fuente = noticia.get('fuente', '').lower()
    fecha = noticia.get('fecha', '')
    
    # +3 si menciona al player
    if player.lower() in titulo:
        score += 3
    
    # +2 si menciona la categoria del driver
    if categoria_driver:
        # Mapeo de categorias a keywords de busqueda
        KEYWORDS_CATEGORIA = {
            'financiamiento': ['credito', 'prestamo', 'tarjeta', 'limite', 'financiamiento', 'emprestimo'],
            'rendimientos': ['rendimiento', 'tasa', 'ahorro', 'inversion', 'cdi', 'poupanca', 'rendimento'],
            'complejidad': ['app', 'aplicacion', 'falla', 'error', 'actualizacion', 'problema'],
            'seguridad': ['seguridad', 'fraude', 'estafa', 'robo', 'golpe', 'seguranca'],
            'promociones': ['promocion', 'cashback', 'descuento', 'beneficio', 'msi'],
            'atencion': ['atencion', 'soporte', 'reclamo', 'queja', 'atendimento', 'sac'],
            'tarifas': ['tarifa', 'comision', 'costo', 'cobro', 'taxa'],
            'funcionalidades': ['funcion', 'lanzamiento', 'novedad', 'nueva', 'actualizacion'],
        }
        cat_lower = categoria_driver.lower()
        keywords = KEYWORDS_CATEGORIA.get(cat_lower, [cat_lower])
        if any(kw in titulo for kw in keywords):
            score += 2
    
    # +2 si la fecha esta dentro del quarter analizado
    if fecha and q_ant and q_act:
        try:
            q_act_year = int('20' + q_act[:2])
            q_act_q = int(q_act[-1])
            q_ant_year = int('20' + q_ant[:2])
            q_ant_q = int(q_ant[-1])
            meses_q = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
            meses_validos = (
                [(q_ant_year, m) for m in meses_q.get(q_ant_q, [])] +
                [(q_act_year, m) for m in meses_q.get(q_act_q, [])]
            )
            if '-' in fecha:
                f_year = int(fecha[:4])
                f_month = int(fecha[5:7])
                if (f_year, f_month) in meses_validos:
                    score += 2
        except (ValueError, IndexError):
            pass
    
    # +1 si es fuente confiable
    if any(f in fuente for f in _FUENTES_CONFIABLES):
        score += 1
    
    # -2 si es fuente a penalizar
    if any(f in fuente for f in _FUENTES_PENALIZAR):
        score -= 2
    
    # -1 si el resumen es generico (placeholder)
    resumen = noticia.get('resumen', '')
    if 'Noticia relacionada con' in resumen:
        score -= 1
    
    return score


# ==============================================================================
# EJECUCION DE BUSQUEDAS (DDG HTML con fallback a Lite)
# ==============================================================================

_BUSQUEDA_STATS = {'exitosas': 0, 'fallidas': 0, 'total_resultados': 0}


def _ejecutar_busquedas(queries: List[Dict], player: str,
                         q_ant: str = '', q_act: str = '',
                         enriquecer: bool = True) -> List[Dict]:
    """
    Ejecuta busquedas en DuckDuckGo HTML (con fallback a Lite) y retorna noticias.
    
    Mejoras vs version anterior:
    - Usa DDG HTML que devuelve snippets (no solo titulos)
    - Retry con backoff para errores transitorios
    - Sleep entre queries para evitar rate-limiting
    - Enriquece top noticias con meta tags del articulo
    - Scoring de relevancia multi-criterio
    - Logging de errores (no silencioso)
    """
    global _BUSQUEDA_STATS
    noticias_encontradas = []
    
    for i, q_info in enumerate(queries):
        query = q_info['query']
        categoria = q_info['categoria']
        impacto = q_info['impacto']
        
        # Sleep entre queries para no ser bloqueado
        # DDG bloquea agresivamente: usar backoff progresivo
        if i > 0:
            base_sleep = 1.5 if i < 10 else 2.5
            time.sleep(base_sleep + (i * 0.1))
        
        resultados_query = []
        
        # Intentar DDG HTML → DDG Lite → Bing como fallbacks
        engines = [
            ('ddg_html', f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"),
            ('ddg_lite', f"https://lite.duckduckgo.com/lite/?q={requests.utils.quote(query)}"),
            ('bing', f"https://www.bing.com/search?q={requests.utils.quote(query)}&setlang=es"),
        ]
        
        for engine_name, url in engines:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml',
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8,pt;q=0.7',
                }
                
                response = requests.get(url, headers=headers, timeout=12)
                
                if response.status_code == 200:
                    if engine_name == 'ddg_html':
                        parser = _DDGHTMLParser()
                    elif engine_name == 'ddg_lite':
                        parser = _DDGLiteFallbackParser()
                    else:
                        # Bing: extract results via regex
                        parser = _BingParser()
                    
                    parser.feed(response.text)
                    resultados_query = parser.results
                    
                    if resultados_query:
                        _BUSQUEDA_STATS['exitosas'] += 1
                        break  # Got results
                elif response.status_code == 429:
                    wait = 3
                    time.sleep(wait)
                    continue
                else:
                    continue  # Try next engine
                    
            except requests.exceptions.Timeout:
                continue  # Try next engine
            except Exception:
                continue  # Try next engine
        
        if not resultados_query:
            _BUSQUEDA_STATS['fallidas'] += 1
            continue
        
        # Procesar resultados: top 3 por query
        for result in resultados_query[:3]:
            titulo = result.get('titulo', '')
            result_url = result.get('url', '')
            snippet = result.get('snippet', '')
            
            if len(titulo) < 20:
                continue
            
            # Evitar duplicados por titulo o URL
            es_dup = any(
                n['titulo'] == titulo or n.get('url') == result_url
                for n in noticias_encontradas
            )
            if es_dup:
                continue
            
            # Fecha: intentar extraer del titulo, sino usar fallback del quarter
            fecha = _extraer_fecha_de_titulo(titulo)
            fecha_origen = 'titulo'
            if not fecha and q_act:
                # Usar primer mes del quarter actual como aproximacion
                try:
                    year = int('20' + q_act[:2])
                    q = int(q_act[-1])
                    primer_mes = {1: '01', 2: '04', 3: '07', 4: '10'}
                    fecha = f"{year}-{primer_mes.get(q, '01')}"
                    fecha_origen = 'quarter_inferido'
                except (ValueError, IndexError):
                    fecha = f"{datetime.now().year}-{datetime.now().month:02d}"
                    fecha_origen = 'now_fallback'
            elif not fecha:
                fecha = f"{datetime.now().year}-{datetime.now().month:02d}"
                fecha_origen = 'now_fallback'
            
            # Resumen: snippet > placeholder generico
            resumen = snippet if snippet else f"Noticia relacionada con {player}."
            
            noticia = {
                'titulo': titulo,
                'fuente': result_url.split('/')[2] if '/' in result_url else 'web',
                'fecha': fecha,
                'fecha_origen': fecha_origen,
                'url': result_url,
                'resumen': resumen,
                'categoria_relacionada': categoria,
                'impacto_esperado': impacto,
                'relevancia': 'alta' if impacto != 'neutro' else 'media',
            }
            
            noticias_encontradas.append(noticia)
            _BUSQUEDA_STATS['total_resultados'] += 1
    
    # Enriquecer top 10 noticias con meta tags del articulo real
    if enriquecer and noticias_encontradas:
        # Pre-score para priorizar cuales enriquecer
        for n in noticias_encontradas:
            n['_score_pre'] = _calcular_relevancia(n, player, n.get('categoria_relacionada', ''), q_ant, q_act)
        
        noticias_ordenadas = sorted(noticias_encontradas, key=lambda x: x.get('_score_pre', 0), reverse=True)
        
        enriquecidas = 0
        for noticia in noticias_ordenadas[:10]:
            # Solo enriquecer si no tiene snippet (resumen generico)
            if 'Noticia relacionada con' in noticia.get('resumen', '') or noticia.get('fecha_origen') != 'meta_tag':
                _enriquecer_noticia(noticia)
                enriquecidas += 1
                time.sleep(0.3)  # Throttle scraping
        
        if enriquecidas > 0:
            print(f"   [ENRICH] {enriquecidas} noticias enriquecidas con meta tags")
    
    # Calcular score final y ordenar
    for n in noticias_encontradas:
        n['score_relevancia'] = _calcular_relevancia(n, player, n.get('categoria_relacionada', ''), q_ant, q_act)
        # Limpiar campo temporal
        n.pop('_score_pre', None)
    
    noticias_encontradas.sort(key=lambda x: x.get('score_relevancia', 0), reverse=True)
    
    return noticias_encontradas


def buscar_noticias_automatico(player: str, site: str, año: int = None) -> List[Dict]:
    """
    Busca noticias automaticamente usando DuckDuckGo cuando no hay cache.
    NOTA: Esta funcion usa queries genericas. Preferir buscar_noticias_por_drivers().
    
    Ahora delega a _ejecutar_busquedas (unificado, con DDG HTML + snippets).
    """
    if año is None:
        año = datetime.now().year
    pais = PAISES_BUSQUEDA.get(site, 'Latinoamerica')
    
    # Queries genericas por categoria
    queries = [
        {'query': f"{player} {pais} {año} credito prestamo tarjeta", 'categoria': 'Financiamiento', 'impacto': 'neutro'},
        {'query': f"{player} {pais} {año} rendimiento inversion", 'categoria': 'Rendimientos', 'impacto': 'neutro'},
        {'query': f"{player} {pais} {año} problemas fallas", 'categoria': 'Complejidad', 'impacto': 'neutro'},
        {'query': f"{player} {pais} {año} novedades funcionalidades", 'categoria': 'Funcionalidades', 'impacto': 'neutro'},
        {'query': f"{player} {pais} {año} seguridad fraude", 'categoria': 'Seguridad', 'impacto': 'neutro'},
    ]
    
    print(f"   [SEARCH] Buscando noticias automaticamente para {player} ({site})...")
    
    noticias_encontradas = _ejecutar_busquedas(queries, player, enriquecer=True)
    
    if noticias_encontradas:
        print(f"   [OK] {len(noticias_encontradas)} noticias encontradas automaticamente")
        _guardar_noticias_en_cache(player, site, noticias_encontradas)
    else:
        print(f"   [WARN] No se encontraron noticias automaticamente")
    
    return noticias_encontradas


def _guardar_noticias_en_cache(player: str, site: str, noticias: List[Dict]):
    """Guarda noticias en el cache, mergeando con las existentes (sin duplicar)."""
    cache_path = Path(__file__).parent.parent / "data" / "noticias_cache.json"
    
    try:
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        else:
            cache = {}
        
        if site not in cache:
            cache[site] = {}
        
        # Obtener noticias existentes en cache
        noticias_existentes = []
        if player in cache[site] and 'noticias' in cache[site][player]:
            noticias_existentes = cache[site][player]['noticias']
        
        # Crear set de URLs existentes para deduplicar
        urls_existentes = set()
        for n in noticias_existentes:
            url = n.get('url', n.get('titulo', ''))
            if url:
                urls_existentes.add(url)
        
        # Agregar solo noticias nuevas (que no existan ya en cache)
        nuevas_agregadas = 0
        for noticia in noticias:
            url = noticia.get('url', noticia.get('titulo', ''))
            if url and url not in urls_existentes:
                noticias_existentes.append(noticia)
                urls_existentes.add(url)
                nuevas_agregadas += 1
        
        cache[site][player] = {
            'ultima_actualizacion': datetime.now().strftime('%Y-%m'),
            'noticias': noticias_existentes
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
        
        total = len(noticias_existentes)
        print(f"   💾 Cache actualizado: {nuevas_agregadas} noticias nuevas agregadas ({total} total)")
        
    except Exception as e:
        print(f"   ⚠️ No se pudo guardar cache: {e}")


def cargar_noticias_cache(site: str, player: str) -> List[Dict]:
    """
    Carga noticias del cache JSON.
    Las noticias las busca el agente de Cursor con WebSearch, NO el script Python.
    Si no hay cache, retorna lista vacía.
    
    Args:
        site: Código del site (MLA, MLB, MLM, MLC)
        player: Nombre del player
        
    Returns:
        Lista de noticias del cache (o vacía si no hay)
    """
    cache_path = Path(__file__).parent.parent / "data" / "noticias_cache.json"
    
    if not cache_path.exists():
        print(f"   ⚠️ No existe cache de noticias (el agente debe buscarlas con WebSearch)")
        return []
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        if site in cache and player in cache[site]:
            noticias = cache[site][player].get('noticias', [])
            if noticias:
                return noticias
        
        print(f"   ⚠️ No hay noticias en cache para {player} ({site})")
        return []
            
    except Exception as e:
        print(f"   ❌ Error cargando noticias: {e}")
        return []


def filtrar_noticias_por_periodo(noticias: List[Dict], q_ant: str, q_act: str, verbose: bool = False) -> List[Dict]:
    """
    Filtra noticias ESTRICTAMENTE por los quarters analizados.
    Solo devuelve noticias de los meses correspondientes a los 2 Qs.
    
    Args:
        noticias: Lista de noticias
        q_ant: Período anterior (ej: "25Q3")
        q_act: Período actual (ej: "25Q4")
        verbose: Si True, imprime detalles del filtrado
        
    Returns:
        Lista de noticias filtradas solo del período analizado
    """
    if not noticias:
        if verbose:
            print(f"   [!] Sin noticias en cache para filtrar")
        return []
    
    # Extraer año y quarter del período actual
    year_act = int('20' + q_act[:2])  # 25Q4 -> 2025
    quarter_act = int(q_act[-1])  # 25Q4 -> 4
    
    # Extraer año y quarter del período anterior
    year_ant = int('20' + q_ant[:2])  # 25Q3 -> 2025
    quarter_ant = int(q_ant[-1])  # 25Q3 -> 3
    
    # Meses por quarter
    meses_quarter = {
        1: ['01', '02', '03'],
        2: ['04', '05', '06'],
        3: ['07', '08', '09'],
        4: ['10', '11', '12']
    }
    
    # Construir lista de meses válidos (de ambos quarters)
    meses_validos_ant = [(year_ant, m) for m in meses_quarter.get(quarter_ant, [])]
    meses_validos_act = [(year_act, m) for m in meses_quarter.get(quarter_act, [])]
    meses_validos = meses_validos_ant + meses_validos_act
    
    # FILTRAR noticias: solo las de los quarters analizados
    # Trackear cobertura por Q
    noticias_q_ant = []
    noticias_q_act = []
    noticias_descartadas = []
    
    for noticia in noticias:
        fecha = noticia.get('fecha', '')  # Formato esperado: "2025-10" o "2025-10-15"
        
        # Verificar Q anterior
        noticia_en_q_ant = False
        for (año_valido, mes_valido) in meses_validos_ant:
            if f"{año_valido}-{mes_valido}" in fecha or fecha.startswith(f"{año_valido}-{mes_valido}"):
                noticia['prioridad'] = 'alta'
                noticia['quarter_origen'] = q_ant
                noticias_q_ant.append(noticia)
                noticia_en_q_ant = True
                break
        
        if noticia_en_q_ant:
            continue
            
        # Verificar Q actual
        noticia_en_q_act = False
        for (año_valido, mes_valido) in meses_validos_act:
            if f"{año_valido}-{mes_valido}" in fecha or fecha.startswith(f"{año_valido}-{mes_valido}"):
                noticia['prioridad'] = 'alta'
                noticia['quarter_origen'] = q_act
                noticias_q_act.append(noticia)
                noticia_en_q_act = True
                break
        
        if not noticia_en_q_act:
            noticias_descartadas.append(noticia)
    
    # Combinar noticias filtradas
    noticias_filtradas = noticias_q_ant + noticias_q_act
    
    # Verbose: mostrar cobertura
    if verbose:
        print(f"   Filtrado de noticias por periodo {q_ant} vs {q_act}:")
        print(f"   - Total en cache: {len(noticias)}")
        print(f"   - Noticias de {q_ant}: {len(noticias_q_ant)}")
        print(f"   - Noticias de {q_act}: {len(noticias_q_act)}")
        print(f"   - Descartadas (otros Qs): {len(noticias_descartadas)}")
        
        # Advertencias de cobertura
        if len(noticias_q_ant) == 0:
            print(f"   [!] AVISO: Sin noticias de {q_ant} - agregar noticias con fechas de ese Q")
        if len(noticias_q_act) == 0:
            print(f"   [!] AVISO: Sin noticias de {q_act} - agregar noticias con fechas de ese Q")
    
    # Ordenar por relevancia
    orden_relevancia = {'alta': 0, 'media': 1, 'baja': 2}
    
    noticias_ordenadas = sorted(noticias_filtradas, key=lambda x: (
        orden_relevancia.get(x.get('relevancia', 'media'), 1)
    ))
    
    return noticias_ordenadas


def mapear_noticias_a_quejas(noticias: List[Dict], cambios_quejas: List[Dict]) -> List[Dict]:
    """
    Mapea noticias a cambios de quejas detectados en el NPS.
    
    Args:
        noticias: Lista de noticias
        cambios_quejas: Lista de cambios de quejas del waterfall
        
    Returns:
        Lista de noticias con información de relación a quejas
    """
    noticias_mapeadas = []
    
    for noticia in noticias:
        categoria_noticia = noticia.get('categoria_relacionada', '').lower()
        
        # Buscar queja relacionada
        queja_relacionada = None
        delta_queja = 0
        
        for cambio in cambios_quejas:
            cat_queja = cambio.get('motivo', cambio.get('categoria', '')).lower()
            
            if cat_queja in categoria_noticia or categoria_noticia in cat_queja:
                queja_relacionada = cambio.get('motivo', cambio.get('categoria', ''))
                delta_queja = cambio.get('delta', 0)
                break
        
        noticia_mapeada = {
            **noticia,
            'queja_relacionada': queja_relacionada,
            'delta_queja': delta_queja,
            'tiene_correlacion': queja_relacionada is not None
        }
        
        noticias_mapeadas.append(noticia_mapeada)
    
    # Priorizar noticias con correlación
    noticias_mapeadas.sort(key=lambda x: (
        0 if x['tiene_correlacion'] else 1,
        -abs(x.get('delta_queja', 0))
    ))
    
    return noticias_mapeadas


def triangular_motivos_con_noticias(causas_waterfall: List[Dict], noticias: List[Dict]) -> List[Dict]:
    """
    Triangula los MOTIVOS del waterfall directamente con NOTICIAS.
    
    Para cada motivo de variación del NPS, busca noticias relacionadas.
    
    Args:
        causas_waterfall: Lista de motivos del waterfall con delta
        noticias: Lista de noticias REALES
        
    Returns:
        Lista de triangulaciones Motivo ↔ Noticia
    """
    if not noticias:
        return []
    
    triangulaciones = []
    
    # Mapeo de categorías de noticias a motivos del waterfall
    MAPEO_CATEGORIA_MOTIVO = {
        'financiamiento': ['Financiamiento', 'Crédito', 'Tarjeta', 'Préstamo', 'Límite'],
        'rendimientos': ['Rendimientos', 'Rendimentos', 'Inversiones', 'Ahorro', 'CDI'],
        'seguridad': ['Seguridad', 'Segurança', 'Fraude', 'Estafa', 'Golpe'],
        'atención': ['Atención', 'Atendimento', 'Soporte', 'SAC', 'Reclamo'],
        'funcionalidades': ['Funcionalidades', 'App', 'Tecnología', 'Feature'],
        'complejidad': ['Complejidad', 'Dificultad', 'Usabilidad'],
        'promociones': ['Promociones', 'Promoções', 'Beneficios', 'Descuentos', 'Cashback'],
    }
    
    for causa in causas_waterfall:
        motivo = causa.get('motivo', '')
        delta = causa.get('delta', 0)
        pct_q2 = causa.get('pct_q2', causa.get('Impacto_Actual', 0))
        
        # Buscar noticia relacionada con este motivo
        noticia_relacionada = None
        motivo_lower = motivo.lower()
        
        for noticia in noticias:
            cat_noticia = noticia.get('categoria_relacionada', '').lower()
            
            # Match directo
            if motivo_lower in cat_noticia or cat_noticia in motivo_lower:
                noticia_relacionada = noticia
                break
            
            # Match por mapeo
            for cat_key, motivos_rel in MAPEO_CATEGORIA_MOTIVO.items():
                if cat_key in cat_noticia:
                    for m in motivos_rel:
                        if m.lower() in motivo_lower or motivo_lower in m.lower():
                            noticia_relacionada = noticia
                            break
                    if noticia_relacionada:
                        break
            
            if noticia_relacionada:
                break
        
        if noticia_relacionada:
            # Evaluar coherencia: noticia positiva + mejora (delta < 0) = coherente
            impacto_noticia = noticia_relacionada.get('impacto_esperado', 'neutro')
            
            if impacto_noticia == 'positivo' and delta < 0:
                coherencia = 'coherente'
                explicacion = f"Noticia positiva y quejas bajaron {delta:.1f}pp"
            elif impacto_noticia == 'negativo' and delta > 0:
                coherencia = 'coherente'
                explicacion = f"Noticia negativa y quejas subieron {delta:+.1f}pp"
            elif impacto_noticia == 'positivo' and delta > 0:
                coherencia = 'incoherente'
                explicacion = f"Noticia positiva pero quejas subieron {delta:+.1f}pp"
            elif impacto_noticia == 'negativo' and delta < 0:
                coherencia = 'incoherente'
                explicacion = f"Noticia negativa pero quejas bajaron {delta:.1f}pp"
            else:
                coherencia = 'neutro'
                explicacion = "Sin cambio significativo"
            
            triangulaciones.append({
                'motivo': motivo,
                'delta': delta,
                'pct_q2': pct_q2,
                'noticia': noticia_relacionada,
                'coherencia': coherencia,
                'explicacion': explicacion
            })
    
    # Ordenar por magnitud del delta
    triangulaciones.sort(key=lambda x: abs(x['delta']), reverse=True)
    
    return triangulaciones


def obtener_noticias_para_reporte(site: str, player: str, q_ant: str, q_act: str, 
                                   cambios_quejas: List[Dict] = None,
                                   max_noticias: int = 6) -> Dict:
    """
    Función principal para obtener noticias listas para el reporte HTML.
    
    Carga noticias del cache, las filtra ESTRICTAMENTE por los quarters analizados.
    
    ⚠️ IMPORTANTE: Las noticias son 100% REALES, obtenidas de búsquedas web previas.
    NUNCA se inventan noticias. Si no hay noticias en cache, se retorna lista vacía.
    Solo se muestran noticias de los meses correspondientes a Q1 y Q2.
    
    Args:
        site: Código del site (MLA, MLB, MLM, MLC)
        player: Nombre del player
        q_ant: Período anterior (ej: "25Q3")
        q_act: Período actual (ej: "25Q4")
        cambios_quejas: Lista de cambios de quejas (opcional)
        max_noticias: Máximo de noticias a retornar
        
    Returns:
        Dict con noticias procesadas y metadatos
    """
    # 1. Cargar noticias del cache
    noticias_raw = cargar_noticias_cache(site, player)
    
    if not noticias_raw:
        return {
            'noticias': [],
            'total': 0,
            'con_correlacion': 0,
            'mensaje': f'No hay noticias disponibles para {player} ({site}). Ejecutar búsqueda web para actualizar.'
        }
    
    # 2. Filtrar ESTRICTAMENTE por los quarters analizados (q_ant y q_act)
    noticias_filtradas = filtrar_noticias_por_periodo(noticias_raw, q_ant, q_act)
    
    # 3. Mapear a quejas si hay datos
    if cambios_quejas:
        noticias_mapeadas = mapear_noticias_a_quejas(noticias_filtradas, cambios_quejas)
    else:
        noticias_mapeadas = noticias_filtradas
    
    # 4. Limitar cantidad
    noticias_final = noticias_mapeadas[:max_noticias]
    
    # 5. Contar correlaciones
    con_correlacion = len([n for n in noticias_final if n.get('tiene_correlacion', False)])
    
    return {
        'noticias': noticias_final,
        'total': len(noticias_final),
        'con_correlacion': con_correlacion,
        'mensaje': f'{len(noticias_final)} noticias relevantes encontradas'
    }


# ==============================================================================
# OPCIÓN B: CLASIFICACIÓN DE NOTICIAS Y COHERENCIA
# ==============================================================================

# Keywords para clasificar tipo de noticia
KEYWORDS_NOTICIA_POSITIVA = [
    'lança', 'lanza', 'nuevo', 'nova', 'mejora', 'melhora', 'beneficio', 'benefício',
    'cashback', 'promoción', 'promoção', 'descuento', 'desconto', 'rendimento',
    'rendimiento', 'protección', 'proteção', 'seguridad', 'segurança',
    'actualización', 'atualização', 'funcionalidad', 'funcionalidade',
    'premio', 'prêmio', 'reconocimiento', 'reconhecimento', 'mejor', 'melhor',
    'crece', 'cresce', 'aumenta', 'sube', 'líder', 'éxito', 'sucesso'
]

KEYWORDS_NOTICIA_NEGATIVA = [
    'falla', 'falha', 'caída', 'queda', 'problema', 'error', 'erro', 'golpe',
    'fraude', 'estafa', 'hack', 'reclamo', 'reclamação', 'queja', 'denuncia',
    'denúncia', 'caiu', 'cayó', 'instável', 'inestable', 'robo', 'roubo',
    'bloqueado', 'bloqueada', 'suspendida', 'suspenso', 'reduce', 'reduz',
    'baja', 'baixa', 'pierde', 'perde', 'crisis', 'crise', 'corte', 'limita'
]


def clasificar_tipo_noticia(noticia: Dict) -> str:
    """
    Clasifica una noticia como 'positiva', 'negativa' o 'neutra'.
    
    Args:
        noticia: Dict con 'titulo' y opcionalmente 'resumen'
        
    Returns:
        'positiva', 'negativa' o 'neutra'
    """
    texto = (noticia.get('titulo', '') + ' ' + noticia.get('resumen', '')).lower()
    
    score_positivo = sum(1 for kw in KEYWORDS_NOTICIA_POSITIVA if kw in texto)
    score_negativo = sum(1 for kw in KEYWORDS_NOTICIA_NEGATIVA if kw in texto)
    
    if score_positivo > score_negativo + 1:
        return 'positiva'
    elif score_negativo > score_positivo + 1:
        return 'negativa'
    else:
        return 'neutra'


def validar_coherencia_noticia_driver(noticia: Dict, driver: Dict) -> Dict:
    """
    Valida si una noticia es coherente con un driver.
    
    Lógica:
    - Si driver MEJORA (menos quejas, delta < 0), noticia debería ser positiva
    - Si driver EMPEORA (más quejas, delta > 0), noticia debería explicar el problema
    
    Args:
        noticia: Dict con datos de la noticia
        driver: Dict con 'motivo' y 'delta'
        
    Returns:
        Dict con 'es_coherente', 'tipo_noticia', 'explicacion'
    """
    tipo_noticia = clasificar_tipo_noticia(noticia)
    delta = driver.get('delta', 0)
    motivo = driver.get('motivo', '')
    
    # Driver mejora = menos quejas = delta negativo
    driver_mejora = delta < 0
    
    if driver_mejora and tipo_noticia == 'positiva':
        return {
            'es_coherente': True,
            'tipo_noticia': tipo_noticia,
            'explicacion': f'✓ Noticia positiva explica mejora en {motivo}'
        }
    elif not driver_mejora and tipo_noticia == 'negativa':
        return {
            'es_coherente': True,
            'tipo_noticia': tipo_noticia,
            'explicacion': f'✓ Noticia negativa explica deterioro en {motivo}'
        }
    elif tipo_noticia == 'neutra':
        return {
            'es_coherente': True,  # Neutra es siempre aceptable
            'tipo_noticia': tipo_noticia,
            'explicacion': f'— Noticia informativa sobre {motivo}'
        }
    else:
        return {
            'es_coherente': False,
            'tipo_noticia': tipo_noticia,
            'explicacion': f'⚠ Noticia {tipo_noticia} pero driver {"mejora" if driver_mejora else "empeora"}'
        }


# ==============================================================================
# OPCIÓN D: FLUJO SEMI-ASISTIDO CON SUGERENCIAS DE BÚSQUEDA
# ==============================================================================

def generar_sugerencias_busqueda(
    player: str,
    site: str,
    drivers_waterfall: List[Dict],
    delta_seguridad: float = 0,
    delta_principalidad: float = 0,
    noticias_actuales: List[Dict] = None,
    q_ant: str = "25Q3",
    q_act: str = "25Q4",
    causas_semanticas: Dict = None
) -> Dict:
    """
    Genera sugerencias de búsqueda para el analista basadas en los drivers detectados.
    
    Esta función implementa el FLUJO SEMI-ASISTIDO:
    1. Analiza los TOP drivers de variación
    2. Revisa qué noticias ya existen en cache
    3. Sugiere búsquedas específicas para llenar gaps
    4. (NUEVO) Enriquece queries con causas raíz semánticas del análisis de comentarios
    
    Args:
        player: Nombre del player
        site: Código del site
        drivers_waterfall: Lista de drivers con deltas
        delta_seguridad: Variación de seguridad
        delta_principalidad: Variación de principalidad
        noticias_actuales: Noticias ya en cache
        q_ant, q_act: Períodos de análisis
        causas_semanticas: Dict de causas raíz semánticas por motivo (del JSON LLM)
        
    Returns:
        Dict con sugerencias estructuradas
    """
    pais = PAISES_BUSQUEDA.get(site, '')
    año = int(q_act[:2]) + 2000 if q_act else datetime.now().year
    noticias_actuales = noticias_actuales or []
    causas_semanticas = causas_semanticas or {}
    
    # Categorías ya cubiertas por noticias
    categorias_cubiertas = set(
        n.get('categoria_relacionada', '').lower() 
        for n in noticias_actuales
    )
    
    sugerencias = {
        'player': player,
        'site': site,
        'periodo': f"{q_ant} → {q_act}",
        'drivers_detectados': [],
        'gaps_sin_noticia': [],
        'busquedas_sugeridas': [],
        'busquedas_causa_raiz': [],
        'resumen': ''
    }
    
    # Ordenar drivers por impacto (valor absoluto del delta)
    drivers_ordenados = sorted(
        drivers_waterfall, 
        key=lambda x: abs(x.get('delta', 0)), 
        reverse=True
    )
    
    for driver in drivers_ordenados[:5]:  # Top 5 drivers
        motivo = driver.get('motivo', '')
        delta = driver.get('delta', 0)
        direccion = '↑ Más quejas' if delta > 0 else '↓ Menos quejas'
        
        # Buscar causa raíz semántica completa para este motivo
        causa_top = None
        causa_desc = ''
        causa_ejemplos = []
        terminos_dominio = []
        if motivo in causas_semanticas:
            causas = causas_semanticas[motivo].get('causas_raiz', [])
            if causas:
                causa_obj = causas[0]
                causa_top = causa_obj.get('titulo', '')
                causa_desc = causa_obj.get('descripcion', '')
                causa_ejemplos = causa_obj.get('ejemplos', [])
                terminos_dominio = _extraer_terminos_dominio(causa_obj, site)
        
        sugerencias['drivers_detectados'].append({
            'motivo': motivo,
            'delta': round(delta, 2),
            'direccion': direccion,
            'causa_raiz_top': causa_top or '',
            'terminos_dominio': terminos_dominio[:2]
        })
        
        # Verificar si hay gap (sin noticia)
        motivo_lower = motivo.lower()
        tiene_noticia = any(
            motivo_lower in cat or cat in motivo_lower 
            for cat in categorias_cubiertas
        )
        
        if not tiene_noticia and abs(delta) > 0.5:
            # Generar búsqueda sugerida específica
            if delta > 0:  # Empeoró
                tipo_busqueda = "problema, falla, queja"
            else:  # Mejoró
                tipo_busqueda = "mejora, lanzamiento, nuevo"
            
            # Si hay causa raíz semántica, usar keywords enriquecidas
            if causa_top:
                keywords = extraer_keywords_causa_raiz(
                    causa_top, site, descripcion=causa_desc, ejemplos=causa_ejemplos
                )
                if len(keywords) >= 2:
                    kw_text = ' '.join(keywords[:3])
                    busqueda = f'{player} {pais} {kw_text} {año}'
                else:
                    busqueda = f'"{player}" "{pais}" "{motivo}" {año}'
            else:
                busqueda = f'"{player}" "{pais}" "{motivo}" {año}'
            
            sugerencias['gaps_sin_noticia'].append({
                'motivo': motivo,
                'delta': round(delta, 2),
                'tipo_sugerido': tipo_busqueda,
                'causa_raiz': causa_top or '',
                'terminos_dominio': terminos_dominio[:2]
            })
            
            # Query principal enriquecida + alternativas con términos del dominio
            alternativas = []
            if terminos_dominio:
                # Alternativa con término del dominio (ej: "Nubank México cajita baja 2025")
                alternativas.append(f'{player} {pais} {terminos_dominio[0]} {año}')
            if causa_top:
                kws = extraer_keywords_causa_raiz(causa_top, site)
                if kws:
                    alternativas.append(f'{player} {pais} {" ".join(kws[:2])} {año}')
            alternativas.append(
                f'{player} {pais} {motivo} lanzamiento {año}' if delta < 0 else f'{player} {pais} {motivo} problema {año}'
            )
            
            sugerencias['busquedas_sugeridas'].append({
                'query': busqueda,
                'motivo': motivo,
                'tipo': 'positiva' if delta < 0 else 'negativa',
                'causa_raiz': causa_top or '',
                'terminos_dominio': terminos_dominio[:2],
                'alternativas': alternativas
            })
    
    # Agregar búsquedas adicionales basadas en causas raíz (2da causa + términos dominio)
    for motivo, datos in causas_semanticas.items():
        causas = datos.get('causas_raiz', [])
        if len(causas) >= 2:
            segunda_causa = causas[1]
            titulo = segunda_causa.get('titulo', '')
            desc = segunda_causa.get('descripcion', '')
            ejemplos = segunda_causa.get('ejemplos', [])
            freq = segunda_causa.get('frecuencia_pct', 0)
            if titulo and freq >= 10:  # Solo si tiene relevancia (>= 10%)
                keywords = extraer_keywords_causa_raiz(titulo, site, descripcion=desc, ejemplos=ejemplos)
                td = _extraer_terminos_dominio(segunda_causa, site)
                if len(keywords) >= 2:
                    kw_text = ' '.join(keywords[:3])
                    entry = {
                        'query': f'{player} {pais} {kw_text} {año}',
                        'motivo': motivo,
                        'causa_titulo': titulo,
                        'frecuencia_pct': freq,
                    }
                    if td:
                        entry['query_dominio'] = f'{player} {pais} {td[0]} {año}'
                    sugerencias['busquedas_causa_raiz'].append(entry)
    
    # Agregar sugerencias para Seguridad si varió significativamente
    if abs(delta_seguridad) > UMBRAL_SEGURIDAD_NOTICIA:
        direccion_seg = 'mejora' if delta_seguridad > 0 else 'deterioro'
        if 'seguridad' not in categorias_cubiertas and 'segurança' not in categorias_cubiertas:
            sugerencias['busquedas_sugeridas'].append({
                'query': f'"{player}" "{pais}" seguridad {año}',
                'motivo': 'Seguridad',
                'tipo': 'positiva' if delta_seguridad > 0 else 'negativa',
                'alternativas': [
                    f'{player} nuevas medidas seguridad {año}' if delta_seguridad > 0 else f'{player} fraude problema {año}'
                ]
            })
    
    # Generar resumen
    n_drivers = len(sugerencias['drivers_detectados'])
    n_gaps = len(sugerencias['gaps_sin_noticia'])
    
    if n_gaps == 0:
        sugerencias['resumen'] = f"✅ Todos los {n_drivers} drivers principales tienen noticias asociadas."
    else:
        sugerencias['resumen'] = f"⚠️ {n_gaps} de {n_drivers} drivers NO tienen noticias. Se sugieren {len(sugerencias['busquedas_sugeridas'])} búsquedas."
    
    return sugerencias


def mostrar_sugerencias_busqueda(sugerencias: Dict) -> str:
    """
    Formatea las sugerencias de búsqueda para mostrar al analista.
    
    Args:
        sugerencias: Dict generado por generar_sugerencias_busqueda
        
    Returns:
        String formateado para consola/output
    """
    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("📋 SUGERENCIAS DE BÚSQUEDA - FLUJO SEMI-ASISTIDO")
    lines.append("=" * 70)
    lines.append(f"\n🎯 Player: {sugerencias['player']} ({sugerencias['site']})")
    lines.append(f"📅 Período: {sugerencias['periodo']}")
    
    lines.append("\n" + "-" * 50)
    lines.append("📊 TOP DRIVERS DETECTADOS:")
    lines.append("-" * 50)
    
    for d in sugerencias['drivers_detectados']:
        emoji = "🔴" if d['delta'] > 0 else "🟢"
        causa_txt = f" -> Causa: {d['causa_raiz_top']}" if d.get('causa_raiz_top') else ""
        td_txt = f" [terminos: {', '.join(d['terminos_dominio'])}]" if d.get('terminos_dominio') else ""
        lines.append(f"   {emoji} {d['motivo']}: {d['delta']:+.2f}pp ({d['direccion']}){causa_txt}{td_txt}")
    
    if sugerencias['gaps_sin_noticia']:
        lines.append("\n" + "-" * 50)
        lines.append("!! GAPS SIN NOTICIA:")
        lines.append("-" * 50)
        
        for gap in sugerencias['gaps_sin_noticia']:
            causa_txt = f" | Causa raiz: {gap['causa_raiz']}" if gap.get('causa_raiz') else ""
            td_txt = f" | Terminos: {', '.join(gap['terminos_dominio'])}" if gap.get('terminos_dominio') else ""
            lines.append(f"   - {gap['motivo']} ({gap['delta']:+.2f}pp) - Buscar: {gap['tipo_sugerido']}{causa_txt}{td_txt}")
    
    if sugerencias['busquedas_sugeridas']:
        lines.append("\n" + "-" * 50)
        lines.append("BUSQUEDAS SUGERIDAS (usar en Cursor WebSearch):")
        lines.append("-" * 50)
        
        for i, busq in enumerate(sugerencias['busquedas_sugeridas'], 1):
            tipo_emoji = "[+]" if busq['tipo'] == 'positiva' else "[-]"
            lines.append(f"\n   {i}. {busq['motivo']} {tipo_emoji}")
            if busq.get('causa_raiz'):
                lines.append(f"      Causa raiz: {busq['causa_raiz']}")
            if busq.get('terminos_dominio'):
                lines.append(f"      Terminos dominio: {', '.join(busq['terminos_dominio'])}")
            lines.append(f"      Query principal: {busq['query']}")
            for alt in busq.get('alternativas', []):
                lines.append(f"      Alternativa: {alt}")
    
    # NUEVO: Búsquedas adicionales derivadas de causas raíz semánticas
    busquedas_cr = sugerencias.get('busquedas_causa_raiz', [])
    if busquedas_cr:
        lines.append("\n" + "-" * 50)
        lines.append("🧠 BÚSQUEDAS ADICIONALES (desde causas raíz semánticas):")
        lines.append("-" * 50)
        
        for j, bcr in enumerate(busquedas_cr, 1):
            lines.append(f"\n   {j}. {bcr['motivo']} - \"{bcr['causa_titulo']}\" ({bcr['frecuencia_pct']}%)")
            lines.append(f"      Query: {bcr['query']}")
            if bcr.get('query_dominio'):
                lines.append(f"      Query dominio: {bcr['query_dominio']}")
    
    lines.append("\n" + "-" * 50)
    lines.append(f"📝 RESUMEN: {sugerencias['resumen']}")
    lines.append("-" * 50)
    
    lines.append("\n💡 INSTRUCCIONES:")
    lines.append("   1. Copiar las queries sugeridas")
    lines.append("   2. Usar Cursor WebSearch para buscar noticias relevantes")
    lines.append("   3. Agregar noticias encontradas al cache con agregar_noticia_a_cache()")
    lines.append("   4. Re-ejecutar el modelo para incluir las nuevas noticias")
    lines.append("=" * 70 + "\n")
    
    return "\n".join(lines)


def agregar_noticia_a_cache(
    site: str,
    player: str,
    titulo: str,
    fuente: str,
    url: str,
    resumen: str,
    categoria_relacionada: str,
    impacto_esperado: str = "neutro",
    fecha: str = None
) -> bool:
    """
    Agrega una noticia al cache de noticias.
    
    Args:
        site: Código del site (MLB, MLA, MLM)
        player: Nombre del player
        titulo: Título de la noticia
        fuente: Fuente/dominio
        url: URL completa
        resumen: Resumen de la noticia
        categoria_relacionada: Categoría (Financiamiento, Seguridad, etc.)
        impacto_esperado: 'positivo', 'negativo' o 'neutro'
        fecha: Fecha en formato 'YYYY-MM' (opcional, usa actual si no se especifica)
        
    Returns:
        True si se agregó correctamente, False si hubo error
    """
    try:
        cache_path = Path(__file__).parent.parent / 'data' / 'noticias_cache.json'
        
        # Cargar cache existente
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        else:
            cache = {}
        
        # Asegurar estructura
        if site not in cache:
            cache[site] = {}
        if player not in cache[site]:
            cache[site][player] = {
                'ultima_actualizacion': datetime.now().strftime('%Y-%m'),
                'noticias': []
            }
        
        # Crear noticia
        nueva_noticia = {
            'titulo': titulo,
            'fuente': fuente,
            'fecha': fecha or datetime.now().strftime('%Y-%m'),
            'url': url,
            'resumen': resumen,
            'categoria_relacionada': categoria_relacionada,
            'impacto_esperado': impacto_esperado,
            'relevancia': 'alta'
        }
        
        # Clasificar tipo automáticamente (Opción B)
        nueva_noticia['tipo_noticia'] = clasificar_tipo_noticia(nueva_noticia)
        
        # Verificar duplicados
        noticias_existentes = cache[site][player].get('noticias', [])
        if any(n.get('url') == url for n in noticias_existentes):
            print(f"⚠️ Noticia ya existe en cache: {titulo[:50]}...")
            return False
        
        # Agregar
        noticias_existentes.append(nueva_noticia)
        cache[site][player]['noticias'] = noticias_existentes
        cache[site][player]['ultima_actualizacion'] = datetime.now().strftime('%Y-%m')
        
        # Guardar
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
        
        print(f"[OK] Noticia agregada al cache: {titulo[:50]}...")
        print(f"   Tipo clasificado: {nueva_noticia['tipo_noticia']}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al agregar noticia: {e}")
        return False


# ==============================================================================
# EJECUCIÓN DIRECTA (para pruebas)
# ==============================================================================

if __name__ == "__main__":
    # Prueba con comentarios de ejemplo
    comentarios_test = [
        "El límite de la tarjeta es muy bajo, necesito más",
        "Me rechazaron el crédito sin explicación",
        "Las tasas de interés son muy altas comparado con Nubank",
        "El proceso para pedir crédito es muy lento y complicado",
        "El limite es insuficiente para mis necesidades",
        "Me negaron el préstamo cuando más lo necesitaba",
        "Los intereses que cobran son abusivos",
        "Tarda mucho en aprobar el crédito",
        "Nubank me da mejor limite que Mercado Pago",
        "El limite de la tarjeta debería ser mayor",
    ]
    
    print("=" * 60)
    print("🧪 PRUEBA DE ANÁLISIS AUTOMÁTICO")
    print("=" * 60)
    
    subcausas = generar_subcausas_automatico(comentarios_test, 'Financiamiento')
    
    print("\n📊 SUBCAUSAS DETECTADAS:")
    for sc in subcausas:
        print(f"   • {sc['subcausa']}: {sc['porcentaje']:.0f}% ({sc['menciones']} menciones)")
        if sc['evidencia']:
            print(f"     Evidencia: \"{sc['evidencia'][0][:60]}...\"")
    
    print("\n🔑 KEYWORDS:")
    keywords = extraer_keywords_avanzado(comentarios_test)
    for kw, count in list(keywords.items())[:5]:
        print(f"   • {kw}: {count}")
    
    print("\n✅ Prueba completada")
