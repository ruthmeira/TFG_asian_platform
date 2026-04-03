from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, Response, stream_with_context
import json
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth  # Nueva importación
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from models import db, User, CollectionItem
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
import threading

GLOBAL_COUNTRIES_LIST = [{"code": "AL", "name": "Albania", "emoji": "🇦🇱"}, {"code": "DE", "name": "Alemania", "emoji": "🇩🇪"}, {"code": "AD", "name": "Andorra", "emoji": "🇦🇩"}, {"code": "AO", "name": "Angola", "emoji": "🇦🇴"}, {"code": "AG", "name": "Antigua y Barbuda", "emoji": "🇦🇬"}, {"code": "SA", "name": "Arabia Saudí", "emoji": "🇸🇦"}, {"code": "DZ", "name": "Argelia", "emoji": "🇩🇿"}, {"code": "AR", "name": "Argentina", "emoji": "🇦🇷"}, {"code": "AU", "name": "Australia", "emoji": "🇦🇺"}, {"code": "AT", "name": "Austria", "emoji": "🇦🇹"}, {"code": "AZ", "name": "Azerbaiyán", "emoji": "🇦🇿"}, {"code": "BS", "name": "Bahamas", "emoji": "🇧🇸"}, {"code": "BB", "name": "Barbados", "emoji": "🇧🇧"}, {"code": "BH", "name": "Baréin", "emoji": "🇧🇭"}, {"code": "BZ", "name": "Belice", "emoji": "🇧🇿"}, {"code": "BM", "name": "Bermudas", "emoji": "🇧🇲"}, {"code": "BY", "name": "Bielorrusia", "emoji": "🇧🇾"}, {"code": "BO", "name": "Bolivia", "emoji": "🇧🇴"}, {"code": "BA", "name": "Bosnia-Herzegovina", "emoji": "🇧🇦"}, {"code": "BR", "name": "Brasil", "emoji": "🇧🇷"}, {"code": "BG", "name": "Bulgaria", "emoji": "🇧🇬"}, {"code": "BF", "name": "Burkina Faso", "emoji": "🇧🇫"}, {"code": "BE", "name": "Bélgica", "emoji": "🇧🇪"}, {"code": "CV", "name": "Cabo Verde", "emoji": "🇨🇻"}, {"code": "CM", "name": "Camerún", "emoji": "🇨🇲"}, {"code": "CA", "name": "Canadá", "emoji": "🇨🇦"}, {"code": "CN", "name": "China", "emoji": "🇨🇳"}, {"code": "QA", "name": "Catar", "emoji": "🇶🇦"}, {"code": "TD", "name": "Chad", "emoji": "🇹🇩"}, {"code": "CL", "name": "Chile", "emoji": "🇨🇱"}, {"code": "CY", "name": "Chipre", "emoji": "🇨🇾"}, {"code": "VA", "name": "Ciudad del Vaticano", "emoji": "🇻🇦"}, {"code": "CO", "name": "Colombia", "emoji": "🇨🇴"}, {"code": "KR", "name": "Corea del Sur", "emoji": "🇰🇷"}, {"code": "CR", "name": "Costa Rica", "emoji": "🇨🇷"}, {"code": "CI", "name": "Costa de Marfil", "emoji": "🇨🇮"}, {"code": "HR", "name": "Croacia", "emoji": "🇭🇷"}, {"code": "CU", "name": "Cuba", "emoji": "🇨🇺"}, {"code": "DK", "name": "Dinamarca", "emoji": "🇩🇰"}, {"code": "EC", "name": "Ecuador", "emoji": "🇪🇨"}, {"code": "EG", "name": "Egipto", "emoji": "🇪🇬"}, {"code": "SV", "name": "El Salvador", "emoji": "🇸🇻"}, {"code": "AE", "name": "Emiratos Árabes Unidos", "emoji": "🇦🇪"}, {"code": "SK", "name": "Eslovaquia", "emoji": "🇸🇰"}, {"code": "SI", "name": "Eslovenia", "emoji": "🇸🇮"}, {"code": "ES", "name": "España", "emoji": "🇪🇸"}, {"code": "US", "name": "Estados Unidos", "emoji": "🇺🇸"}, {"code": "EE", "name": "Estonia", "emoji": "🇪🇪"}, {"code": "PH", "name": "Filipinas", "emoji": "🇵🇭"}, {"code": "FI", "name": "Finlandia", "emoji": "🇫🇮"}, {"code": "FJ", "name": "Fiyi", "emoji": "🇫🇯"}, {"code": "FR", "name": "Francia", "emoji": "🇫🇷"}, {"code": "GH", "name": "Ghana", "emoji": "🇬🇭"}, {"code": "GI", "name": "Gibraltar", "emoji": "🇬🇮"}, {"code": "GR", "name": "Grecia", "emoji": "🇬🇷"}, {"code": "GP", "name": "Guadalupe", "emoji": "🇬🇵"}, {"code": "GT", "name": "Guatemala", "emoji": "🇬🇹"}, {"code": "GF", "name": "Guayana Francesa", "emoji": "🇬🇫"}, {"code": "GQ", "name": "Guinea Ecuatorial", "emoji": "🇬🇶"}, {"code": "GY", "name": "Guyana", "emoji": "🇬🇾"}, {"code": "HN", "name": "Honduras", "emoji": "🇭🇳"}, {"code": "HU", "name": "Hungría", "emoji": "🇭🇺"}, {"code": "IN", "name": "India", "emoji": "🇮🇳"}, {"code": "ID", "name": "Indonesia", "emoji": "🇮🇩"}, {"code": "IQ", "name": "Iraq", "emoji": "🇮🇶"}, {"code": "IE", "name": "Irlanda", "emoji": "🇮🇪"}, {"code": "IS", "name": "Islandia", "emoji": "🇮🇸"}, {"code": "TC", "name": "Islas Turcas y Caicos", "emoji": "🇹🇨"}, {"code": "IL", "name": "Israel", "emoji": "🇮🇱"}, {"code": "IT", "name": "Italia", "emoji": "🇮🇹"}, {"code": "JM", "name": "Jamaica", "emoji": "🇯🇲"}, {"code": "JP", "name": "Japón", "emoji": "🇯🇵"}, {"code": "JO", "name": "Jordania", "emoji": "🇯🇴"}, {"code": "KE", "name": "Kenia", "emoji": "🇰🇪"}, {"code": "XK", "name": "Kosovo", "emoji": "🇽🇰"}, {"code": "KW", "name": "Kuwait", "emoji": "🇰🇼"}, {"code": "LV", "name": "Letonia", "emoji": "🇱🇻"}, {"code": "LY", "name": "Libia", "emoji": "🇱🇾"}, {"code": "LI", "name": "Liechtenstein", "emoji": "🇱🇮"}, {"code": "LT", "name": "Lituania", "emoji": "🇱🇹"}, {"code": "LU", "name": "Luxemburgo", "emoji": "🇱🇺"}, {"code": "LB", "name": "Líbano", "emoji": "🇱🇧"}, {"code": "MO", "name": "Macao", "emoji": "🇲🇴"}, {"code": "MK", "name": "Macedonia", "emoji": "🇲🇰"}, {"code": "MG", "name": "Madagascar", "emoji": "🇲🇬"}, {"code": "MY", "name": "Malasía", "emoji": "🇲🇾"}, {"code": "MW", "name": "Malaui", "emoji": "🇲🇼"}, {"code": "ML", "name": "Mali", "emoji": "🇲🇱"}, {"code": "MT", "name": "Malta", "emoji": "🇲🇹"}, {"code": "MA", "name": "Marruecos", "emoji": "🇲🇦"}, {"code": "MU", "name": "Mauricio", "emoji": "🇲🇺"}, {"code": "MD", "name": "Moldavia", "emoji": "🇲🇩"}, {"code": "ME", "name": "Montenegro", "emoji": "🇲🇪"}, {"code": "MZ", "name": "Mozambique", "emoji": "🇲🇿"}, {"code": "MX", "name": "México", "emoji": "🇲🇽"}, {"code": "MC", "name": "Mónaco", "emoji": "🇲🇨"}, {"code": "NI", "name": "Nicaragua", "emoji": "🇳🇮"}, {"code": "NG", "name": "Nigeria", "emoji": "🇳🇬"}, {"code": "NO", "name": "Noruega", "emoji": "🇳🇴"}, {"code": "NZ", "name": "Nueva Zelanda", "emoji": "🇳🇿"}, {"code": "NE", "name": "Níger", "emoji": "🇳🇪"}, {"code": "OM", "name": "Omán", "emoji": "🇴🇲"}, {"code": "PK", "name": "Pakistán", "emoji": "🇵🇰"}, {"code": "PA", "name": "Panamá", "emoji": "🇵🇦"}, {"code": "PG", "name": "Papúa Nueva Guinea", "emoji": "🇵🇬"}, {"code": "PY", "name": "Paraguay", "emoji": "🇵🇾"}, {"code": "NL", "name": "Países Bajos", "emoji": "🇳🇱"}, {"code": "PE", "name": "Perú", "emoji": "🇵🇪"}, {"code": "PF", "name": "Polinesia Francesa", "emoji": "🇵🇫"}, {"code": "PL", "name": "Polonia", "emoji": "🇵🇱"}, {"code": "PT", "name": "Portugal", "emoji": "🇵🇹"}, {"code": "HK", "name": "RAE de Hong Kong (China)", "emoji": "🇭🇰"}, {"code": "GB", "name": "Reino Unido", "emoji": "🇬🇧"}, {"code": "CZ", "name": "República Checa", "emoji": "🇨🇿"}, {"code": "CD", "name": "República Democrática del Congo", "emoji": "🇨🇩"}, {"code": "DO", "name": "República Dominicana", "emoji": "🇩🇴"}, {"code": "RO", "name": "Rumanía", "emoji": "🇷🇴"}, {"code": "RU", "name": "Rusia", "emoji": "🇷🇺"}, {"code": "SM", "name": "San Marino", "emoji": "🇸🇲"}, {"code": "LC", "name": "Santa Lucía", "emoji": "🇱🇨"}, {"code": "SN", "name": "Senegal", "emoji": "🇸🇳"}, {"code": "RS", "name": "Serbia", "emoji": "🇷🇸"}, {"code": "SC", "name": "Seychelles", "emoji": "🇸🇨"}, {"code": "SG", "name": "Singapur", "emoji": "🇸🇬"}, {"code": "ZA", "name": "Sudáfrica", "emoji": "🇿🇦"}, {"code": "SE", "name": "Suecia", "emoji": "🇸🇪"}, {"code": "CH", "name": "Suiza", "emoji": "🇨🇭"}, {"code": "TH", "name": "Tailandia", "emoji": "🇹🇭"}, {"code": "TW", "name": "Taiwán", "emoji": "🇹🇼"}, {"code": "TZ", "name": "Tanzania", "emoji": "🇹🇿"}, {"code": "PS", "name": "Territorios Palestinos", "emoji": "🇵🇸"}, {"code": "TT", "name": "Trinidad y Tobago", "emoji": "🇹🇹"}, {"code": "TR", "name": "Turquía", "emoji": "🇹🇷"}, {"code": "TN", "name": "Túnez", "emoji": "🇹🇳"}, {"code": "UA", "name": "Ucrania", "emoji": "🇺🇦"}, {"code": "UG", "name": "Uganda", "emoji": "🇺🇬"}, {"code": "UY", "name": "Uruguay", "emoji": "🇺🇾"}, {"code": "VE", "name": "Venezuela", "emoji": "🇻🇪"}, {"code": "YE", "name": "Yemen", "emoji": "🇾🇪"}, {"code": "ZM", "name": "Zambia", "emoji": "🇿🇲"}, {"code": "ZW", "name": "Zimbabue", "emoji": "🇿🇼"}]


