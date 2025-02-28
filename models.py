from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date, timedelta
import re
import random, string
from sqlalchemy.sql import func

# ✅ User Loader (Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ✅ User Model
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    is_premium = db.Column(db.Boolean, default=False)  # ✅ Premium Status
    premium_expiry = db.Column(db.DateTime, nullable=True)  # ✅ Expiry Date
    
    is_admin = db.Column(db.Boolean, default=False)  # ✅ Admin Privilege
    
    # ✅ Tracking Referral Earnings
    premium_subscribers_count = db.Column(db.Integer, default=0)  # ✅ How many premium users this creator referred
    total_earnings = db.Column(db.Float, default=0.0)  # ✅ Creator's total earnings from referrals

    # Relationships
    posts = db.relationship("Post", back_populates="user", cascade="all, delete-orphan")
    subscribers = db.relationship("Subscriber", back_populates="blogger", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="creator", cascade="all, delete-orphan")

    def is_premium_active(self):
        """Check if user has an active premium subscription."""
        return self.is_premium and (self.premium_expiry is None or self.premium_expiry > datetime.utcnow())

    def grant_premium(self, days=365, referrer=None):
        """
        Grant premium access for a specified number of days (default: 1 year).
        If a referrer is provided, increase their earnings & referral count.
        """
        if self.premium_expiry is None or self.premium_expiry < datetime.utcnow():
            self.premium_expiry = datetime.utcnow() + timedelta(days=days)
        else:
            self.premium_expiry += timedelta(days=days)
        self.is_premium = True

        # ✅ If referred by a creator, update their earnings
        if referrer:
            referrer.premium_subscribers_count += 1
            referrer.total_earnings += 10  # Example: Pay $10 per referral

        db.session.commit()



# ✅ Subscriber Model
class Subscriber(db.Model):
    __tablename__ = "subscriber"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)  # ✅ Allow multiple subscriptions
    blogger_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # ✅ Blogger Subscription
    timestamp = db.Column(db.DateTime, default=func.now())  # ✅ Subscription Timestamp

    blogger = db.relationship("User", back_populates="subscribers")  # ✅ Relation to User


# ✅ Generate SEO-Friendly Slugs
def generate_slug(title):
    return re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')


# ✅ Post Model
class Post(db.Model):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.current_timestamp())
    
    youtube_url = db.Column(db.String(255), nullable=True)  # ✅ Support for YouTube Embeds
    media_url = db.Column(db.String(255), nullable=True)  # ✅ Support for Uploaded Files
    
    is_premium = db.Column(db.Boolean, default=False)  # ✅ Premium Post
    
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="posts")
    views = db.relationship("PostView", back_populates="post", cascade="all, delete-orphan")

    def __init__(self, title, content, user_id, youtube_url=None, media_url=None, is_premium=False):
        self.title = title
        self.slug = generate_slug(title) + "-" + datetime.utcnow().strftime("%Y-%m-%d")  # ✅ Generate Unique Slug
        self.content = content
        self.user_id = user_id
        self.youtube_url = youtube_url
        self.media_url = media_url
        self.is_premium = is_premium


# ✅ Post View Tracking Model
class PostView(db.Model):
    __tablename__ = "post_view"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    visit_date = db.Column(db.Date, default=date.today)  # ✅ Tracks Unique Visits Per Day
    ip_address = db.Column(db.String(100), nullable=True)  # ✅ Track Visitor's IP
    referrer = db.Column(db.String(255), nullable=True)  # ✅ Store Referrer Info

    # Relationships
    post = db.relationship("Post", back_populates="views")


# ✅ Site Visit Model (Tracks General Page Visits)
class SiteVisit(db.Model):
    __tablename__ = "site_visit"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)  # ✅ Tracks Any Visited Page
    referrer = db.Column(db.String(255), nullable=True)  # ✅ Tracks Referrer
    visitor_count = db.Column(db.Integer, default=1)  # ✅ Count Total Visits
    last_visited = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())  # ✅ Last Visit Time


# ✅ Access Code Model (For One-Time Access)
class AccessCode(db.Model):
    __tablename__ = "access_code"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)  # ✅ Unique Access Code
    days_valid = db.Column(db.Integer, nullable=False)  # ✅ Validity Period (In Days)
    is_used = db.Column(db.Boolean, default=False)  # ✅ Has the Code Been Used?
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Created Timestamp

    def __init__(self, days_valid):
        self.code = self.generate_code()
        self.days_valid = days_valid

    @staticmethod
    def generate_code():
        """Generate a random 10-character access code."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    def mark_used(self):
        """Mark this access code as used."""
        self.is_used = True
        
class CreatorPayment(db.Model):
    __tablename__ = "creator_payment"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', back_populates='payments')
