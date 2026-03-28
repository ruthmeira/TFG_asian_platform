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

GLOBAL_COUNTRIES_LIST = [{"code": "AL", "name": "Albania", "emoji": "🇦🇱"}, {"code": "DE", "name": "Alemania", "emoji": "🇩🇪"}, {"code": "AD", "name": "Andorra", "emoji": "🇦🇩"}, {"code": "AO", "name": "Angola", "emoji": "🇦🇴"}, {"code": "AG", "name": "Antigua y Barbuda", "emoji": "🇦🇬"}, {"code": "SA", "name": "Arabia Saudí", "emoji": "🇸🇦"}, {"code": "DZ", "name": "Argelia", "emoji": "🇩🇿"}, {"code": "AR", "name": "Argentina", "emoji": "🇦🇷"}, {"code": "AU", "name": "Australia", "emoji": "🇦🇺"}, {"code": "AT", "name": "Austria", "emoji": "🇦🇹"}, {"code": "AZ", "name": "Azerbaiyán", "emoji": "🇦🇿"}, {"code": "BS", "name": "Bahamas", "emoji": "🇧🇸"}, {"code": "BB", "name": "Barbados", "emoji": "🇧🇧"}, {"code": "BH", "name": "Baréin", "emoji": "🇧🇭"}, {"code": "BZ", "name": "Belice", "emoji": "🇧🇿"}, {"code": "BM", "name": "Bermudas", "emoji": "🇧🇲"}, {"code": "BY", "name": "Bielorrusia", "emoji": "🇧🇾"}, {"code": "BO", "name": "Bolivia", "emoji": "🇧🇴"}, {"code": "BA", "name": "Bosnia-Herzegovina", "emoji": "🇧🇦"}, {"code": "BR", "name": "Brasil", "emoji": "🇧🇷"}, {"code": "BG", "name": "Bulgaria", "emoji": "🇧🇬"}, {"code": "BF", "name": "Burkina Faso", "emoji": "🇧🇫"}, {"code": "BE", "name": "Bélgica", "emoji": "🇧🇪"}, {"code": "CV", "name": "Cabo Verde", "emoji": "🇨🇻"}, {"code": "CM", "name": "Camerún", "emoji": "🇨🇲"}, {"code": "CA", "name": "Canadá", "emoji": "🇨🇦"}, {"code": "QA", "name": "Catar", "emoji": "🇶🇦"}, {"code": "TD", "name": "Chad", "emoji": "🇹🇩"}, {"code": "CL", "name": "Chile", "emoji": "🇨🇱"}, {"code": "CY", "name": "Chipre", "emoji": "🇨🇾"}, {"code": "VA", "name": "Ciudad del Vaticano", "emoji": "🇻🇦"}, {"code": "CO", "name": "Colombia", "emoji": "🇨🇴"}, {"code": "KR", "name": "Corea del Sur", "emoji": "🇰🇷"}, {"code": "CR", "name": "Costa Rica", "emoji": "🇨🇷"}, {"code": "CI", "name": "Costa de Marfil", "emoji": "🇨🇮"}, {"code": "HR", "name": "Croacia", "emoji": "🇭🇷"}, {"code": "CU", "name": "Cuba", "emoji": "🇨🇺"}, {"code": "DK", "name": "Dinamarca", "emoji": "🇩🇰"}, {"code": "EC", "name": "Ecuador", "emoji": "🇪🇨"}, {"code": "EG", "name": "Egipto", "emoji": "🇪🇬"}, {"code": "SV", "name": "El Salvador", "emoji": "🇸🇻"}, {"code": "AE", "name": "Emiratos Árabes Unidos", "emoji": "🇦🇪"}, {"code": "SK", "name": "Eslovaquia", "emoji": "🇸🇰"}, {"code": "SI", "name": "Eslovenia", "emoji": "🇸🇮"}, {"code": "ES", "name": "España", "emoji": "🇪🇸"}, {"code": "US", "name": "Estados Unidos", "emoji": "🇺🇸"}, {"code": "EE", "name": "Estonia", "emoji": "🇪🇪"}, {"code": "PH", "name": "Filipinas", "emoji": "🇵🇭"}, {"code": "FI", "name": "Finlandia", "emoji": "🇫🇮"}, {"code": "FJ", "name": "Fiyi", "emoji": "🇫🇯"}, {"code": "FR", "name": "Francia", "emoji": "🇫🇷"}, {"code": "GH", "name": "Ghana", "emoji": "🇬🇭"}, {"code": "GI", "name": "Gibraltar", "emoji": "🇬🇮"}, {"code": "GR", "name": "Grecia", "emoji": "🇬🇷"}, {"code": "GP", "name": "Guadalupe", "emoji": "🇬🇵"}, {"code": "GT", "name": "Guatemala", "emoji": "🇬🇹"}, {"code": "GF", "name": "Guayana Francesa", "emoji": "🇬🇫"}, {"code": "GQ", "name": "Guinea Ecuatorial", "emoji": "🇬🇶"}, {"code": "GY", "name": "Guyana", "emoji": "🇬🇾"}, {"code": "HN", "name": "Honduras", "emoji": "🇭🇳"}, {"code": "HU", "name": "Hungría", "emoji": "🇭🇺"}, {"code": "IN", "name": "India", "emoji": "🇮🇳"}, {"code": "ID", "name": "Indonesia", "emoji": "🇮🇩"}, {"code": "IQ", "name": "Iraq", "emoji": "🇮🇶"}, {"code": "IE", "name": "Irlanda", "emoji": "🇮🇪"}, {"code": "IS", "name": "Islandia", "emoji": "🇮🇸"}, {"code": "TC", "name": "Islas Turcas y Caicos", "emoji": "🇹🇨"}, {"code": "IL", "name": "Israel", "emoji": "🇮🇱"}, {"code": "IT", "name": "Italia", "emoji": "🇮🇹"}, {"code": "JM", "name": "Jamaica", "emoji": "🇯🇲"}, {"code": "JP", "name": "Japón", "emoji": "🇯🇵"}, {"code": "JO", "name": "Jordania", "emoji": "🇯🇴"}, {"code": "KE", "name": "Kenia", "emoji": "🇰🇪"}, {"code": "XK", "name": "Kosovo", "emoji": "🇽🇰"}, {"code": "KW", "name": "Kuwait", "emoji": "🇰🇼"}, {"code": "LV", "name": "Letonia", "emoji": "🇱🇻"}, {"code": "LY", "name": "Libia", "emoji": "🇱🇾"}, {"code": "LI", "name": "Liechtenstein", "emoji": "🇱🇮"}, {"code": "LT", "name": "Lituania", "emoji": "🇱🇹"}, {"code": "LU", "name": "Luxemburgo", "emoji": "🇱🇺"}, {"code": "LB", "name": "Líbano", "emoji": "🇱🇧"}, {"code": "MK", "name": "Macedonia", "emoji": "🇲🇰"}, {"code": "MG", "name": "Madagascar", "emoji": "🇲🇬"}, {"code": "MY", "name": "Malasia", "emoji": "🇲🇾"}, {"code": "MW", "name": "Malaui", "emoji": "🇲🇼"}, {"code": "ML", "name": "Mali", "emoji": "🇲🇱"}, {"code": "MT", "name": "Malta", "emoji": "🇲🇹"}, {"code": "MA", "name": "Marruecos", "emoji": "🇲🇦"}, {"code": "MU", "name": "Mauricio", "emoji": "🇲🇺"}, {"code": "MD", "name": "Moldavia", "emoji": "🇲🇩"}, {"code": "ME", "name": "Montenegro", "emoji": "🇲🇪"}, {"code": "MZ", "name": "Mozambique", "emoji": "🇲🇿"}, {"code": "MX", "name": "México", "emoji": "🇲🇽"}, {"code": "MC", "name": "Mónaco", "emoji": "🇲🇨"}, {"code": "NI", "name": "Nicaragua", "emoji": "🇳🇮"}, {"code": "NG", "name": "Nigeria", "emoji": "🇳🇬"}, {"code": "NO", "name": "Noruega", "emoji": "🇳🇴"}, {"code": "NZ", "name": "Nueva Zelanda", "emoji": "🇳🇿"}, {"code": "NE", "name": "Níger", "emoji": "🇳🇪"}, {"code": "OM", "name": "Omán", "emoji": "🇴🇲"}, {"code": "PK", "name": "Pakistán", "emoji": "🇵🇰"}, {"code": "PA", "name": "Panamá", "emoji": "🇵🇦"}, {"code": "PG", "name": "Papúa Nueva Guinea", "emoji": "🇵🇬"}, {"code": "PY", "name": "Paraguay", "emoji": "🇵🇾"}, {"code": "NL", "name": "Países Bajos", "emoji": "🇳🇱"}, {"code": "PE", "name": "Perú", "emoji": "🇵🇪"}, {"code": "PF", "name": "Polinesia Francesa", "emoji": "🇵🇫"}, {"code": "PL", "name": "Polonia", "emoji": "🇵🇱"}, {"code": "PT", "name": "Portugal", "emoji": "🇵🇹"}, {"code": "HK", "name": "RAE de Hong Kong (China)", "emoji": "🇭🇰"}, {"code": "GB", "name": "Reino Unido", "emoji": "🇬🇧"}, {"code": "CZ", "name": "República Checa", "emoji": "🇨🇿"}, {"code": "CD", "name": "República Democrática del Congo", "emoji": "🇨🇩"}, {"code": "DO", "name": "República Dominicana", "emoji": "🇩🇴"}, {"code": "RO", "name": "Rumanía", "emoji": "🇷🇴"}, {"code": "RU", "name": "Rusia", "emoji": "🇷🇺"}, {"code": "SM", "name": "San Marino", "emoji": "🇸🇲"}, {"code": "LC", "name": "Santa Lucía", "emoji": "🇱🇨"}, {"code": "SN", "name": "Senegal", "emoji": "🇸🇳"}, {"code": "RS", "name": "Serbia", "emoji": "🇷🇸"}, {"code": "SC", "name": "Seychelles", "emoji": "🇸🇨"}, {"code": "SG", "name": "Singapur", "emoji": "🇸🇬"}, {"code": "ZA", "name": "Sudáfrica", "emoji": "🇿🇦"}, {"code": "SE", "name": "Suecia", "emoji": "🇸🇪"}, {"code": "CH", "name": "Suiza", "emoji": "🇨🇭"}, {"code": "TH", "name": "Tailandia", "emoji": "🇹🇭"}, {"code": "TW", "name": "Taiwán", "emoji": "🇹🇼"}, {"code": "TZ", "name": "Tanzania", "emoji": "🇹🇿"}, {"code": "PS", "name": "Territorios Palestinos", "emoji": "🇵🇸"}, {"code": "TT", "name": "Trinidad y Tobago", "emoji": "🇹🇹"}, {"code": "TR", "name": "Turquía", "emoji": "🇹🇷"}, {"code": "TN", "name": "Túnez", "emoji": "🇹🇳"}, {"code": "UA", "name": "Ucrania", "emoji": "🇺🇦"}, {"code": "UG", "name": "Uganda", "emoji": "🇺🇬"}, {"code": "UY", "name": "Uruguay", "emoji": "🇺🇾"}, {"code": "VE", "name": "Venezuela", "emoji": "🇻🇪"}, {"code": "YE", "name": "Yemen", "emoji": "🇾🇪"}, {"code": "ZM", "name": "Zambia", "emoji": "🇿🇲"}, {"code": "ZW", "name": "Zimbabue", "emoji": "🇿🇼"}]

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

