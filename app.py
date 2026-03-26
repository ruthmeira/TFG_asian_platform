from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
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

        if password != confirm_password:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("El email ya está registrado.")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("El nombre de usuario ya está en uso.")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        # Loguear con sesión persistente tras el registro
        login_user(new_user, remember=True)
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['email']  # email o username
        password = request.form['password']
        user = User.query.filter_by(email=identifier).first() or User.query.filter_by(username=identifier).first()
        if user and user.check_password(password):
            remember = True if request.form.get('remember') else False
            login_user(user, remember=remember)
            return redirect(url_for('home'))
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

# --- RUTAS GOOGLE OAUTH ---
@app.route('/login/google')
def login_google():
    # Detectamos la intención (si viene de register o de login normal)
    action = request.args.get('action', 'login')
    session['google_auth_action'] = action
    
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
        return redirect(url_for('home'))
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

                paises_origin = item.get('origin_country', [])
                paises_prod = [c['iso_3166_1'] for c in det_res.get('production_countries', [])]
                todos_los_paises = [p.upper() for p in (paises_origin + paises_prod)]

                if 'TW' in todos_los_paises: item['flag'] = '🇹🇼'
                elif 'HK' in todos_los_paises: item['flag'] = '🇭🇰'
                elif 'CN' in todos_los_paises: item['flag'] = '🇨🇳'
                elif 'KR' in todos_los_paises: item['flag'] = '🇰🇷'
                elif 'JP' in todos_los_paises: item['flag'] = '🇯🇵'

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
        print(f"✅ [BACKGROUND] Caché {window} actualizada correctamente.")
    except Exception as e:
        print(f"❌ [BACKGROUND] Error al refrescar caché {window}: {e}")

# --- INICIALIZACIÓN DEL PLANIFICADOR (SCHEDULER) ---
scheduler = BackgroundScheduler()

# Tarea para 'day' cada 4 horas
scheduler.add_job(func=refresh_trending_cache, trigger="interval", seconds=14400, args=['day'])
# Tarea para 'week' cada 24 horas
scheduler.add_job(func=refresh_trending_cache, trigger="interval", seconds=86400, args=['week'])

scheduler.start()

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

        if User.query.filter(User.id != current_user.id, User.username == username).first():
            flash("Ese nombre de usuario ya está en uso.")
            return redirect(url_for('edit_profile'))
        if User.query.filter(User.id != current_user.id, User.email == email).first():
            flash("Ese email ya está en uso.")
            return redirect(url_for('edit_profile'))

        current_user.username = username
        current_user.email = email
        if password: current_user.set_password(password)
        db.session.commit()
        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html')

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

    # --- LÓGICA DE BANDERA ---
    paises_prod = [c['iso_3166_1'].upper() for c in res.get('production_countries', [])]
    paises_origin = [p.upper() for p in res.get('origin_country', [])]
    todos_paises = list(set(paises_prod + paises_origin))
    idioma_orig = res.get('original_language', '').lower()

    bandera_final = None
    if 'KR' in todos_paises: bandera_final = '🇰🇷'
    elif 'JP' in todos_paises: bandera_final = '🇯🇵'
    elif 'HK' in todos_paises: bandera_final = '🇭🇰'
    elif 'TW' in todos_paises: bandera_final = '🇹🇼'
    elif 'CN' in todos_paises: bandera_final = '🇨🇳'
    elif 'TH' in todos_paises: bandera_final = '🇹🇭'
    elif 'VN' in todos_paises: bandera_final = '🇻🇳'
    elif 'IN' in todos_paises: bandera_final = '🇮🇳'
    elif 'PH' in todos_paises: bandera_final = '🇵🇭'

    if not bandera_final:
        if idioma_orig == 'ko': bandera_final = '🇰🇷'
        elif idioma_orig == 'ja': bandera_final = '🇯🇵'
        elif idioma_orig in ['zh', 'cn', 'yue']: bandera_final = '🇭🇰' if idioma_orig == 'yue' else '🇨🇳'
        elif idioma_orig == 'th': bandera_final = '🇹🇭'
        elif idioma_orig == 'vn': bandera_final = '🇻🇳'
        elif idioma_orig == 'hi': bandera_final = '🇮🇳'
        else: bandera_final = '🌏'
    
    res['flag'] = bandera_final

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
        current_status=current_status
    )


@app.route('/explore')
def explore():
    media_type = request.args.get('type', 'tv') 
    year = request.args.get('year', '')
    country_code = request.args.get('lang', '') 
    genre_id = request.args.get('genre', '')
    sort_by = request.args.get('sort_by', 'popularity.desc')
    status_id = request.args.get('status', '')

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
                           current_genre=genre_id, current_sort=sort_by, current_status_id=status_id,
                           asia_langs=asia_countries, genres_by_type=genres_by_type, 
                           sort_options=sort_options, status_options=status_options)

