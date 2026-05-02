# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    region = db.Column(db.String(10), nullable=True) # Código ISO del país (ej: 'ES', 'MX')
    profile_image = db.Column(db.String(255), nullable=True) # Ruta de la foto
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False) # Protocolo de Baneo Shiori
    collections = db.relationship('CollectionItem', backref='user', cascade='all, delete-orphan', lazy=True)
    # Relación para ver todos los reportes hechos POR este usuario
    reports_made = db.relationship('ReviewReport', backref='reporter', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CollectionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    media_id = db.Column(db.Integer)
    media_type = db.Column(db.String(10)) # 'movie' o 'tv'
    # --- Datos de caché para evitar llamadas extra ---
    title = db.Column(db.String(255))
    original_title = db.Column(db.String(255))
    poster_path = db.Column(db.String(255))
    vote_average = db.Column(db.Float)
    flag = db.Column(db.String(50))
    # --------------------------
    status = db.Column(db.String(20))
    is_favorite = db.Column(db.Boolean, default=False)
    media_subtype = db.Column(db.String(20)) # 'Serie' o 'Programa'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con el calendario (Libreta de fechas)
    events = db.relationship('MediaEvent', backref='collection_item', cascade='all, delete-orphan', lazy=True)

class MediaEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    collection_item_id = db.Column(db.Integer, db.ForeignKey('collection_item.id'), nullable=False)
    event_type = db.Column(db.String(100)) # Ej: 'Estreno Original', 'Estreno España', 'T1 E5'
    event_date = db.Column(db.Date, nullable=False)
    season_number = db.Column(db.Integer, nullable=True)
    episode_number = db.Column(db.Integer, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, nullable=False)
    media_type = db.Column(db.String(10), nullable=False) # 'movie' o 'tv'
    rating = db.Column(db.Float) # Se cambió de Integer a Float para permitir 9.5, etc.
    comment = db.Column(db.Text) # Opinión larga
    status = db.Column(db.String(20), default='approved') # 'approved' por defecto ahora
    report_count = db.Column(db.Integer, default=0) # Contador de denuncias
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- Datos de caché para administración y listados rápidos ---
    media_title = db.Column(db.String(255))
    # -----------------------------------------------------------



    # Relación para acceder al usuario autor de la reseña
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    # Relación para votos
    votes_objs = db.relationship('ReviewVote', backref='review', cascade='all, delete-orphan', lazy=True)
    # Relación para reportes (para ver quién denunció)
    reports = db.relationship('ReviewReport', backref='review_obj', cascade='all, delete-orphan', lazy=True)

class ReviewVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False) # 'like' o 'dislike'
    
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='unique_user_review_vote'),)

class ReviewReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='unique_user_review_report'),)

class ModerationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Autor de la reseña
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Quien denunció (si hubo)
    review_id = db.Column(db.Integer, nullable=True) # ID de la reseña moderada
    review_content_snapshot = db.Column(db.Text, nullable=True) # MEMORIA FORENSE: Lo que escribió
    action = db.Column(db.String(50)) # 'deleted_review', 'dismissed_report'
    reason = db.Column(db.String(50)) # 'auto_filter', 'user_report'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones para estadísticas rápidas
    author = db.relationship('User', foreign_keys=[author_id], backref=db.backref('moderation_history', lazy=True))
    reporter_user = db.relationship('User', foreign_keys=[reporter_id], backref=db.backref('reports_history', lazy=True))

class MediaReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, nullable=False)
    media_type = db.Column(db.String(20), nullable=False) # 'movie' o 'tv'
    media_title = db.Column(db.String(255), nullable=True) # Nombre guardado para el admin
    field_type = db.Column(db.String(50), nullable=False) # La sección (Título, Sinopsis, etc.)
    description = db.Column(db.Text, nullable=False)      # El mensaje del usuario
    status = db.Column(db.String(20), default='pending') # 'pending', 'resolved', 'ignored'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='data_reports')