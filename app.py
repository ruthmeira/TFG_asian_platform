from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from deep_translator import GoogleTranslator # Añade esto arriba con los otros imports
from dotenv import load_dotenv
from models import db, User, CollectionItem
from datetime import datetime
import requests
import os
import time

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/asian_platform'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret_key'

db.init_app(app)

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
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['email']  # email o username
        password = request.form['password']
        user = User.query.filter_by(email=identifier).first() or User.query.filter_by(username=identifier).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

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


@app.route('/')
def home():
    api_key = os.getenv("TMDB_API_KEY")
    window = request.args.get('window', 'day')
    if window not in ['day', 'week']: 
        window = 'day'

    current_time = time.time()
    cache = api_cache[window]
    seconds_passed = current_time - cache['last_updated']
    
    # Si el cache está vacío o expiró, cargamos las 3 categorías
    if not cache.get('series') or seconds_passed > cache['expire']:
        print(f"🔄 Sincronizando {window} con TMDB...")
        
        cache['series'] = get_top_20(api_key, 'tv', window)
        cache['movies'] = get_top_20(api_key, 'movie', window)
        cache['shows'] = get_top_20(api_key, 'show', window) # <--- EL NUEVO TOP
        
        cache['last_updated'] = current_time
    else:
        faltan = int((cache['expire'] - seconds_passed) / 60)
        print(f"⚡ Usando caché para {window}. Expira en {faltan} minutos.")

    return render_template('index.html', 
                           series=cache['series'], 
                           movies=cache['movies'], 
                           shows=cache.get('shows', []), # <--- ENVIADO AL HTML
                           active_window=window)

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
        flash("Perfil actualizado correctamente.")
        return redirect(url_for('profile'))
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
        ).all()

    favorites = CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True).all()
    return render_template('collections.html', collections=user_collections, favorites=favorites)



