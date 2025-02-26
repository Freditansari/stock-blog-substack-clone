import os

# ✅ Define upload folder path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')

# ✅ Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi', 'mov'}

# ✅ Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HCAPTCHA_SITE_KEY ='35184564-7ffe-4128-9dba-bec61be0143c'
HCAPTCHA_SECRET_KEY ='ES_3c988b3d17d540a29bce22b9a3d80aad'
