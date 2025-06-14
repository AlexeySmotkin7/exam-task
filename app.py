import os
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError # Для обработки ошибок уникальности и т.п.
from functools import wraps
import qrcode
from PIL import Image # Pillow
import hashlib
from datetime import datetime # Для purchase_date

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


@app.route('/equipment/add', methods=['GET', 'POST'])
@role_required('administrator')
def add_equipment():
    form = AssetForm()
    # Dynamic choices for responsible_persons must be set before validation
    form.responsible_persons.choices = [(p.id, p.full_name) for p in ResponsiblePerson.query.order_by(ResponsiblePerson.full_name).all()]

    if form.validate_on_submit():
        new_image = None
        current_image_path = None # Для временного хранения файла изображения
        try:
            # Обработка загрузки файла
            if form.photo.data:
                file = form.photo.data
                if file and allowed_file(file.filename):
                    # Сохраняем файл временно для вычисления MD5
                    temp_filename = secure_filename(file.filename)
                    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                    file.save(temp_filepath)

                    md5_hash = calculate_md5(temp_filepath)
                    existing_image = Image.query.filter_by(md5_hash=md5_hash).first()

                    if existing_image:
                        new_image = existing_image
                        # Удаляем временный файл, т.к. он уже есть в базе
                        os.remove(temp_filepath)
                    else:
                        # Создаем новую запись изображения
                        new_image = Image(filename='', mime_type=file.content_type, md5_hash=md5_hash)
                        db.session.add(new_image)
                        db.session.flush() # Получаем ID для имени файла
                        
                        # Сохраняем файл с именем, основанным на ID
                        final_filename = f"{new_image.id}_{temp_filename}"
                        os.rename(temp_filepath, os.path.join(app.config['UPLOAD_FOLDER'], final_filename))
                        new_image.filename = final_filename
                        current_image_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename) # Сохраняем для возможного удаления при ошибке

            # Проверка на уникальность инвентарного номера
            existing_asset = Asset.query.filter_by(inventory_number=form.inventory_number.data).first()
            if existing_asset:
                flash(f'Инвентарный номер "{form.inventory_number.data}" уже используется. Пожалуйста, выберите другой.', 'danger')
                return render_template('equipment_form.html', title='Добавить оборудование', form=form)

            # Создание нового оборудования
            asset = Asset(
                name=form.name.data,
                inventory_number=form.inventory_number.data,
                category_id=form.category_id.data,
                purchase_date=form.purchase_date.data,
                cost=form.cost.data,
                status=form.status.data,
                notes=form.notes.data,
                image=new_image if new_image else None # Связываем с изображением
            )

            asset.responsible_persons = [] 

            selected_persons_data = form.responsible_persons.data
            selected_persons_ids_to_query = []

            # Гарантируем, что selected_persons_data является списком ID
            if selected_persons_data is not None:
                if isinstance(selected_persons_data, list):
                    # Если это уже список, используем его
                    selected_persons_ids_to_query = selected_persons_data
                else:
                    # Если это одиночное значение (например, int), преобразуем в список
                    selected_persons_ids_to_query = [selected_persons_data]

            if selected_persons_ids_to_query:
                # Запрашиваем ResponsiblePerson объекты по их ID
                selected_persons = ResponsiblePerson.query.filter(ResponsiblePerson.id.in_(selected_persons_ids_to_query)).all()
                # Присваиваем обновленный список ответственных лиц
                asset.responsible_persons.extend(selected_persons)

            db.session.add(asset)
            db.session.flush() # Получаем ID для связей many-to-many

            db.session.commit()
            flash('Оборудование успешно добавлено!', 'success')
            return redirect(url_for('view_equipment', asset_id=asset.id))

        except IntegrityError:
            db.session.rollback()
            # Удалить файл, если произошла ошибка БД после сохранения файла
            if current_image_path and os.path.exists(current_image_path):
                os.remove(current_image_path)
            flash('При сохранении данных возникла ошибка. Возможно, инвентарный номер уже существует.', 'danger')
        except Exception as e:
            db.session.rollback()
            if current_image_path and os.path.exists(current_image_path):
                os.remove(current_image_path)
            flash(f'При сохранении данных возникла ошибка: {e}. Проверьте корректность введённых данных.', 'danger')

    return render_template('equipment_form.html', title='Добавить оборудование', form=form)