@app.route('/collections/<status>')
@login_required
def view_collection(status):
    # 'favoritos' es un caso especial porque no es un 'status' en la DB, sino un booleano
    if status.lower() == 'favoritos':
        items = CollectionItem.query.filter_by(user_id=current_user.id, is_favorite=True).all()
        display_name = "Mis Favoritos"
    else:
        items = CollectionItem.query.filter_by(user_id=current_user.id, status=status).all()
        display_name = status

    return render_template('collection_view.html', items=items, display_name=display_name)


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
            is_favorite=True
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
            status=new_status
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

    # Mapeo de estados (lo que ya tenías)
    status_map = {
        'Ended':'Finalizada','Returning Series':'En emisión',
        'Planned':'Planeada','Canceled':'Cancelada',
        'In Production':'En producción','Released':'Estrenada'
    }
    res['status'] = status_map.get(res.get('status'), res.get('status'))

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
    api_key = os.getenv("TMDB_API_KEY")
    
    # Capturamos el tipo original (movie, tv, o el nuevo 'show' para programas)
    media_type = request.args.get('type', 'tv') 
    year = request.args.get('year', '')
    country_code = request.args.get('lang', '') 
    genre_id = request.args.get('genre', '')
    page_to_start = request.args.get('page', 1, type=int) 
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Determinamos el target para la API de TMDB
    # Si es 'show', la API sigue siendo 'tv' pero con filtros de género
    target_type = 'movie' if media_type == 'movie' else 'tv'
    
    final_items = []
    current_api_page = page_to_start
    max_pages_to_scan = current_api_page + 10 

    idiomas_asiaticos = ['ko', 'ja', 'zh', 'cn', 'yue', 'th', 'vi', 'hi', 'tl', 'fil', 'id', 'ms']

    # IDs de Géneros de No-Ficción: Reality (10764), Documental (99), News (10763), Talk (10767)
    genres_no_ficcion = "10764|99|10763|10767"

    while len(final_items) < 20 and current_api_page < max_pages_to_scan:
        url = f"https://api.themoviedb.org/3/discover/{target_type}?api_key={api_key}&language=es-ES&page={current_api_page}&sort_by=popularity.desc"
        
        if target_type == 'tv':
            url += f"&first_air_date.lte={today}"
            # --- LÓGICA DE CATEGORÍAS ---
            if media_type == 'show':
                # Solo programas: incluimos los géneros de no-ficción
                url += f"&with_genres={genres_no_ficcion}"
            else:
                # Series normales: excluimos los géneros de no-ficción
                url += f"&without_genres={genres_no_ficcion}"
        else:
            url += f"&primary_release_date.lte={today}"

        if country_code:
            url += f"&with_origin_country={country_code}"
        else:
            url += "&with_origin_country=KR|JP|CN|TW|HK|TH|VN|IN|PH|ID|MY"

        if year:
            year_param = 'first_air_date_year' if target_type == 'tv' else 'primary_release_year'
            url += f"&{year_param}={year}"

        if genre_id:
            # TMDB tiene IDs distintos para algunos géneros en TV vs Movie
            actual_genre = genre_id
            if target_type == 'tv':
                if genre_id == '28': actual_genre = '10759' # Action & Adventure
                elif genre_id == '10749': actual_genre = '10766' # Romance -> Soap (donde están los dramas)
                elif genre_id == '14' or genre_id == '878': actual_genre = '10765' # Sci-Fi & Fantasy
            
            url += f"&with_genres={actual_genre}"

        try:
            res = requests.get(url).json()
            results = res.get('results', [])
        except: break
        
        if not results: break 

        for item in results:
            idioma_orig = item.get('original_language', '').lower()

            if idioma_orig not in idiomas_asiaticos:
                continue

            item_id = item.get('id')
            item['media_type_fixed'] = target_type
            
            # Ajuste de etiqueta según tu nueva lógica
            if target_type == 'movie':
                item['tipo_label'] = 'Película'
            elif media_type == 'show':
                item['tipo_label'] = 'Programa'
            else:
                item['tipo_label'] = 'Serie'
            
            det_url = f"https://api.themoviedb.org/3/{target_type}/{item_id}?api_key={api_key}&language=en-US"
            try:
                det_res = requests.get(det_url).json()
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
                elif idioma_orig in ['zh', 'cn', 'yue']:
                    bandera_final = '🇭🇰' if idioma_orig == 'yue' else '🇨🇳'
                elif idioma_orig == 'th': bandera_final = '🇹🇭'
                else: bandera_final = '🌏'

            if country_code and country_code.upper() == 'HK' and bandera_final == '🇨🇳':
                continue
            
            item['flag'] = bandera_final

            title_es = item.get('name') if target_type == 'tv' else item.get('title')
            orig_title = item.get('original_name') if target_type == 'tv' else item.get('original_title')
            if title_es == orig_title or not title_es:
                eng_title = det_res.get('name') if target_type == 'tv' else det_res.get('title')
                item['display_title'] = eng_title if eng_title else orig_title
            else:
                item['display_title'] = title_es

            item['original_title_h6'] = orig_title
            final_items.append(item)

            if len(final_items) >= 20: break
            
        current_api_page += 1

    if is_ajax:
        return jsonify({
            'html': render_template('explore_items.html', items=final_items),
            'next_api_page': current_api_page
        })

    asia_countries = {
        'KR': 'Corea del Sur', 'JP': 'Japón', 'CN': 'China', 'TW': 'Taiwán', 
        'HK': 'Hong Kong', 'TH': 'Tailandia', 'VN': 'Vietnam', 'IN': 'India', 
        'PH': 'Filipinas', 'ID': 'Indonesia', 'MY': 'Malasia'
    }

    # Géneros comunes (IDs unificados o mayoritarios)
    common_genres = {
        '18': 'Drama', '35': 'Comedia', '10749': 'Romance', '28': 'Acción', 
        '80': 'Crimen', '9648': 'Misterio', '14': 'Fantasía', '16': 'Animación', 
        '10751': 'Familia', '27': 'Terror', '53': 'Thriller'
    }

    return render_template('explore.html', items=final_items, media_type=media_type, 
                           current_year=year, current_lang=country_code, current_genre=genre_id,
                           asia_langs=asia_countries, genres=common_genres, next_api_page=current_api_page)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)