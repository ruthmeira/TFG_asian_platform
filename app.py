from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, Response, stream_with_context
import json
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from models import db, User, CollectionItem, Review, ReviewVote, ReviewReport, ModerationLog, MediaReport, GlobalEpisode
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import calendar
from sqlalchemy.orm import joinedload, subqueryload
from urllib.parse import quote
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
import threading
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

GLOBAL_COUNTRIES_LIST = [{"code": "AL", "name": "Albania", "emoji": "🇦🇱"}, {"code": "DE", "name": "Alemania", "emoji": "🇩🇪"}, {"code": "AD", "name": "Andorra", "emoji": "🇦🇩"}, {"code": "AO", "name": "Angola", "emoji": "🇦🇴"}, {"code": "AG", "name": "Antigua y Barbuda", "emoji": "🇦🇬"}, {"code": "SA", "name": "Arabia Saudí", "emoji": "🇸🇦"}, {"code": "DZ", "name": "Argelia", "emoji": "🇩🇿"}, {"code": "AR", "name": "Argentina", "emoji": "🇦🇷"}, {"code": "AU", "name": "Australia", "emoji": "🇦🇺"}, {"code": "AT", "name": "Austria", "emoji": "🇦🇹"}, {"code": "AZ", "name": "Azerbaiyán", "emoji": "🇦🇿"}, {"code": "BS", "name": "Bahamas", "emoji": "🇧🇸"}, {"code": "BB", "name": "Barbados", "emoji": "🇧🇧"}, {"code": "BH", "name": "Baréin", "emoji": "🇧🇭"}, {"code": "BZ", "name": "Belice", "emoji": "🇧🇿"}, {"code": "BM", "name": "Bermudas", "emoji": "🇧🇲"}, {"code": "BY", "name": "Bielorrusia", "emoji": "🇧🇾"}, {"code": "BO", "name": "Bolivia", "emoji": "🇧🇴"}, {"code": "BA", "name": "Bosnia-Herzegovina", "emoji": "🇧🇦"}, {"code": "BR", "name": "Brasil", "emoji": "🇧🇷"}, {"code": "BG", "name": "Bulgaria", "emoji": "🇧🇬"}, {"code": "BF", "name": "Burkina Faso", "emoji": "🇧🇫"}, {"code": "BE", "name": "Bélgica", "emoji": "🇧🇪"}, {"code": "CV", "name": "Cabo Verde", "emoji": "🇨🇻"}, {"code": "CM", "name": "Camerún", "emoji": "🇨🇲"}, {"code": "CA", "name": "Canadá", "emoji": "🇨🇦"}, {"code": "CN", "name": "China", "emoji": "🇨🇳"}, {"code": "QA", "name": "Catar", "emoji": "🇶🇦"}, {"code": "TD", "name": "Chad", "emoji": "🇹🇩"}, {"code": "CL", "name": "Chile", "emoji": "🇨🇱"}, {"code": "CY", "name": "Chipre", "emoji": "🇨🇾"}, {"code": "VA", "name": "Ciudad del Vaticano", "emoji": "🇻🇦"}, {"code": "CO", "name": "Colombia", "emoji": "🇨🇴"}, {"code": "KR", "name": "Corea del Sur", "emoji": "🇰🇷"}, {"code": "CR", "name": "Costa Rica", "emoji": "🇨🇷"}, {"code": "CI", "name": "Costa de Marfil", "emoji": "🇨🇮"}, {"code": "HR", "name": "Croacia", "emoji": "🇭🇷"}, {"code": "CU", "name": "Cuba", "emoji": "🇨🇺"}, {"code": "DK", "name": "Dinamarca", "emoji": "🇩🇰"}, {"code": "EC", "name": "Ecuador", "emoji": "🇪🇨"}, {"code": "EG", "name": "Egipto", "emoji": "🇪🇬"}, {"code": "SV", "name": "El Salvador", "emoji": "🇸🇻"}, {"code": "AE", "name": "Emiratos Árabes Unidos", "emoji": "🇦🇪"}, {"code": "SK", "name": "Eslovaquia", "emoji": "🇸🇰"}, {"code": "SI", "name": "Eslovenia", "emoji": "🇸🇮"}, {"code": "ES", "name": "España", "emoji": "🇪🇸"}, {"code": "US", "name": "Estados Unidos", "emoji": "🇺🇸"}, {"code": "EE", "name": "Estonia", "emoji": "🇪🇪"}, {"code": "PH", "name": "Filipinas", "emoji": "🇵🇭"}, {"code": "FI", "name": "Finlandia", "emoji": "🇫🇮"}, {"code": "FJ", "name": "Fiyi", "emoji": "🇫🇯"}, {"code": "FR", "name": "Francia", "emoji": "🇫🇷"}, {"code": "GH", "name": "Ghana", "emoji": "🇬🇭"}, {"code": "GI", "name": "Gibraltar", "emoji": "🇬🇮"}, {"code": "GR", "name": "Grecia", "emoji": "🇬🇷"}, {"code": "GP", "name": "Guadalupe", "emoji": "🇬🇵"}, {"code": "GT", "name": "Guatemala", "emoji": "🇬🇹"}, {"code": "GF", "name": "Guayana Francesa", "emoji": "🇬🇫"}, {"code": "GQ", "name": "Guinea Ecuatorial", "emoji": "🇬🇶"}, {"code": "GY", "name": "Guyana", "emoji": "🇬🇾"}, {"code": "HN", "name": "Honduras", "emoji": "🇭🇳"}, {"code": "HU", "name": "Hungría", "emoji": "🇭🇺"}, {"code": "IN", "name": "India", "emoji": "🇮🇳"}, {"code": "ID", "name": "Indonesia", "emoji": "🇮🇩"}, {"code": "IQ", "name": "Iraq", "emoji": "🇮🇶"}, {"code": "IE", "name": "Irlanda", "emoji": "🇮🇪"}, {"code": "IS", "name": "Islandia", "emoji": "🇮🇸"}, {"code": "TC", "name": "Islas Turcas y Caicos", "emoji": "🇹🇨"}, {"code": "IL", "name": "Israel", "emoji": "🇮🇱"}, {"code": "IT", "name": "Italia", "emoji": "🇮🇹"}, {"code": "JM", "name": "Jamaica", "emoji": "🇯🇲"}, {"code": "JP", "name": "Japón", "emoji": "🇯🇵"}, {"code": "JO", "name": "Jordania", "emoji": "🇯🇴"}, {"code": "KE", "name": "Kenia", "emoji": "🇰🇪"}, {"code": "XK", "name": "Kosovo", "emoji": "🇽🇰"}, {"code": "KW", "name": "Kuwait", "emoji": "🇰🇼"}, {"code": "LV", "name": "Letonia", "emoji": "🇱🇻"}, {"code": "LY", "name": "Libia", "emoji": "🇱🇾"}, {"code": "LI", "name": "Liechtenstein", "emoji": "🇱🇮"}, {"code": "LT", "name": "Lituania", "emoji": "🇱🇹"}, {"code": "LU", "name": "Luxemburgo", "emoji": "🇱🇺"}, {"code": "LB", "name": "Líbano", "emoji": "🇱🇧"}, {"code": "MO", "name": "Macao", "emoji": "🇲🇴"}, {"code": "MK", "name": "Macedonia", "emoji": "🇲🇰"}, {"code": "MG", "name": "Madagascar", "emoji": "🇲🇬"}, {"code": "MY", "name": "Malasía", "emoji": "🇲🇾"}, {"code": "MW", "name": "Malaui", "emoji": "🇲🇼"}, {"code": "ML", "name": "Mali", "emoji": "🇲🇱"}, {"code": "MT", "name": "Malta", "emoji": "🇲🇹"}, {"code": "MA", "name": "Marruecos", "emoji": "🇲🇦"}, {"code": "MU", "name": "Mauricio", "emoji": "🇲🇺"}, {"code": "MD", "name": "Moldavia", "emoji": "🇲🇩"}, {"code": "ME", "name": "Montenegro", "emoji": "🇲🇪"}, {"code": "MZ", "name": "Mozambique", "emoji": "🇲🇿"}, {"code": "MX", "name": "México", "emoji": "🇲🇽"}, {"code": "MC", "name": "Mónaco", "emoji": "🇲🇨"}, {"code": "NI", "name": "Nicaragua", "emoji": "🇳🇮"}, {"code": "NG", "name": "Nigeria", "emoji": "🇳🇬"}, {"code": "NO", "name": "Noruega", "emoji": "🇳🇴"}, {"code": "NZ", "name": "Nueva Zelanda", "emoji": "🇳🇿"}, {"code": "NE", "name": "Níger", "emoji": "🇳🇪"}, {"code": "OM", "name": "Omán", "emoji": "🇴🇲"}, {"code": "PK", "name": "Pakistán", "emoji": "🇵🇰"}, {"code": "PA", "name": "Panamá", "emoji": "🇵🇦"}, {"code": "PG", "name": "Papúa Nueva Guinea", "emoji": "🇵🇬"}, {"code": "PY", "name": "Paraguay", "emoji": "🇵🇾"}, {"code": "NL", "name": "Países Bajos", "emoji": "🇳🇱"}, {"code": "PE", "name": "Perú", "emoji": "🇵🇪"}, {"code": "PF", "name": "Polinesia Francesa", "emoji": "🇵🇫"}, {"code": "PL", "name": "Polonia", "emoji": "🇵🇱"}, {"code": "PT", "name": "Portugal", "emoji": "🇵🇹"}, {"code": "HK", "name": "RAE de Hong Kong (China)", "emoji": "🇭🇰"}, {"code": "GB", "name": "Reino Unido", "emoji": "🇬🇧"}, {"code": "CZ", "name": "República Checa", "emoji": "🇨🇿"}, {"code": "CD", "name": "República Democrática del Congo", "emoji": "🇨🇩"}, {"code": "DO", "name": "República Dominicana", "emoji": "🇩🇴"}, {"code": "RO", "name": "Rumanía", "emoji": "🇷🇴"}, {"code": "RU", "name": "Rusia", "emoji": "🇷🇺"}, {"code": "SM", "name": "San Marino", "emoji": "🇸🇲"}, {"code": "LC", "name": "Santa Lucía", "emoji": "🇱🇨"}, {"code": "SN", "name": "Senegal", "emoji": "🇸🇳"}, {"code": "RS", "name": "Serbia", "emoji": "🇷🇸"}, {"code": "SC", "name": "Seychelles", "emoji": "🇸🇨"}, {"code": "SG", "name": "Singapur", "emoji": "🇸🇬"}, {"code": "ZA", "name": "Sudáfrica", "emoji": "🇿🇦"}, {"code": "SE", "name": "Suecia", "emoji": "🇸🇪"}, {"code": "CH", "name": "Suiza", "emoji": "🇨🇭"}, {"code": "TH", "name": "Tailandia", "emoji": "🇹🇭"}, {"code": "TW", "name": "Taiwán", "emoji": "🇹🇼"}, {"code": "TZ", "name": "Tanzania", "emoji": "🇹🇿"}, {"code": "PS", "name": "Territorios Palestinos", "emoji": "🇵🇸"}, {"code": "TT", "name": "Trinidad y Tobago", "emoji": "🇹🇹"}, {"code": "TR", "name": "Turquía", "emoji": "🇹🇷"}, {"code": "TN", "name": "Túnez", "emoji": "🇹🇳"}, {"code": "UA", "name": "Ucrania", "emoji": "🇺🇦"}, {"code": "UG", "name": "Uganda", "emoji": "🇺🇬"}, {"code": "UY", "name": "Uruguay", "emoji": "🇺🇾"}, {"code": "VE", "name": "Venezuela", "emoji": "🇻🇪"}, {"code": "YE", "name": "Yemen", "emoji": "🇾🇪"}, {"code": "ZM", "name": "Zambia", "emoji": "🇿🇲"}, {"code": "ZW", "name": "Zimbabue", "emoji": "🇿🇼"}]


