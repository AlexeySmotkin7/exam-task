import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError # Для обработки ошибок уникальности и т.п.
from functools import wraps
import qrcode
from PIL import Image # Pillow
import hashlib

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации."
login_manager.login_message_category = "warning"

# Убедимся, что папки для загрузки существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

# Импортируем модели и формы после инициализации db
from models import User, Role, Category, Image, Asset, MaintenanceLog, ResponsiblePerson, AssetResponsiblePerson
from forms import LoginForm, AssetForm, MaintenanceLogForm, AssetFilterForm # Будут добавлены позже

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Кастомный декоратор для проверки ролей
def role_required(*roles_allowed):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Для выполнения данного действия необходимо пройти процедуру аутентификации.", "warning")
                return redirect(url_for('login'))
            if not current_user.role.name in roles_allowed:
                flash("У вас недостаточно прав для выполнения данного действия.", "danger")
                return redirect(url_for('main_page')) # Или другой редирект
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# Простые маршруты заглушки
@app.route('/')
def main_page():
    # Эта страница будет доработана в следующих коммитах
    return render_template('equipment_list.html', title='Список оборудования')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Эта страница будет доработана в следующем коммите
    return render_template('login.html', title='Вход')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('main_page'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Создание таблиц при первом запуске
    app.run(debug=True)

# Вспомогательные функции для изображений
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()