# --- AUTH ---
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
    
    return render_template('register.html', countries_list=GLOBAL_COUNTRIES_LIST)

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
        
        # Mensaje unificado (si existe o si no) para máxima privacidad
        flash("Si el email existe en nuestra base de datos, recibirás un enlace de recuperación en unos minutos. Revisa tu carpeta de spam.", "success")
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
    # Filtro de idiomas asiáticos
    asia_languages = ['ko', 'ja', 'zh', 'cn', 'th', 'hi', 'te', 'ta', 'vi', 'id', 'tl']
    
    # IDs de no-ficción: Reality (10764), Documental (99), Noticias (10763), Talk Show (10767)
    generos_no_ficcion = [10764, 99, 10763, 10767]
    
    # Para TMDB, tanto 'series' como 'programas' usan el endpoint 'tv'
    api_media_type = 'tv' if media_type in ['tv', 'show'] else 'movie'

    banderas_base = {
        'ko': '🇰🇷', 'ja': '🇯🇵', 'zh': '🇨🇳', 'cn': '🇨🇳', 
        'th': '🇹🇭', 'vi': '🇻🇳', 'id': '🇮🇩', 'tl': '🇵🇭',
        'hi': '🇮🇳', 'te': '🇮🇳', 'ta': '🇮🇳'
    }

    final_list = []
    seen_ids = set() 
    page = 1
    
    while len(final_list) < 20 and page < 40:
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
                es_no_ficcion = any(g in item_genres for g in generos_no_ficcion)
                
                if media_type == 'tv' and es_no_ficcion:
                    continue  # Si buscamos Series, saltamos Programas
                elif media_type == 'show' and not es_no_ficcion:
                    continue  # Si buscamos Programas, saltamos Series
            
            if lang in asia_languages and item_id not in seen_ids and item.get('poster_path'):
                item['flag'] = banderas_base.get(lang, '🌏')

                # Detalles (usamos api_media_type para la ruta correcta)
                det_url = f"https://api.themoviedb.org/3/{api_media_type}/{item_id}?api_key={api_key}&language=en-US"
                det_res = requests.get(det_url).json()

                # --- LÓGICA DE BANDERA ROBUSTA ---
                paises_origin = [p.upper() for p in item.get('origin_country', [])]
                paises_prod = [c['iso_3166_1'].upper() for c in det_res.get('production_countries', [])]
                todos_paises = list(set(paises_origin + paises_prod))
                idioma_orig = item.get('original_language', '').lower()

                mapa_banderas = {'KR':'🇰🇷','JP':'🇯🇵','CN':'🇨🇳','TW':'🇹🇼','HK':'🇭🇰','TH':'🇹🇭','VN':'🇻🇳','IN':'🇮🇳','PH':'🇵🇭','ID':'🇮🇩','MY':'🇲🇾'}
                codigo_final = None
                bandera_final = None

                # 1. SERIES: Priorizar origin_country
                if api_media_type == 'tv' and paises_origin:
                    lang_to_c = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID','ms':'MY'}
                    c_sug = lang_to_c.get(idioma_orig)
                    codigo_final = c_sug if (c_sug and c_sug in paises_origin) else paises_origin[0]
                    bandera_final = mapa_banderas.get(codigo_final)

                # 2. PELÍCULAS o fallback: idioma_orig
                if not bandera_final:
                    lang_map = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','id':'ID','tl':'PH','fil':'PH','ms':'MY'}
                    if idioma_orig in ['zh', 'cn', 'yue']:
                        if 'HK' in todos_paises: codigo_final = 'HK'
                        elif 'TW' in todos_paises: codigo_final = 'TW'
                        else: codigo_final = 'CN'
                    elif idioma_orig in lang_map:
                        codigo_final = lang_map[idioma_orig]
                    if codigo_final: bandera_final = mapa_banderas.get(codigo_final)

                # 3. Fallback: Priority list
                if not bandera_final:
                    for code in ['KR', 'JP', 'HK', 'TW', 'CN', 'TH', 'VN', 'IN', 'PH', 'ID', 'MY']:
                        if code in todos_paises:
                            codigo_final = code
                            bandera_final = mapa_banderas.get(code)
                            break

                item['flag'] = bandera_final or '🌏'

                curr_title = item.get('name') if api_media_type == 'tv' else item.get('title')
                orig_title = item.get('original_name') if api_media_type == 'tv' else item.get('original_title')

                if curr_title == orig_title:
                    new_name = det_res.get('name') if api_media_type == 'tv' else det_res.get('title')
                    if new_name:
                        if api_media_type == 'tv': item['name'] = new_name
                        else: item['title'] = new_name
                    
                    if not item.get('overview'):
                        item['overview'] = det_res.get('overview')

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
        if password: current_user.set_password(password)
        db.session.commit()
        next_page = request.args.get('next')
        if not next_page:
            flash("Perfil actualizado correctamente.", "success")
        return redirect(next_page or url_for('edit_profile'))
    
    return render_template('edit_profile.html', countries_list=GLOBAL_COUNTRIES_LIST)

