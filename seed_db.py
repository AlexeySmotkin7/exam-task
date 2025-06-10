from app import app, db
from models import User, Role, Category, ResponsiblePerson
from werkzeug.security import generate_password_hash # Импортируем явно

def seed_data():
    with app.app_context():
        db.create_all() # Убедимся, что таблицы созданы

        # 1. Создание ролей
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

        # 2. Создание администратора (если его нет)
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', role=admin_role)
            admin_user.set_password('admin123') # Установите надежный пароль для продакшена
            db.session.add(admin_user)
            print("Создан пользователь: admin / admin123 (Администратор)")
        else:
            print("Пользователь 'admin' уже существует.")

        if not User.query.filter_by(username='tech').first():
            tech_user = User(username='tech', role=tech_role)
            tech_user.set_password('tech123')
            db.session.add(tech_user)
            print("Создан пользователь: tech / tech123 (Технический специалист)")
        else:
            print("Пользователь 'tech' уже существует.")

        if not User.query.filter_by(username='user').first():
            standard_user = User(username='user', role=user_role)
            standard_user.set_password('user123')
            db.session.add(standard_user)
            print("Создан пользователь: user / user123 (Пользователь)")
        else:
            print("Пользователь 'user' уже существует.")

        # 3. Добавление тестовых категорий (если их нет)
        if not Category.query.first():
            categories = [
                Category(name='Компьютер', description='Персональные компьютеры и ноутбуки'),
                Category(name='Принтер', description='Лазерные и струйные принтеры'),
                Category(name='Сканер', description='Планшетные и протяжные сканеры'),
                Category(name='Монитор', description='Мониторы для ПК')
            ]
            db.session.add_all(categories)
            print("Добавлены тестовые категории.")
        else:
            print("Категории уже существуют.")

        # 4. Добавление тестовых ответственных лиц (если их нет)
        if not ResponsiblePerson.query.first():
            persons = [
                ResponsiblePerson(full_name='Иванов Иван Иванович', position='Начальник отдела', contact_info='ivanov@example.com'),
                ResponsiblePerson(full_name='Петров Петр Петрович', position='Менеджер', contact_info='petrov@example.com'),
                ResponsiblePerson(full_name='Сидоров Сидор Сидорович', position='Инженер', contact_info='sidorov@example.com')
            ]
            db.session.add_all(persons)
            print("Добавлены тестовые ответственные лица.")
        else:
            print("Ответственные лица уже существуют.")

        db.session.commit()
        print("База данных успешно инициализирована тестовыми данными.")

if __name__ == '__main__':
    seed_data()