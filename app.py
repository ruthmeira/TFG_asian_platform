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

GLOBAL_COUNTRIES_LIST = [{"code": "AL", "name": "Albania", "emoji": "🇦🇱"}, {"code": "DE", "name": "Alemania", "emoji": "🇩🇪"}, {"code": "AD", "name": "Andorra", "emoji": "🇦🇩"}, {"code": "AO", "name": "Angola", "emoji": "🇦🇴"}, {"code": "AG", "name": "Antigua y Barbuda", "emoji": "🇦🇬"}, {"code": "SA", "name": "Arabia Saudí", "emoji": "🇸🇦"}, {"code": "DZ", "name": "Argelia", "emoji": "🇩🇿"}, {"code": "AR", "name": "Argentina", "emoji": "🇦🇷"}, {"code": "AU", "name": "Australia", "emoji": "🇦🇺"}, {"code": "AT", "name": "Austria", "emoji": "🇦🇹"}, {"code": "AZ", "name": "Azerbaiyán", "emoji": "🇦🇿"}, {"code": "BS", "name": "Bahamas", "emoji": "🇧🇸"}, {"code": "BB", "name": "Barbados", "emoji": "🇧🇧"}, {"code": "BH", "name": "Baréin", "emoji": "🇧🇭"}, {"code": "BZ", "name": "Belice", "emoji": "🇧🇿"}, {"code": "BM", "name": "Bermudas", "emoji": "🇧🇲"}, {"code": "BY", "name": "Bielorrusia", "emoji": "🇧🇾"}, {"code": "BO", "name": "Bolivia", "emoji": "🇧🇴"}, {"code": "BA", "name": "Bosnia-Herzegovina", "emoji": "🇧🇦"}, {"code": "BR", "name": "Brasil", "emoji": "🇧🇷"}, {"code": "BG", "name": "Bulgaria", "emoji": "🇧🇬"}, {"code": "BF", "name": "Burkina Faso", "emoji": "🇧🇫"}, {"code": "BE", "name": "Bélgica", "emoji": "🇧🇪"}, {"code": "CV", "name": "Cabo Verde", "emoji": "🇨🇻"}, {"code": "CM", "name": "Camerún", "emoji": "🇨🇲"}, {"code": "CA", "name": "Canadá", "emoji": "🇨🇦"}, {"code": "CN", "name": "China", "emoji": "🇨🇳"}, {"code": "QA", "name": "Catar", "emoji": "🇶🇦"}, {"code": "TD", "name": "Chad", "emoji": "🇹🇩"}, {"code": "CL", "name": "Chile", "emoji": "🇨🇱"}, {"code": "CY", "name": "Chipre", "emoji": "🇨🇾"}, {"code": "VA", "name": "Ciudad del Vaticano", "emoji": "🇻🇦"}, {"code": "CO", "name": "Colombia", "emoji": "🇨🇴"}, {"code": "KR", "name": "Corea del Sur", "emoji": "🇰🇷"}, {"code": "CR", "name": "Costa Rica", "emoji": "🇨🇷"}, {"code": "CI", "name": "Costa de Marfil", "emoji": "🇨🇮"}, {"code": "HR", "name": "Croacia", "emoji": "🇭🇷"}, {"code": "CU", "name": "Cuba", "emoji": "🇨🇺"}, {"code": "DK", "name": "Dinamarca", "emoji": "🇩🇰"}, {"code": "EC", "name": "Ecuador", "emoji": "🇪🇨"}, {"code": "EG", "name": "Egipto", "emoji": "🇪🇬"}, {"code": "SV", "name": "El Salvador", "emoji": "🇸🇻"}, {"code": "AE", "name": "Emiratos Árabes Unidos", "emoji": "🇦🇪"}, {"code": "SK", "name": "Eslovaquia", "emoji": "🇸🇰"}, {"code": "SI", "name": "Eslovenia", "emoji": "🇸🇮"}, {"code": "ES", "name": "España", "emoji": "🇪🇸"}, {"code": "US", "name": "Estados Unidos", "emoji": "🇺🇸"}, {"code": "EE", "name": "Estonia", "emoji": "🇪🇪"}, {"code": "PH", "name": "Filipinas", "emoji": "🇵🇭"}, {"code": "FI", "name": "Finlandia", "emoji": "🇫🇮"}, {"code": "FJ", "name": "Fiyi", "emoji": "🇫🇯"}, {"code": "FR", "name": "Francia", "emoji": "🇫🇷"}, {"code": "GH", "name": "Ghana", "emoji": "🇬🇭"}, {"code": "GI", "name": "Gibraltar", "emoji": "🇬🇮"}, {"code": "GR", "name": "Grecia", "emoji": "🇬🇷"}, {"code": "GP", "name": "Guadalupe", "emoji": "🇬🇵"}, {"code": "GT", "name": "Guatemala", "emoji": "🇬🇹"}, {"code": "GF", "name": "Guayana Francesa", "emoji": "🇬🇫"}, {"code": "GQ", "name": "Guinea Ecuatorial", "emoji": "🇬🇶"}, {"code": "GY", "name": "Guyana", "emoji": "🇬🇾"}, {"code": "HN", "name": "Honduras", "emoji": "🇭🇳"}, {"code": "HU", "name": "Hungría", "emoji": "🇭🇺"}, {"code": "IN", "name": "India", "emoji": "🇮🇳"}, {"code": "ID", "name": "Indonesia", "emoji": "🇮🇩"}, {"code": "IQ", "name": "Iraq", "emoji": "🇮🇶"}, {"code": "IE", "name": "Irlanda", "emoji": "🇮🇪"}, {"code": "IS", "name": "Islandia", "emoji": "🇮🇸"}, {"code": "TC", "name": "Islas Turcas y Caicos", "emoji": "🇹🇨"}, {"code": "IL", "name": "Israel", "emoji": "🇮🇱"}, {"code": "IT", "name": "Italia", "emoji": "🇮🇹"}, {"code": "JM", "name": "Jamaica", "emoji": "🇯🇲"}, {"code": "JP", "name": "Japón", "emoji": "🇯🇵"}, {"code": "JO", "name": "Jordania", "emoji": "🇯🇴"}, {"code": "KE", "name": "Kenia", "emoji": "🇰🇪"}, {"code": "XK", "name": "Kosovo", "emoji": "🇽🇰"}, {"code": "KW", "name": "Kuwait", "emoji": "🇰🇼"}, {"code": "LV", "name": "Letonia", "emoji": "🇱🇻"}, {"code": "LY", "name": "Libia", "emoji": "🇱🇾"}, {"code": "LI", "name": "Liechtenstein", "emoji": "🇱🇮"}, {"code": "LT", "name": "Lituania", "emoji": "🇱🇹"}, {"code": "LU", "name": "Luxemburgo", "emoji": "🇱🇺"}, {"code": "LB", "name": "Líbano", "emoji": "🇱🇧"}, {"code": "MO", "name": "Macao", "emoji": "🇲🇴"}, {"code": "MK", "name": "Macedonia", "emoji": "🇲🇰"}, {"code": "MG", "name": "Madagascar", "emoji": "🇲🇬"}, {"code": "MY", "name": "Malasía", "emoji": "🇲🇾"}, {"code": "MW", "name": "Malaui", "emoji": "🇲🇼"}, {"code": "ML", "name": "Mali", "emoji": "🇲🇱"}, {"code": "MT", "name": "Malta", "emoji": "🇲🇹"}, {"code": "MA", "name": "Marruecos", "emoji": "🇲🇦"}, {"code": "MU", "name": "Mauricio", "emoji": "🇲🇺"}, {"code": "MD", "name": "Moldavia", "emoji": "🇲🇩"}, {"code": "ME", "name": "Montenegro", "emoji": "🇲🇪"}, {"code": "MZ", "name": "Mozambique", "emoji": "🇲🇿"}, {"code": "MX", "name": "México", "emoji": "🇲🇽"}, {"code": "MC", "name": "Mónaco", "emoji": "🇲🇨"}, {"code": "NI", "name": "Nicaragua", "emoji": "🇳🇮"}, {"code": "NG", "name": "Nigeria", "emoji": "🇳🇬"}, {"code": "NO", "name": "Noruega", "emoji": "🇳🇴"}, {"code": "NZ", "name": "Nueva Zelanda", "emoji": "🇳🇿"}, {"code": "NE", "name": "Níger", "emoji": "🇳🇪"}, {"code": "OM", "name": "Omán", "emoji": "🇴🇲"}, {"code": "PK", "name": "Pakistán", "emoji": "🇵🇰"}, {"code": "PA", "name": "Panamá", "emoji": "🇵🇦"}, {"code": "PG", "name": "Papúa Nueva Guinea", "emoji": "🇵🇬"}, {"code": "PY", "name": "Paraguay", "emoji": "🇵🇾"}, {"code": "NL", "name": "Países Bajos", "emoji": "🇳🇱"}, {"code": "PE", "name": "Perú", "emoji": "🇵🇪"}, {"code": "PF", "name": "Polinesia Francesa", "emoji": "🇵🇫"}, {"code": "PL", "name": "Polonia", "emoji": "🇵🇱"}, {"code": "PT", "name": "Portugal", "emoji": "🇵🇹"}, {"code": "HK", "name": "RAE de Hong Kong (China)", "emoji": "🇭🇰"}, {"code": "GB", "name": "Reino Unido", "emoji": "🇬🇧"}, {"code": "CZ", "name": "República Checa", "emoji": "🇨🇿"}, {"code": "CD", "name": "República Democrática del Congo", "emoji": "🇨🇩"}, {"code": "DO", "name": "República Dominicana", "emoji": "🇩🇴"}, {"code": "RO", "name": "Rumanía", "emoji": "🇷🇴"}, {"code": "RU", "name": "Rusia", "emoji": "🇷🇺"}, {"code": "SM", "name": "San Marino", "emoji": "🇸🇲"}, {"code": "LC", "name": "Santa Lucía", "emoji": "🇱🇨"}, {"code": "SN", "name": "Senegal", "emoji": "🇸🇳"}, {"code": "RS", "name": "Serbia", "emoji": "🇷🇸"}, {"code": "SC", "name": "Seychelles", "emoji": "🇸🇨"}, {"code": "SG", "name": "Singapur", "emoji": "🇸🇬"}, {"code": "ZA", "name": "Sudáfrica", "emoji": "🇿🇦"}, {"code": "SE", "name": "Suecia", "emoji": "se"}, {"code": "HK", "name": "RAE de Hong Kong (China)", "emoji": "🇭🇰"}, {"code": "GB", "name": "Reino Unido", "emoji": "🇬🇧"}, {"code": "CZ", "name": "República Checa", "emoji": "🇨🇿"}, {"code": "CD", "name": "República Democrática del Congo", "emoji": "🇨🇩"}, {"code": "DO", "name": "República Dominicana", "emoji": "🇩🇴"}, {"code": "RO", "name": "Rumanía", "emoji": "🇷🇴"}, {"code": "RU", "name": "Rusia", "emoji": "🇷🇺"}, {"code": "SM", "name": "San Marino", "emoji": "🇸🇲"}, {"code": "LC", "name": "Santa Lucía", "emoji": "🇱🇨"}, {"code": "SN", "name": "Senegal", "emoji": "🇸🇳"}, {"code": "RS", "name": "Serbia", "emoji": "🇷🇸"}, {"code": "SC", "name": "Seychelles", "emoji": "🇸🇨"}, {"code": "SG", "name": "Singapur", "emoji": "🇸🇬"}, {"code": "ZA", "name": "Sudáfrica", "emoji": "🇿🇦"}, {"code": "SE", "name": "Suecia", "emoji": "🇸🇪"}, {"code": "CH", "name": "Suiza", "emoji": "🇨🇭"}, {"code": "TH", "name": "Tailandia", "emoji": "🇹🇭"}, {"code": "TW", "name": "Taiwán", "emoji": "🇹🇼"}, {"code": "TZ", "name": "Tanzania", "emoji": "🇹🇿"}, {"code": "PS", "name": "Territorios Palestinos", "emoji": "🇵🇸"}, {"code": "TT", "name": "Trinidad y Tobago", "emoji": "🇹🇹"}, {"code": "TR", "name": "Turquía", "emoji": "🇹🇷"}, {"code": "TN", "name": "Túnez", "emoji": "🇹🇳"}, {"code": "UA", "name": "Ucrania", "emoji": "🇺🇦"}, {"code": "UG", "name": "Uganda", "emoji": "🇺🇬"}, {"code": "UY", "name": "Uruguay", "emoji": "🇺🇾"}, {"code": "VE", "name": "Venezuela", "emoji": "🇻🇪"}, {"code": "YE", "name": "Yemen", "emoji": "🇾🇪"}, {"code": "ZM", "name": "Zambia", "emoji": "🇿🇲"}, {"code": "ZW", "name": "Zimbabue", "emoji": "🇿🇼"}]

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
GENRES_PROGRAMAS = [10764, 99, 10763, 10767] # Reality, Docu, Noticias, Talk Show