REGIONS_MAP = {c['code']: c['emoji'] for c in GLOBAL_COUNTRIES_LIST}

ASIA_LANGUAGES = [
    'ko', 'ja', 'zh', 'cn', 'yue', 'bo', 'ug', 'mn',
    'th', 'vi', 'tl', 'fil', 'id', 'ms', 'km', 'my', 'lo',
    'hi', 'ne', 'ta', 'te', 'ml', 'kn', 'bn', 'mr', 'gu', 'pa', 'ur', 'or', 'as', 'sd', 'ks'
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
    'as':'Asamés', 'sd':'Sindi', 'ks':'Cachemiro', 'bo':'Tibetano', 'ug':'Uigur'
}
GENRES_PROGRAMAS = [10764, 99, 10763, 10767]

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

tmdb_session = requests.Session()

# --- SUPABASE CLIENT ---
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = None

if supabase_url and supabase_key and create_client:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"Error inicializando cliente Supabase: {e}")







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

    if lang in ['zh', 'cn', 'yue']:
        if paises_ordenados and paises_ordenados[0] in ['CN', 'HK', 'TW', 'MO']:
            return ASIA_FLAGS_MAP[paises_ordenados[0]]
            
        if lang == 'yue' and 'HK' in paises_ordenados: return ASIA_FLAGS_MAP['HK']
        if lang in ['zh', 'cn'] and 'CN' in paises_ordenados: return ASIA_FLAGS_MAP['CN']
        
        for p in ['CN', 'HK', 'TW', 'MO']:
            if p in paises_ordenados: return ASIA_FLAGS_MAP[p]

    if c_sug and c_sug in paises_ordenados:
        return ASIA_FLAGS_MAP.get(c_sug, '🌏')

    if paises_ordenados:
        for p in paises_ordenados:
            if p in ASIA_FLAGS_MAP: return ASIA_FLAGS_MAP[p]

    if c_sug and c_sug in ASIA_FLAGS_MAP:
        return ASIA_FLAGS_MAP[c_sug]

    if country_hint in ASIA_FLAGS_MAP:
        return ASIA_FLAGS_MAP[country_hint]
        
    return '🌏'

def get_tiered_field(raw, field='title', media_type='movie'):
    """
    Recupera un campo (título o sinopsis) con lógica de fallback: ES > MX > EN > Original
    'raw' debe ser un dict con {'es': data, 'mx': data, 'en': data}
    """
    res_es, res_mx, res_en = raw.get('es', {}), raw.get('mx', {}), raw.get('en', {})
    
    orig_f = 'original_title' if media_type == 'movie' else 'original_name'
    curr_f = 'title' if media_type == 'movie' else 'name'
    orig_val = res_es.get(orig_f)

    if field == 'title' or field == 'name':
        f_key = 'title' if (field == 'title' and media_type == 'movie') else 'name'
        
        val = res_es.get(f_key)
        if val and val != orig_val: return val
        val = res_mx.get(f_key)
        if val and val != orig_val: return val
        val = res_en.get(f_key)
        if val: return val
        return orig_val or "-"

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
load_dotenv(override=True)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

db.init_app(app)
 
UPLOAD_FOLDER = 'static/uploads/profiles'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    
    data['cached_watch_providers'] = process_watch_providers(data.get('watch/providers', {}), user_region)
    data['cached_user_region'] = user_region
    
    USER_CONTEXT_CACHES[u_id] = {
        'media_id': media_id,
        'data': data,
        'cast_data': None,
        'seasons_data': None
    }
    cleanup_user_caches()

def cleanup_user_caches():
    if len(USER_CONTEXT_CACHES) > 500:
        keys_to_del = list(USER_CONTEXT_CACHES.keys())[:100]
        for k in keys_to_del:
            USER_CONTEXT_CACHES.pop(k, None)


def fetch_json(url):
    try:
        response = tmdb_session.get(url, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_media_summary(m_id, m_type, country_hint=None, include_db=True):
    """
    Obtiene los datos base (tarjeta) de un medio usando la jerarquía ES/MX/EN.
    Optimizado: 1 sola llamada usando append_to_response=translations.
    """
    api_key = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={api_key}&language=es-ES&append_to_response=translations"
    
    res_es = fetch_json(url)
    if not res_es or not res_es.get('id'): return None
    
    trans = res_es.get('translations', {}).get('translations', [])
    t_es = next((x['data'] for x in trans if x['iso_3166_1'] == 'ES'), {})
    t_mx = next((x['data'] for x in trans if x['iso_3166_1'] == 'MX'), {})
    t_en = next((x['data'] for x in trans if x['iso_639_1'] == 'en'), {})

    best_title = t_es.get('title') or t_es.get('name') or \
                 t_mx.get('title') or t_mx.get('name') or \
                 t_en.get('title') or t_en.get('name') or \
                 res_es.get('original_title') or res_es.get('original_name') or "-"

    summary = {
        'id': res_es.get('id'),
        'title': best_title,
        'poster_path': res_es.get('poster_path'),
        'vote_average': res_es.get('vote_average', 0),
        'original_title': res_es.get('original_title' if m_type=='movie' else 'original_name'),
        'flag': get_media_flag(res_es, res_es, country_hint=country_hint)
    }
    
    genre_ids = [g.get('id') for g in res_es.get('genres', [])]
    if m_type == 'movie':
        summary['media_subtype'] = 'Película'
    else:
        is_prod = any(gid in GENRES_PROGRAMAS for gid in genre_ids)
        summary['media_subtype'] = 'Programa' if is_prod else 'Serie'
    
    if include_db:
        try:
            with app.app_context():
                s_rating = db.session.query(db.func.avg(Review.rating)).filter_by(
                    media_id=m_id, media_type=m_type, status='approved'
                ).scalar() or 0
                s_count = Review.query.filter_by(
                    media_id=m_id, media_type=m_type, status='approved'
                ).count()
                summary['shiori_rating'] = round(float(s_rating), 1)
                summary['shiori_count'] = s_count
        except Exception as e:
            summary['shiori_rating'] = 0
            summary['shiori_count'] = 0
            print(f"⚠️ Error cargando rating Shiori para {m_id}: {e}")
    else:
        summary['shiori_rating'] = 0
        summary['shiori_count'] = 0
        
    return summary

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
        identifier = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=identifier).first() or User.query.filter_by(username=identifier).first()
        
        if user and user.check_password(password):
            if user.is_banned:
                flash("Tu cuenta ha sido bloqueada permanentemente por administración de Shiori. Acceso denegado. Si crees que es un error, contacta con contacto.shiori@gmail.com", "error")
                return redirect(url_for('login'))
                
            remember = True if request.form.get('remember') else False
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

