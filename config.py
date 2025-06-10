import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_super_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    QR_CODE_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'qrcodes')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    PER_PAGE = 10 # Записей на страницу для пагинации
    WTF_CSRF_ENABLED = True