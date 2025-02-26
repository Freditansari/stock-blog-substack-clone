from flask import request, render_template, redirect, url_for, flash, jsonify, \
    Response, request, stream_with_context, session, request
from flask_login import login_required, current_user, logout_user, login_user
from app import app, db, bcrypt
from models import User, Subscriber, Post, SiteVisit, AccessCode
from utils import track_page_visit, require_human_verification
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime, timedelta
import random
import requests

@app.route('/video/<filename>')
def stream_video(filename):
    """Serve videos efficiently using a non-blocking generator."""
    video_path = os.path.join(app.static_folder, 'uploads', filename)

    if not os.path.exists(video_path):
        return "Video Not Found", 404

    def generate():
        """Stream the video file in chunks to prevent blocking the Flask app."""
        chunk_size = 1024 * 1024  # 1MB per chunk
        with open(video_path, "rb") as video:
            while chunk := video.read(chunk_size):
                yield chunk

    return Response(stream_with_context(generate()), mimetype="video/mp4")

# ✅ Homepage
@app.route('/')
def index():
    # ✅ Check if user is already verified
    if session.get("is_human"):
        return render_template("index.html")  # Allow access

    # ✅ 30% Chance to Show CAPTCHA
    if random.random() < 0.3:
        return redirect(url_for("captcha"))

    return render_template("index.html")

@app.route('/captcha', methods=['GET', 'POST'])
def captcha():
    if request.method == "POST":
        hcaptcha_response = request.form.get("h-captcha-response")
        if not hcaptcha_response:
            flash("❌ Please complete the CAPTCHA!", "danger")
            return redirect(url_for("captcha"))

        # ✅ Verify hCaptcha with the hCaptcha API
        verify_url = "https://api.hcaptcha.com/siteverify"
        payload = {
            "secret": app.config["HCAPTCHA_SECRET_KEY"],  # ✅ Correct way to access config
            "response": hcaptcha_response,
        }
        response = requests.post(verify_url, data=payload)
        result = response.json()

        if result.get("success"):
            session["is_human"] = True  # ✅ Mark user as verified
            flash("✅ Verification successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("❌ CAPTCHA verification failed. Try again.", "danger")
            return redirect(url_for("captcha"))

    return render_template("captcha.html", hcaptcha_site_key=app.config["HCAPTCHA_SITE_KEY"])


# ✅ Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('user_home', username=user.username))
        else:
            flash('Invalid login credentials.', 'danger')

    return render_template('login.html')

# ✅ Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ✅ User Profile Route (Tracks Profile Visits)
@app.route('/<username>')
@require_human_verification
@track_page_visit
def user_home(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(db.text("strftime('%Y-%m-%d %H:%M:%S', timestamp) DESC")).all()
    return render_template('user_home.html', user=user, posts=posts)

@app.route('/subscribe/<username>', methods=['POST'])
def subscribe(username):
    blogger = User.query.filter_by(username=username).first_or_404()  # Find the blogger
    email = request.form['email']

    # Check if already subscribed to this blogger
    existing_subscription = Subscriber.query.filter_by(email=email, blogger_id=blogger.id).first()
    if existing_subscription:
        flash('You are already subscribed to this blogger!', 'warning')
        return redirect(request.referrer or url_for('user_home', username=blogger.username))

    # Create a new subscription
    new_subscriber = Subscriber(email=email, blogger_id=blogger.id)
    db.session.add(new_subscriber)
    db.session.commit()
    
    flash(f'Subscribed successfully to {blogger.username}!', 'success')
    return redirect(request.referrer or url_for('user_home', username=blogger.username))


# ✅ Create New Post
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        youtube_url = request.form.get('youtube_url')
        file = request.files.get('media')
        is_premium = 'is_premium' in request.form  # ✅ Check if premium

        # ✅ Handle File Upload
        media_url = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            media_url = f'/static/uploads/{filename}'

        # ✅ Save Post
        new_post = Post(
            title=title,
            content=content,
            youtube_url=youtube_url,
            media_url=media_url,
            user_id=current_user.id,
            is_premium=is_premium  # ✅ Save premium flag
        )

        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for('user_home', username=current_user.username))

    return render_template('create_post.html')


# ✅ Manage Posts (Edit & Delete Access)
@app.route('/manage-posts')
@login_required
def manage_posts():
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).all()
    return render_template('manage_posts.html', posts=posts)