# Mapa de banderas para acceso rápido en plantillas
REGIONS_MAP = {c['code']: c['emoji'] for c in GLOBAL_COUNTRIES_LIST}

# --- CONSTANTES MAESTRAS ASIÁTICAS ---
ASIA_LANGUAGES = [
    # Corea, Japón, China y regiones
    'ko', 'ja', 'zh', 'cn', 'yue', 'bo', 'ug', 'mn',
    # Sudeste Asiático (Países ASEAN)
    'th', 'vi', 'tl', 'fil', 'id', 'ms', 'km', 'my', 'lo',
    # Sur de Asia (India, Nepal, etc.)
    'hi', 'ne', 'ta', 'te', 'ml', 'kn', 'bn', 'mr', 'gu', 'pa', 'ur', 'or', 'as', 'sd', 'si', 'dz', 'ks'
]
ASIA_COUNTRIES = [
    'KR', 'JP', 'CN', 'TW', 'HK', 'TH', 'VN', 'IN', 'PH', 'ID', 'MY', 'SG', 'MO',
    'MN', 'KH', 'MM', 'LA', 'NP'
]
ASIA_FLAGS_MAP = {
    'KR':'🇰🇷','JP':'🇯🇵','CN':'🇨🇳','TW':'🇹🇼','HK':'🇭🇰','TH':'🇹🇭','VN':'🇻🇳','IN':'🇮🇳',
    'PH':'🇵🇭','ID':'🇮🇩','MY':'🇲🇾','SG':'🇸🇬','MO':'🇲🇴','MN':'🇲🇳','KH':'🇰🇭','MM':'🇲🇲',
    'LA':'🇱🇦','NP':'🇳🇵'
}
ASIA_LANG_NAMES = {
    'ko':'Coreano', 'ja':'Japonés', 'zh':'Chino', 'cn':'Chino', 'yue':'Cantonés',
    'th':'Tailandés', 'vi':'Vietnamita', 'id':'Indonesio', 'tl':'Filipino', 'fil':'Filipino',
    'ms':'Malayo', 'mn':'Mongol', 'km':'Camboyano', 'my':'Birmano', 'lo':'Laosiano',
    'ne':'Nepalí', 'hi':'Hindi', 'ta':'Tamil', 'te':'Telugu', 'ml':'Malayalam', 'kn':'Canarés',
    'bn':'Bengalí', 'mr':'Maratí', 'gu':'Guyaratí', 'pa':'Panyabí', 'ur':'Urdu', 'or':'Oriya',
    'as':'Asamés', 'sd':'Sindi', 'si':'Cingalés', 'dz':'Butanés', 'ks':'Cachemiro',
    'bo':'Tibetano', 'ug':'Uigur'
}
GENRES_PROGRAMAS = [10764, 99, 10763, 10767] # Reality, Docu, Noticias, Talk Show

# --- MAPEOS DE TRADUCCIÓN Y CÓDIGOS ---
LANG_TO_COUNTRY_MAP = {
    'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN',
    'id':'ID','tl':'PH','fil':'PH','ms':'MY','mn':'MN',
    'km':'KH','my':'MM','lo':'LA','ne':'NP',
    'zh':'CN', 'cn':'CN', 'yue':'HK',
    'ta':'IN','te':'IN','ml':'IN','kn':'IN','bn':'IN',
    'mr':'IN','gu':'IN','pa':'IN','ur':'IN','or':'IN',
    'as':'IN','sd':'IN','ks':'IN',
    'bo':'CN','ug':'CN'
}

ELITE_PROVIDER_IDS = {8, 337, 283, 119, 9, 149, 115, 1899, 384, 350, 344, 1773, 188}
PROVIDER_UPGRADE_MAP = {9:119, 115:149, 1899:384}

GENRE_MAP_ES = {'Action & Adventure': 'Acción y Aventura', 'Kids': 'Infantil', 'News': 'Noticias', 'Sci-Fi & Fantasy': 'Ciencia Ficción y Fantasía', 'War & Politics': 'Guerra y Política'}
STATUS_MAP_ES = {'Ended':'Finalizada','Returning Series':'En emisión','Planned':'Planeada','Canceled':'Cancelada','In Production':'En producción','Released':'Estrenada'}
DEPT_MAP_ES = {"Directing": "Dirección", "Writing": "Guion", "Production": "Producción", "Art": "Arte", "Camera": "Cámara", "Costume & Make-Up": "Vestuario y Maquillaje", "Visual Effects": "Efectos Visuales", "Sound": "Sonido", "Editing": "Edición", "Crew": "Equipo", "Lighting": "Iluminación", "Actors": "Actores"}

# Datos para filtros de exploración
ASIA_COUNTRIES_DATA = {
    'KR': 'Corea del Sur', 'JP': 'Japón', 'CN': 'China', 'TW': 'Taiwán', 
    'HK': 'Hong Kong', 'MO': 'Macao', 'MN': 'Mongolia', 'TH': 'Tailandia', 
    'VN': 'Vietnam', 'IN': 'India', 'NP': 'Nepal', 'PH': 'Filipinas', 
    'ID': 'Indonesia', 'MY': 'Malasia', 'SG': 'Singapur', 'KH': 'Camboya', 
    'MM': 'Myanmar', 'LA': 'Laos'
}

GENRES_BY_TYPE = {
    'movie': {
        '28':'Acción', '16':'Animación', '12':'Aventura', '10752':'Bélica', '878':'Ciencia ficción', 
        '35':'Comedia', '80':'Crimen', '99':'Documental', '18':'Drama', '10751':'Familia', 
        '14':'Fantasía', '36':'Historia', '9648':'Misterio', '10402':'Música', '10770':'Película de TV', 
        '10749':'Romance', '53':'Suspense', '27':'Terror', '37':'Western'
    },
    'tv': {
        '10759':'Acción y Aventura', '16':'Animación', '35':'Comedia', '80':'Crimen', 
        '18':'Drama', '10751':'Familia', '10762':'Infantil', '9648':'Misterio', 
        '10765':'Ciencia Ficción y Fantasía', '10766':'Soap', '10768':'Guerra y Política', '37':'Western'
    },
    'show': {
        '10764':'Reality', '99':'Documental', '10763':'Noticias', '10767':'Talk Show'
    }
}

# --- UTILIDADES MAESTRAS ---
tmdb_session = requests.Session()

