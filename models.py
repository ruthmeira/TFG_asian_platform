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
    bio = db.Column(db.String(500), nullable=True) # Biografía personalizada
    collections = db.relationship('CollectionItem', backref='user', lazy=True)

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

    # Relación para acceder al usuario autor de la reseña
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    # Relación para votos
    votes_objs = db.relationship('ReviewVote', backref='review', cascade='all, delete-orphan', lazy=True)

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