def clean_overview(text):
    if not text: return None
    placeholders = ["sinopsis no disponible", "no hay sinopsis disponible", "no overview", "add a plot"]
    t_lower = text.lower()
    for p in placeholders:
        if p in t_lower and len(text) < 50:
            return None
    return text

def fetch_json(url):
    try:
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

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

from werkzeug.utils import secure_filename

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
    watch_providers = []
    if user_region:
        flatrate = data.get('watch/providers', {}).get('results', {}).get(user_region, {}).get('flatrate', [])
        elite_ids = {8, 337, 283, 119, 9, 149, 115, 1899, 384, 350, 344, 1773, 188}
        seen_p = set()
        for p in flatrate:
            pid = p['provider_id']
            if pid in elite_ids:
                pid = {9:119, 115:149, 1899:384}.get(pid, pid)
                if pid not in seen_p:
                    watch_providers.append({'id': pid, 'name': p['provider_name']})
                    seen_p.add(pid)
    
    data['cached_watch_providers'] = watch_providers
    data['cached_user_region'] = user_region
    
    USER_CONTEXT_CACHES[u_id] = {
        'media_id': media_id,
        'data': data,
        'cast_data': None,
        'seasons_data': None
    }

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

from itsdangerous import URLSafeTimedSerializer

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

    banderas_base = {
        'ko': '🇰🇷', 'ja': '🇯🇵', 'zh': '🇨🇳', 'cn': '🇨🇳', 
        'th': '🇹🇭', 'vi': '🇻🇳', 'id': '🇮🇩', 'tl': '🇵🇭',
        'hi': '🇮🇳', 'te': '🇮🇳', 'ta': '🇮🇳'
    }

    final_list = []
    seen_ids = set() 
    page = 1
    
    while len(final_list) < 20 and page < 80:
        # Usamos api_media_type para la consulta real a la API
        url = f"https://api.themoviedb.org/3/trending/{api_media_type}/{time_window}?api_key={api_key}&language=es-ES&page={page}"
        response = requests.get(url)
        
        if response.status_code != 200:
            break
            
        data = response.json()
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
                # Detalles (usamos api_media_type para la ruta correcta)
                det_url = f"https://api.themoviedb.org/3/{api_media_type}/{item_id}?api_key={api_key}&language=en-US"
                det_res = requests.get(det_url).json()

                # --- LÓGICA DE BANDERA ROBUSTA (UNIFICADA) ---
                paises_origin = [p.upper() for p in item.get('origin_country', [])]
                paises_prod = [c['iso_3166_1'].upper() for c in det_res.get('production_countries', [])]
                todos_paises = list(set(paises_origin + paises_prod))
                idioma_orig = item.get('original_language', '').lower()

                codigo_final = None
                bandera_final = None

                # 1. SERIES: Priorizar origin_country
                if api_media_type == 'tv' and paises_origin:
                    lang_to_c = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID','ms':'MY','zh':'CN'}
                    c_sug = lang_to_c.get(idioma_orig)
                    codigo_final = c_sug if (c_sug and c_sug in paises_origin) else paises_origin[0]
                    bandera_final = ASIA_FLAGS_MAP.get(codigo_final)

                # 2. PELÍCULAS o fallback: idioma_orig + producción inteligente
                if not bandera_final:
                    lang_map = {
                        'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN',
                        'id':'ID','tl':'PH','fil':'PH','ms':'MY','mn':'MN',
                        'km':'KH','my':'MM','lo':'LA','ne':'NP',
                        'ta':'IN','te':'IN','ml':'IN','kn':'IN','bn':'IN',
                        'mr':'IN','gu':'IN','pa':'IN','ur':'IN','or':'IN',
                        'as':'IN','sd':'IN','ks':'IN',
                        'bo':'CN','ug':'CN'
                    }
                    if idioma_orig in ['zh', 'cn', 'yue']:
                        if 'HK' in todos_paises: codigo_final = 'HK'
                        elif 'TW' in todos_paises: codigo_final = 'TW'
                        elif 'MO' in todos_paises: codigo_final = 'MO'
                        else: codigo_final = 'CN'
                    elif idioma_orig in lang_map:
                        codigo_final = lang_map[idioma_orig]
                    if codigo_final: bandera_final = ASIA_FLAGS_MAP.get(codigo_final)

                # 3. Fallback: Priority list
                if not bandera_final:
                    for code in ASIA_COUNTRIES:
                        if code in todos_paises:
                            bandera_final = ASIA_FLAGS_MAP.get(code)
                            break

                item['flag'] = bandera_final or '🌏'

                curr_title = item.get('name') if api_media_type == 'tv' else item.get('title')
                orig_title = item.get('original_name') if api_media_type == 'tv' else item.get('original_title')

                # --- TÍTULO: TIERED FALLBACK (ES-ES > ES-MX > EN-US) ---
                if not curr_title or curr_title == orig_title:
                    # Nivel 2: México
                    try:
                        mx_res = requests.get(f"https://api.themoviedb.org/3/{api_media_type}/{item_id}?api_key={api_key}&language=es-MX").json()
                        mx_title = mx_res.get('title') if api_media_type == 'movie' else mx_res.get('name')
                        if mx_title and mx_title != orig_title:
                            if api_media_type == 'tv': item['name'] = mx_title
                            else: item['title'] = mx_title
                        else:
                            # Nivel 3: Inglés
                            en_title = det_res.get('title') if api_media_type == 'movie' else det_res.get('name')
                            if en_title:
                                if api_media_type == 'tv': item['name'] = en_title
                                else: item['title'] = en_title
                    except: pass

                # --- SINOPSIS: TIERED FALLBACK (ES-ES > ES-MX > EN-US + TRAD) ---
                if not item.get('overview'):
                    # Nivel 2: México
                    try:
                        mx_res = mx_res if 'mx_res' in locals() else requests.get(f"https://api.themoviedb.org/3/{api_media_type}/{item_id}?api_key={api_key}&language=es-MX").json()
                        mx_overview = mx_res.get('overview')
                        if mx_overview:
                            item['overview'] = mx_overview
                        else:
                            # Nivel 3: Inglés + Traducción
                            en_overview = det_res.get('overview')
                            if en_overview:
                                try:
                                    item['overview'] = GoogleTranslator(source='en', target='es').translate(en_overview)
                                except:
                                    item['overview'] = en_overview
                    except: pass

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