@app.route('/login/google')
def login_google():
    action = request.args.get('action', 'login')
    session['google_auth_action'] = action
    session['google_auth_next'] = request.args.get('next')
    
    redirect_uri = url_for('google_authorize', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            resp = google.get('userinfo')
            user_info = resp.json()
        
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        
        user = User.query.filter_by(email=email).first()
        action = session.get('google_auth_action', 'login')
        
        if not user:
            if action == 'register':
                base_username = name.replace(" ", "").lower()
                username = base_username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                    
                user = User(username=username, email=email)
                user.set_password("OAUTH_GOOGLE_USER")
                db.session.add(user)
                db.session.commit()
            else:
                flash("No encontramos ninguna cuenta de SHIORI vinculada a este correo. Regístrate primero para poder conectar con Google.", "error")
                return redirect(url_for('login'))
        
        if user and user.is_banned:
            flash("Esta cuenta ha sido bloqueada permanentemente de Shiori. Acceso denegado. Si crees que es un error, contacta con contacto.shiori@gmail.com", "error")
            return redirect(url_for('login'))

        login_user(user, remember=True)
        next_page = session.pop('google_auth_next', None)
        return redirect(next_page or url_for('home'))
    except Exception as e:
        print(f"❌ Error en Google Auth: {str(e)}")
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
                msg.html = render_template('emails/reset_password_email.html', reset_url=reset_url)
                msg.body = f"Para reestablecer tu contraseña en SHIORI, haz clic en el siguiente enlace: {reset_url}"
                
                mail.send(msg)
            except Exception as e:
                print(f"❌ Error enviando email: {e}")
                flash("Error al enviar el email de recuperación.", "error")
                return redirect(url_for('forgot_password'))
        
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
        login_user(user, remember=True)
        return redirect(url_for('home'))

    return render_template('reset_password.html', token=token)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


api_cache = {'day': {'series': [], 'movies': [], 'shows': [], 'last_updated': 0, 'expire': 14400},
             'week': {'series': [], 'movies': [], 'shows': [], 'last_updated': 0, 'expire': 86400}}

def get_top_20(api_key, media_type, time_window):
    """
    Obtiene el Top 20 asiático para una categoría usando get_media_summary para consistencia.
    """
    api_media_type = 'tv' if media_type in ['tv', 'show'] else 'movie'
    final_list = []
    seen_ids = set() 
    page = 1
    
    while len(final_list) < 20 and page < 80:
        url = f"https://api.themoviedb.org/3/trending/{api_media_type}/{time_window}?api_key={api_key}&language=es-ES&page={page}"
        data = fetch_json(url)
        if not data: break
        results = data.get('results', [])
        if not results: break
            
        for item in results:
            item_id = item.get('id')
            lang = item.get('original_language', '').lower()
            countries = [c.upper() for c in item.get('origin_country', [])]
            
            is_asian = lang in ASIA_LANGUAGES or any(c in ASIA_COUNTRIES for c in countries)
            
            if is_asian and item_id not in seen_ids and item.get('poster_path'):
                if api_media_type == 'tv':
                    genre_ids = item.get('genre_ids', [])
                    es_no_ficcion = any(g in genre_ids for g in GENRES_PROGRAMAS)
                    if media_type == 'tv' and es_no_ficcion: continue
                    if media_type == 'show' and not es_no_ficcion: continue

                summary = get_media_summary(item_id, api_media_type)
                if summary:
                    summary['type'] = api_media_type
                    final_list.append(summary)
                    seen_ids.add(item_id)
                    print(f"Top {media_type} [Summary]: {summary['title']} [{summary['flag']}]")
                
                if len(final_list) >= 20: break
        page += 1
        
    return final_list


def refresh_trending_cache(window):
    """
    Función para actualizar el caché de tendencias en segundo plano.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        print(f"Error: TMDB_API_KEY no encontrada al refrescar cache {window}")
        return

    print(f"[BACKGROUND] Refrescando cache de {window} con TMDB...")
    try:
        api_cache[window]['series'] = get_top_20(api_key, 'tv', window)
        api_cache[window]['movies'] = get_top_20(api_key, 'movie', window)
        api_cache[window]['shows'] = get_top_20(api_key, 'show', window)
        api_cache[window]['last_updated'] = time.time()
        print(f"[BACKGROUND] Cache {window} reemplazada con exito con 20 nuevos items por categoria.")
        print(f"Proxima actualizacion programada segun intervalo.")
    except Exception as e:
        print(f"[BACKGROUND] Error al refrescar cache {window}: {e}")

scheduler = BackgroundScheduler()

scheduler.add_job(
    func=refresh_trending_cache, 
    trigger="interval", 
    seconds=14400, 
    args=['day'],
    id='refresh_day',
    misfire_grace_time=3600,
    coalesce=True
)

scheduler.add_job(
    func=refresh_trending_cache, 
    trigger="interval", 
    seconds=86400, 
    args=['week'],
    id='refresh_week',
    misfire_grace_time=3600,
    coalesce=True
)

def sync_all_media_changes():
    """
    Sincronizador Pro: Busca cambios en TMDB y actualiza Shiori si es necesario.
    Se ejecuta una vez al día.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key: return

    print("[SYNC-GLOBAL] Iniciando sincronización diaria con TMDB...")
    
    with app.app_context():
        unique_medias = db.session.query(CollectionItem.media_id, CollectionItem.media_type).distinct().all()
    
    if not unique_medias: return

    changed_ids = set()
    for m_type in ['movie', 'tv']:
        res = fetch_json(f"https://api.themoviedb.org/3/{m_type}/changes?api_key={api_key}")
        for item in res.get('results', []):
            changed_ids.add((item['id'], m_type))

    to_update = [m for m in unique_medias if (m.media_id, m.media_type) in changed_ids]
    
    if not to_update:
        print("[SYNC-GLOBAL] Nada que actualizar hoy. ¡Todo al día!")
        return

    print(f"[SYNC-GLOBAL] Detectados {len(to_update)} medios con cambios. Actualizando...")
    
    for m_id, m_type in to_update:
        summary = get_media_summary(m_id, m_type, include_db=False)
        if summary:
            print(f"   🔄 Sincronizando: {summary.get('title', m_id)}")
            with app.app_context():
                CollectionItem.query.filter_by(media_id=m_id, media_type=m_type).update({
                    "title": summary['title'],
                    "original_title": summary.get('original_title'),
                    "poster_path": summary['poster_path'],
                    "vote_average": summary.get('vote_average'),
                    "flag": summary['flag'],
                    "media_subtype": summary['media_subtype']
                })
                db.session.commit()
                db.session.remove()
                
        sync_media_calendar_data(m_id, m_type)
    
    print("[SYNC-GLOBAL] Sincronización finalizada con éxito.")

scheduler.add_job(
    func=sync_all_media_changes,
    trigger="interval",
    seconds=86400,
    id='sync_media_changes',
    misfire_grace_time=3600,
    coalesce=True
)


with app.app_context():
    if not api_cache['day']['series']:
        threading.Thread(target=refresh_trending_cache, args=['day']).start()
        threading.Thread(target=refresh_trending_cache, args=['week']).start()
 
def hydrate_trending_ratings(items):
    """
    Actualiza las notas de Shiori en tiempo real para una lista de items de tendencias.
    """
    if not items:
        return
    
    media_ids = [it.get('id') for it in items if it.get('id')]
    
    if media_ids:
        ratings_raw = db.session.query(
            Review.media_id, Review.media_type, db.func.avg(Review.rating)
        ).filter(
            Review.media_id.in_(media_ids),
            Review.status == 'approved'
        ).group_by(Review.media_id, Review.media_type).all()
        
        ratings_map = {(r[0], r[1]): round(float(r[2]), 1) for r in ratings_raw}
        
        for it in items:
            m_id = it.get('id')
            m_type = it.get('type')
            it['shiori_rating'] = ratings_map.get((m_id, m_type), 0.0)

@app.route('/')
def home():
    window = request.args.get('window', 'day')
    if window not in ['day', 'week']: 
        window = 'day'
    
    cache = api_cache[window]
    trending_data = {
        'series': cache.get('series', []),
        'movies': cache.get('movies', []),
        'shows': cache.get('shows', [])
    }
    
    for cat in trending_data:
        hydrate_trending_ratings(trending_data[cat])
    
    return render_template('index.html', 
                           active_window=window, 
                           trending_data=trending_data)

@app.route('/legal/<type>')
def legal_pages(type):
    legal_titles = {
        'terms': 'Términos de Uso',
        'privacy': 'Política de Privacidad',
        'cookies': 'Política de Cookies',
        'contact': 'Contacto'
    }
    
    if type not in legal_titles:
        return redirect(url_for('home'))
        
    return render_template(f'legal/{type}.html', title=legal_titles[type])
 
@app.route('/api/trending')
def api_trending():
    api_key = os.getenv("TMDB_API_KEY")
    window = request.args.get('window', 'day')
    media_type = request.args.get('type', 'series')
    
    if window not in ['day', 'week']: 
        window = 'day'

    current_time = time.time()
    cache = api_cache[window]
    
    type_map = {
        'series': 'tv',
        'movies': 'movie',
        'shows': 'show'
    }
    
    if not cache.get(media_type):
        api_type = type_map.get(media_type, 'tv')
        print(f"⚠️ Caché {window}/{media_type} vacía. Realizando carga manual de emergencia...")
        cache[media_type] = get_top_20(api_key, api_type, window)
        cache['last_updated'] = current_time
    
    items = cache.get(media_type, [])
    hydrate_trending_ratings(items)

    return jsonify({
        media_type: items
    })

@app.route('/profile')
@login_required
def profile():
    t_counts = {
        'favoritos': CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True).count(),
        'viendo': CollectionItem.query.filter_by(user_id=current_user.id, status='Viendo').count(),
        'vistos': CollectionItem.query.filter_by(user_id=current_user.id, status='Visto').count(),
        'pendientes': CollectionItem.query.filter_by(user_id=current_user.id, status='Pendiente').count(),
        'abandonados': CollectionItem.query.filter_by(user_id=current_user.id, status='Abandonado').count()
    }
    return render_template('profile.html', counts=t_counts)

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

        file = request.files.get('profile_image')
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(f"user_{current_user.id}_{int(time.time())}_{file.filename}")
            
            if supabase:
                try:
                    # Subir a Supabase Storage (Bucket 'profiles')
                    file_content = file.read()
                    supabase.storage.from_('profiles').upload(
                        path=filename,
                        file=file_content,
                        file_options={"content-type": file.content_type}
                    )
                    # Obtener la URL pública
                    public_url = supabase.storage.from_('profiles').get_public_url(filename)
                    current_user.profile_image = public_url
                except Exception as e:
                    print(f"Error subiendo a Supabase: {e}")
                    flash("Hubo un error al subir la imagen a la nube.")
            else:
                # Fallback local por si acaso
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


