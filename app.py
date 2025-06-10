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
from models import User, Role, Category, Image, Asset, MaintenanceLog, ResponsiblePerson
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

@app.route('/', methods=['GET'])
def main_page():
    form = AssetFilterForm(request.args)
    query = Asset.query.order_by(Asset.purchase_date.desc()) # Сортировка по дате покупки

    # Применение фильтров
    if form.validate_on_submit(): # Валидация при GET запросе с submit
        # Для GET запросов, данные уже в request.args, поэтому form.data уже заполнены
        pass 

    if form.category.data and form.category.data != 0: # 0 или '' для 'Все'
        query = query.filter(Asset.category_id == form.category.data)
    
    if form.status.data:
        query = query.filter(Asset.status == form.status.data)
    
    if form.purchase_date_start.data:
        query = query.filter(Asset.purchase_date >= form.purchase_date_start.data)

    if form.purchase_date_end.data:
        query = query.filter(Asset.purchase_date <= form.purchase_date_end.data)

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=app.config['PER_PAGE'], error_out=False)
    assets = pagination.items

    return render_template('equipment_list.html', 
                           title='Список оборудования', 
                           assets=assets, 
                           pagination=pagination, 
                           form=form, 
                           current_user=current_user)


# Маршруты для входа и выхода
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_page'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Невозможно аутентифицироваться с указанными логином и паролем.', 'danger')
            return render_template('login.html', title='Вход', form=form)
        login_user(user, remember=form.remember_me.data)
        flash('Вы успешно вошли в систему!', 'success')
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main_page'))
    return render_template('login.html', title='Вход', form=form)

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