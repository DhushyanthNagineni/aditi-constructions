# import os
# BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# class Config:
#         SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
#         SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
#         'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'site.db')
#         SQLALCHEMY_TRACK_MODIFICATIONS = False
#         UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
#         ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

#for render 
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")

    # Required for Render (writable DB location)
    SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/render.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