# En modo debug de Flask, el scheduler arrancaría dos veces. 
# WERKZEUG_RUN_MAIN asegura que solo se inicie en el proceso principal.
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler.start()
    print("🚀 Scheduler iniciado: 'day' cada 20 min, 'week' cada 24 h")

# Forzar una carga inicial de TODO (en paralelo) para que las primeras personas no tengan que esperar
with app.app_context():
    # Solo disparamos la inicial si el caché de 'day' está vacío (indica reinicio o primer arranque)
    if not api_cache['day']['series']:
        import threading
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


# --- MEDIA DETAIL ---
tmdb_session = requests.Session()

def fetch_json(url):
    try:
        response = tmdb_session.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

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
        watch_providers = cached.get('cached_watch_providers', [])
        if cached.get('cached_user_region') != user_region:
            watch_providers = []
            if user_region:
                flatrate = cached.get('watch/providers', {}).get('results', {}).get(user_region, {}).get('flatrate', [])
                elite_ids = {8, 337, 283, 119, 9, 149, 115, 1899, 384, 350, 344, 1773, 188}
                seen_p = set()
                for p in flatrate:
                    pid = p['provider_id']
                    if pid in elite_ids:
                        pid = {9:119, 115:149, 1899:384}.get(pid, pid)
                        if pid not in seen_p:
                            watch_providers.append({'id': pid, 'name': p['provider_name']})
                            seen_p.add(pid)
            cached['cached_watch_providers'] = watch_providers
            cached['cached_user_region'] = user_region

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
    append_master = "external_ids,videos,keywords,watch/providers"
    append_master += ",aggregate_credits" if is_tv else ",credits"
    
    urls = {
        'es': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES&append_to_response={append_master}",
        'mx': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-MX&append_to_response={append_master}",
        'en': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US&append_to_response={append_master}"
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(fetch_json, url): name for name, url in urls.items()}
        raw = {future_to_url[future]: future.result() for future in future_to_url}

    res = raw['es']
    if not res or 'id' not in res:
        res = raw['mx'] if (raw['mx'] and 'id' in raw['mx']) else raw['en']
    if not res: return "Error cargando medios", 404

    # PROCESAMIENTO TÍTULO / OVERVIEW
    res['display_title'] = res.get('title') if media_type == 'movie' else res.get('name')
    orig_title = res.get('original_title') if media_type == 'movie' else res.get('original_name')
    if not res['display_title'] or res['display_title'] == orig_title:
        mx_t = raw['mx'].get('title' if media_type == 'movie' else 'name')
        if mx_t and mx_t != orig_title: res['display_title'] = mx_t
        else: res['display_title'] = raw['en'].get('title' if media_type == 'movie' else 'name') or orig_title

    if not res.get('overview') or not clean_overview(res.get('overview')):
        res['overview'] = clean_overview(raw['mx'].get('overview')) or clean_overview(raw['en'].get('overview'))
        if res['overview'] == clean_overview(raw['en'].get('overview')) and res['overview'] and len(res['overview']) > 10:
            try: res['overview'] = GoogleTranslator(source='en', target='es').translate(res['overview'])
            except: pass
    res['overview'] = clean_overview(res.get('overview'))

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
    genre_map = {'Action & Adventure': 'Acción y Aventura', 'Kids': 'Infantil', 'News': 'Noticias', 'Sci-Fi & Fantasy': 'Ciencia Ficción y Fantasía', 'War & Politics': 'Guerra y Política'}
    if 'genres' in res: 
        for g in res['genres']: g['name'] = genre_map.get(g['name'], g['name'])
    status_map = {'Ended':'Finalizada','Returning Series':'En emisión','Planned':'Planeada','Canceled':'Cancelada','In Production':'En producción','Released':'Estrenada'}
    res['status'] = status_map.get(res.get('status'), res.get('status'))
    res['media_subtype'] = 'Programa' if (media_type == 'tv' and any(g['name'] in ['Reality', 'Talk Show', 'Documental', 'Noticias'] for g in res.get('genres', []))) else 'Serie'
    
    paises = list(set([p.upper() for p in res.get('origin_country', [])] + [c['iso_3166_1'].upper() for c in res.get('production_countries', [])]))
    lang = res.get('original_language', '').lower()
    lang_to_c = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID','ms':'MY','zh':'CN','yue':'HK'}
    codigo_final = lang_to_c.get(lang) if (is_tv and lang_to_c.get(lang) in paises) else (lang_to_c.get(lang) or (paises[0] if paises else None))
    res['flag'] = ASIA_FLAGS_MAP.get(codigo_final, '🌏')

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
                last_season['overview'] = clean_overview(s_mx.get('overview')) or clean_overview(s_en.get('overview'))
                if last_season['overview'] == clean_overview(s_en.get('overview')) and last_season['overview']:
                    try: last_season['overview'] = GoogleTranslator(source='en', target='es').translate(last_season['overview'])
                    except: pass
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
    res['original_language_name'] = {'ko':'Coreano','ja':'Japonés','zh':'Chino','cn':'Chino','yue':'Cantonés','th':'Tailandés','vi':'Vietnamita','hi':'Hindi','tl':'Filipino','id':'Indonesio'}.get(lang, lang.upper())

    credits = res.get('aggregate_credits' if is_tv else 'credits', {})
    final_cast_preview = []
    if is_tv:
        # Cogemos solo los 9 primeros para procesar menos
        for a_orig in credits.get('cast', [])[:9]:
            if a_orig.get('roles'):
                a = a_orig.copy() # COPIA para no guarrear el caché maestro
                roles = sorted(a['roles'], key=lambda x: x.get('episode_count', 0), reverse=True)
                valid_roles = [r for r in roles if r.get('character')]
                if valid_roles:
                    first = valid_roles[0]
                    # Formato "1 personaje + contador" (original)
                    char_text = f"{first['character']} <small style='opacity:0.6'>({first['episode_count']} episodio{'s' if first['episode_count']!=1 else ''})</small>"
                    if len(valid_roles) > 1:
                        char_text += f"<br>y {len(valid_roles)-1} más..."
                    a['character'] = char_text
                else: a['character'] = "N/A"
                final_cast_preview.append(a)
            else:
                final_cast_preview.append(a_orig)
    else:
        # PARA PELÍCULAS: Reparto estándar (mucho más simple)
        final_cast_preview = credits.get('cast', [])[:9]
    
    keywords = res.get('keywords', {}).get('results' if is_tv else 'keywords', [])
    res['cast_processed'] = final_cast_preview
    res['crew_processed'] = credits.get('crew', [])
    res['keywords_processed'] = keywords[:15]
    res['raw_data'] = raw
    
    # GUARDAR EN CACHÉ Y RENDERIZAR
    set_cached_media(media_id, res, user_region)
    return media_detail(media_type, media_id)


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
        if not response.get('overview'): response['overview'] = raw['mx'].get('overview') or raw['en'].get('overview')
        
        # Título tiered fallback
        title_es = response.get('name')
        orig_title = response.get('original_name')
        if not title_es or title_es == orig_title:
            mx_title = raw['mx'].get('name')
            response['display_title'] = mx_title if (mx_title and mx_title != orig_title) else (raw['en'].get('name') or orig_title)
        
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
        
        if not s.get('name') or "Temporada" in s.get('name', ''):
            if s_mx.get('name') and "Temporada" not in s_mx['name']: s['name'] = s_mx['name']
            elif s_en.get('name') and "Season" not in s_en['name']: s['name'] = s_en['name']

        if not s.get('overview') or not clean_overview(s.get('overview')):
            if clean_overview(s_mx.get('overview')): s['overview'] = clean_overview(s_mx['overview'])
            elif clean_overview(s_en.get('overview')):
                translations_needed.append((s, s_en['overview']))

        if s.get('air_date'):
            try:
                dt = datetime.strptime(s['air_date'], '%Y-%m-%d')
                s['air_date_formatted'] = f"{dt.day} {meses_f[dt.month-1]} {dt.year}"
            except: s['air_date_formatted'] = s['air_date']
        all_seasons.append(s)

    if translations_needed:
        def translate_overview(item_tuple):
            season_dict, text_en = item_tuple
            try:
                season_dict['overview'] = GoogleTranslator(source='en', target='es').translate(text_en)
            except:
                season_dict['overview'] = text_en
                
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(translate_overview, translations_needed)

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
    else:
        # Petición de emergencia
        urls = {
            'es': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES&append_to_response={'aggregate_credits' if is_tv else 'credits'}",
            'mx': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-MX",
            'en': f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US"
        }
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {name: executor.submit(fetch_json, url) for name, url in urls.items()}
            raw = {name: future.result() for name, future in futures.items()}
        res = raw['es']
        if not res.get('id'): res = raw['mx'] or raw['en']
        
        res['display_title'] = res.get('title') if media_type == 'movie' else res.get('name')
        orig_title = res.get('original_title') if media_type == 'movie' else res.get('original_name')
        if not res['display_title'] or res['display_title'] == orig_title:
            res['display_title'] = raw['mx'].get('name') or raw['en'].get('name') or orig_title

    credits = res.get('aggregate_credits' if is_tv else 'credits', {})
    final_cast, final_crew = credits.get('cast', []), credits.get('crew', [])
    
    # Normalizamos los roles y equipos como COPIAS para no afectar al caché global
    final_cast_display = []
    final_crew_display = []

    if is_tv:
        for a_orig in final_cast:
            if 'roles' in a_orig and a_orig['roles']:
                a = a_orig.copy()
                sorted_roles = sorted(a['roles'], key=lambda x: x.get('episode_count', 0), reverse=True)
                valid_roles = [r for r in sorted_roles if r.get('character')]
                if valid_roles:
                    parts = [f"{r['character']} <small style='opacity:0.6'>({r['episode_count']} episodio{'s' if r['episode_count']!=1 else ''})</small>" for r in valid_roles]
                    a['character'] = ", ".join(parts)
                else: a['character'] = "N/A"
                final_cast_display.append(a)
            else:
                final_cast_display.append(a_orig)
        
        for m_orig in final_crew:
            if 'jobs' in m_orig and m_orig['jobs']:
                m = m_orig.copy()
                valid_jobs = sorted([j for j in m['jobs'] if j.get('job')], key=lambda x: x.get('episode_count', 0), reverse=True)
                if valid_jobs:
                    parts = [f"{j['job']} <small style='opacity:0.6'>({j['episode_count']} episodio{'s' if j['episode_count']!=1 else ''})</small>" for j in valid_jobs]
                    m['job'] = ", ".join(parts)
                else: m['job'] = "N/A"
                final_crew_display.append(m)
            else:
                final_crew_display.append(m_orig)
    else:
        final_cast_display = final_cast
        final_crew_display = final_crew

    crew_by_dept = {}
    dept_translations = {"Directing": "Dirección", "Writing": "Guion", "Production": "Producción", "Art": "Arte", "Camera": "Cámara", "Costume & Make-Up": "Vestuario y Maquillaje", "Visual Effects": "Efectos Visuales", "Sound": "Sonido", "Editing": "Edición", "Crew": "Equipo", "Lighting": "Iluminación", "Actors": "Actores"}
    for member in final_crew_display:
        dept_es = dept_translations.get(member.get('department', 'Others'), member.get('department', 'Others'))
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

    asia_countries = {
        'KR': 'Corea del Sur', 'JP': 'Japón', 'CN': 'China', 'TW': 'Taiwán', 
        'HK': 'Hong Kong', 'MO': 'Macao', 'MN': 'Mongolia', 'TH': 'Tailandia', 
        'VN': 'Vietnam', 'IN': 'India', 'NP': 'Nepal', 'PH': 'Filipinas', 
        'ID': 'Indonesia', 'MY': 'Malasia', 'SG': 'Singapur', 'KH': 'Camboya', 
        'MM': 'Myanmar', 'LA': 'Laos'
    }
    
    genres_by_type = {
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
                           asia_langs=asia_countries, genres_by_type=genres_by_type, 
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

            if country_code: url += f"&with_origin_country={country_code}"
            else: url += f"&with_origin_country={'|'.join(ASIA_COUNTRIES)}"

            # --- FILTRADO DE ORIGEN: Solo idiomas asiáticos (Corrige el contador) ---
            url += f"&with_original_language={'|'.join(ASIA_LANGUAGES)}"

            if year:
                year_param = 'first_air_date_year' if target_type == 'tv' else 'primary_release_year'
                url += f"&{year_param}={year}"

            if watch_providers:
                url += f"&with_watch_providers={watch_providers}&watch_region={watch_region}&with_watch_monetization_types=flatrate|free"

            if keywords:
                # El formato ahora es ID_Nombre|ID_Nombre... para persistencia
                keyword_ids = [k.split('_')[0] for k in keywords.split('|') if k]
                if keyword_ids:
                    url += f"&with_keywords={'|'.join(keyword_ids)}"

            # --- GESTIÓN UNIFICADA DE GÉNEROS (Para que el contador sea exacto) ---
            with_ids = []
            without_ids = []

            # 1. Programas vs Series (Lógica fija)
            if target_type == 'tv':
                if media_type == 'show': 
                    with_ids.append(genres_programas_or) # Usamos OR '|' para incluir alguno
                elif media_type == 'tv': 
                    without_ids.append(genres_programas_and) # Usamos AND ',' para excluir cualquier

            # 2. Géneros a INCLUIR (Si el usuario los elige)
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
                with_ids.append('|'.join(processed_genres)) # Siempre OR para incluir varios

            # 3. Géneros a EXCLUIR (Si el usuario los elige)
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
                without_ids.append(','.join(processed_without)) # Siempre AND ',' para excluir cualquier

            # --- CONSTRUCCIÓN FINAL DE PARÁMETROS (Sin duplicados) ---
            if with_ids: 
                # Unimos con comas o barras según convenga, pero aquí buscamos añadir filtros
                url += f"&with_genres={','.join(with_ids)}"
            if without_ids:
                url += f"&without_genres={','.join(without_ids)}"

            try:
                res = requests.get(url).json()
                results = res.get('results', [])
                total_pages = res.get('total_pages', 1)
                total_results = res.get('total_results', 0)
                
                # Reportar metadata inicial (Solo en el primer yield de este bloque)
                if not total_metadata_sent:
                    yield json.dumps({
                        'total_results': total_results, 
                        'total_pages': total_pages
                    }) + '\n'
                    total_metadata_sent = True

                items_processed_in_this_page = 0
            except: 
                break
                
            if not results: 
                break 

            for item in results:
                mx_res = None
                det_res = None
                items_processed_in_this_page += 1
                
                # 1. Lógica de salto (PRECISIÓN: No repetir ni saltar series)
                if current_api_page == api_start_page and to_skip > 0:
                    to_skip -= 1
                    continue

                # --- SISTEMA DE FILTRADO MANUAL (Garantiza Pureza Total) ---
                genre_ids = item.get('genre_ids', [])
                es_programa = any(gid in GENRES_PROGRAMAS for gid in genre_ids)

                if media_type == 'tv' and es_programa: continue # Fuera intrusos en Series
                if media_type == 'show' and not es_programa: continue # Fuera intrusos en Programas

                idioma_orig = item.get('original_language', '').lower()
                if idioma_orig not in ASIA_LANGUAGES: continue

                item_id = item.get('id')
                item['media_type_fixed'] = target_type
                
                # Detectar tipo_label correctamente (Igual que en Home)
                if target_type == 'movie':
                    item['tipo_label'] = 'Película'
                else:
                    if es_programa:
                         item['tipo_label'] = 'Programa'
                    else:
                         item['tipo_label'] = 'Serie'
                
                det_url = f"https://api.themoviedb.org/3/{target_type}/{item_id}?api_key={api_key}&language=en-US"
                try: 
                    det_res = requests.get(det_url).json()
                except: 
                    det_res = {}

                # --- LÓGICA DE BANDERA ROBUSTA (UNIFICADA) ---
                paises_origin = [p.upper() for p in item.get('origin_country', [])]
                paises_prod = [c['iso_3166_1'].upper() for c in det_res.get('production_countries', [])]
                todos_paises = list(set(paises_origin + paises_prod))
                idioma_orig = item.get('original_language', '').lower()

                codigo_final = None
                bandera_final = None

                # 1. SERIES: Priorizar origin_country
                if target_type == 'tv' and paises_origin:
                    lang_to_c = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID','ms':'MY','zh':'CN'}
                    c_sug = lang_to_c.get(idioma_orig)
                    codigo_final = c_sug if (c_sug and c_sug in paises_origin) else paises_origin[0]
                    bandera_final = ASIA_FLAGS_MAP.get(codigo_final)

                # 2. PELÍCULAS o fallback: idioma_orig
                if not bandera_final:
                    lang_map = {
                        'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN',
                        'id':'ID','tl':'PH','fil':'PH','ms':'MY','mn':'MN',
                        'km':'KH','my':'MM','lo':'LA','ne':'NP',
                        'ta':'IN','te':'IN','ml':'IN','kn':'IN','bn':'IN',
                        'mr':'IN','gu':'IN','pa':'IN','ur':'IN','or':'IN',
                        'as':'IN','sd':'IN','ks':'IN',
                        'bo':'CN','ug':'CN'
                    }
                    if idioma_orig in ['zh', 'cn', 'yue']:
                        if 'HK' in todos_paises: codigo_final = 'HK'
                        elif 'TW' in todos_paises: codigo_final = 'TW'
                        elif 'MO' in todos_paises: codigo_final = 'MO'
                        else: codigo_final = 'CN'
                    elif idioma_orig in lang_map:
                        codigo_final = lang_map[idioma_orig]
                    if codigo_final: bandera_final = ASIA_FLAGS_MAP.get(codigo_final)

                # 3. Fallback: Priority list
                if not bandera_final:
                    for code in ASIA_COUNTRIES:
                        if code in todos_paises:
                            bandera_final = ASIA_FLAGS_MAP.get(code)
                            break

                # --- FILTRADO ESTRICTO ---
                # Si estamos filtrando por país, el código determinado debe estar en la lista seleccionada
                if country_code:
                    selected_countries = country_code.upper().split('|')
                    if codigo_final not in selected_countries:
                        continue

                item['flag'] = bandera_final or '🌏'
                title_es = item.get('name') if target_type == 'tv' else item.get('title')
                orig_title = item.get('original_name') if target_type == 'tv' else item.get('original_title')
                
                item['original_title_h6'] = orig_title
                item['media_type_fixed'] = target_type
                item['tipo_label'] = 'Película' if target_type == 'movie' else ('Programa' if es_programa else 'Serie')
                
                # --- TÍTULO: TIERED FALLBACK (ES-ES > ES-MX > EN-US) ---
                if not title_es or title_es == orig_title:
                    # Nivel 2: México
                    try:
                        if not mx_res:
                            mx_url = f"https://api.themoviedb.org/3/{target_type}/{item_id}?api_key={api_key}&language=es-MX"
                            mx_res = requests.get(mx_url).json()
                        
                        mx_title = mx_res.get('title') if target_type == 'movie' else mx_res.get('name')
                        if mx_title and mx_title != orig_title:
                            item['display_title'] = mx_title
                        else:
                            # Nivel 3: Inglés (Usamos el det_res ya cargado arriba)
                            eng_title = det_res.get('name') if target_type == 'tv' else det_res.get('title')
                            item['display_title'] = eng_title if eng_title else orig_title
                    except:
                        item['display_title'] = orig_title
                else: 
                    item['display_title'] = title_es

                # --- SINOPSIS: TIERED FALLBACK (ES-ES > ES-MX > EN-US + TRAD) ---
                if not item.get('overview'):
                    # Nivel 2: México
                    try:
                        if not mx_res:
                            mx_res = requests.get(f"https://api.themoviedb.org/3/{target_type}/{item_id}?api_key={api_key}&language=es-MX").json()
                        
                        mx_overview = mx_res.get('overview')
                        if mx_overview:
                            item['overview'] = mx_overview
                        else:
                            # Nivel 3: Inglés + Traducción
                            en_overview = det_res.get('overview')
                            if en_overview:
                                try:
                                    item['overview'] = GoogleTranslator(source='en', target='es').translate(en_overview)
                                except:
                                    item['overview'] = en_overview
                    except: pass

                # Renderizar HTML para este item solo
                html = render_template('explore_items.html', items=[item])
                yield json.dumps({'item_html': html}) + '\n'
                
                final_items_count += 1
                if final_items_count >= 20: 
                    # GUARDAMOS EL PUNTO EXACTO DE SALIDA (Para no repetir ni saltar)
                    last_api_page = current_api_page
                    last_api_skip = items_processed_in_this_page
                    break
            
            if final_items_count >= 20: 
                break 

            current_api_page += 1
            to_skip = 0 # En las siguientes páginas de este bloque arrancamos de cero

        # Al terminar enviamos el estado para que la siguiente UI Page sepa donde seguir
        yield json.dumps({
            'done': True, 
            'next_api_page': last_api_page,
            'next_api_skip': last_api_skip,
            'total_found': final_items_count,
            'total_pages': total_pages
        }) + '\n'

    return Response(stream_with_context(generate()), mimetype='application/x-ndjson')


@app.route('/api/keywords/search')
def api_keywords_search():
    api_key = os.getenv("TMDB_API_KEY")
    query = request.args.get('q', '')
    if not query:
        return jsonify({'results': []})
    
    url = f"https://api.themoviedb.org/3/search/keyword?api_key={api_key}&query={query}"
    try:
        res = requests.get(url).json()
        return jsonify(res)
    except:
        return jsonify({'results': []})


@app.route('/person/<person_id>')
def person_detail(person_id):
    api_key = os.getenv("TMDB_API_KEY")
    
    import re
    asian_re = re.compile(r'[\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf\uac00-\ud7af]')
    
    # --- LANZADERA 1: ESPAÑA, MÉXICO, EEUU Y TRADUCCIONES (UNIVERSAL) ---
    def fetch_data(url):
        try: return requests.get(url, timeout=5).json()
        except: return {}

    initial_urls = {
        "es": f"https://api.themoviedb.org/3/person/{person_id}?api_key={api_key}&language=es-ES&append_to_response=external_ids",
        "mx": f"https://api.themoviedb.org/3/person/{person_id}?api_key={api_key}&language=es-MX",
        "en": f"https://api.themoviedb.org/3/person/{person_id}?api_key={api_key}&language=en-US",
        "trans": f"https://api.themoviedb.org/3/person/{person_id}/translations?api_key={api_key}"
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_url = {executor.submit(fetch_data, url): name for name, url in initial_urls.items()}
        results = {name: future.result() for future, name in future_to_url.items()}

    res = results["es"]
    res_mx = results["mx"]
    res_en = results["en"]
    res_trans = results["trans"]
    if not res or 'id' not in res: return "Error", 404

    # --- LANZADERA 2: DETECCIÓN UNIVERSAL ASÍATICA (USANDO TU LISTA ASIA_LANGUAGES) ---
    res['artistic_name'] = "-"
    
    # Buscamos en todas sus traducciones cuál coincide con tus lenguajes asiáticos configurados
    translations = res_trans.get('translations', [])
    for t in translations:
        lang = t.get('iso_639_1')
        if lang in ASIA_LANGUAGES:
            n_name = t.get('data', {}).get('name')
            if n_name and asian_re.search(n_name):
                res['artistic_name'] = n_name
                break

    # Fallback AKA (seguridad extra)
    if res['artistic_name'] == "-":
        aka_list = res.get('also_known_as', [])
        for aka in aka_list:
            if asian_re.search(aka):
                res['artistic_name'] = aka
                break

    # --- FUSIÓN INTELIGENTE DE BIOGRAFÍAS CON TRADUCCIÓN (MANTENIDA) ---
    bio = res.get('biography')
    if not bio or len(bio) < 10:
        bio = res_mx.get('biography')
    
    if (not bio or len(bio) < 10) and res_en.get('biography'):
        en_bio = res_en.get('biography')
        try:
            bio = GoogleTranslator(source='auto', target='es').translate(en_bio)
        except:
            bio = en_bio
            
    res['biography'] = bio or "No tenemos una biografía disponible de momento."
    
    if not res.get('place_of_birth'): 
        res['place_of_birth'] = res_mx.get('place_of_birth') or res_en.get('place_of_birth') or "-"

    best_name = res.get('name') or res_mx.get('name') or res_en.get('name')
    if best_name and asian_re.search(best_name):
        if res_mx.get('name') and not asian_re.search(res_mx['name']): best_name = res_mx['name']
        elif res_en.get('name') and not asian_re.search(res_en['name']): best_name = res_en['name']
    res['name'] = best_name or "-"

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

    aka_list_final = res.get('also_known_as', [])
    res['aka_list'] = [aka for aka in aka_list_final if aka != res['artistic_name']]
    if not res['aka_list']: res['aka_list'] = ["-"]

    return render_template('person_detail.html', person=res, known_for=[])


@app.route('/api/person/<int:person_id>/projects')
def api_person_projects(person_id):
    api_key = os.getenv("TMDB_API_KEY")
    
    def fetch_data(url):
        try: return requests.get(url, timeout=5).json()
        except: return {}

    # AQUÍ MUDAMOS LA LANZADERA DE CRÉDITOS
    urls = {
        "es": f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=es-ES",
        "mx": f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=es-MX",
        "en": f"https://api.themoviedb.org/3/person/{person_id}/combined_credits?api_key={api_key}&language=en-US"
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(fetch_data, url): name for name, url in urls.items()}
        results = {name: future.result() for future, name in future_to_url.items()}

    c_es = results["es"]
    c_mx = results["mx"]
    c_en = results["en"]

    mx_map = {f"{w.get('media_type')}_{w.get('id')}": (w.get('title') or w.get('name')) for w in (c_mx.get('cast', []) + c_mx.get('crew', []))}
    en_map = {f"{w.get('media_type')}_{w.get('id')}": (w.get('title') or w.get('name')) for w in (c_en.get('cast', []) + c_en.get('crew', []))}

    all_credits = c_es.get('cast', []) + c_es.get('crew', [])
    seen_ids = set()
    known_for = []

    def relevance_key(x):
        genre_ids = x.get('genre_ids', [])
        is_ficcion = not any(gid in genre_ids for gid in GENRES_PROGRAMAS)
        return (is_ficcion, x.get('vote_count', 0), x.get('popularity', 0))

    sorted_works = sorted(all_credits, key=relevance_key, reverse=True)

    for work in sorted_works:
        cid = work.get('id')
        media_type = work.get('media_type', 'movie')
        if cid in seen_ids: continue
        idioma_orig = work.get('original_language', '').lower()
        if idioma_orig not in ASIA_LANGUAGES: continue
        seen_ids.add(cid)
        
        # TU LÓGICA DE TÍTULO JERÁRQUICA ESTRICTA
        key = f"{media_type}_{cid}"
        orig_title = (work.get('original_title') or work.get('original_name') or "").strip()
        title_es = (work.get('title') or work.get('name') or "").strip()
        
        best_t = title_es
        if idioma_orig != 'es' and (not title_es or title_es.lower() == orig_title.lower()):
            title_mx = (mx_map.get(key) or "").strip()
            title_en = (en_map.get(key) or "").strip()
            if title_mx and title_mx.lower() != orig_title.lower(): best_t = title_mx
            else: best_t = title_en or title_es or orig_title

        work['display_title'] = best_t
        work['original_title_h6'] = orig_title
        work['media_type_fixed'] = media_type
        if media_type == 'movie':
            work['tipo_label'] = 'Película'
        else:
            item_genres = work.get('genre_ids', [])
            work['tipo_label'] = 'Programa' if any(g in item_genres for g in GENRES_PROGRAMAS) else 'Serie'

        # TU LÓGICA DE BANDERAS
        paises_origin = [p.upper() for p in work.get('origin_country', [])]
        bandera_final = '🌏'
        if paises_origin:
            lang_to_c = {'ko':'KR','ja':'JP','zh':'CN','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID'}
            codigo = lang_to_c.get(idioma_orig, paises_origin[0])
            if idioma_orig in ['zh', 'cn', 'yue']:
                if 'HK' in paises_origin: codigo = 'HK'
                elif 'TW' in paises_origin: codigo = 'TW'
                else: codigo = 'CN'
            bandera_final = ASIA_FLAGS_MAP.get(codigo, '🌏')
        else:
            c_f = {'ko':'KR','ja':'JP','zh':'CN','th':'TH','vi':'VN','hi':'IN'}.get(idioma_orig)
            bandera_final = ASIA_FLAGS_MAP.get(c_f, '🌏')

        work['flag'] = bandera_final
        known_for.append(work)
        if len(known_for) >= 60: break
    
    return render_template('person_items.html', known_for=known_for)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)