def fetch_json(url):
    try:
        response = tmdb_session.get(url, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

# --- SISTEMA DE SINCRONIZACIÓN AUTOMÁTICA (Silent Refresh) ---
def get_media_summary(m_id, m_type):
    """
    Obtiene los datos base (tarjeta) de un medio usando la jerarquía ES/MX/EN.
    Retorna un dict con título, póster, voto, bandera y tipo.
    """
    api_key = os.getenv("TMDB_API_KEY")
    urls = {
        'es': f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={api_key}&language=es-ES",
        'mx': f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={api_key}&language=es-MX",
        'en': f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={api_key}&language=en-US"
    }
    
    raw = {}
    for lang, url in urls.items():
        resp = fetch_json(url)
        if resp and resp.get('id'): raw[lang] = resp
    
    if not raw.get('en'): return None

    # Procesamiento unificado de la "card"
    summary = {
        'title': get_tiered_field(raw, 'title', m_type),
        'poster_path': raw.get('es', {}).get('poster_path') or raw.get('en', {}).get('poster_path'),
        'vote_average': raw.get('en', {}).get('vote_average', 0),
        'original_title': raw['en'].get('original_title' if m_type=='movie' else 'original_name'),
    }
    
    # Bandera y Subtipo (Basado en IDs para consistencia total)
    res_en = raw['en']
    summary['flag'] = get_media_flag(raw.get('es', res_en), res_en)
    
    genre_ids = [g.get('id') for g in res_en.get('genres', [])]
    if m_type == 'movie':
        summary['media_subtype'] = 'Película'
    else:
        is_prod = any(gid in GENRES_PROGRAMAS for gid in genre_ids)
        summary['media_subtype'] = 'Programa' if is_prod else 'Serie'
    
    return summary

def sync_collections():
    """
    Vigila los cambios globales en TMDB y actualiza nuestra caché local de colecciones.
    """
    with app.app_context():
        api_key = os.getenv("TMDB_API_KEY")
        if not api_key: return

        try:
            # 1. Lista de cambios globales
            movie_changes = fetch_json(f"https://api.themoviedb.org/3/movie/changes?api_key={api_key}").get('results', [])
            tv_changes = fetch_json(f"https://api.themoviedb.org/3/tv/changes?api_key={api_key}").get('results', [])
            
            changed_ids = {
                'movie': {x['id'] for x in movie_changes},
                'tv': {x['id'] for x in tv_changes}
            }
            
            # 2. Cruce con DB
            all_media_ids = db.session.query(CollectionItem.media_id, CollectionItem.media_type).distinct().all()
            to_refresh = [(m_id, m_type) for m_id, m_type in all_media_ids if m_id in changed_ids.get(m_type, {})]
            
            if not to_refresh: return

            # 3. Refresco rápido usando el nuevo helper
            for m_id, m_type in to_refresh:
                new_data = get_media_summary(m_id, m_type)
                if not new_data: continue

                items_in_db = CollectionItem.query.filter_by(media_id=m_id, media_type=m_type).all()
                for item in items_in_db:
                    item.title = new_data['title']
                    item.poster_path = new_data['poster_path']
                    item.vote_average = new_data['vote_average']
                    item.flag = new_data['flag']
                    item.original_title = new_data['original_title']
                    item.media_subtype = new_data['media_subtype']
                
                db.session.commit()
                time.sleep(0.2) 
                
        except Exception as e:
            print(f"[Sync] Error: {str(e)}")

# Configuración del Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=sync_collections, trigger="interval", hours=24)
# ------------------------------------------------------------


def clean_overview(text):
    if not text: return None
    placeholders = ["sinopsis no disponible", "no hay sinopsis disponible", "no overview", "add a plot"]
    t_lower = text.lower()
    for p in placeholders:
        if p in t_lower and len(text) < 50:
            return None
    return text

def get_media_flag(item, det_res=None, country_hint=None):
    """
    Lógica maestra de banderas:
    1. Si el idioma coincide con uno de los países de producción, manda ese (Corea+China hablando coreano = Corea).
    2. Si el idioma no coincide con ninguno, manda el primer país del registro (Singapur hablando chino = Singapur).
    3. Fallback inteligente con Hint (Taiwán/HK) si no hay países.
    4. Fallback final por mapeo de idioma.
    """
    paises_origin = [p.upper() for p in item.get('origin_country', [])]
    paises_prod = []
    if det_res:
         paises_prod = [c['iso_3166_1'].upper() for c in det_res.get('production_countries', [])]
    
    todos_paises = list(set(paises_origin + paises_prod))
    # Para mantener el orden de prioridad del registro original (TV tiene primacía en origin_country)
    paises_ordenados = []
    if item.get('origin_country'): 
        for p in item['origin_country']:
            if p.upper() not in paises_ordenados: paises_ordenados.append(p.upper())
    if det_res and det_res.get('production_countries'):
        for c in det_res['production_countries']:
            p = c['iso_3166_1'].upper()
            if p not in paises_ordenados: paises_ordenados.append(p)

    lang = item.get('original_language', '').lower()
    c_sug = LANG_TO_COUNTRY_MAP.get(lang)

    # REGLA 1: COINCIDENCIA IDIOMA-PAÍS (Prioridad Inteligente y Respeto al Orden)
    # Refinamiento para co-producciones Chinas/HK/TW (Tal como pidió el usuario)
    if lang in ['zh', 'cn', 'yue']:
        # Si el PRIMER país ya es de habla china, manda el orden oficial
        if paises_ordenados and paises_ordenados[0] in ['CN', 'HK', 'TW', 'MO']:
            return ASIA_FLAGS_MAP[paises_ordenados[0]]
            
        # Si el primero no lo es, buscamos el "match" más lógico segun dialecto
        if lang == 'yue' and 'HK' in paises_ordenados: return ASIA_FLAGS_MAP['HK']
        if lang in ['zh', 'cn'] and 'CN' in paises_ordenados: return ASIA_FLAGS_MAP['CN']
        
        # Por si acaso, si hay algun territorio chino en la lista aunque no sea el primero
        for p in ['CN', 'HK', 'TW', 'MO']:
            if p in paises_ordenados: return ASIA_FLAGS_MAP[p]

    # Caso estándar (Corea -> KR, Japón -> JP, etc.)
    if c_sug and c_sug in paises_ordenados:
        return ASIA_FLAGS_MAP.get(c_sug, '🌏')

    # REGLA 2: NO COINCIDE IDIOMA-PAÍS -> EL PRIMER PAÍS ASIÁTICO REGISTRADO
    if paises_ordenados:
        for p in paises_ordenados:
            if p in ASIA_FLAGS_MAP: return ASIA_FLAGS_MAP[p]

    # REGLA 3: FALLBACK POR IDIOMA (Para consistencia en Home, Explorar y Personas)
    if c_sug and c_sug in ASIA_FLAGS_MAP:
        return ASIA_FLAGS_MAP[c_sug]

    # REGLA 4: FALLBACK POR ARTISTA (Lugar de nacimiento como último recurso absoluto)
    if country_hint in ASIA_FLAGS_MAP:
        return ASIA_FLAGS_MAP[country_hint]
        
    return '🌏'

def get_tiered_field(raw, field='title', media_type='movie'):
    """
    Recupera un campo (título o sinopsis) con lógica de fallback: ES > MX > EN+Trad
    'raw' debe ser un dict con {'es': data, 'mx': data, 'en': data}
    """
    res_es, res_mx, res_en = raw.get('es', {}), raw.get('mx', {}), raw.get('en', {})
    
    orig_f = 'original_title' if media_type == 'movie' else 'original_name'
    curr_f = 'title' if media_type == 'movie' else 'name'
    orig_val = res_es.get(orig_f)

    if field == 'title':
        title_es = res_es.get(curr_f)
        title_mx = res_mx.get(curr_f)
        title_en = res_en.get(curr_f)
        
        # El original real (para saber si el de ES/MX es solo un relleno)
        ref_val = orig_val if orig_val else title_en
        
        # 1. ES (Si no es igual al original y no está vacío)
        if title_es and title_es != ref_val: return title_es
        # 2. MX (Idem)
        if title_mx and title_mx != ref_val: return title_mx
        # 3. EN
        return title_en or title_es or orig_val

    if field == 'name':
        # Alias para campos que se llaman 'name' en lugar de 'title' (Temporadas, Personas)
        name_es = res_es.get('name')
        name_mx = res_mx.get('name')
        name_en = res_en.get('name')
        
        # Usamos el de EN como referencia si no hay original explícito
        ref_val = orig_val if orig_val else name_en
        
        if name_es and name_es != ref_val: return name_es
        if name_mx and name_mx != ref_val: return name_mx
        return name_en or name_es or orig_val

    if field == 'overview':
        ov = clean_overview(res_es.get('overview'))
        if ov: return ov
        ov = clean_overview(res_mx.get('overview'))
        if ov: return ov
        ov_en = clean_overview(res_en.get('overview'))
        if ov_en:
            try: return GoogleTranslator(source='en', target='es').translate(ov_en)
            except: return ov_en
    if field == 'biography':
        b_es = clean_overview(res_es.get('biography'))
        if b_es: return b_es
        b_mx = clean_overview(res_mx.get('biography'))
        if b_mx: return b_mx
        b_en = clean_overview(res_en.get('biography'))
        if b_en:
            try: return GoogleTranslator(source='en', target='es').translate(b_en)
            except: return b_en
    return None

def process_watch_providers(providers_data, region):
    """ Filtra y normaliza los proveedores de streaming para una región """
    if not region: return []
    flatrate = providers_data.get('results', {}).get(region, {}).get('flatrate', [])
    watch_providers = []
    seen_p = set()
    for p in flatrate:
        pid = p['provider_id']
        if pid in ELITE_PROVIDER_IDS:
            pid = PROVIDER_UPGRADE_MAP.get(pid, pid)
            if pid not in seen_p:
                watch_providers.append({'id': pid, 'name': p['provider_name']})
                seen_p.add(pid)
    return watch_providers

app = Flask(__name__)
load_dotenv()

# Permitir HTTP local para OAuth (Google permite localhost)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/asian_platform'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret_key')

# --- CONFIGURACIÓN DE CORREO GMAIL ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

db.init_app(app)
 
# --- CONFIGURACIÓN DE UPLOAD ---
UPLOAD_FOLDER = 'static/uploads/profiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- CONFIGURACIÓN GOOGLE OAUTH ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.before_request
def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())

# --- CACHÉ DE CONTEXTO POR USUARIO (Speed Triangle) ---
# Guardamos solo el último medio procesado PARA CADA USUARIO
USER_CONTEXT_CACHES = {}

def get_cached_media(media_id, media_type):
    u_id = session.get('session_id')
    if not u_id or u_id not in USER_CONTEXT_CACHES:
        return None
    
    u_cache = USER_CONTEXT_CACHES[u_id]
    if u_cache.get('media_id') == media_id:
        return u_cache.get('data')
    return None

def set_cached_media(media_id, data, user_region=None):
    u_id = session.get('session_id')
    if not u_id:
        session['session_id'] = str(uuid.uuid4())
        u_id = session['session_id']
    
    # Pre-procesamos los providers para esa región específica
    data['cached_watch_providers'] = process_watch_providers(data.get('watch/providers', {}), user_region)
    data['cached_user_region'] = user_region
    
    USER_CONTEXT_CACHES[u_id] = {
        'media_id': media_id,
        'data': data,
        'cast_data': None,
        'seasons_data': None
    }
    cleanup_user_caches()