@app.route('/equipment/edit/<int:asset_id>', methods=['GET', 'POST'])
@role_required('administrator')
def edit_equipment(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    form = AssetForm(obj=asset)
    # Dynamic choices for responsible_persons must be set before validation
    form.responsible_persons.choices = [(p.id, p.full_name) for p in ResponsiblePerson.query.order_by(ResponsiblePerson.full_name).all()]

    if request.method == 'GET':
        # Для SELECT multiple, нужно установить form.responsible_persons.data в список ID
        form.responsible_persons.data = [p.id for p in asset.responsible_persons]

    if form.validate_on_submit():
        old_image = asset.image # Сохраняем старое изображение для возможного удаления
        current_image_path = None # Для временного хранения файла изображения, если новый

        try:
            # Обработка нового изображения
            if form.photo.data:
                file = form.photo.data
                if file and allowed_file(file.filename):
                    # Сохраняем файл временно для вычисления MD5
                    temp_filename = secure_filename(file.filename)
                    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                    file.save(temp_filepath)

                    md5_hash = calculate_md5(temp_filepath)
                    existing_image = Image.query.filter_by(md5_hash=md5_hash).first()

                    if existing_image:
                        asset.image = existing_image
                        os.remove(temp_filepath) # Удаляем временный файл
                    else:
                        new_image = Image(filename='', mime_type=file.content_type, md5_hash=md5_hash)
                        db.session.add(new_image)
                        db.session.flush()
                        
                        final_filename = f"{new_image.id}_{temp_filename}"
                        os.rename(temp_filepath, os.path.join(app.config['UPLOAD_FOLDER'], final_filename))
                        new_image.filename = final_filename
                        asset.image = new_image
                        current_image_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename) # Сохраняем для возможного удаления при ошибке

                    # Если была старая картинка и она больше не используется нигде, удаляем
                    if old_image and old_image != asset.image and old_image.assets.count() == 0:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image.filename)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                        db.session.delete(old_image)
            # Если фото не загружено, но старое было, его сохраняем.
            # Если форма предполагает удаление фото (например, чекбокс "Удалить фото"), нужно добавить логику.

            # Обновление данных оборудования
            asset.name = form.name.data
            # Проверка на уникальность инвентарного номера только если он изменился
            if asset.inventory_number != form.inventory_number.data:
                existing_asset = Asset.query.filter_by(inventory_number=form.inventory_number.data).first()
                if existing_asset and existing_asset.id != asset.id:
                    flash(f'Инвентарный номер "{form.inventory_number.data}" уже используется. Пожалуйста, выберите другой.', 'danger')
                    return render_template('equipment_form.html', title='Редактировать оборудование', form=form, asset=asset)
            asset.inventory_number = form.inventory_number.data

            asset.category_id = form.category_id.data
            asset.purchase_date = form.purchase_date.data
            asset.cost = form.cost.data
            asset.status = form.status.data
            asset.notes = form.notes.data

            asset.responsible_persons = [] 

            selected_persons_data = form.responsible_persons.data
            selected_persons_ids_to_query = []

            # Гарантируем, что selected_persons_data является списком ID
            if selected_persons_data is not None:
                if isinstance(selected_persons_data, list):
                    # Если это уже список, используем его
                    selected_persons_ids_to_query = selected_persons_data
                else:
                    # Если это одиночное значение (например, int), преобразуем в список
                    selected_persons_ids_to_query = [selected_persons_data]

            if selected_persons_ids_to_query:
                # Запрашиваем ResponsiblePerson объекты по их ID
                selected_persons = ResponsiblePerson.query.filter(ResponsiblePerson.id.in_(selected_persons_ids_to_query)).all()
                # Присваиваем обновленный список ответственных лиц
                asset.responsible_persons.extend(selected_persons)
            
            db.session.commit()
            flash('Оборудование успешно обновлено!', 'success')
            return redirect(url_for('view_equipment', asset_id=asset.id))

        except IntegrityError as e:
            db.session.rollback()
            if current_image_path and os.path.exists(current_image_path):
                os.remove(current_image_path)
            flash(f'При сохранении данных возникла ошибка целостности: {e}. Возможно, инвентарный номер уже существует.', 'danger')
        except Exception as e:
            db.session.rollback()
            if current_image_path and os.path.exists(current_image_path):
                os.remove(current_image_path)
            flash(f'При сохранении данных возникла ошибка: {e}. Проверьте корректность введённых данных.', 'danger')
    
    # Если GET запрос или валидация не прошла
    return render_template('equipment_form.html', title='Редактировать оборудование', form=form, asset=asset)