# --- COLLECTIONS ---
@app.route('/collections')
@login_required
def collections():
    statuses = ['Viendo', 'Visto', 'Pendiente', 'Abandonado']
    user_collections = {}

    for status in statuses:
        user_collections[status] = CollectionItem.query.filter_by(
            user_id=current_user.id, status=status
        ).order_by(CollectionItem.created_at.desc()).limit(15).all()

    favorites = CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True).order_by(CollectionItem.created_at.desc()).limit(15).all()
    return render_template('collections.html', collections=user_collections, favorites=favorites)



@app.route('/collections/<status>')
@login_required
def view_collection(status):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = CollectionItem.query.filter_by(user_id=current_user.id).order_by(CollectionItem.created_at.desc())

    if status.lower() == 'favoritos':
        query = query.filter_by(is_favorite=True)
        display_name = "Mis Favoritos"
    else:
        query = query.filter_by(status=status)
        display_name = status

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    return render_template('collection_view.html', 
                          items=items, 
                          display_name=display_name, 
                          pagination=pagination, 
                          status=status)


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
@app.route('/media/<media_type>/<int:media_id>')
def media_detail(media_type, media_id):
    api_key = os.getenv("TMDB_API_KEY")
    
    # 1. Intentamos primero en Español
    url_es = f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=es-ES"
    res = requests.get(url_es).json()
    
    # 2. Comprobamos si falta la sinopsis (overview) o el título
    # Si la sinopsis está vacía, pedimos los datos en Inglés
    if not res.get('overview') or res.get('overview') == "":
        url_en = f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}&language=en-US"
        res_en = requests.get(url_en).json()
        
        # Usamos el título en inglés si el español no existe (para evitar caracteres asiáticos)
        res['title'] = res_en.get('title') or res_en.get('name')
        
        # Traducimos la sinopsis del inglés al español
        en_overview = res_en.get('overview')
        if en_overview:
            try:
                res['overview'] = GoogleTranslator(source='en', target='es').translate(en_overview)
            except:
                res['overview'] = en_overview # Si falla el traductor, dejamos la inglesa
        else:
            res['overview'] = "Sinopsis no disponible en este momento."

    # --- TRADUCCIÓN DE GÉNEROS ---
    # Traducimos géneros específicos de series (TV) que TMDB suele dejar en inglés
    genre_map = {
        'Action & Adventure': 'Acción y Aventura',
        'Kids': 'Infantil',
        'News': 'Noticias',
        'Sci-Fi & Fantasy': 'Ciencia Ficción y Fantasía',
        'War & Politics': 'Guerra y Política'
    }

    if 'genres' in res:
        for g in res['genres']:
            # Si el género está en nuestro mapa, lo traducimos
            if g['name'] in genre_map:
                g['name'] = genre_map[g['name']]

    # Mapeo de estados
    status_map = {
        'Ended':'Finalizada','Returning Series':'En emisión',
        'Planned':'Planeada','Canceled':'Cancelada',
        'In Production':'En producción','Released':'Estrenada'
    }
    res['status'] = status_map.get(res.get('status'), res.get('status'))

    # --- LÓGICA DE PROGRAMA (Reality, Talk, Docu, News) ---
    res['media_subtype'] = 'Serie'
    if media_type == 'tv' and 'genres' in res:
        nombres_programa = ['Reality', 'Talk Show', 'Documental', 'Noticias']
        if any(g['name'] in nombres_programa for g in res['genres']):
            res['media_subtype'] = 'Programa'

    # --- LÓGICA DE BANDERA ROBUSTA ---
    paises_prod = [c['iso_3166_1'].upper() for c in res.get('production_countries', [])]
    paises_origin = [p.upper() for p in res.get('origin_country', [])]
    todos_paises = list(set(paises_prod + paises_origin))
    idioma_orig = res.get('original_language', '').lower()

    mapa_banderas = {'KR':'🇰🇷','JP':'🇯🇵','CN':'🇨🇳','TW':'🇹🇼','HK':'🇭🇰','TH':'🇹🇭','VN':'🇻🇳','IN':'🇮🇳','PH':'🇵🇭','ID':'🇮🇩','MY':'🇲🇾'}
    codigo_final = None
    bandera_final = None

    # 1. SERIES: Priorizar origin_country
    if media_type == 'tv' and paises_origin:
        lang_to_c = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID','ms':'MY'}
        c_sug = lang_to_c.get(idioma_orig)
        codigo_final = c_sug if (c_sug and c_sug in paises_origin) else paises_origin[0]
        bandera_final = mapa_banderas.get(codigo_final)

    # 2. PELÍCULAS o fallback: idioma_orig
    if not bandera_final:
        lang_map = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','id':'ID','tl':'PH','fil':'PH','ms':'MY'}
        if idioma_orig in ['zh', 'cn', 'yue']:
            if 'HK' in todos_paises: codigo_final = 'HK'
            elif 'TW' in todos_paises: codigo_final = 'TW'
            else: codigo_final = 'CN'
        elif idioma_orig in lang_map:
            codigo_final = lang_map[idioma_orig]
        if codigo_final: bandera_final = mapa_banderas.get(codigo_final)

    # 3. Fallback: Priority list
    if not bandera_final:
        for code in ['KR', 'JP', 'HK', 'TW', 'CN', 'TH', 'VN', 'IN', 'PH', 'ID', 'MY']:
            if code in todos_paises:
                codigo_final = code
                bandera_final = mapa_banderas.get(code)
                break
    
    res['flag'] = bandera_final or '🌏'

    # --- NOMBRE DEL IDIOMA ---
    lang_names = {
        'ko': 'Coreano', 'ja': 'Japonés', 'zh': 'Chino', 'cn': 'Chino', 'yue': 'Cantonés',
        'th': 'Tailandés', 'vi': 'Vietnamita', 'hi': 'Hindi', 'tl': 'Filipino', 
        'fil': 'Filipino', 'id': 'Indonesio', 'ms': 'Malayo', 'en': 'Inglés',
        'ta': 'Tamil', 'te': 'Telugu'
    }
    res['original_language_name'] = lang_names.get(idioma_orig, idioma_orig.upper())

    # --- LÓGICA DE PROVEEDORES DE STREAMING ---
    user_region = None
    if current_user.is_authenticated:
        user_region = current_user.region
    
    # Si no hay región, podemos intentar detectarla o dejarla vacía para el aviso
    watch_providers = []
    has_region = True if user_region else False
    
    if has_region:
        wp_url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers?api_key={api_key}"
        try:
            wp_res = requests.get(wp_url).json()
            results = wp_res.get('results', {})
            region_data = results.get(user_region, {})
            # Buscamos en suscripción plana (flatrate)
            flatrate = region_data.get('flatrate', [])
            
            # IDs de los canales "Elite" que tenemos en el explorador
            elite_ids = [8, 337, 283, 119, 9, 149, 115, 1899, 384, 350, 344, 1773, 188]
            for p in flatrate:
                pid = p['provider_id']
                if pid in elite_ids:
                    # Normalización simple para agrupar (HBO/Max, Amazon, Movistar)
                    if pid == 9: pid = 119
                    if pid == 115: pid = 149
                    if pid == 1899: pid = 384
                    
                    if pid not in [wp['id'] for wp in watch_providers]:
                        watch_providers.append({
                            'id': pid,
                            'name': p['provider_name']
                        })
        except Exception as e:
            print(f"Error fetching providers: {e}")
            pass

    # Lógica de favoritos y status (lo que ya tenías)
    current_status = None
    is_favorite = False
    if current_user.is_authenticated:
        item = CollectionItem.query.filter_by(user_id=current_user.id, media_id=media_id, media_type=media_type).first()
        if item:
            current_status = item.status
            is_favorite = item.is_favorite

    return render_template(
        'media_detail.html',
        media=res,
        is_favorite=is_favorite,
        current_status=current_status,
        watch_providers=watch_providers,
        has_region=has_region,
        user_region=user_region
    )


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
    watch_region = request.args.get('watch_region', 'ES') # España por defecto
    keywords = request.args.get('keywords', '')

    asia_countries = {'KR': 'Corea del Sur', 'JP': 'Japón', 'CN': 'China', 'TW': 'Taiwán', 'HK': 'Hong Kong', 'TH': 'Tailandia', 'VN': 'Vietnam', 'IN': 'India', 'PH': 'Filipinas', 'ID': 'Indonesia', 'MY': 'Malasia'}
    
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
                           available_countries=GLOBAL_COUNTRIES_LIST)

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
    idiomas_asiaticos = ['ko', 'ja', 'zh', 'cn', 'yue', 'th', 'vi', 'hi', 'tl', 'fil', 'id', 'ms']
    # Filtro de programas: Reality(10764), Docu(99), Noticias(10763), Talk(10767)
    genres_programas_or = "10764|99|10763|10767"
    genres_programas_and = "10764,99,10763,10767"

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
            else: url += "&with_origin_country=KR|JP|CN|TW|HK|TH|VN|IN|PH|ID|MY"

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
                items_processed_in_this_page += 1
                
                # 1. Lógica de salto (PRECISIÓN: No repetir ni saltar series)
                if current_api_page == api_start_page and to_skip > 0:
                    to_skip -= 1
                    continue

                # --- SISTEMA DE FILTRADO MANUAL (Garantiza Pureza Total) ---
                genre_ids = item.get('genre_ids', [])
                # Reality(10764), Docu(99), Noticias(10763), Talk(10767)
                ids_programas = [10764, 99, 10763, 10767]
                es_programa = any(gid in ids_programas for gid in genre_ids)

                if media_type == 'tv' and es_programa: continue # Fuera intrusos en Series
                if media_type == 'show' and not es_programa: continue # Fuera intrusos en Programas

                idioma_orig = item.get('original_language', '').lower()
                if idioma_orig not in idiomas_asiaticos: continue

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

                # --- LÓGICA DE BANDERA ROBUSTA ---
                paises_origin = [p.upper() for p in item.get('origin_country', [])]
                paises_prod = [c['iso_3166_1'].upper() for c in det_res.get('production_countries', [])]
                todos_paises = list(set(paises_origin + paises_prod))
                idioma_orig = item.get('original_language', '').lower()

                mapa_banderas = {'KR':'🇰🇷','JP':'🇯🇵','CN':'🇨🇳','TW':'🇹🇼','HK':'🇭🇰','TH':'🇹🇭','VN':'🇻🇳','IN':'🇮🇳','PH':'🇵🇭','ID':'🇮🇩','MY':'🇲🇾'}
                codigo_final = None
                bandera_final = None

                # 1. SERIES: Priorizar origin_country
                if target_type == 'tv' and paises_origin:
                    lang_to_c = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','tl':'PH','id':'ID','ms':'MY'}
                    c_sug = lang_to_c.get(idioma_orig)
                    codigo_final = c_sug if (c_sug and c_sug in paises_origin) else paises_origin[0]
                    bandera_final = mapa_banderas.get(codigo_final)

                # 2. PELÍCULAS o fallback: idioma_orig
                if not bandera_final:
                    lang_map = {'ko':'KR','ja':'JP','th':'TH','vi':'VN','hi':'IN','id':'ID','tl':'PH','fil':'PH','ms':'MY'}
                    if idioma_orig in ['zh', 'cn', 'yue']:
                        if 'HK' in todos_paises: codigo_final = 'HK'
                        elif 'TW' in todos_paises: codigo_final = 'TW'
                        else: codigo_final = 'CN'
                    elif idioma_orig in lang_map:
                        codigo_final = lang_map[idioma_orig]
                    if codigo_final: bandera_final = mapa_banderas.get(codigo_final)

                # 3. Fallback: Priority list
                if not bandera_final:
                    for code in ['KR', 'JP', 'HK', 'TW', 'CN', 'TH', 'VN', 'IN', 'PH', 'ID', 'MY']:
                        if code in todos_paises:
                            codigo_final = code
                            bandera_final = mapa_banderas.get(code)
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
                if title_es == orig_title or not title_es:
                    eng_title = det_res.get('name') if target_type == 'tv' else det_res.get('title')
                    item['display_title'] = eng_title if eng_title else orig_title
                else: 
                    item['display_title'] = title_es

                item['original_title_h6'] = orig_title
                
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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)