@app.route('/api/explore')
def api_explore():
    api_key = os.getenv("TMDB_API_KEY")
    media_type = request.args.get('type', 'tv') 
    year = request.args.get('year', '')
    country_code = request.args.get('lang', '') 
    genre_id = request.args.get('genre', '')
    sort_by = request.args.get('sort_by', 'popularity.desc')
    status_id = request.args.get('status', '')
    page = request.args.get('page', 1, type=int) 
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Determinamos el target para la API de TMDB
    # Si es 'show', la API sigue siendo 'tv' pero con filtros de género
    target_type = 'movie' if media_type == 'movie' else 'tv'
    
    final_items = []
    current_api_page = page
    max_pages_to_scan = current_api_page + 10 

    idiomas_asiaticos = ['ko', 'ja', 'zh', 'cn', 'yue', 'th', 'vi', 'hi', 'tl', 'fil', 'id', 'ms']

    # IDs de Géneros de No-Ficción: Reality (10764), Documental (99), News (10763), Talk (10767)
    genres_no_ficcion = "10764|99|10763|10767"

    while len(final_items) < 20 and current_api_page < max_pages_to_scan:
        url = f"https://api.themoviedb.org/3/discover/{target_type}?api_key={api_key}&language=es-ES&page={current_api_page}&sort_by={sort_by}"
        if 'vote_average' in sort_by: url += "&vote_count.gte=100"
        
        if target_type == 'tv':
            url += f"&first_air_date.lte={today}"
            if media_type == 'show': url += f"&with_genres={genres_no_ficcion}"
            else: url += f"&without_genres={genres_no_ficcion}"
        else:
            url += f"&primary_release_date.lte={today}"

        if country_code: url += f"&with_origin_country={country_code}"
        else: url += "&with_origin_country=KR|JP|CN|TW|HK|TH|VN|IN|PH|ID|MY"

        if year:
            year_param = 'first_air_date_year' if target_type == 'tv' else 'primary_release_year'
            url += f"&{year_param}={year}"

        if genre_id:
            actual_genre = genre_id
            if target_type == 'tv':
                if genre_id == '28': actual_genre = '10759'
                elif genre_id == '10749': actual_genre = '10766|10749|18' # Soap, Romance or Drama
                elif genre_id == '14' or genre_id == '878': actual_genre = '10765'
            url += f"&with_genres={actual_genre}"
        
        if status_id and target_type == 'tv': url += f"&with_status={status_id}"

        try:
            res = requests.get(url).json()
            results = res.get('results', [])
        except: break
        if not results: break 

        for item in results:
            idioma_orig = item.get('original_language', '').lower()
            if idioma_orig not in idiomas_asiaticos: continue

            item_id = item.get('id')
            item['media_type_fixed'] = target_type
            
            if target_type == 'movie': item['tipo_label'] = 'Película'
            elif media_type == 'show': item['tipo_label'] = 'Programa'
            else: item['tipo_label'] = 'Serie'
            
            det_url = f"https://api.themoviedb.org/3/{target_type}/{item_id}?api_key={api_key}&language=en-US"
            try: det_res = requests.get(det_url).json()
            except: det_res = {}

            paises_origin = [p.upper() for p in item.get('origin_country', [])]
            paises_prod = [c['iso_3166_1'].upper() for c in det_res.get('production_countries', [])]
            todos_paises = list(set(paises_origin + paises_prod))

            bandera_final = None
            if country_code and country_code.upper() in todos_paises:
                mapa_filtro = {'KR':'🇰🇷','JP':'🇯🇵','CN':'🇨🇳','TW':'🇹🇼','HK':'🇭🇰','TH':'🇹🇭','VN':'🇻🇳','IN':'🇮🇳','PH':'🇵🇭','ID':'🇮🇩','MY':'🇲🇾'}
                bandera_final = mapa_filtro.get(country_code.upper())

            if not bandera_final:
                if 'KR' in todos_paises: bandera_final = '🇰🇷'
                elif 'JP' in todos_paises: bandera_final = '🇯🇵'
                elif 'HK' in todos_paises: bandera_final = '🇭🇰'
                elif 'TW' in todos_paises: bandera_final = '🇹🇼'
                elif 'CN' in todos_paises: bandera_final = '🇨🇳'
                elif 'TH' in todos_paises: bandera_final = '🇹🇭'
                elif 'VN' in todos_paises: bandera_final = '🇻🇳'
                elif 'IN' in todos_paises: bandera_final = '🇮🇳'

            if not bandera_final:
                if idioma_orig == 'ko': bandera_final = '🇰🇷'
                elif idioma_orig == 'ja': bandera_final = '🇯🇵'
                elif idioma_orig in ['zh', 'cn', 'yue']: bandera_final = '🇭🇰' if idioma_orig == 'yue' else '🇨🇳'
                elif idioma_orig == 'th': bandera_final = '🇹🇭'
                else: bandera_final = '🌏'

            if country_code and country_code.upper() == 'HK' and bandera_final == '🇨🇳': continue
            
            item['flag'] = bandera_final
            title_es = item.get('name') if target_type == 'tv' else item.get('title')
            orig_title = item.get('original_name') if target_type == 'tv' else item.get('original_title')
            if title_es == orig_title or not title_es:
                eng_title = det_res.get('name') if target_type == 'tv' else det_res.get('title')
                item['display_title'] = eng_title if eng_title else orig_title
            else: item['display_title'] = title_es

            item['original_title_h6'] = orig_title
            final_items.append(item)
            if len(final_items) >= 20: break
        current_api_page += 1

    return jsonify({
        'html': render_template('explore_items.html', items=final_items),
        'next_api_page': current_api_page
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)