# Limpieza periódica de memoria (opcional) cada 200 entradas borramos las más viejas
def cleanup_user_caches():
    if len(USER_CONTEXT_CACHES) > 500:
        # Borrado simple por antigüedad (las primeras llaves)
        keys_to_del = list(USER_CONTEXT_CACHES.keys())[:100]
        for k in keys_to_del:
            USER_CONTEXT_CACHES.pop(k, None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        region = request.form.get('region')

        if password != confirm_password:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("El email ya está registrado.")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya está en uso.")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, region=region)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash("Cuenta creada correctamente. ¡Bienvenido!", "success")
        return redirect(url_for('explore'))
    
    return render_template('register.html', countries_list=GLOBAL_COUNTRIES_LIST, regions_map=REGIONS_MAP)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['email']  # email o username
        password = request.form['password']
        user = User.query.filter_by(email=identifier).first() or User.query.filter_by(username=identifier).first()
        if user and user.check_password(password):
            remember = True if request.form.get('remember') else False
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

# --- RUTAS GOOGLE OAUTH ---
@app.route('/login/google')
def login_google():
    # Detectamos la intención (si viene de register o de login normal)
    action = request.args.get('action', 'login')
    session['google_auth_action'] = action
    session['google_auth_next'] = request.args.get('next')
    
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    try:
        token = google.authorize_access_token()
        # En Authlib 1.0+, el token ya suele incluir la información del usuario si hay OpenID
        user_info = token.get('userinfo')
        if not user_info:
            # Si no, la pedimos manualmente
            resp = google.get('userinfo')
            user_info = resp.json()
        
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        
        # Buscar usuario por email
        user = User.query.filter_by(email=email).first()
        action = session.get('google_auth_action', 'login')
        
        if not user:
            if action == 'register':
                # Solo creamos el usuario si viene explícitamente de la página de registro
                # Generar nombre de usuario único
                base_username = name.replace(" ", "").lower()
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                    
                user = User(username=username, email=email)
                # IMPORTANTE: Como tu DB pide que no sea NULL, ponemos un marcador interno.
                # El usuario no se logueará nunca con esta clave, entrará via Google.
                user.set_password("OAUTH_GOOGLE_USER")
                db.session.add(user)
                db.session.commit()
            else:
                # Si viene de Login normal y no existe, mostramos el error útil de antes
                flash("No encontramos ninguna cuenta de SHIORI vinculada a este correo. Regístrate primero para poder conectar con Google.", "error")
                return redirect(url_for('login'))
        
        # Loguear al usuario existente con sesión persistente (por comodidad)
        login_user(user, remember=True)
        next_page = session.pop('google_auth_next', None)
        return redirect(next_page or url_for('home'))
    except Exception as e:
        print(f"❌ Error en Google Auth: {str(e)}")
        # Miramos si el usuario intentaba registrarse o entrar
        action = session.get('google_auth_action', 'login')
        flash("Error de autenticación con Google. Por favor, reintenta o usa login normal.", "error")
        return redirect(url_for(action))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            
            try:
                msg = Message("SHIORI - Reestablecer Contraseña 🏮",
                              recipients=[user.email])
                # Plantilla HTML con el diseño premium
                msg.html = render_template('emails/reset_password_email.html', reset_url=reset_url)
                # Fallback en texto plano por seguridad
                msg.body = f"Para reestablecer tu contraseña en SHIORI, haz clic en el siguiente enlace: {reset_url}"
                
                mail.send(msg)
            except Exception as e:
                print(f"❌ Error enviando email: {e}")
                flash("Error al enviar el email de recuperación.", "error")
                return redirect(url_for('forgot_password'))
        
        # Mensaje unificado amigable (si existe o si no)
        flash("🏮 ¡Enviado! Si el correo es correcto, recibirás el enlace en tu buzón en breves momentos.", "success")
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace de recuperación es inválido o ha expirado.", "error")
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        return redirect(url_for('home'))

    if request.method == 'POST':
        new_password = request.form['password']
        user.set_password(new_password)
        db.session.commit()
        # Loguear automáticamente con sesión persistente tras resetear
        login_user(user, remember=True)
        return redirect(url_for('home'))

    return render_template('reset_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- HOME & TMDB ---

api_cache = {'day': {'series': [], 'movies': [], 'shows': [], 'last_updated': 0, 'expire': 14400},
             'week': {'series': [], 'movies': [], 'shows': [], 'last_updated': 0, 'expire': 86400}}

def get_top_20(api_key, media_type, time_window):
    # Usamos api_media_type para la consulta real a la API
    api_media_type = 'tv' if media_type in ['tv', 'show'] else 'movie'

    final_list = []
    seen_ids = set() 
    page = 1
    
    while len(final_list) < 20 and page < 80:
        # Usamos api_media_type para la consulta real a la API
        url = f"https://api.themoviedb.org/3/trending/{api_media_type}/{time_window}?api_key={api_key}&language=es-ES&page={page}"
        data = fetch_json(url)
        
        if not data:
            break
            
        results = data.get('results', [])
        
        if not results:
            break
            
        for item in results:
            item_id = item.get('id')
            lang = item.get('original_language', '').lower()

            # --- LÓGICA DE FILTRADO POR GÉNERO ---
            if api_media_type == 'tv':
                item_genres = item.get('genre_ids', [])
                es_no_ficcion = any(g in item_genres for g in GENRES_PROGRAMAS)
                
                if media_type == 'tv' and es_no_ficcion:
                    continue  # Si buscamos Series, saltamos Programas
                elif media_type == 'show' and not es_no_ficcion:
                    continue  # Si buscamos Programas, saltamos Series
            
            if lang in ASIA_LANGUAGES and item_id not in seen_ids and item.get('poster_path'):
                # Detalles paralelos (MX y EN) para el fallback tiered
                urls = {
                    'mx': f"https://api.themoviedb.org/3/{api_media_type}/{item_id}?api_key={api_key}&language=es-MX",
                    'en': f"https://api.themoviedb.org/3/{api_media_type}/{item_id}?api_key={api_key}&language=en-US"
                }
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
                    res_extra = {name: future.result() for name, future in futures.items()}

                # --- METADATA UNIFICADA ---
                item['flag'] = get_media_flag(item, res_extra['en'])
                
                # Títulos y Sinopsis con Fallback Tiered Real (ES > MX > EN)
                raw_bundle = {'es': item, 'mx': res_extra['mx'], 'en': res_extra['en']}
                
                if api_media_type == 'tv':
                     item['name'] = get_tiered_field(raw_bundle, 'title', 'tv')
                     item['overview'] = get_tiered_field(raw_bundle, 'overview', 'tv')
                else:
                     item['title'] = get_tiered_field(raw_bundle, 'title', 'movie')
                     item['overview'] = get_tiered_field(raw_bundle, 'overview', 'movie')

                final_list.append(item)
                seen_ids.add(item_id)
                
                print(f"✅ Añadido al Top {media_type}: {item.get('name') if api_media_type == 'tv' else item.get('title')} [{item['flag']}]")
                
                if len(final_list) >= 20:
                    break
        page += 1
        
    return final_list


def refresh_trending_cache(window):
    """
    Función para actualizar el caché de tendencias en segundo plano.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print(f"❌ Error: TMDB_API_KEY no encontrada al refrescar caché {window}")
        return

    print(f"🔄 [BACKGROUND] Refrescando caché de {window} con TMDB...")
    try:
        api_cache[window]['series'] = get_top_20(api_key, 'tv', window)
        api_cache[window]['movies'] = get_top_20(api_key, 'movie', window)
        api_cache[window]['shows'] = get_top_20(api_key, 'show', window)
        api_cache[window]['last_updated'] = time.time()
        # Log más detallado para confirmar el reemplazo de datos
        print(f"✅ [BACKGROUND] Caché {window} reemplazada con éxito con 20 nuevos items por categoría.")
        print(f"⏰ Próxima actualización programada según intervalo.")
    except Exception as e:
        print(f"❌ [BACKGROUND] Error al refrescar caché {window}: {e}")

# --- INICIALIZACIÓN DEL PLANIFICADOR (SCHEDULER) ---
# Usamos misfire_grace_time=300 (5 min) para que si el servidor está ocupado, el job se ejecute aunque se pase unos minutos
scheduler = BackgroundScheduler()

scheduler.add_job(
    func=refresh_trending_cache, 
    trigger="interval", 
    seconds=14400, 
    args=['day'],
    id='refresh_day',
    misfire_grace_time=300
)

scheduler.add_job(
    func=refresh_trending_cache, 
    trigger="interval", 
    seconds=86400, 
    args=['week'],
    id='refresh_week',
    misfire_grace_time=300
)


# Forzar una carga inicial de TODO (en paralelo) para que las primeras personas no tengan que esperar
with app.app_context():
    # Solo disparamos la inicial si el caché de 'day' está vacío (indica reinicio o primer arranque)
    if not api_cache['day']['series']:
        # Lanzamos dos hilos de forma paralela para acelerar el arranque
        threading.Thread(target=refresh_trending_cache, args=['day']).start()
        threading.Thread(target=refresh_trending_cache, args=['week']).start()
 
@app.route('/')
def home():
    window = request.args.get('window', 'day')
    if window not in ['day', 'week']: 
        window = 'day'
    
    # MODO HÍBRIDO: 
    # - Si el caché tiene datos, los mandamos (SSR rápido).
    # - Si la caché está vacía, MANDAMOS LISTAS VACÍAS para no bloquear el servidor.
    #   El JS de index.html detectará que no hay caché y lanzará el AJAX.
    cache = api_cache[window]
    trending_data = {
        'series': cache.get('series', []),
        'movies': cache.get('movies', []),
        'shows': cache.get('shows', [])
    }
    
    return render_template('index.html', 
                           active_window=window, 
                           trending_data=trending_data)
 
@app.route('/api/trending')
def api_trending():
    api_key = os.getenv("TMDB_API_KEY")
    window = request.args.get('window', 'day')
    media_type = request.args.get('type', 'series') # series, movies, shows
    
    if window not in ['day', 'week']: 
        window = 'day'

    current_time = time.time()
    cache = api_cache[window]
    
    # Mapeo interno de tipos
    type_map = {
        'series': 'tv',
        'movies': 'movie',
        'shows': 'show'
    }
    
    # Si el cache del tipo específico está vacío, disparamos carga manual
    if not cache.get(media_type):
        api_type = type_map.get(media_type, 'tv')
        print(f"⚠️ Caché {window}/{media_type} vacía. Realizando carga manual de emergencia...")
        cache[media_type] = get_top_20(api_key, api_type, window)
        cache['last_updated'] = current_time
    
    # Devolvemos solo lo solicitado para optimizar carga paralela
    return jsonify({
        media_type: cache.get(media_type, [])
    })

# --- PROFILE ---
@app.route('/profile')
@login_required
def profile():
    counts = {
        'favoritos': CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True).count(),
        'viendo': CollectionItem.query.filter_by(user_id=current_user.id, status='Viendo').count(),
        'vistos': CollectionItem.query.filter_by(user_id=current_user.id, status='Visto').count(),
        'pendientes': CollectionItem.query.filter_by(user_id=current_user.id, status='Pendiente').count(),
        'abandonados': CollectionItem.query.filter_by(user_id=current_user.id, status='Abandonado').count()
    }
    return render_template('profile.html', counts=counts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form.get('password')
        region = request.form.get('region')

        if User.query.filter(User.id != current_user.id, User.username == username).first():
            flash("Ese nombre de usuario ya está en uso.")
            return redirect(url_for('edit_profile'))
        if User.query.filter(User.id != current_user.id, User.email == email).first():
            flash("Ese email ya está en uso.")
            return redirect(url_for('edit_profile'))

        current_user.username = username
        current_user.email = email
        current_user.region = region
        current_user.bio = request.form.get('bio') # Actualizar Bio

        # --- Lógica de Foto de Perfil ---
        file = request.files.get('profile_image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"user_{current_user.id}_{int(time.time())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            current_user.profile_image = f"uploads/profiles/{filename}"

        if password: current_user.set_password(password)
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page:
            flash("Perfil actualizado correctamente.", "success")
        return redirect(next_page or url_for('edit_profile'))
    
    return render_template('edit_profile.html', countries_list=GLOBAL_COUNTRIES_LIST, regions_map=REGIONS_MAP)

# --- COLLECTIONS ---
@app.route('/collections')
@login_required
def collections():
    statuses = ['Viendo', 'Visto', 'Pendiente', 'Abandonado']
    user_collections = {}

    for status in statuses:
        user_collections[status] = CollectionItem.query.filter_by(
            user_id=current_user.id, status=status
        ).order_by(CollectionItem.created_at.desc()).limit(10).all()

    favorites = CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True).order_by(CollectionItem.created_at.desc()).limit(10).all()
    return render_template('collections.html', collections=user_collections, favorites=favorites)



@app.route('/collections/<status>')
@login_required
def view_collection(status):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 18, type=int)
    ajax = request.args.get('ajax', 0, type=int)
    
    query = CollectionItem.query.filter_by(user_id=current_user.id).order_by(CollectionItem.created_at.desc())

    if status.lower() == 'favoritos':
        query = query.filter_by(is_favorite=True)
        display_name = "Mis Favoritos"
    else:
        query = query.filter_by(status=status)
        display_name = status

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    # SI ES AJAX, ENVIAMOS SOLO LA REJILLA (Sin cabecera ni navbar)
    if ajax:
        return render_template('partials/collection_grid.html', 
                             items=items, 
                             pagination=pagination, 
                             status=status,
                             per_page=per_page)

    return render_template('collection_view.html', 
                          items=items, 
                          display_name=display_name, 
                          pagination=pagination, 
                          status=status,
                          per_page=per_page)


# --- AJAX FAVORITE / COLLECTION ---
@app.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    data = request.json
    media_id = data.get('media_id')
    
    item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id).first()

    if item:
        item.is_favorite = not item.is_favorite
        # LÓGICA DE BORRADO: Si ya no es favorito y no tiene estado asignado
        if not item.is_favorite and not item.status:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'favorite': False, 'deleted': True})
    else:
        # Si no existe, lo creamos con los datos que envía tu JS
        item = CollectionItem(
            user_id=current_user.id,
            media_id=media_id,
            media_type=data.get('media_type'),
            title=data.get('title'),
            original_title=data.get('original_title'),
            poster_path=data.get('poster'),
            vote_average=data.get('vote_average'),
            flag=data.get('flag'),
            is_favorite=True,
            media_subtype=data.get('media_subtype', 'Serie')
        )
        db.session.add(item)

    db.session.commit()
    return jsonify({'favorite': item.is_favorite})

@app.route('/toggle_status', methods=['POST'])
@login_required
def toggle_status():
    data = request.json
    media_id = data.get('media_id')
    new_status = data.get('status')
    
    item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id).first()

    if item:
        # Si pulsas el botón que ya está activo, quitamos el status (toggle)
        if item.status == new_status:
            item.status = None
        else:
            item.status = new_status
            # Actualizamos título y poster por si acaso
            item.title = data.get('title')
            item.original_title = data.get('original_title')
            item.poster_path = data.get('poster')
            item.vote_average = data.get('vote_average')
            item.flag = data.get('flag')
            
        # LÓGICA DE BORRADO: Si tras el cambio no hay status ni es favorito
        if not item.status and not item.is_favorite:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'current_status': None, 'deleted': True})
    else:
        # Si no existe, creamos el registro
        item = CollectionItem(
            user_id=current_user.id,
            media_id=media_id,
            media_type=data.get('media_type'),
            title=data.get('title'),
            original_title=data.get('original_title'),
            poster_path=data.get('poster'),
            vote_average=data.get('vote_average'),
            flag=data.get('flag'),
            status=new_status,
            media_subtype=data.get('media_subtype', 'Serie')
        )
        db.session.add(item)
    
    db.session.commit()
    return jsonify({'current_status': item.status})


# --- RUTAS DE MEDIA (REFACTORIZADAS) ---
@app.route('/media/<media_type>/<int:media_id>')
def media_detail(media_type, media_id):
    # 1. ¿Está en caché de contexto?
    cached = get_cached_media(media_id, media_type)
    
    # Lógica de Auth y Región (Siempre fresca)
    current_status, is_favorite = (None, False)
    user_region = current_user.region if (current_user.is_authenticated and current_user.region) else None
    if current_user.is_authenticated:
        item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=media_type).first()
        if item: current_status, is_favorite = item.status, item.is_favorite

    if cached:
        # Pre-procesar providers si la región cambió o no estaban
        if cached.get('cached_user_region') != user_region:
            cached['cached_watch_providers'] = process_watch_providers(cached.get('watch/providers', {}), user_region)
            cached['cached_user_region'] = user_region
        
        watch_providers = cached.get('cached_watch_providers', [])

        return render_template('media_detail.html', 
                               media=cached, 
                               is_favorite=is_favorite, 
                               current_status=current_status, 
                               watch_providers=watch_providers, 
                               has_region=bool(user_region), 
                               user_region=user_region, 
                               keywords=cached.get('keywords_processed', []), 
                               real_media_type='movie' if media_type == 'movie' else ('show' if cached.get('media_subtype') == 'Programa' else 'tv'), 
                               cast=cached.get('cast_processed', []), 
                               crew=cached.get('crew_processed', []))

    api_key = os.getenv("TMDB_API_KEY")
    is_tv = media_type == 'tv' or ('show' in request.path)
    
    # 2. ÚNICA OLEADA DE PETICIONES (Sin cascada)
    append_base = "external_ids,videos,keywords,watch/providers,translations"
    append_credits = ",aggregate_credits" if is_tv else ",credits"
    
    urls = {
        'es': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES&append_to_response={append_base}",
        'mx': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-MX&append_to_response={append_base}",
        'en': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US&append_to_response={append_base + append_credits}"
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(fetch_json, url): name for name, url in urls.items()}
        raw = {future_to_url[future]: future.result() for future in future_to_url}

    res = raw['es']
    if not res or 'id' not in res:
        res = raw['mx'] if (raw['mx'] and 'id' in raw['mx']) else raw['en']
    if not res: return "Error cargando medios", 404

    lang = res.get('original_language', '').lower()
    # PROCESAMIENTO TÍTULO / OVERVIEW
    res['display_title'] = get_tiered_field(raw, 'title', 'movie' if media_type == 'movie' else 'tv')
    res['overview'] = get_tiered_field(raw, 'overview', 'movie' if media_type == 'movie' else 'tv')

    # Trailers & Social
    ext_ids = res.get('external_ids', {})
    
    # Unificación total de Redes en Media
    res['social_links'] = {}
    for k in ['instagram', 'twitter', 'facebook', 'tiktok']:
        val = ext_ids.get(f'{k}_id')
        if val:
            prefix = "@" if k == 'tiktok' else ""
            res['social_links'][k] = f"https://{k}.com/{prefix}{val}"
    
    if ext_ids.get('youtube_id'):
        res['social_links']['youtube'] = f"https://youtube.com/{ext_ids['youtube_id']}"
        
    if res.get('homepage'):
        res['social_links']['homepage'] = res['homepage']

    videos_es = res.get('videos', {}).get('results', [])
    res['trailer_key'] = next((v['key'] for v in videos_es if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
    if not res['trailer_key']:
        res['trailer_key'] = next((v['key'] for v in raw['en'].get('videos', {}).get('results', []) if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)

    # Status, Genres, Flags
    if 'genres' in res: 
        for g in res['genres']: g['name'] = GENRE_MAP_ES.get(g['name'], g['name'])
    res['status'] = STATUS_MAP_ES.get(res.get('status'), res.get('status'))
    res['media_subtype'] = 'Programa' if (media_type == 'tv' and any(g['name'] in ['Reality', 'Talk Show', 'Documental', 'Noticias'] for g in res.get('genres', []))) else 'Serie'
    
    res['flag'] = get_media_flag(res, res)

    # TEMPORADAS (Usa info de Wave 1)
    last_season = None
    has_multiple_seasons = False
    if is_tv:
        # LÓGICA DE EPISODIOS INTELIGENTE (Detecta el más reciente y decide etiqueta)
        last_meta = res.get('last_episode_to_air', {}) or {}
        next_meta = res.get('next_episode_to_air', {}) or {}
        l_date = last_meta.get('air_date')
        n_date = next_meta.get('air_date')
        
        target_date_raw = n_date if (n_date and (not l_date or n_date >= l_date)) else l_date
        
        if target_date_raw:
            try:
                dt_target = datetime.strptime(target_date_raw, '%Y-%m-%d').date()
                today = datetime.now().date()
                label = "Próximo" if dt_target >= today else "Último"
                
                meses_f = ['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sep.', 'oct.', 'nov.', 'dic.']
                res['smart_episode_label'] = label
                res['smart_episode_date'] = f"{dt_target.day} {meses_f[dt_target.month-1]} {dt_target.year}"
            except: pass
        
        seasons_list = [s for s in res.get('seasons', []) if s.get('season_number', 0) > 0]
        if seasons_list:
            last_season = seasons_list[-1]
            has_multiple_seasons = len(seasons_list) > 1
            s_num = last_season['season_number']
            s_mx = next((s for s in raw['mx'].get('seasons', []) if s.get('season_number') == s_num), {})
            s_en = next((s for s in raw['en'].get('seasons', []) if s.get('season_number') == s_num), {})
            
            if not last_season.get('overview') or not clean_overview(last_season.get('overview')):
                last_season['overview'] = get_tiered_field({'mx': s_mx, 'en': s_en}, 'overview', 'tv')
            last_season['overview'] = clean_overview(last_season.get('overview'))
            if not last_season.get('name') or "Temporada" in last_season.get('name', ''):
                if s_mx.get('name') and "Temporada" not in s_mx['name']: last_season['name'] = s_mx['name']
                elif s_en.get('name') and "Season" not in s_en['name']: last_season['name'] = s_en['name']
            if not last_season.get('poster_path'): last_season['poster_path'] = s_mx.get('poster_path') or s_en.get('poster_path')
            if last_season.get('air_date'):
                try:
                    dt = datetime.strptime(last_season['air_date'], '%Y-%m-%d')
                    last_season['air_date_formatted'] = f"{dt.day} {['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sep.', 'oct.', 'nov.', 'dic.'][dt.month-1]} {dt.year}"
                except: last_season['air_date_formatted'] = last_season['air_date']

    res['last_season'] = last_season
    res['has_multiple_seasons'] = has_multiple_seasons
    res['last_episode_date_formatted'] = res.get('smart_episode_date')

    # Procesado final
    ert = res.get('episode_run_time') or [0]
    runtime = res.get('runtime') or (ert[0] if is_tv and ert else 0)
    res['runtime_formatted'] = f"{runtime // 60}h {runtime % 60}m" if runtime > 60 else f"{runtime}m"
    res['original_language_name'] = ASIA_LANG_NAMES.get(lang, lang.upper())

    # DETERMINAR MEJOR FUENTE DE CRÉDITOS (Using TMDB Translation Info)
    def get_best_credits_source(r_es, r_mx, r_en, tv=False):
        key = 'aggregate_credits' if tv else 'credits'
        # Los nombres de actores y personajes son universales; el inglés es la fuente más completa
        return r_en.get(key, {})

    credits_master = get_best_credits_source(raw['es'], raw['mx'], raw['en'], is_tv)
    
    final_cast_preview = []
    cast_source = credits_master.get('cast', [])[:9]
    
    for a_orig in cast_source:
        a = a_orig.copy()
        if is_tv and a.get('roles'):
            roles = sorted(a['roles'], key=lambda x: x.get('episode_count', 0), reverse=True)
            valid_roles = [r for r in roles if r.get('character')]
            if valid_roles:
                first = valid_roles[0]
                char_text = f"{first['character']} <small style='opacity:0.6'>({first['episode_count']} episodio{'s' if first['episode_count']!=1 else ''})</small>"
                if len(valid_roles) > 1:
                    char_text += f"<br>y {len(valid_roles)-1} más..."
                a['character'] = char_text
            else: a['character'] = "N/A"
        else:
            a['character'] = a.get('character', 'N/A')
            
        final_cast_preview.append(a)
    res['cast_processed'] = final_cast_preview
    res['crew_processed'] = credits_master.get('crew', [])
    res['keywords_processed'] = res.get('keywords', {}).get('results' if is_tv else 'keywords', [])[:15]
    res['raw_data'] = raw
    
    # GUARDAR EN CACHÉ Y RENDERIZAR
    set_cached_media(media_id, res, user_region)
    watch_providers = process_watch_providers(res.get('watch/providers', {}), user_region)
    return render_template('media_detail.html', 
                           media=res, 
                           is_favorite=is_favorite, 
                           current_status=current_status, 
                           watch_providers=watch_providers, 
                           has_region=bool(user_region), 
                           user_region=user_region, 
                           keywords=res.get('keywords_processed', []), 
                           real_media_type='movie' if media_type == 'movie' else ('show' if res.get('media_subtype') == 'Programa' else 'tv'), 
                           cast=res.get('cast_processed', []), 
                           crew=res.get('crew_processed', []))


@app.route('/media/tv/<int:media_id>/seasons')
def seasons(media_id):
    meses_f = ['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sep.', 'oct.', 'nov.', 'dic.']
    cached = get_cached_media(media_id, 'tv')
    # Si tenemos los datos cacheados y además ya procesamos las temporadas antes, las usamos
    u_id = session.get('session_id')
    if cached and u_id and USER_CONTEXT_CACHES.get(u_id, {}).get('seasons_data'):
        return render_template('seasons.html', series=cached, seasons=USER_CONTEXT_CACHES[u_id]['seasons_data'])

    api_key = os.getenv('TMDB_API_KEY')
    
    # Si tenemos el cache del media pero no las temporadas procesadas, lo hacemos ahora
    if cached:
        response = cached
        raw_seasons = sorted(response.get('seasons', []), key=lambda x: x.get('season_number', 0))
        data_mx = cached['raw_data']['mx']
        data_en = cached['raw_data']['en']
    else:
        # Petición de emergencia si entran directo por URL (Paralelizada REAL)
        urls = {
            'es': f"https://api.themoviedb.org/3/tv/{media_id}?api_key={api_key}&language=es-ES&append_to_response=external_ids",
            'mx': f"https://api.themoviedb.org/3/tv/{media_id}?api_key={api_key}&language=es-MX",
            'en': f"https://api.themoviedb.org/3/tv/{media_id}?api_key={api_key}&language=en-US"
        }
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Lanzamos los 3 a la vez
            futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
            # Recolectamos todo (esperando solo al que más tarde, no sumándolos)
            raw = {name: future.result() for name, future in futures.items()}
        
        response = raw['es']
        # Título tiered fallback
        response['display_title'] = get_tiered_field(raw, 'title', 'tv')
        response['overview'] = get_tiered_field(raw, 'overview', 'tv')
        
        # LÓGICA SMART (Emergency path)
        last_meta = response.get('last_episode_to_air', {}) or {}
        next_meta = response.get('next_episode_to_air', {}) or {}
        l_date = last_meta.get('air_date')
        n_date = next_meta.get('air_date')
        target_date_raw = n_date if (n_date and (not l_date or n_date >= l_date)) else l_date

        if target_date_raw:
            try:
                dt_target = datetime.strptime(target_date_raw, '%Y-%m-%d').date()
                today = datetime.now().date()
                response['smart_episode_label'] = "Próximo" if dt_target >= today else "Último"
                response['smart_episode_date'] = f"{dt_target.day} {meses_f[dt_target.month-1]} {dt_target.year}"
            except: pass

        series = response # Para mantener el nombre esperado en el render
        raw_seasons = sorted(series.get('seasons', []), key=lambda x: x.get('season_number', 0))
        data_mx, data_en = raw['mx'], raw['en']

    # --- PROCESADO DE TEMPORADAS (OPTIMIZADO O(1) + PARALELO) ---
    all_seasons = []
    
    mx_dict = {x.get('season_number'): x for x in data_mx.get('seasons', [])}
    en_dict = {x.get('season_number'): x for x in data_en.get('seasons', [])}
    translations_needed = []
    
    for s in raw_seasons:
        s_num = s.get('season_number')
        s_mx = mx_dict.get(s_num, {})
        s_en = en_dict.get(s_num, {})
        
        if not s.get('poster_path'):
            s['poster_path'] = s_mx.get('poster_path') or s_en.get('poster_path')
        
        # Lógica de nombre inteligente: Si en ES/MX es genérico (Temporada 1), usamos el de EN si es descriptivo
        name_es = s.get('name')
        name_mx = s_mx.get('name')
        name_en = s_en.get('name')
        
        def is_generic(n):
            if not n: return True
            nl = n.lower()
            # Detecta "Temporada X" o "Season X"
            return nl.startswith("temporada") or nl.startswith("season")

        if is_generic(name_es):
            if name_mx and not is_generic(name_mx):
                s['name'] = name_mx
            elif name_en and not is_generic(name_en):
                s['name'] = name_en
            else:
                s['name'] = name_es # Se queda como está si ninguno tiene nombre real

        if not s.get('overview') or not clean_overview(s.get('overview')):
            s['overview'] = get_tiered_field({'es': s, 'mx': s_mx, 'en': s_en}, 'overview', 'tv')
        
        all_seasons.append(s)

    # Guardamos en caché de contexto el resultado de las temporadas para rapidez total
    if u_id and u_id in USER_CONTEXT_CACHES:
        USER_CONTEXT_CACHES[u_id]['seasons_data'] = all_seasons
    return render_template('seasons.html', series=response, seasons=all_seasons)

@app.route('/media/<media_type>/<int:media_id>/cast')
def media_cast(media_type, media_id):
    cached = get_cached_media(media_id, media_type)
    u_id = session.get('session_id')
    if cached and u_id and USER_CONTEXT_CACHES.get(u_id, {}).get('cast_data'):
        return render_template('cast.html', **USER_CONTEXT_CACHES[u_id]['cast_data'])

    api_key = os.getenv("TMDB_API_KEY")
    is_tv = media_type == 'tv'

    if cached:
        res = cached
        raw = res.get('raw_data', {})
    else:
        # Petición de emergencia
        append_credits = 'aggregate_credits' if is_tv else 'credits'
        urls = {
            'es': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES&append_to_response=translations",
            'mx': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-MX",
            'en': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US&append_to_response={append_credits}"
        }
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
            raw = {name: future.result() for name, future in futures.items()}
        # Títulos con Fallback centralizado
        res['display_title'] = get_tiered_field(raw, 'title', media_type)
        res['raw_data'] = raw

    # DETERMINAR FUENTE DE CRÉDITOS (English-first Strategy)
    def get_best_credits_source(r_es, r_mx, r_en, tv=False):
        key = 'aggregate_credits' if tv else 'credits'
        # Priorizamos el inglés por mayor completitud en nombres propios de cast y crew
        return r_en.get(key, {})

    # Fallback si por algún motivo 'raw' no tiene los datos (ej: cache viejo)
    if not 'raw' in locals() or not raw or 'es' not in raw or ('en' in raw and ('aggregate_credits' if is_tv else 'credits') not in raw['en']):
        append_credits = 'aggregate_credits' if is_tv else 'credits'
        urls_raw = {
            'es': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES&append_to_response=translations",
            'mx': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-MX",
            'en': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US&append_to_response={append_credits}"
        }
        with ThreadPoolExecutor(max_workers=3) as executor:
            raw = {name: executor.submit(fetch_json, url).result() for name, url in urls_raw.items()}

    credits_master = get_best_credits_source(raw['es'], raw['mx'], raw['en'], is_tv)
    final_cast, final_crew = credits_master.get('cast', []), credits_master.get('crew', [])
    
    # Normalizamos los roles y equipos como COPIAS para no afectar al caché global
    final_cast_display = []
    final_crew_display = []
    
    if is_tv:
        for a_orig in final_cast:
            a = a_orig.copy()
            if a.get('roles'):
                sorted_roles = sorted(a['roles'], key=lambda x: x.get('episode_count', 0), reverse=True)
                valid_roles = [r for r in sorted_roles if r.get('character')]
                
                if valid_roles:
                    parts = []
                    for r in valid_roles:
                        parts.append(f"{r['character']} <small style='opacity:0.6'>({r['episode_count']} episodio{'s' if r['episode_count']!=1 else ''})</small>")
                    a['character'] = ", ".join(parts)
                else: a['character'] = "N/A"
                final_cast_display.append(a)
            else:
                final_cast_display.append(a_orig)
        
        for m_orig in final_crew:
            m = m_orig.copy()
            final_crew_display.append(m)
    else:
        # PELÍCULAS: Reparto estándar desde la mejor fuente
        for a_orig in final_cast:
            a = a_orig.copy()
            a['name'] = a.get('name', 'N/A')
            a['character'] = a.get('character', 'N/A')
            final_cast_display.append(a)
            
        final_crew_display = final_crew

    crew_by_dept = {}
    for member in final_crew_display:
        dept_es = DEPT_MAP_ES.get(member.get('department', 'Others'), member.get('department', 'Others'))
        if dept_es not in crew_by_dept: crew_by_dept[dept_es] = []
        crew_by_dept[dept_es].append(member)

    sorted_crew = {dept: sorted(crew_by_dept[dept], key=lambda x: x.get('job', '')) for dept in sorted(crew_by_dept.keys())}
    
    cast_payload = {
        'media': res, 'cast': final_cast_display, 'crew_by_dept': sorted_crew, 
        'crew_total': len(final_crew_display), 'media_type': media_type, 'media_id': media_id
    }
    if u_id and u_id in USER_CONTEXT_CACHES:
        USER_CONTEXT_CACHES[u_id]['cast_data'] = cast_payload
    return render_template('cast.html', **cast_payload)


@app.route('/explore')
def explore():
    media_type = request.args.get('type', 'tv') 
    year = request.args.get('year', '')
    country_code = request.args.get('lang', '') 
    genre_id = request.args.get('genre', '')
    without_genre_id = request.args.get('without_genre', '')
    sort_by = request.args.get('sort_by', 'popularity.desc')
    status_id = request.args.get('status', '')
    watch_providers = request.args.get('watch_providers', '')
    # Priorizar la región del usuario si está identificado, si no usar España (ES) como reserva
    default_region = current_user.region if (current_user.is_authenticated and current_user.region) else 'ES'
    watch_region = request.args.get('watch_region', default_region)
    keywords = request.args.get('keywords', '')

    target_type = 'movie' if media_type == 'movie' else 'tv'
    date_key = 'primary_release_date' if target_type == 'movie' else 'first_air_date'
    sort_options = {'popularity.desc': 'Más Populares', 'popularity.asc': 'Menos Populares', 'vote_average.desc': 'Mejor Valorados', 'vote_average.asc': 'Peor Valorados', f'{date_key}.desc': 'Más Recientes', f'{date_key}.asc': 'Más Antiguos', 'vote_count.desc': 'Más Votados', 'vote_count.asc': 'Menos Votados'}
    status_options = {'0': 'En Emisión', '3': 'Finalizada', '4': 'Cancelada'}

    return render_template('explore.html', items=[], media_type=media_type, 
                           current_year=year, current_lang=country_code, 
                           current_genre=genre_id, current_without_genre=without_genre_id,
                           current_sort=sort_by, current_status_id=status_id,
                           current_providers=watch_providers, current_region=watch_region,
                           current_keywords=keywords,
                           asia_langs=ASIA_COUNTRIES_DATA, genres_by_type=GENRES_BY_TYPE, 
                           sort_options=sort_options, status_options=status_options,
                           available_countries=GLOBAL_COUNTRIES_LIST,
                           regions_map=REGIONS_MAP)

# --- API EXPLORE ---

@app.route('/api/explore')
def api_explore():
    api_key = os.getenv("TMDB_API_KEY")
    media_type = request.args.get('type', 'tv') 
    year = request.args.get('year', '')
    country_code = request.args.get('lang', '') 
    genre_id = request.args.get('genre', '')
    without_genre_id = request.args.get('without_genre', '')
    sort_by = request.args.get('sort_by', 'popularity.desc')
    status_id = request.args.get('status', '')
    watch_providers = request.args.get('watch_providers', '')
    watch_region = request.args.get('watch_region', 'ES')
    keywords = request.args.get('keywords', '')
    page = request.args.get('page', 1, type=int) 
    # Punto de inicio real y cuántos saltar (Sync para no repetir ni saltar series)
    api_start_page = request.args.get('api_page', page, type=int) 
    api_skip = request.args.get('api_skip', 0, type=int) 
    
    today = datetime.now().strftime('%Y-%m-%d')
    target_type = 'movie' if media_type == 'movie' else 'tv'
    # Filtro de programas: Reality(10764), Docu(99), Noticias(10763), Talk(10767)
    genres_programas_or = "|".join(map(str, GENRES_PROGRAMAS))
    genres_programas_and = ",".join(map(str, GENRES_PROGRAMAS))

    def generate():
        final_items_count = 0
        seen_ids = set() # Escudo anti-duplicados
        current_api_page = api_start_page
        to_skip = api_skip # Ítems de la primera página a ignorar (ya vistos)
        max_pages_to_scan = current_api_page + 10 
        
        last_api_page = current_api_page
        last_api_skip = 0
        total_pages = 500
        total_metadata_sent = False
        
        while final_items_count < 20 and current_api_page < max_pages_to_scan:
            url = f"https://api.themoviedb.org/3/discover/{target_type}?api_key={api_key}&language=es-ES&page={current_api_page}&sort_by={sort_by}"
            if 'vote_average' in sort_by: url += "&vote_count.gte=100"
            if target_type == 'tv':
                url += f"&first_air_date.lte={today}"
                if status_id: url += f"&with_status={status_id}"
            else:
                url += f"&primary_release_date.lte={today}"

            # --- FILTRADO DE ADN (Búsqueda inicial) ---
            if country_code: 
                # Si hay país, permitimos búsqueda por idiomas asiáticos + Inglés (para catch global como Pachinko)
                url += f"&with_origin_country={country_code}"
                url += f"&with_original_language={'|'.join(ASIA_LANGUAGES + ['en'])}"
            else:
                url += f"&with_origin_country={'|'.join(ASIA_COUNTRIES)}"
                url += f"&with_original_language={'|'.join(ASIA_LANGUAGES)}"

            if year and str(year).strip():
                y_val = str(year).strip()
                url += f"&{target_type == 'movie' and 'primary_release_year' or 'first_air_date_year'}={y_val}"

            if watch_providers:
                url += f"&with_watch_providers={watch_providers}&watch_region={watch_region}&with_watch_monetization_types=flatrate|free"

            if keywords:
                keyword_ids = [k.split('_')[0] for k in keywords.split('|') if k]
                if keyword_ids: url += f"&with_keywords={'|'.join(keyword_ids)}"

            # Gestión de Géneros
            with_ids = []
            without_ids = []
            if target_type == 'tv':
                if media_type == 'show': with_ids.append("|".join(map(str, GENRES_PROGRAMAS)))
                elif media_type == 'tv': without_ids.append(",".join(map(str, GENRES_PROGRAMAS)))
            if genre_id:
                genre_list = genre_id.split('|')
                processed_genres = []
                for gid in genre_list:
                    actual_gid = gid
                    if target_type == 'tv':
                        if gid == '28': actual_gid = '10759'
                        elif gid == '10749': actual_gid = '10766|10749|18'
                        elif gid in ['14', '878']: actual_gid = '10765'
                    processed_genres.append(actual_gid)
                with_ids.append('|'.join(processed_genres))
            if without_genre_id:
                without_genre_list = without_genre_id.split('|')
                processed_without = []
                for gid in without_genre_list:
                    actual_gid = gid
                    if target_type == 'tv':
                        if gid == '28': actual_gid = '10759'
                        elif gid == '10749': actual_gid = '10766|10749|18'
                        elif gid in ['14', '878']: actual_gid = '10765'
                    processed_without.append(actual_gid)
                without_ids.append(','.join(processed_without))
            if with_ids: url += f"&with_genres={','.join(with_ids)}"
            if without_ids: url += f"&without_genres={','.join(without_ids)}"

            try:
                res = fetch_json(url)
                results = res.get('results', [])
                total_pages = res.get('total_pages', 1)
                total_results = res.get('total_results', 0)
                if not total_metadata_sent:
                    yield json.dumps({'total_results': total_results, 'total_pages': total_pages}) + '\n'
                    total_metadata_sent = True
                
                # PARALELIZACIÓN DE PÁGINA (Máxima velocidad SHIORI)
                def fetch_full_info(item):
                    i_id = item.get('id')
                    url_en = f"https://api.themoviedb.org/3/{target_type}/{i_id}?api_key={api_key}&language=en-US"
                    url_mx = f"https://api.themoviedb.org/3/{target_type}/{i_id}?api_key={api_key}&language=es-MX"
                    return {'en': fetch_json(url_en), 'mx': fetch_json(url_mx)}

                with ThreadPoolExecutor(max_workers=20) as executor:
                    full_info_list = list(executor.map(fetch_full_info, results))

                items_processed_in_this_page = 0
            except: break
            if not results: break 

            for item, info in zip(results, full_info_list):
                item_id = item.get('id')
                det_res = info.get('en', {})
                mx_res = info.get('mx', {})

                if item_id in seen_ids:
                    items_processed_in_this_page += 1
                    continue
                seen_ids.add(item_id)
                items_processed_in_this_page += 1
                
                if current_api_page == api_start_page and to_skip > 0:
                    to_skip -= 1
                    continue

                genre_ids = item.get('genre_ids', [])
                es_programa = any(gid in GENRES_PROGRAMAS for gid in genre_ids)
                if media_type == 'tv' and es_programa: continue 
                if media_type == 'show' and not es_programa: continue 

                # REGLAS DE ORO: Validación final de la bandera
                item['flag'] = get_media_flag(item, det_res)
                if country_code:
                    requested_flag = ASIA_FLAGS_MAP.get(country_code.upper())
                    if requested_flag and item['flag'] != requested_flag:
                        continue 

                item['media_type_fixed'] = target_type
                item['tipo_label'] = 'Película' if target_type == 'movie' else ('Programa' if es_programa else 'Serie')
                raw_bundle = {'es': item, 'mx': mx_res, 'en': det_res}
                item['display_title'] = get_tiered_field(raw_bundle, 'title', target_type)
                item['original_title_h6'] = item.get('original_title') if target_type == 'movie' else item.get('original_name')

                html = render_template('explore_items.html', items=[item])
                yield json.dumps({'item_html': html}) + '\n'
                
                final_items_count += 1
                if final_items_count >= 20: 
                    last_api_page = current_api_page
                    last_api_skip = items_processed_in_this_page
                    break
            
            if final_items_count >= 20: break 
            current_api_page += 1
            to_skip = 0 

        yield json.dumps({
            'done': True, 'next_api_page': last_api_page, 'next_api_skip': last_api_skip,
            'total_found': final_items_count, 'total_pages': total_pages
        }, ensure_ascii=False) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')


@app.route('/api/keywords/search')
def api_keywords_search():
    api_key = os.getenv("TMDB_API_KEY")
    query = request.args.get('q', '')
    if not query:
        return jsonify({'results': []})
    
    url = f"https://api.themoviedb.org/3/search/keyword?api_key={api_key}&query={query}"
    res = fetch_json(url)
    return jsonify(res)


@app.route('/person/<person_id>')
def person_detail(person_id):
    api_key = os.getenv("TMDB_API_KEY")
    
    # --- LANZADERA 1: ESPAÑA, MÉXICO, EEUU (OPTIMIZADA) ---
    initial_urls = {
        "es": f"https://api.themoviedb.org/3/person/{person_id}?api_key={api_key}&language=es-ES&append_to_response=external_ids,translations",
        "mx": f"https://api.themoviedb.org/3/person/{person_id}?api_key={api_key}&language=es-MX",
        "en": f"https://api.themoviedb.org/3/person/{person_id}?api_key={api_key}&language=en-US"
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(fetch_json, url) for name, url in initial_urls.items()}
        results = {name: future.result() for name, future in futures.items()}

    res = results["es"]
    res_mx = results["mx"]
    res_en = results["en"]
    if not res or 'id' not in res: return "Error", 404

    # --- NOMBRE (Directamente del inglés como fuente maestra) ---
    res['name'] = res_en.get('name') or res.get('name') or "-"


    # --- FUSIÓN INTELIGENTE DE BIOGRAFÍAS (Tiered) ---
    res['biography'] = get_tiered_field(results, 'biography', 'person') or "No tenemos una biografía disponible de momento."

    birthday = res.get('birthday')
    today = datetime.today()
    if birthday:
        try:
            b_date = datetime.strptime(birthday, "%Y-%m-%d")
            deathday = res.get('deathday')
            ref_date = datetime.strptime(deathday, "%Y-%m-%d") if deathday else today
            age = ref_date.year - b_date.year - ((ref_date.month, ref_date.day) < (b_date.month, b_date.day))
            res['birthday'] = f"{b_date.strftime('%d/%m/%Y')} ({age} años)"
        except: res['birthday'] = birthday
    else: res['birthday'] = "-"

    if deathday_ext := res.get('deathday'):
        try: res['deathday'] = datetime.strptime(deathday_ext, "%Y-%m-%d").strftime("%d/%m/%Y")
        except: pass
    
    res['gender_name'] = {1: "Femenino", 2: "Masculino", 3: "No Binario"}.get(res.get('gender'), "-")
    ext_ids = res.get('external_ids', {})
    res['socials'] = {
        'instagram': f"https://instagram.com/{ext_ids['instagram_id']}" if ext_ids.get('instagram_id') else None,
        'twitter': f"https://twitter.com/{ext_ids['twitter_id']}" if ext_ids.get('twitter_id') else None,
        'tiktok': f"https://tiktok.com/@{ext_ids['tiktok_id']}" if ext_ids.get('tiktok_id') else None,
        'facebook': f"https://facebook.com/{ext_ids['facebook_id']}" if ext_ids.get('facebook_id') else None,
        'youtube': f"https://youtube.com/{ext_ids['youtube_id']}" if ext_ids.get('youtube_id') else None,
        'homepage': res.get('homepage')
    }

    res['aka_list'] = res.get('also_known_as', [])
    if not res['aka_list']: res['aka_list'] = ["-"]

    # Deteción de origen (Hint para banderas de proyectos)
    place = res.get('place_of_birth', '').lower() if res.get('place_of_birth') else ""
    country_hint = ""
    if 'taiwan' in place: country_hint = 'TW'
    elif 'hong kong' in place: country_hint = 'HK'
    elif 'macao' in place or 'macau' in place: country_hint = 'MO'
    res['country_hint'] = country_hint

    return render_template('person_detail.html', person=res, known_for=[])


@app.route('/api/person/<int:person_id>/projects')
def api_person_projects(person_id):
    api_key = os.getenv("TMDB_API_KEY")

    # 1. LANZADERA DE CRÉDITOS (Jerarquía ES/MX/EN)
    urls = {
        "es": f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=es-ES",
        "mx": f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=es-MX",
        "en": f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=en-US"
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
        results = {name: future.result() for name, future in futures.items()}

    c_es, c_mx, c_en = results["es"], results["mx"], results["en"]
    mx_map = {f"{w.get('media_type', 'movie')}_{w.get('id')}": w for w in (c_mx.get('cast', []) + c_mx.get('crew', []))}
    en_map = {f"{w.get('media_type', 'movie')}_{w.get('id')}": w for w in (c_en.get('cast', []) + c_en.get('crew', []))}

    # 2. FILTRADO Y ORDENACIÓN INICIAL (Top 60 Relevantes)
    all_credits = c_es.get('cast', []) + c_es.get('crew', [])
    def relevance_key(x):
        genre_ids = x.get('genre_ids', [])
        is_ficcion = not any(gid in genre_ids for gid in GENRES_PROGRAMAS)
        return (is_ficcion, x.get('vote_count', 0), x.get('popularity', 0))

    sorted_works = sorted(all_credits, key=relevance_key, reverse=True)
    
    top_works = []
    seen_ids = set()
    for w in sorted_works:
        cid = w.get('id')
        m_type = w.get('media_type', 'movie')
        if cid in seen_ids: continue
        if w.get('original_language', '').lower() not in ASIA_LANGUAGES: continue
        seen_ids.add(cid)
        top_works.append(w)
        if len(top_works) >= 60: break

    # 3. LANZADERA DE PRECISIÓN (Fetching details for each movie/tv show in parallel)
    def fetch_full_detail(w):
        m_id = w.get('id')
        m_type = w.get('media_type', 'movie')
        url = f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={api_key}&language=en-US"
        return fetch_json(url)

    with ThreadPoolExecutor(max_workers=20) as executor:
        full_details_results = list(executor.map(fetch_full_detail, top_works))

    # 4. PROCESADO FINAL CON METADATA COMPLETA
    known_for = []
    hint = request.args.get('h')
    for work, det_res in zip(top_works, full_details_results):
        cid = work.get('id')
        media_type = work.get('media_type', 'movie')
        
        c_mx_item = mx_map.get(f"{media_type}_{cid}", {})
        c_en_item = en_map.get(f"{media_type}_{cid}", {})
        orig_title = (work.get('original_title') or work.get('original_name') or "").strip()

        # Metadatos del trabajo
        work['display_title'] = get_tiered_field({'es': work, 'mx': c_mx_item, 'en': c_en_item}, 'title', media_type)
        work['original_title_h6'] = orig_title
        work['media_type_fixed'] = media_type
        
        # Etiquetado Serie/Peli/Programa
        if media_type == 'movie':
            work['tipo_label'] = 'Película'
        else:
            item_genres = work.get('genre_ids', [])
            work['tipo_label'] = 'Programa' if any(g in item_genres for g in GENRES_PROGRAMAS) else 'Serie'

        # BANDERA DE MÁXIMA PRECISIÓN (Usamos det_res para tener production_countries)
        work['flag'] = get_media_flag(work, det_res, country_hint=hint)
        known_for.append(work)
    
    return render_template('person_items.html', known_for=known_for)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Arrancar el scheduler solo en el proceso principal (evita duplicados al recargar en desarrollo)
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        scheduler.start()
        
    app.run(debug=True)