@app.route('/collections')
@login_required
def collections():
    statuses = ['Viendo', 'Visto', 'Pendiente', 'Abandonado']
    user_collections = {}
    t_counts = {}
    
    fav_query = CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True)
    t_counts['favoritos'] = fav_query.count()
    favorites = fav_query.order_by(CollectionItem.created_at.desc()).limit(16).all()
    
    for status in statuses:
        status_query = CollectionItem.query.filter_by(user_id=current_user.id, status=status)
        t_counts[status] = status_query.count()
        items = status_query.order_by(CollectionItem.created_at.desc()).limit(16).all()
        user_collections[status] = items

    all_raw_items = favorites + [item for sublist in user_collections.values() for item in sublist]
    all_ids = [it.media_id for it in all_raw_items]
    
    ratings_map = {}
    if all_ids:
        ratings_raw = db.session.query(
            Review.media_id, Review.media_type, db.func.avg(Review.rating), db.func.count(Review.id)
        ).filter(Review.media_id.in_(all_ids), Review.status == 'approved').group_by(Review.media_id, Review.media_type).all()
        ratings_map = {(r[0], r[1]): {'avg': round(float(r[2]), 1), 'count': r[3]} for r in ratings_raw}

        for item in all_raw_items:
            r_info = ratings_map.get((item.media_id, item.media_type), {'avg': 0, 'count': 0})
            item.shiori_rating = r_info['avg']
            item.shiori_count = r_info['count']

    return render_template('collections.html', collections=user_collections, favorites=favorites, counts=t_counts)



@app.route('/collections/<status>')
@login_required
def view_collection(status):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 16, type=int)
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


    if items:
        ratings_raw = db.session.query(
            Review.media_id, Review.media_type, db.func.avg(Review.rating)
        ).filter_by(status='approved').group_by(Review.media_id, Review.media_type).all()
        ratings_map = {(r[0], r[1]): round(float(r[2]), 1) for r in ratings_raw}
        for item in items:
            item.shiori_rating = ratings_map.get((item.media_id, item.media_type), 0)

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


@app.route('/toggle_favorite', methods=['POST'])
@login_required
def toggle_favorite():
    data = request.json
    media_id = data.get('media_id')
    
    poster_raw = data.get('poster')
    poster_fixed = poster_raw if poster_raw and str(poster_raw).strip() not in ["", "None", "null", "undefined"] else None

    item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=data.get('media_type')).first()

    if item:
        item.is_favorite = not item.is_favorite
        if not item.is_favorite and not item.status:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'favorite': False, 'deleted': True})
    else:
        item = CollectionItem(
            user_id=current_user.id,
            media_id=media_id,
            media_type=data.get('media_type'),
            title=data.get('title'),
            original_title=data.get('original_title'),
            poster_path=poster_fixed,
            vote_average=data.get('vote_average'),
            flag=data.get('flag'),
            is_favorite=True,
            media_subtype=data.get('media_subtype', 'Serie')
        )
        db.session.add(item)
        db.session.flush()
        
        threading.Thread(target=sync_media_calendar_data, args=(item.media_id, item.media_type)).start()

    db.session.commit()
    return jsonify({'favorite': item.is_favorite})

@app.route('/toggle_status', methods=['POST'])
@login_required
def toggle_status():
    data = request.json
    media_id = data.get('media_id')
    new_status = data.get('status')
    
    poster_raw = data.get('poster')
    poster_fixed = poster_raw if poster_raw and str(poster_raw).strip() not in ["", "None", "null", "undefined"] else None
    
    item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=data.get('media_type')).first()

    if item:
        if item.status == new_status:
            item.status = None
        else:
            item.status = new_status
            item.title = data.get('title')
            item.original_title = data.get('original_title')
            item.poster_path = poster_fixed
            item.vote_average = data.get('vote_average')
            item.flag = data.get('flag')
            
        if not item.status and not item.is_favorite:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'current_status': None, 'deleted': True})
    else:
        item = CollectionItem(
            user_id=current_user.id,
            media_id=media_id,
            media_type=data.get('media_type'),
            title=data.get('title'),
            original_title=data.get('original_title'),
            poster_path=poster_fixed,
            vote_average=data.get('vote_average'),
            flag=data.get('flag'),
            status=new_status,
            media_subtype=data.get('media_subtype', 'Serie')
        )
        db.session.add(item)
        db.session.flush()
        
        threading.Thread(target=sync_media_calendar_data, args=(item.media_id, item.media_type)).start()
    
    db.session.commit()
    return jsonify({'current_status': item.status})



def sync_media_calendar_data(m_id, m_type):
    """
    Sincroniza episodios en la tabla GLOBAL compartida. 
    Si ya existen y son recientes, no hace nada (ahorro de API).
    """
    with app.app_context():
        try:
            existing = GlobalEpisode.query.filter_by(media_id=m_id, media_type=m_type).first()
            if existing and (datetime.now(timezone.utc) - existing.last_updated.replace(tzinfo=timezone.utc)) < timedelta(hours=24):
                return 

            print(f"[CALENDAR-SYNC] 🔄 Actualizando episodios globales para {m_type} {m_id}...")
            api_key = os.getenv("TMDB_API_KEY")
            
            # Borramos lo viejo para esta serie específica en la tabla global
            GlobalEpisode.query.filter_by(media_id=m_id, media_type=m_type).delete()
            
            if m_type == 'movie':
                url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={api_key}&language=es-ES"
                res = fetch_json(url)
                if res and res.get('release_date'):
                    new_ev = GlobalEpisode(
                        media_id=m_id, media_type='movie',
                        air_date=datetime.strptime(res['release_date'], '%Y-%m-%d').date(),
                        title=res.get('title', 'Estreno')
                    )
                    db.session.add(new_ev)
            else:
                url_base = f"https://api.themoviedb.org/3/tv/{m_id}?api_key={api_key}&language=es-ES"
                res_base = fetch_json(url_base)
                if not res_base: return
                
                seasons = res_base.get('seasons', [])
                for s in seasons:
                    s_num = s.get('season_number')
                    if s_num == 0: continue 
                    
                    url_s = f"https://api.themoviedb.org/3/tv/{m_id}/season/{s_num}?api_key={api_key}&language=es-ES"
                    res_s = fetch_json(url_s)
                    if res_s and res_s.get('episodes'):
                        for ep in res_s['episodes']:
                            if ep.get('air_date'):
                                new_ep = GlobalEpisode(
                                    media_id=m_id, media_type='tv',
                                    season_number=s_num,
                                    episode_number=ep.get('episode_number'),
                                    air_date=datetime.strptime(ep['air_date'], '%Y-%m-%d').date(),
                                    title=ep.get('name', f"Episodio {ep.get('episode_number')}")
                                )
                                db.session.add(new_ep)
            
            db.session.commit()
            print(f"[CALENDAR-SYNC] ✅ Episodios de {m_id} sincronizados.")
        except Exception as e:
            db.session.rollback()
            print(f"[CALENDAR-SYNC] ❌ Error sincronizando {m_id}: {e}")
        finally:
            db.session.remove()


@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')

@app.route('/api/calendar/events')
@login_required
def api_calendar_events():
    month = request.args.get('month', datetime.now().month, type=int)
    year = request.args.get('year', datetime.now().year, type=int)
    
    last_day = calendar.monthrange(year, month)[1]
    start_date = datetime(year, month, 1).date()
    end_date = datetime(year, month, last_day).date()

    # Hacemos un JOIN entre tu colección y los episodios GLOBALES
    events_query = db.session.query(GlobalEpisode, CollectionItem).join(
        CollectionItem,
        (GlobalEpisode.media_id == CollectionItem.media_id) & 
        (GlobalEpisode.media_type == CollectionItem.media_type)
    ).filter(
        CollectionItem.user_id == current_user.id,
        GlobalEpisode.air_date >= start_date,
        GlobalEpisode.air_date <= end_date
    ).all()

    all_events = []
    for event, item in events_query:
        # Construimos el texto del evento (Ej: "T2 E5: Nombre")
        if event.media_type == 'tv':
            label = f"T{event.season_number} E{event.episode_number}: {event.title}"
        else:
            label = f"Estreno: {event.title}"

        all_events.append({
            'id': item.media_id,
            'type': item.media_type,
            'title': item.title,
            'date': event.air_date.isoformat(),
            'poster': item.poster_path,
            'event_type': label,
            'subtype': item.media_subtype
        })
    
    all_events.sort(key=lambda x: x['date'])
    return jsonify(all_events)


