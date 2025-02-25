from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date
import re
from sqlalchemy.sql import func
import uuid



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=False, nullable=False)  # Allow same email for multiple bloggers
    blogger_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the blogger
    timestamp = db.Column(db.DateTime, default=db.func.now())  # Store subscription time

    blogger = db.relationship('User', backref=db.backref('subscribers', lazy=True))  # Relationship to User
    
def generate_slug(title):
    """Generate an SEO-friendly slug from the post title."""
    return re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    youtube_url = db.Column(db.String(255), nullable=True)  # ✅ Added YouTube URL support
    media_url = db.Column(db.String(255), nullable=True)  # ✅ Added media file support
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    
    def __init__(self, title, content, user_id, youtube_url=None, media_url=None):
        self.title = title
        self.slug = generate_slug(title) + "-" + datetime.utcnow().strftime("%Y-%m-%d")  # ✅ Generate slug
        self.content = content
        self.user_id = user_id
        self.youtube_url = youtube_url
        self.media_url = media_url


class PostView(db.Model):
    """Model to track daily unique visits and referrer sources."""
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    visit_date = db.Column(db.Date, default=date.today)  # Track visits per day
    ip_address = db.Column(db.String(100), nullable=True)  # Unique visitor tracking
    referrer = db.Column(db.String(255), nullable=True)  # Store the referring URL

    post = db.relationship('Post', backref=db.backref('views', lazy=True))
    


class SiteVisit(db.Model):
    """Model to track visits to any URL on the website."""
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False, unique=False)  # Any visited page URL
    referrer = db.Column(db.String(255), nullable=True)  # Referrer (if any)
    visitor_count = db.Column(db.Integer, default=1)  # Total visits
    last_visited = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())  # Last visit timestamp
