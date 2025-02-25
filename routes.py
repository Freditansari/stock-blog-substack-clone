from flask import request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, logout_user, login_user
from app import app, db, bcrypt
from models import User, Subscriber, Post, SiteVisit
from utils import track_page_visit
from werkzeug.utils import secure_filename
import os
import uuid

# ✅ Homepage
@app.route('/')
def index():
    return render_template('index.html')

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
        youtube_url = request.form.get('youtube_url')  # ✅ Get YouTube link
        file = request.files.get('media')  # ✅ Get uploaded file

        media_url = None
        if file and allowed_file(file.filename):
            file_extension = file.filename.rsplit('.', 1)[1].lower()  # ✅ Extract file extension
            random_filename = f"{uuid.uuid4().hex}.{file_extension}"  # ✅ Generate random filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], random_filename)
            file.save(file_path)
            media_url = f'/static/uploads/{random_filename}'  # ✅ Store media URL

        # ✅ Create a new post with the uploaded file or YouTube link
        new_post = Post(
            title=title,
            content=content,
            youtube_url=youtube_url,
            media_url=media_url,
            user_id=current_user.id
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
def view_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    user = post.user  # ✅ Assign user from the post
    return render_template('view_post.html', post=post, user=user)

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