@app.route('/equipment/<int:asset_id>', methods=['GET', 'POST'])
@login_required # Доступна всем авторизованным пользователям
def view_equipment(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    maintenance_form = MaintenanceLogForm()

    # Dynamic choices for responsible_persons must be set before validation
    maintenance_form.log_date.default = datetime.now().date() # Установить дату по умолчанию
    if request.method == 'GET':
        maintenance_form.process() # Применить default значение для GET запроса

    if request.method == 'POST' and maintenance_form.validate_on_submit():
        # Проверка прав для добавления записи об обслуживании
        if not (current_user.is_admin or current_user.is_tech_specialist):
            flash("У вас недостаточно прав для добавления записи об обслуживании.", "danger")
            return redirect(url_for('view_equipment', asset_id=asset.id))
        
        try:
            log = MaintenanceLog(
                asset_id=asset.id,
                log_date=maintenance_form.log_date.data,
                maintenance_type=maintenance_form.maintenance_type.data,
                comment=maintenance_form.comment.data
            )
            db.session.add(log)
            db.session.commit()
            flash('Запись об обслуживании успешно добавлена!', 'success')
            return redirect(url_for('view_equipment', asset_id=asset.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении записи об обслуживании: {e}', 'danger')

    return render_template('equipment_detail.html', 
                           title=f'Оборудование: {asset.name}', 
                           asset=asset, 
                           maintenance_form=maintenance_form, 
                           current_user=current_user,
                           MaintenanceLog=MaintenanceLog) # <-- ДОБАВЬТЕ ЭТУ СТРОКУ


@app.route('/equipment/delete/<int:asset_id>', methods=['POST'])
@role_required('administrator')
def delete_equipment(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    
    try:
        # Сохраняем информацию об изображении до удаления оборудования
        image_to_delete = asset.image
        
        db.session.delete(asset)
        db.session.commit()

        # Если изображение было привязано к этому оборудованию и больше ни к чему не привязано, удаляем файл и запись об изображении
        if image_to_delete and image_to_delete.assets.count() == 0:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete.filename)
            if os.path.exists(image_path):
                os.remove(image_path)
            db.session.delete(image_to_delete)
            db.session.commit() # Отдельный коммит для удаления записи об изображении

        flash(f'Оборудование "{asset.name}" успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении оборудования: {e}', 'danger')
    
    return redirect(url_for('main_page'))

@app.route('/generate_qr_code/<string:inventory_number>')
def generate_qr_code(inventory_number):
    asset = Asset.query.filter_by(inventory_number=inventory_number).first_or_404()
    
    # URL, который будет закодирован в QR
    qr_data_url = url_for('view_equipment', asset_id=asset.id, _external=True)

    # Генерация QR-кода
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    qr_filename = f"qr_{secure_filename(inventory_number)}.png"
    qr_filepath = os.path.join(app.config['QR_CODE_FOLDER'], qr_filename)
    
    # Сохраняем QR-код, если его нет
    if not os.path.exists(qr_filepath):
        img.save(qr_filepath)

    # Возвращаем файл QR-кода
    return send_from_directory(app.config['QR_CODE_FOLDER'], qr_filename)


@app.route('/qr_scanner')
def qr_scanner():
    return render_template('qr_scanner.html', title='Сканер QR-кодов')

# Дополнительный маршрут, если QR-код содержит только инвентарный номер, а не полный URL
@app.route('/equipment/view_by_inventory/<string:inventory_num>')
@login_required # Только для авторизованных, как указано в задании
def view_equipment_by_inventory(inventory_num):
    asset = Asset.query.filter_by(inventory_number=inventory_num).first()
    if asset:
        return redirect(url_for('view_equipment', asset_id=asset.id))
    else:
        flash(f'Оборудование с инвентарным номером "{inventory_num}" не найдено.', 'danger')
        return redirect(url_for('main_page'))