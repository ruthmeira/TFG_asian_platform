from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255))
    region = db.Column(db.String(10), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    collections = db.relationship('CollectionItem', backref='user', cascade='all, delete-orphan', lazy=True)
    reports_made = db.relationship('ReviewReport', backref='reporter', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class CollectionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    media_id = db.Column(db.Integer)
    media_type = db.Column(db.String(10))
    title = db.Column(db.String(255))
    original_title = db.Column(db.String(255))
    poster_path = db.Column(db.String(255))
    vote_average = db.Column(db.Float)
    flag = db.Column(db.String(50))
    status = db.Column(db.String(20))
    is_favorite = db.Column(db.Boolean, default=False)
    media_subtype = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, nullable=False)
    media_type = db.Column(db.String(10), nullable=False)
    rating = db.Column(db.Float)
    comment = db.Column(db.Text)
    status = db.Column(db.String(20), default='approved')
    report_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    media_title = db.Column(db.String(255))



    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    votes_objs = db.relationship('ReviewVote', backref='review', cascade='all, delete-orphan', lazy=True)
    reports = db.relationship('ReviewReport', backref='review_obj', cascade='all, delete-orphan', lazy=True)

class ReviewVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='unique_user_review_vote'),)

class ReviewReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'review_id', name='unique_user_review_report'),)

class ModerationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    review_id = db.Column(db.Integer, nullable=True)
    review_content_snapshot = db.Column(db.Text, nullable=True)
    action = db.Column(db.String(50))
    reason = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    author = db.relationship('User', foreign_keys=[author_id], backref=db.backref('moderation_history', lazy=True))
    reporter_user = db.relationship('User', foreign_keys=[reporter_id], backref=db.backref('reports_history', lazy=True))

class MediaReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    media_title = db.Column(db.String(255), nullable=True)
    field_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='data_reports')

class GlobalEpisode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    media_id = db.Column(db.Integer, index=True)
    media_type = db.Column(db.String(10)) # 'movie' or 'tv'
    season_number = db.Column(db.Integer, nullable=True)
    episode_number = db.Column(db.Integer, nullable=True)
    air_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(255))
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (db.UniqueConstraint('media_id', 'media_type', 'season_number', 'episode_number', name='unique_global_episode'),)