@app.route('/media/<media_type>/<int:media_id>')
def media_detail(media_type, media_id):
    cached = get_cached_media(media_id, media_type)
    
    current_status, is_favorite = (None, False)
    user_region = current_user.region if (current_user.is_authenticated and current_user.region) else None
    if current_user.is_authenticated:
        item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=media_type).first()
        if item: current_status, is_favorite = item.status, item.is_favorite

    shiori_rating = db.session.query(db.func.avg(Review.rating)).filter_by(media_id=media_id, media_type=media_type, status='approved').scalar() or 0
    shiori_count = Review.query.filter_by(media_id=media_id, media_type=media_type, status='approved').count()
    approved_reviews = Review.query.filter_by(media_id=media_id, media_type=media_type, status='approved')\
        .options(joinedload(Review.user), subqueryload(Review.votes_objs))\
        .order_by(Review.created_at.desc()).all()
    
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=media_type).first()

    if cached:
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
                               crew=cached.get('crew_processed', []),
                               shiori_rating=shiori_rating,
                               shiori_count=shiori_count,
                               reviews=approved_reviews,
                               user_review=user_review,
                               recommendations=cached.get('recommendations_processed', []))

    api_key = os.getenv("TMDB_API_KEY")
    is_tv = media_type == 'tv' or ('show' in request.path)
    
    append_base = "external_ids,videos,keywords,watch/providers,translations,recommendations"
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



    if not res.get('poster_path'):
        res['poster_path'] = raw['mx'].get('poster_path') or raw['en'].get('poster_path')

    lang = res.get('original_language', '').lower()
    res['display_title'] = get_tiered_field(raw, 'title', 'movie' if media_type == 'movie' else 'tv')
    res['overview'] = get_tiered_field(raw, 'overview', 'movie' if media_type == 'movie' else 'tv')

    ext_ids = res.get('external_ids', {})
    
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

    if 'genres' in res: 
        for g in res['genres']: g['name'] = GENRE_MAP_ES.get(g['name'], g['name'])
    res['status'] = STATUS_MAP_ES.get(res.get('status'), res.get('status'))
    res['media_subtype'] = 'Programa' if (media_type == 'tv' and any(g['name'] in ['Reality', 'Talk Show', 'Documental', 'Noticias'] for g in res.get('genres', []))) else 'Serie'
    
    res['flag'] = get_media_flag(res, res)

    recs_es = raw['es'].get('recommendations', {}).get('results', [])
    recs_mx = raw['mx'].get('recommendations', {}).get('results', [])
    recs_en = raw['en'].get('recommendations', {}).get('results', [])
    
    mx_map = {r['id']: r for r in recs_mx}
    en_map = {r['id']: r for r in recs_en}

    asia_recs = []
    for r in recs_es:
        rid = r['id']
        r_lang = r.get('original_language', '').lower()
        r_countries = [c.upper() for c in r.get('origin_country', [])]
        is_r_asian = r_lang in ASIA_LANGUAGES or any(c in ASIA_COUNTRIES for c in r_countries)
        
        r_mx = mx_map.get(rid, {})
        r_en = en_map.get(rid, {})
        
        if is_r_asian:
            r['poster_path'] = r.get('poster_path') or r_mx.get('poster_path') or r_en.get('poster_path')
            
            if r['poster_path']:
                m_type_r = r.get('media_type') or ('movie' if (r.get('title') or r_mx.get('title')) else 'tv')
                r['media_type_fixed'] = m_type_r
                
                r['display_title'] = r.get('title') or r.get('name') or \
                                     r_mx.get('title') or r_mx.get('name') or \
                                     r_en.get('title') or r_en.get('name') or "-"
                
                r['original_title_h6'] = r.get('original_title') or r.get('original_name') or \
                                         r_mx.get('original_title') or r_mx.get('original_name') or "-"
                
                r['flag'] = get_media_flag(r, r)
                
                if m_type_r == 'movie':
                    r['tipo_label'] = 'Película'
                else:
                    r_genre_ids = r.get('genre_ids', [])
                    is_prod = any(gid in GENRES_PROGRAMAS for gid in r_genre_ids)
                    r['tipo_label'] = 'Programa' if is_prod else 'Serie'
                    
                asia_recs.append(r)
        if len(asia_recs) >= 8: break
    
    if asia_recs:
        rec_ids = [it['id'] for it in asia_recs]
        rec_ratings = db.session.query(
            Review.media_id, Review.media_type, db.func.avg(Review.rating)
        ).filter(Review.status == 'approved', Review.media_id.in_(rec_ids)).group_by(Review.media_id, Review.media_type).all()
        
        rec_ratings_map = {(r[0], r[1]): round(float(r[2]), 1) for r in rec_ratings}
        for it in asia_recs:
            it['shiori_rating'] = rec_ratings_map.get((it['id'], it['media_type_fixed']), 0)

    res['recommendations_processed'] = asia_recs

    last_season = None
    has_multiple_seasons = False
    if is_tv:
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

    ert = res.get('episode_run_time') or [0]
    runtime = res.get('runtime') or (ert[0] if is_tv and ert else 0)
    res['runtime_formatted'] = f"{runtime // 60}h {runtime % 60}m" if runtime > 60 else f"{runtime}m"
    res['original_language_name'] = ASIA_LANG_NAMES.get(lang, lang.upper())

    def get_best_credits_source(r_es, r_mx, r_en, tv=False):
        key = 'aggregate_credits' if tv else 'credits'
        return r_en.get(key, {})

    credits_master = get_best_credits_source(raw['es'], raw['mx'], raw['en'], is_tv)
    
    final_cast_preview = []
    cast_source = credits_master.get('cast', [])[:9]
    
    for a_orig in cast_source:
        a = a_orig.copy()
        if is_tv and a.get('roles'):
            roles = sorted(a['roles'], key=lambda x: x.get('episode_count', 0), reverse=True)
            if roles:
                first = roles[0]
                char_name = first.get('character', '').strip() or "—"
                char_text = f"{char_name} <small style='opacity:0.6'>({first['episode_count']} episodio{'s' if first['episode_count']!=1 else ''})</small>"
                if len(roles) > 1:
                    char_text += f"<br>y {len(roles)-1} más..."
                a['character'] = char_text
            else:
                a['character'] = ""
        else:
            a['character'] = a.get('character', '').strip() or ""
            
        final_cast_preview.append(a)
    res['cast_processed'] = final_cast_preview
    res['crew_processed'] = credits_master.get('crew', [])
    res['keywords_processed'] = res.get('keywords', {}).get('results' if is_tv else 'keywords', [])[:15]
    res['raw_data'] = raw
    
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
                           crew=res.get('crew_processed', []),
                           shiori_rating=shiori_rating,
                           shiori_count=shiori_count,
                           reviews=approved_reviews,
                           user_review=user_review,
                           recommendations=res.get('recommendations_processed', []))


@app.route('/review/<int:review_id>/vote', methods=['POST'])
@login_required
def vote_review(review_id):
    data = request.get_json() or {}
    vote_type = data.get('vote_type')
    if vote_type not in ['like', 'dislike']:
        return jsonify({'message': 'Voto no válido'}), 400
    
    existing_vote = ReviewVote.query.filter_by(user_id=current_user.id, review_id=review_id).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            db.session.delete(existing_vote)
            action = 'removed'
        else:
            existing_vote.vote_type = vote_type
            action = 'changed'
    else:
        new_vote = ReviewVote(user_id=current_user.id, review_id=review_id, vote_type=vote_type)
        db.session.add(new_vote)
        action = 'added'
        
    db.session.commit()
    
    likes = ReviewVote.query.filter_by(review_id=review_id, vote_type='like').count()
    dislikes = ReviewVote.query.filter_by(review_id=review_id, vote_type='dislike').count()
    
    return jsonify({
        'action': action,
        'likes': likes,
        'dislikes': dislikes,
        'current_vote': vote_type if action != 'removed' else None
    })


@app.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'message': 'No tienes permiso para borrar esta opinión.', 'category': 'error'}), 403
    
    db.session.delete(review)
    db.session.commit()
    return jsonify({'message': 'Opinión borrada con éxito.', 'category': 'success'}), 200