# ✅ Edit Post
@app.route('/edit-post/<slug>', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    if post.user_id != current_user.id:
        flash("You are not authorized to edit this post.", "danger")
        return redirect(url_for('manage_posts'))

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.image_url = request.form.get('image_url')
        post.video_url = request.form.get('video_url')
        db.session.commit()
        flash("Post updated successfully!", "success")
        return redirect(url_for('manage_posts'))

    return render_template('edit_post.html', post=post)

# ✅ Delete Post
@app.route('/delete-post/<slug>', methods=['POST'])
@login_required
def delete_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    if post.user_id != current_user.id:
        flash("You are not authorized to delete this post.", "danger")
        return redirect(url_for('manage_posts'))

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for('manage_posts'))

# ✅ View Blog Post (Tracks Blog Visits)
@app.route('/post/<slug>')
@track_page_visit
@require_human_verification
def view_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()

    # ✅ If post is premium, check user subscription
    if post.is_premium and (not current_user.is_premium or current_user.premium_expiry < datetime.utcnow()):
        flash("🔒 This content is only available for premium members!", "danger")
        return redirect(url_for('subscribe_page'))

    return render_template('view_post.html', post=post)


# ✅ Site Analytics API (Most Visited Pages)
@app.route('/site-analytics')
def site_analytics():
    top_visited = db.session.query(SiteVisit.url, db.func.sum(SiteVisit.visitor_count))\
        .group_by(SiteVisit.url)\
        .order_by(db.func.sum(SiteVisit.visitor_count).desc())\
        .limit(10).all()

    return jsonify([
        {"url": site[0], "visits": site[1]}
        for site in top_visited
    ])
    
@app.route('/manage-subscribers')
@login_required
def manage_subscribers():
    subscribers = Subscriber.query.filter_by(blogger_id=current_user.id).all()
    return render_template('manage_subscribers.html', subscribers=subscribers)

@app.route('/subscribe')
@login_required
def subscribe_page():
    return render_template('subscribe.html')

@app.route('/payment-success')
@login_required
def payment_success():
    current_user.is_premium = True
    current_user.premium_expiry = datetime.utcnow() + timedelta(days=365)  # ✅ 1-year premium
    db.session.commit()
    flash(f"You are now a premium subscriber until {current_user.premium_expiry.strftime('%B %d, %Y')}", "success")
    return redirect(url_for('user_home', username=current_user.username))

@app.route('/generate-code', methods=['POST'])
@login_required
def generate_code():
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for('user_home', username=current_user.username))

    days_valid = int(request.form['days_valid'])  # ⏳ How many days the code is valid for
    new_code = AccessCode(days_valid=days_valid)

    db.session.add(new_code)
    db.session.commit()

    flash(f"✅ Access code '{new_code.code}' created for {days_valid} days!", "success")
    return redirect(url_for('manage_access_codes'))

@app.route('/apply-access-code', methods=['POST'])
@login_required
def apply_access_code():
    code = request.form['access_code'].strip().upper()
    access_code = AccessCode.query.filter_by(code=code, is_used=False).first()

    if access_code:
        # ✅ Activate premium access
        current_user.is_premium = True
        current_user.premium_expiry = datetime.utcnow() + timedelta(days=access_code.days_valid)
        access_code.is_used = True  # ✅ Mark as used
        db.session.commit()

        flash(f"Access code applied! Premium valid until {current_user.premium_expiry.strftime('%B %d, %Y')}.", "success")
        return redirect(url_for('user_home', username=current_user.username))

    flash("Invalid or already used access code.", "danger")
    return redirect(url_for('subscribe_page'))


@app.route('/paypal-success', methods=['POST'])
@login_required
def paypal_success():
    data = json.loads(request.data)

    # ✅ Verify payment (for real apps, check PayPal API)
    if data.get("orderID"):
        current_user.is_premium = True
        current_user.premium_expiry = datetime.utcnow() + timedelta(days=365)  # ✅ 1 Year Premium
        db.session.commit()

        return jsonify({"success": True}), 200

    return jsonify({"success": False}), 400



@app.route('/manage-access-codes')
@login_required
def manage_access_codes():
    if not current_user.is_admin:
        flash("Unauthorized", "danger")
        return redirect(url_for('user_home', username=current_user.username))

    access_codes = AccessCode.query.order_by(AccessCode.created_at.desc()).all()
    return render_template('manage_access_codes.html', access_codes=access_codes)



