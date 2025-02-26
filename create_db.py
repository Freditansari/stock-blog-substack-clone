from app import app, db, bcrypt
from models import User, Post, AccessCode
import os
from datetime import datetime

# ✅ Ensure the app context is set
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully!")

    # ✅ Create an upload directory if it doesn't exist
    UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # ✅ Create Admin User
    admin_email = "admin@example.com"
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        hashed_password = bcrypt.generate_password_hash("adminpassword").decode('utf-8')
        admin_user = User(username="admin", email=admin_email, password_hash=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created!")
    else:
        print("ℹ️ Admin user already exists, skipping creation.")

    # ✅ Create a test user
    test_user = User.query.filter_by(username="johndoe").first()
    if not test_user:
        hashed_password = bcrypt.generate_password_hash("testpassword").decode('utf-8')
        test_user = User(username="johndoe", email="johndoe@example.com", password_hash=hashed_password)
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test user created!")
    else:
        print("ℹ️ User 'johndoe' already exists, skipping creation.")

    # ✅ Insert sample posts for test user
    if test_user:
        existing_posts = Post.query.filter_by(user_id=test_user.id).count()
        if existing_posts == 0:
            sample_posts = [
                Post(
                    title="The Rise of AI in 2025",
                    content="AI is transforming industries worldwide.",
                    youtube_url="https://www.youtube.com/watch?v=3rUX3CThCqY",
                    user_id=test_user.id
                ),
                Post(
                    title="Why Remote Work is the Future",
                    content="The shift towards remote work is accelerating due to productivity benefits.",
                    media_url="/static/uploads/sample-video.mp4",
                    user_id=test_user.id
                ),
                Post(
                    title="10 Tips for Financial Freedom",
                    content="Here are ten proven strategies to achieve financial independence.",
                    media_url="/static/uploads/sample-image.jpg",
                    user_id=test_user.id
                )
            ]

            db.session.bulk_save_objects(sample_posts)
            db.session.commit()
            print("✅ Dummy posts added!")
        else:
            print("ℹ️ Sample posts already exist, skipping creation.")

    # ✅ Generate Default Access Codes
    default_days_valid = [365, 180, 30]  # ⏳ 1 year, 6 months, 1 month

    for days in default_days_valid:
        new_code = AccessCode(days_valid=days)
        # Prevent duplicate access codes
        if not AccessCode.query.filter_by(code=new_code.code).first():
            db.session.add(new_code)
            print(f"✅ Access Code '{new_code.code}' created for {days} days.")

    db.session.commit()
    print("✅ Default access codes added!")

print("🎯 Database setup complete!")
