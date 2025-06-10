import os
from datetime import datetime, timedelta
from app import app, db
from models import User, Role, Category, Image, Asset, MaintenanceLog, ResponsiblePerson, generate_password_hash
import hashlib
from PIL import Image as PILImage # Используем псевдоним, чтобы не конфликтовать с моделью Image

# Функция для создания заглушек изображений
def create_dummy_image_file(filename, content="Dummy image content"):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        try:
            # Создаем очень маленькое изображение
            img = PILImage.new('RGB', (10, 10), color = 'red')
            img.save(filepath)
            print(f"  - Создан заглушка файла изображения: {filename}")
        except Exception as e:
            print(f"  - Не удалось создать заглушку изображения {filename}: {e}")
    return filepath

def calculate_md5_for_file(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def seed_data():
    with app.app_context():
        db.create_all() # Убедимся, что таблицы созданы

        print("--- Наполнение базы данных тестовыми данными ---")

        # 1. Создание ролей
        print("1. Создание или проверка ролей...")
        admin_role = Role.query.filter_by(name='administrator').first()
        tech_role = Role.query.filter_by(name='technical_specialist').first()
        user_role = Role.query.filter_by(name='user').first()

        if not admin_role:
            admin_role = Role(name='administrator')
            db.session.add(admin_role)
        if not tech_role:
            tech_role = Role(name='technical_specialist')
            db.session.add(tech_role)
        if not user_role:
            user_role = Role(name='user')
            db.session.add(user_role)
        
        db.session.commit()
        print("   Роли 'administrator', 'technical_specialist', 'user' созданы/проверены.")

        # 2. Создание пользователей (если их нет)
        print("2. Создание или проверка пользователей...")
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role=admin_role)
            admin_user.set_password('admin123') # Установите надежный пароль для продакшена
            db.session.add(admin_user)
            print("  - Создан пользователь: admin / admin123 (Администратор)")
        else:
            print("  - Пользователь 'admin' уже существует.")

        if not User.query.filter_by(username='tech').first():
            tech_user = User(username='tech', role=tech_role)
            tech_user.set_password('tech123')
            db.session.add(tech_user)
            print("  - Создан пользователь: tech / tech123 (Технический специалист)")
        else:
            print("  - Пользователь 'tech' уже существует.")

        if not User.query.filter_by(username='user').first():
            standard_user = User(username='user', role=user_role)
            standard_user.set_password('user123')
            db.session.add(standard_user)
            print("  - Создан пользователь: user / user123 (Пользователь)")
        else:
            print("  - Пользователь 'user' уже существует.")

        db.session.commit()

        # 3. Добавление тестовых категорий (если их нет)
        print("3. Добавление или проверка категорий...")
        if not Category.query.first():
            categories = [
                Category(name='Компьютер', description='Персональные компьютеры и ноутбуки'),
                Category(name='Принтер', description='Лазерные и струйные принтеры'),
                Category(name='Сканер', description='Планшетные и протяжные сканеры'),
                Category(name='Монитор', description='Мониторы для ПК'),
                Category(name='Проектор', description='Мультимедийные проекторы'),
                Category(name='МФУ', description='Многофункциональные устройства'),
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("   Добавлены тестовые категории.")
        else:
            print("   Категории уже существуют.")
        
        computer_cat = Category.query.filter_by(name='Компьютер').first()
        printer_cat = Category.query.filter_by(name='Принтер').first()
        scanner_cat = Category.query.filter_by(name='Сканер').first()
        monitor_cat = Category.query.filter_by(name='Монитор').first()
        projector_cat = Category.query.filter_by(name='Проектор').first()
        mfu_cat = Category.query.filter_by(name='МФУ').first()

        # 4. Добавление тестовых ответственных лиц (если их нет)
        print("4. Добавление или проверка ответственных лиц...")
        if not ResponsiblePerson.query.first():
            persons = [
                ResponsiblePerson(full_name='Иванов Иван Иванович', position='Начальник отдела', contact_info='ivanov@example.com'),
                ResponsiblePerson(full_name='Петров Петр Петрович', position='Менеджер', contact_info='petrov@example.com'),
                ResponsiblePerson(full_name='Сидоров Сидор Сидорович', position='Инженер', contact_info='sidorov@example.com'),
                ResponsiblePerson(full_name='Кузнецова Анна Николаевна', position='Специалист по IT', contact_info='kuznetsova@example.com')
            ]
            db.session.add_all(persons)
            db.session.commit()
            print("   Добавлены тестовые ответственные лица.")
        else:
            print("   Ответственные лица уже существуют.")

        ivanov = ResponsiblePerson.query.filter_by(full_name='Иванов Иван Иванович').first()
        petrov = ResponsiblePerson.query.filter_by(full_name='Петров Петр Петрович').first()
        sidorov = ResponsiblePerson.query.filter_by(full_name='Сидоров Сидор Сидорович').first()
        kuznetsova = ResponsiblePerson.query.filter_by(full_name='Кузнецова Анна Николаевна').first()

        # 5. Создание заглушек изображений и добавление их в БД
        print("5. Создание или проверка изображений...")
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        images_to_add = []
        dummy_files = [
            ("sample_pc.png", "image/png"),
            ("sample_printer.png", "image/png"),
            ("sample_monitor.png", "image/png"),
            ("sample_projector.png", "image/png")
        ]

        for original_filename, mime_type in dummy_files:
            dummy_filepath = create_dummy_image_file(original_filename)
            md5_hash = calculate_md5_for_file(dummy_filepath)
            
            existing_img = Image.query.filter_by(md5_hash=md5_hash).first()
            if not existing_img:
                new_img = Image(filename=original_filename, mime_type=mime_type, md5_hash=md5_hash)
                images_to_add.append(new_img)
            else:
                print(f"  - Изображение '{original_filename}' (MD5: {md5_hash}) уже существует.")

        if images_to_add:
            db.session.add_all(images_to_add)
            db.session.flush() # Получаем ID для сохранения файлов с новым именем
            for img_obj in images_to_add:
                # Переименуем файл по ID
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], img_obj.filename)
                new_filename = f"{img_obj.id}_{img_obj.filename}"
                new_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                os.rename(old_path, new_path)
                img_obj.filename = new_filename
            db.session.commit()
            print("   Новые изображения добавлены в БД и файлы переименованы.")
        else:
            print("   Все необходимые изображения уже существуют.")
        
        # Получаем объекты изображений для связывания с оборудованием
        img_pc = Image.query.filter_by(md5_hash=calculate_md5_for_file(os.path.join(app.config['UPLOAD_FOLDER'], '1_sample_pc.png'))).first() # Assuming ID 1
        img_printer = Image.query.filter_by(md5_hash=calculate_md5_for_file(os.path.join(app.config['UPLOAD_FOLDER'], '2_sample_printer.png'))).first() # Assuming ID 2
        img_monitor = Image.query.filter_by(md5_hash=calculate_md5_for_file(os.path.join(app.config['UPLOAD_FOLDER'], '3_sample_monitor.png'))).first() # Assuming ID 3
        img_projector = Image.query.filter_by(md5_hash=calculate_md5_for_file(os.path.join(app.config['UPLOAD_FOLDER'], '4_sample_projector.png'))).first() # Assuming ID 4

        # 6. Добавление тестового оборудования
        print("6. Добавление тестового оборудования...")
        if not Asset.query.first():
            assets_to_add = [
                Asset(
                    name='Игровой ПК HP Omen 30L',
                    inventory_number='PC-001',
                    category=computer_cat,
                    purchase_date=datetime(2023, 1, 15).date(),
                    cost=150000.00,
                    status='in_use',
                    notes='Высокопроизводительный ПК для графических задач.',
                    image=img_pc,
                    responsible_persons=[ivanov]
                ),
                Asset(
                    name='Принтер HP LaserJet Pro MFP M227fdn',
                    inventory_number='PR-002',
                    category=printer_cat,
                    purchase_date=datetime(2022, 3, 20).date(),
                    cost=25000.00,
                    status='in_use',
                    notes='МФУ для офисной печати.',
                    image=img_printer,
                    responsible_persons=[petrov, sidorov]
                ),
                Asset(
                    name='Сканер Epson Perfection V600',
                    inventory_number='SC-003',
                    category=scanner_cat,
                    purchase_date=datetime(2021, 6, 1).date(),
                    cost=18000.00,
                    status='under_repair',
                    notes='Не работает автоподатчик документов. Ожидает запчастей.',
                    image=None,
                    responsible_persons=[petrov]
                ),
                Asset(
                    name='Монитор Dell U2415',
                    inventory_number='MON-004',
                    category=monitor_cat,
                    purchase_date=datetime(2018, 11, 10).date(),
                    cost=12000.00,
                    status='written_off',
                    notes='Списан по истечении срока службы. Битые пиксели.',
                    image=img_monitor,
                    responsible_persons=[] # Нет ответственных
                ),
                Asset(
                    name='Ноутбук Lenovo IdeaPad 3',
                    inventory_number='NB-005',
                    category=computer_cat,
                    purchase_date=datetime(2023, 9, 1).date(),
                    cost=45000.00,
                    status='in_use',
                    notes='Для повседневных задач сотрудников.',
                    image=None,
                    responsible_persons=[kuznetsova]
                ),
                Asset(
                    name='Сетевой принтер Canon i-SENSYS LBP6030',
                    inventory_number='PR-006',
                    category=printer_cat,
                    purchase_date=datetime(2022, 11, 25).date(),
                    cost=15000.00,
                    status='in_use',
                    notes='Расположен в общем доступе.',
                    image=None,
                    responsible_persons=[sidorov]
                ),
                Asset(
                    name='Проектор Optoma HD144X',
                    inventory_number='PRO-007',
                    category=projector_cat,
                    purchase_date=datetime(2023, 4, 1).date(),
                    cost=55000.00,
                    status='in_use',
                    notes='Используется в конференц-зале.',
                    image=img_projector,
                    responsible_persons=[ivanov]
                ),
                Asset(
                    name='МФУ Brother DCP-T710W',
                    inventory_number='MFU-008',
                    category=mfu_cat,
                    purchase_date=datetime(2022, 7, 7).date(),
                    cost=30000.00,
                    status='in_use',
                    notes='Струйное МФУ.',
                    image=None,
                    responsible_persons=[kuznetsova, petrov]
                )
            ]
            db.session.add_all(assets_to_add)
            db.session.flush() # Для получения ID оборудования перед добавлением логов

            # Добавим еще немного оборудования для тестирования пагинации (без изображений для простоты)
            for i in range(9, 17): # Добавим 8 дополнительных единиц
                asset = Asset(
                    name=f'Тестовый Компьютер #{i}',
                    inventory_number=f'TEST-PC-{i:03d}',
                    category=computer_cat,
                    purchase_date=(datetime(2024, 1, 1) - timedelta(days=i*10)).date(),
                    cost=30000.00 + i*100,
                    status='in_use' if i % 3 != 0 else 'under_repair',
                    notes=f'Тестовое оборудование для проверки пагинации #{i}.',
                    image=None,
                    responsible_persons=[sidorov]
                )
                db.session.add(asset)
                assets_to_add.append(asset)
            
            db.session.commit()
            print("   Тестовое оборудование добавлено.")
        else:
            print("   Тестовое оборудование уже существует.")

        # 7. Добавление тестовых записей об обслуживании
        print("7. Добавление тестовых записей об обслуживании...")
        if not MaintenanceLog.query.first():
            pc_001 = Asset.query.filter_by(inventory_number='PC-001').first()
            pr_002 = Asset.query.filter_by(inventory_number='PR-002').first()
            sc_003 = Asset.query.filter_by(inventory_number='SC-003').first()
            nb_005 = Asset.query.filter_by(inventory_number='NB-005').first()
            pro_007 = Asset.query.filter_by(inventory_number='PRO-007').first()

            maintenance_logs = []
            if pc_001:
                maintenance_logs.extend([
                    MaintenanceLog(asset=pc_001, log_date=datetime(2023, 7, 1).date(), maintenance_type='Плановое ТО', comment='Чистка от пыли, замена термопасты.'),
                    MaintenanceLog(asset=pc_001, log_date=datetime(2023, 9, 10).date(), maintenance_type='Установка ПО', comment='Установка нового графического редактора.')
                ])
            if pr_002:
                maintenance_logs.append(MaintenanceLog(asset=pr_002, log_date=datetime(2023, 10, 5).date(), maintenance_type='Замена картриджа', comment='Заменен тонер-картридж на новый черный.'))
            if sc_003:
                maintenance_logs.append(MaintenanceLog(asset=sc_003, log_date=datetime(2023, 11, 15).date(), maintenance_type='Диагностика', comment='Предварительная диагностика, выявлена неисправность автоподатчика. Требуется заказ запчастей.'))
            if nb_005:
                maintenance_logs.append(MaintenanceLog(asset=nb_005, log_date=datetime(2024, 1, 20).date(), maintenance_type='Обновление ОС', comment='Обновление до Windows 11. Установлены последние драйверы.'))
            if pro_007:
                maintenance_logs.append(MaintenanceLog(asset=pro_007, log_date=datetime(2024, 2, 28).date(), maintenance_type='Чистка объектива', comment='Плановая чистка проектора и фильтров.'))

            db.session.add_all(maintenance_logs)
            db.session.commit()
            print("   Тестовые записи об обслуживании добавлены.")
        else:
            print("   Записи об обслуживании уже существуют.")

        print("--- База данных успешно инициализирована тестовыми данными! ---")

if __name__ == '__main__':
    seed_data()