@app.route('/review/<int:review_id>/report', methods=['POST'])
@login_required
def report_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id == current_user.id:
        return jsonify({'category': 'error', 'message': 'No puedes reportar tu propia opinión.'}), 400
    existing_report = ReviewReport.query.filter_by(user_id=current_user.id, review_id=review_id).first()
    if existing_report:
        return jsonify({'category': 'info', 'message': 'Ya has reportado esta opinión anteriormente.'}), 200
    try:
        report = ReviewReport(user_id=current_user.id, review_id=review_id)
        review.report_count += 1
        db.session.add(report)
        db.session.commit()
        return jsonify({'category': 'success', 'message': 'Opinión reportada correctamente. El equipo la revisará pronto.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'category': 'error', 'message': 'Error al procesar el reporte.'}), 500


@app.route('/media/<media_type>/<int:media_id>/report_data', methods=['POST'])
@login_required
def report_media_data(media_type, media_id):
    field_type = request.form.get('field_type')
    description = request.form.get('description')
    media_title = request.form.get('media_title')
    
    if not field_type or not description:
        flash('Por favor, rellena todos los campos del reporte.', 'error')
        return redirect(url_for('media_detail', media_type=media_type, media_id=media_id))
    
    try:
        existing_report = MediaReport.query.filter_by(
            user_id=current_user.id,
            media_id=media_id,
            media_type=media_type,
            field_type=field_type,
            status='pending'
        ).first()

        if existing_report:
            return jsonify({
                'category': 'info', 
                'message': f'Ya has enviado un reporte para la sección "{field_type}" de esta obra que está pendiente de revisión.'
            })

        if not media_title:

            cached = get_cached_media(media_id, media_type)
            if cached:
                media_title = cached.get('display_title') or cached.get('title')
            else:
                summary = get_media_summary(media_id, media_type, include_db=False)
                if summary:
                    media_title = summary.get('title')

        report = MediaReport(
            user_id=current_user.id,
            media_id=media_id,
            media_type=media_type,
            media_title=media_title,
            field_type=field_type,
            description=description
        )

        db.session.add(report)
        db.session.commit()
        return jsonify({'category': 'success', 'message': '¡Hecho! Shiori revisará tu reporte pronto para mejorar la base de datos.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'category': 'error', 'message': 'Hubo un error al enviar el reporte. Inténtalo de nuevo.'}), 500




from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash("Acceso denegado. Se requieren permisos de administrador.", "error")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/reviews')
@login_required
@admin_required
def admin_reviews():
    reviews_to_moderate = Review.query.filter(
        (Review.status == 'pending') | (Review.report_count > 0)
    ).order_by(Review.report_count.desc(), Review.created_at.asc()).all()
    
    for r in reviews_to_moderate:
        r.author_strikes = ModerationLog.query.filter_by(author_id=r.user_id, action='deleted_review').count()
        
        for report in r.reports:
            report.reporter_toxic_level = ModerationLog.query.filter_by(reporter_id=report.user_id, action='dismissed_report').count()
            
        r.previous_rejections = ModerationLog.query.filter_by(review_id=r.id, action='dismissed_report').count()
        r.previous_approvals = ModerationLog.query.filter_by(review_id=r.id, action='approved_after_filter').count()
        
    return render_template('admin_reviews.html', reviews=reviews_to_moderate)

@app.route('/admin/review/<int:review_id>/accept_report', methods=['POST'])
@login_required
@admin_required
def admin_accept_report(review_id):
    review = Review.query.get_or_404(review_id)
    for report in review.reports:
         log = ModerationLog(
             author_id=review.user_id, 
             reporter_id=report.user_id, 
             review_id=review.id, 
             review_content_snapshot=review.comment,
             action='deleted_review', 
             reason='user_report'
         )
         db.session.add(log)
    
    if not review.reports:
        log = ModerationLog(
            author_id=review.user_id, 
            review_id=review.id, 
            review_content_snapshot=review.comment,
            action='deleted_review', 
            reason='auto_filter'
        )
        db.session.add(log)

    db.session.delete(review)
    db.session.commit()
    return redirect(url_for('admin_reviews'))

@app.route('/admin/review/<int:review_id>/reject_report', methods=['POST'])
@login_required
@admin_required
def admin_reject_report(review_id):
    review = Review.query.get_or_404(review_id)
    
    for report in review.reports:
        log = ModerationLog(
            reporter_id=report.user_id,
            review_id=review.id, 
            review_content_snapshot=review.comment,
            action='dismissed_report', 
            reason='user_report'
        )
        db.session.add(log)
    
    if not review.reports:
        log = ModerationLog(
            author_id=review.user_id, 
            review_id=review.id, 
            action='approved_after_filter', 
            reason='auto_filter'
        )
        db.session.add(log)

    review.status = 'approved'
    review.report_count = 0
    ReviewReport.query.filter_by(review_id=review_id).delete()
    
    db.session.commit()
    return redirect(url_for('admin_reviews'))


@app.route('/admin/user/<int:user_id>/history')
@login_required
@admin_required
def admin_user_history(user_id):
    target_user = User.query.get_or_404(user_id)
    
    approved_reviews_count = Review.query.filter_by(user_id=user_id, status='approved').count()
    
    author_logs = ModerationLog.query.filter_by(author_id=user_id, action='deleted_review').order_by(ModerationLog.created_at.desc()).all()
    deleted_reviews_count = len(author_logs)
    
    accepted_reports_count = ModerationLog.query.filter_by(reporter_id=user_id, action='deleted_review').count()
    
    reporter_logs = ModerationLog.query.filter_by(reporter_id=user_id, action='dismissed_report').order_by(ModerationLog.created_at.desc()).all()
    rejected_reports_count = len(reporter_logs)
    
    data_reports_resolved = MediaReport.query.filter_by(user_id=user_id, status='resolved').count()
    
    data_reports_ignored = MediaReport.query.filter_by(user_id=user_id, status='ignored').count()
    
    return render_template('admin_user_history.html', 
                           target_user=target_user, 
                           author_logs=author_logs, 
                           reporter_logs=reporter_logs,
                           approved_reviews_count=approved_reviews_count,
                           deleted_reviews_count=deleted_reviews_count,
                           accepted_reports_count=accepted_reports_count,
                           rejected_reports_count=rejected_reports_count,
                           data_reports_resolved=data_reports_resolved,
                           data_reports_ignored=data_reports_ignored)



@app.route('/admin/user/<int:user_id>/toggle_ban', methods=['POST'])
@login_required
@admin_required
def admin_toggle_ban(user_id):
    target_user = User.query.get_or_404(user_id)
    
    if target_user.id == current_user.id:
        flash("🛑 No puedes banearte a ti mismo, Sensei.", "error")
        return redirect(url_for('admin_user_history', user_id=user_id))

    new_status = not target_user.is_banned
    target_user.is_banned = new_status
    
    if new_status:
        try:
            ReviewVote.query.filter_by(user_id=user_id).delete()
            ReviewReport.query.filter_by(user_id=user_id).delete()
            MediaReport.query.filter_by(user_id=user_id).delete()
            
            CollectionItem.query.filter_by(user_id=user_id).delete(synchronize_session=False)
            
            user_reviews = Review.query.filter_by(user_id=user_id).all()
            for r in user_reviews:
                log = ModerationLog(
                    author_id=user_id, 
                    review_id=r.id, 
                    review_content_snapshot=r.comment, 
                    action='deleted_review', 
                    reason='ban_cleanup'
                )
                db.session.add(log)
                db.session.delete(r) 
            
            message = f"BANEO TOTAL APLICADO. Se ha purgado TODA la información de {target_user.username} (Colecciones, Calendario y Reseñas)."
        except Exception as e:
            db.session.rollback()
            return jsonify({'category': 'error', 'message': f"Error en la purga total: {str(e)}"}), 500
    else:
        message = f"Usuario {target_user.username} reactivado. Nota: Su actividad anterior fue eliminada durante el baneo."

    db.session.commit()
    return jsonify({
        'category': 'success',
        'message': message,
        'is_banned': target_user.is_banned
    })

@app.route('/admin/banned_users')
@login_required
@admin_required
def admin_banned_list():
    banned_users = User.query.filter_by(is_banned=True).order_by(User.username).all()
    return render_template('admin_banned_list.html', banned_users=banned_users)


@app.route('/admin/data-reports')

@login_required
@admin_required
def admin_data_reports():
    reports = MediaReport.query.filter_by(status='pending').order_by(MediaReport.created_at.desc()).all()
    return render_template('admin_data_reports.html', reports=reports)



@app.route('/admin/data-report/<int:report_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_data_report(report_id):
    report = MediaReport.query.get_or_404(report_id)
    report.status = 'resolved'
    db.session.commit()
    return jsonify({'category': 'success', 'message': 'Reporte marcado como resuelto.'})

@app.route('/admin/data-report/<int:report_id>/dismiss', methods=['POST'])
@login_required
@admin_required
def dismiss_data_report(report_id):
    report = MediaReport.query.get_or_404(report_id)
    report.status = 'ignored'
    db.session.commit()
    return jsonify({'category': 'success', 'message': 'Reporte ignorado.'})




@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_id = current_user.id
    try:
        CollectionItem.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        
        ReviewVote.query.filter_by(user_id=user_id).delete()
        ReviewReport.query.filter_by(user_id=user_id).delete()
        MediaReport.query.filter_by(user_id=user_id).delete()
        
        user_reviews = Review.query.filter_by(user_id=user_id).all()
        for r in user_reviews:
            db.session.delete(r)
        
        user = User.query.get(user_id)

        db.session.delete(user)
        db.session.commit()
        
        logout_user()
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar la cuenta: {str(e)}", "error")
        return redirect(url_for('profile'))


@app.route('/media/<media_type>/<int:media_id>/review', methods=['POST'])
@login_required
def post_review(media_type, media_id):
    rating = request.form.get('rating', type=float)
    comment = request.form.get('comment', '').strip()
    
    if rating is None or rating < 0 or rating > 10.0:
        return jsonify({'message': 'La puntuación debe estar entre 0 y 10.', 'category': 'error'}), 400

    BAD_WORDS = ["insulto1", "insulto2", "spam", "foll", "mierd", "put", "idiot"]
    final_status = 'approved'
    for word in BAD_WORDS:
        if word in comment.lower():
            final_status = 'pending'
            break

    media_title = request.form.get('media_title')

    review = Review.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=media_type).first()
    
    if review:
        review.rating = rating
        review.comment = comment
        review.status = final_status
        review.media_title = media_title
        review.created_at = datetime.now(timezone.utc)
        msg = "Tu opinión ha sido actualizada." if final_status == 'approved' else "Tu opinión contiene palabras sensibles y será revisada."
        response_cat = 'success'
    else:
        new_review = Review(
            user_id=current_user.id,
            media_id=media_id,
            media_type=media_type,
            rating=rating,
            comment=comment,
            status=final_status,
            media_title=media_title
        )
        db.session.add(new_review)


        msg = "¡Gracias por votar en Shiori! ❤️" if final_status == 'approved' else "Tu reseña será revisada antes de publicarse."
        response_cat = 'success'
    
    db.session.commit()
    return jsonify({'message': msg, 'category': response_cat})


@app.route('/media/tv/<int:media_id>/seasons')
def seasons(media_id):
    meses_f = ['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sep.', 'oct.', 'nov.', 'dic.']
    cached = get_cached_media(media_id, 'tv')
    u_id = session.get('session_id')
    if cached and u_id and USER_CONTEXT_CACHES.get(u_id, {}).get('seasons_data'):
        return render_template('seasons.html', series=cached, seasons=USER_CONTEXT_CACHES[u_id]['seasons_data'])

    api_key = os.getenv('TMDB_API_KEY')
    
    if cached:
        response = cached
        raw_seasons = sorted(response.get('seasons', []), key=lambda x: x.get('season_number', 0))
        data_mx = cached['raw_data']['mx']
        data_en = cached['raw_data']['en']
    else:
        urls = {
            'es': f"https://api.themoviedb.org/3/tv/{media_id}?api_key={api_key}&language=es-ES&append_to_response=external_ids",
            'mx': f"https://api.themoviedb.org/3/tv/{media_id}?api_key={api_key}&language=es-MX",
            'en': f"https://api.themoviedb.org/3/tv/{media_id}?api_key={api_key}&language=en-US"
        }
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
            raw = {name: future.result() for name, future in futures.items()}
        
        response = raw['es']
        response['display_title'] = get_tiered_field(raw, 'title', 'tv')
        response['overview'] = get_tiered_field(raw, 'overview', 'tv')
        
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

        series = response
        raw_seasons = sorted(series.get('seasons', []), key=lambda x: x.get('season_number', 0))
        data_mx, data_en = raw['mx'], raw['en']

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
        
        name_es = s.get('name')
        name_mx = s_mx.get('name')
        name_en = s_en.get('name')
        
        def is_generic(n):
            if not n: return True
            nl = n.lower()
            return nl.startswith("temporada") or nl.startswith("season")

        if is_generic(name_es):
            if name_mx and not is_generic(name_mx):
                s['name'] = name_mx
            elif name_en and not is_generic(name_en):
                s['name'] = name_en
            else:
                s['name'] = name_es

        if not s.get('overview') or not clean_overview(s.get('overview')):
            s['overview'] = get_tiered_field({'es': s, 'mx': s_mx, 'en': s_en}, 'overview', 'tv')
        
        all_seasons.append(s)

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
        append_credits = 'aggregate_credits' if is_tv else 'credits'
        urls = {
            'es': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES&append_to_response=translations",
            'mx': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-MX",
            'en': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US&append_to_response={append_credits}"
        }
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
            raw = {name: future.result() for name, future in futures.items()}
        res = raw['es']
        res['display_title'] = get_tiered_field(raw, 'title', media_type)
        res['raw_data'] = raw

    def get_best_credits_source(r_es, r_mx, r_en, tv=False):
        key = 'aggregate_credits' if tv else 'credits'
        return r_en.get(key, {})

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
    
    final_cast_display = []
    final_crew_display = []
    
    if is_tv:
        for a_orig in final_cast:
            a = a_orig.copy()
            if a.get('roles'):
                sorted_roles = sorted(a['roles'], key=lambda x: x.get('episode_count', 0), reverse=True)
                
                parts = []
                for r in sorted_roles:
                    char_name = r.get('character', '').strip() or "—"
                    parts.append(f"{char_name} <small style='opacity:0.6'>({r['episode_count']} episodio{'s' if r['episode_count']!=1 else ''})</small>")
                
                a['character'] = ", ".join(parts)
                final_cast_display.append(a)
            else:
                final_cast_display.append(a_orig)
        
        for m_orig in final_crew:
            m = m_orig.copy()
            if m.get('jobs'):
                sorted_jobs = sorted(m['jobs'], key=lambda x: x.get('episode_count', 0), reverse=True)
                
                parts = []
                for j in sorted_jobs:
                    job_name = j.get('job', '').strip() or "Staff"
                    parts.append(f"{job_name} <small style='opacity:0.6'>({j['episode_count']} episodio{'s' if j['episode_count']!=1 else ''})</small>")
                
                m['job'] = ", ".join(parts)
            final_crew_display.append(m)
    else:
        for a_orig in final_cast:
            a = a_orig.copy()
            a['name'] = a.get('name', '')
            a['character'] = a.get('character', '')
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
    api_start_page = request.args.get('api_page', page, type=int) 
    api_skip = request.args.get('api_skip', 0, type=int) 
    
    today = datetime.now().strftime('%Y-%m-%d')
    target_type = 'movie' if media_type == 'movie' else 'tv'
    genres_programas_or = "|".join(map(str, GENRES_PROGRAMAS))
    genres_programas_and = ",".join(map(str, GENRES_PROGRAMAS))

    if target_type == 'movie' and 'first_air_date' in sort_by:
        sort_by = sort_by.replace('first_air_date', 'primary_release_date')
    elif target_type == 'tv' and 'primary_release_date' in sort_by:
        sort_by = sort_by.replace('primary_release_date', 'first_air_date')

    def generate():
        final_items_count = 0
        seen_ids = set()
        current_api_page = api_start_page
        to_skip = api_skip
        max_pages_to_scan = current_api_page + 10 
        
        last_api_page = current_api_page
        last_api_skip = 0
        total_pages = 500
        total_metadata_sent = False
        
        while final_items_count < 20 and current_api_page < max_pages_to_scan:
            url = f"https://api.themoviedb.org/3/discover/{target_type}?api_key={api_key}&language=es-ES&page={current_api_page}&sort_by={sort_by}"
            if 'vote_average' in sort_by: url += "&vote_count.gte=10"
            if target_type == 'tv':
                url += f"&first_air_date.lte={today}"
                if status_id: url += f"&with_status={status_id}"
            else:
                url += f"&primary_release_date.lte={today}"

            if country_code: 
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
                
                page_ids = [it.get('id') for it in results if it.get('id')]
                ratings_map = {}
                if page_ids:
                    with app.app_context():
                        ratings_data = db.session.query(
                            Review.media_id, 
                            Review.media_type, 
                            db.func.avg(Review.rating), 
                            db.func.count(Review.id)
                        ).filter(
                            Review.media_id.in_(page_ids), 
                            Review.media_type == target_type, 
                            Review.status == 'approved'
                        ).group_by(Review.media_id, Review.media_type).all()
                        
                        ratings_map = {r[0]: {'avg': round(float(r[2]), 1), 'count': r[3]} for r in ratings_data}

                with ThreadPoolExecutor(max_workers=20) as executor:
                    full_summaries = list(executor.map(lambda x: get_media_summary(x.get('id'), target_type, include_db=False), results))
                
                for s in full_summaries:
                    if s:
                        r_data = ratings_map.get(s['id'], {'avg': 0, 'count': 0})
                        s['shiori_rating'] = r_data['avg']
                        s['shiori_count'] = r_data['count']

                items_processed_in_this_page = 0
            except Exception as e: 
                print(f"Error en Explore Stream: {e}")
                break
            if not results: break 

            for summary in full_summaries:
                if not summary: continue
                item_id = summary['id']

                if item_id in seen_ids:
                    items_processed_in_this_page += 1
                    continue
                seen_ids.add(item_id)
                items_processed_in_this_page += 1
                
                if current_api_page == api_start_page and to_skip > 0:
                    to_skip -= 1
                    continue

                if country_code:
                    requested_flag = ASIA_FLAGS_MAP.get(country_code.upper())
                    if requested_flag and summary['flag'] != requested_flag:
                        continue 

                summary['display_title'] = summary['title']
                summary['original_title_h6'] = summary['original_title']
                summary['tipo_label'] = summary['media_subtype']
                summary['media_type_fixed'] = target_type

                html = render_template('explore_items.html', items=[summary])
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


    res['name'] = res_en.get('name') or res.get('name') or "-"


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

    url = f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=es-ES"
    credits_res = fetch_json(url)

    all_credits = credits_res.get('cast', []) + credits_res.get('crew', [])
    def relevance_key(x):
        genre_ids = x.get('genre_ids', [])
        is_ficcion = not any(gid in genre_ids for gid in GENRES_PROGRAMAS)
        return (is_ficcion, x.get('vote_count', 0), x.get('popularity', 0))

    sorted_works = sorted(all_credits, key=relevance_key, reverse=True)
    
    top_works = []
    seen_ids = set()
    for w in sorted_works:
        cid = w.get('id')
        if cid in seen_ids: continue
        if w.get('original_language', '').lower() not in ASIA_LANGUAGES: continue
        seen_ids.add(cid)
        top_works.append(w)
        if len(top_works) >= 60: break

    hint = request.args.get('h')
    
    def process_work(w):
        return get_media_summary(w.get('id'), w.get('media_type', 'movie'), country_hint=hint)

    with ThreadPoolExecutor(max_workers=20) as executor:
        summaries = list(executor.map(process_work, top_works))

    known_for = []
    for w_base, summary in zip(top_works, summaries):
        if not summary: continue
        
        media_type = w_base.get('media_type', 'movie')
        
        summary['display_title'] = summary['title']
        summary['original_title_h6'] = summary.get('original_title', '')
        summary['media_type_fixed'] = media_type
        summary['tipo_label'] = summary.get('media_subtype', 'Serie')
        
        known_for.append(summary)
    
    return render_template('person_items.html', known_for=known_for)


@app.route('/search')
def search():
    query = request.args.get('q', '')
    return render_template('search.html', query=query)


@app.route('/api/search/unified')
def api_search_unified():
    api_key = os.getenv("TMDB_API_KEY")
    query = request.args.get('q', '')
    if not query:
        return jsonify({'results': {}, 'counts': {}})

    q_safe = quote(query)

    def generate():
        try:
            seen_media_ids = set()
            ROLE_MAP = {'Acting': 'Actuación', 'Directing': 'Dirección', 'Production': 'Producción', 'Writing': 'Guion', 'Editing': 'Montaje', 'Art': 'Arte', 'Sound': 'Sonido', 'Camera': 'Cámara', 'Visual Effects': 'Efectos Visuales', 'Costume & Make-Up': 'Vestuario', 'Crew': 'Equipo'}
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                f_p1 = executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/person?api_key={api_key}&language=en-US&query={q_safe}&include_adult=false&page=1")
                f_k1 = executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/keyword?api_key={api_key}&query={q_safe}&page=1")
                f_m1 = executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={q_safe}&page=1")
                f_t1 = executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={q_safe}&page=1")
                
                p1, k1, m1, t1 = f_p1.result(), f_k1.result(), f_m1.result(), f_t1.result()

            total_p = min(p1.get('total_pages', 0), 25)
            total_k = min(k1.get('total_pages', 0), 25)
            total_m = min(m1.get('total_pages', 0), 500)
            total_t = min(t1.get('total_pages', 0), 500)
            
            max_p_total = max(total_p, total_k, total_m, total_t)
            
            def process_media_batch(batch, m_type):
                asian_items = []
                for item in batch:
                    m_id = item.get('id')
                    if m_id in seen_media_ids: continue
                    lang = item.get('original_language', '').lower()
                    countries = [c.upper() for c in item.get('origin_country', [])]
                    if lang in ASIA_LANGUAGES or any(c in ASIA_COUNTRIES for c in countries):
                        seen_media_ids.add(m_id)
                        asian_items.append((item, m_type))
                
                if not asian_items: return
                
                with ThreadPoolExecutor(max_workers=10) as trans_executor:
                    results = list(trans_executor.map(lambda x: (enrich_with_translation(x[0], x[1]), x[1]), asian_items))
                    for item, original_m_type in results:
                        cat = original_m_type
                        if original_m_type == 'tv':
                            genre_ids = item.get('genre_ids', [])
                            cat = 'program' if any(gid in genre_ids for gid in GENRES_PROGRAMAS) else 'series'
                        
                        lang = item.get('original_language', '').lower()
                        countries = [c.upper() for c in item.get('origin_country', [])]
                        c_code = LANG_TO_COUNTRY_MAP.get(lang)
                        if not c_code or (countries and c_code not in countries):
                            if countries: c_code = countries[0]
                        
                        yield_data = json.dumps({
                            'category': cat, 'id': item.get('id'), 'type': original_m_type,
                            'title': item.get('title'),
                            'original_title': item.get('original_title') or item.get('original_name') or "",
                            'image': f"https://image.tmdb.org/t/p/w300{item.get('poster_path')}" if item.get('poster_path') else None,
                            'rating': item.get('vote_average', 0), 'flag': ASIA_FLAGS_MAP.get(c_code, '🌏')
                        }, ensure_ascii=False) + '\n'

            def enrich_with_translation(media_item, m_type_fixed):
                it_id = media_item.get('id')
                try:
                    t_data = fetch_json(f"https://api.themoviedb.org/3/{m_type_fixed}/{it_id}/translations?api_key={api_key}")
                    trans = t_data.get('translations', [])
                    t_es = next((x['data'] for x in trans if x['iso_3166_1'] == 'ES'), {})
                    t_mx = next((x['data'] for x in trans if x['iso_3166_1'] == 'MX'), {})
                    best_title = t_es.get('title') or t_es.get('name') or \
                                 t_mx.get('title') or t_mx.get('name') or \
                                 media_item.get('title') or media_item.get('name') or \
                                 media_item.get('original_title') or media_item.get('original_name') or "-"
                    media_item['title'] = best_title
                except: pass
                return media_item

            for current_page in range(1, max_p_total + 1):
                futures = {}
                with ThreadPoolExecutor(max_workers=4) as wave_executor:
                    if current_page <= total_p:
                        futures['p'] = p1 if current_page == 1 else wave_executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/person?api_key={api_key}&language=en-US&query={q_safe}&include_adult=false&page={current_page}")
                    if current_page <= total_k:
                        futures['k'] = k1 if current_page == 1 else wave_executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/keyword?api_key={api_key}&query={q_safe}&page={current_page}")
                    if current_page <= total_m:
                        futures['m'] = m1 if current_page == 1 else wave_executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={q_safe}&page={current_page}")
                    if current_page <= total_t:
                        futures['t'] = t1 if current_page == 1 else wave_executor.submit(fetch_json, f"https://api.themoviedb.org/3/search/tv?api_key={api_key}&query={q_safe}&page={current_page}")

                
                if 'p' in futures:
                    res = futures['p'] if current_page == 1 else futures['p'].result()
                    for p in res.get('results', []):
                        img = p.get('profile_path')
                        role_en = p.get('known_for_department', 'Talento')
                        yield json.dumps({
                            'category': 'person', 'id': p.get('id'), 'type': 'person', 'title': p.get('name', '-'),
                            'image': f"https://image.tmdb.org/t/p/w200{img}" if img else None,
                            'department': ROLE_MAP.get(role_en, role_en)
                        }, ensure_ascii=False) + '\n'

                if 'k' in futures:
                    res = futures['k'] if current_page == 1 else futures['k'].result()
                    for kw in res.get('results', []):
                        yield json.dumps({
                            'category': 'keyword', 'id': kw.get('id'), 'type': 'keyword', 'title': kw.get('name', '').capitalize()
                        }, ensure_ascii=False) + '\n'

                media_batch = []
                if 'm' in futures:
                    res = futures['m'] if current_page == 1 else futures['m'].result()
                    media_batch.extend([(item, 'movie') for item in res.get('results', [])])
                if 't' in futures:
                    res = futures['t'] if current_page == 1 else futures['t'].result()
                    media_batch.extend([(item, 'tv') for item in res.get('results', [])])

                asian_items_to_process = []
                asian_ids = []
                for item, m_type in media_batch:
                    m_id = item.get('id')
                    if m_id in seen_media_ids: continue
                    lang = item.get('original_language', '').lower()
                    countries = [c.upper() for c in item.get('origin_country', [])]
                    if lang in ASIA_LANGUAGES or any(c in ASIA_COUNTRIES for c in countries):
                        seen_media_ids.add(m_id)
                        asian_items_to_process.append((item, m_type))
                        asian_ids.append(m_id)

                if asian_items_to_process:
                    with app.app_context():
                        ratings_data = db.session.query(
                            Review.media_id, 
                            Review.media_type, 
                            db.func.avg(Review.rating), 
                            db.func.count(Review.id)
                        ).filter(
                            Review.media_id.in_(asian_ids),
                            Review.status == 'approved'
                        ).group_by(Review.media_id, Review.media_type).all()
                        
                        ratings_map = {(r[0], r[1]): {'avg': round(float(r[2]), 1), 'count': r[3]} for r in ratings_data}

                    with ThreadPoolExecutor(max_workers=10) as t_executor:
                        enriched = list(t_executor.map(lambda x: (get_media_summary(x[0]['id'], x[1], include_db=False), x[1], x[0]['id']), asian_items_to_process))
                        
                        for summary, original_m_type, it_id in enriched:
                            if not summary: continue
                            
                            shiori = ratings_map.get((it_id, original_m_type), {'avg': 0, 'count': 0})
                            
                            yield json.dumps({
                                'category': summary['media_subtype'].lower().replace('película', 'movie').replace('serie', 'series').replace('programa', 'program'),
                                'id': it_id,
                                'type': original_m_type,
                                'title': summary['title'],
                                'original_title': summary.get('original_title', ""),
                                'image': f"https://image.tmdb.org/t/p/w300{summary['poster_path']}" if summary['poster_path'] else None,
                                'rating': summary.get('vote_average', 0), 
                                'shiori_rating': shiori['avg'],
                                'shiori_count': shiori['count'],
                                'flag': summary.get('flag', '🌏')
                            }, ensure_ascii=False) + '\n'

            yield json.dumps({'done': True}) + '\n'

        except Exception as e:
            print(f"❌ Error en Stream de Búsqueda: {str(e)}")
            yield json.dumps({'done': True, 'error': str(e)}) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        scheduler.start()
        
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
