from app import app, db, bcrypt
from models import User, Post
import os

# ✅ Ensure the app context is set
with app.app_context():
    # ✅ Create all tables
    db.create_all()
    print("✅ Tables created successfully!")

    # ✅ Create an upload directory if it doesn't exist
    UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # ✅ Create a test user
    user_exists = User.query.filter_by(username="johndoe").first()
    if not user_exists:
        hashed_password = bcrypt.generate_password_hash("testpassword").decode('utf-8')
        test_user = User(username="johndoe", email="johndoe@example.com", password_hash=hashed_password)
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test user created!")
    else:
        print("ℹ️ User 'johndoe' already exists, skipping user creation.")

    # ✅ Insert sample posts for test user
    user = User.query.filter_by(username="johndoe").first()
    if user:
        existing_posts = Post.query.filter_by(user_id=user.id).count()
        if existing_posts == 0:
            sample_posts = [
                Post(
                    title="The Rise of AI in 2025",
                    content="AI is transforming industries worldwide.",
                    youtube_url="https://www.youtube.com/watch?v=3rUX3CThCqY",
                    user_id=user.id
                ),
                Post(
                    title="Why Remote Work is the Future",
                    content="The shift towards remote work is accelerating due to productivity benefits.",
                    media_url="/static/uploads/sample-video.mp4",
                    user_id=user.id
                ),
                Post(
                    title="10 Tips for Financial Freedom",
                    content="Here are ten proven strategies to achieve financial independence.",
                    media_url="/static/uploads/sample-image.jpg",
                    user_id=user.id
                )
            ]

            db.session.bulk_save_objects(sample_posts)
            db.session.commit()
            print("✅ Dummy posts added!")
        else:
            print("ℹ️ Sample posts already exist, skipping post creation.")

print("🎯 Database setup complete!")
