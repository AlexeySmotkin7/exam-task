from app import db # Импортируем db из app.py
from flask_login import UserMixin
from datetime import datetime

# Вспомогательная таблица для связи многие-ко-многим между Asset и ResponsiblePerson
asset_responsible_person_association = db.Table(
    'asset_responsible_person',
    db.Column('asset_id', db.Integer, db.ForeignKey('assets.id', ondelete='CASCADE')),
    db.Column('person_id', db.Integer, db.ForeignKey('responsible_persons.id', ondelete='CASCADE'))
)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role.name == 'administrator'

    @property
    def is_tech_specialist(self):
        return self.role.name == 'technical_specialist'

    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    assets = db.relationship('Asset', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False) # Store the actual filename used on disk
    mime_type = db.Column(db.String(128), nullable=False)
    md5_hash = db.Column(db.String(32), unique=True, nullable=False) # MD5 hash to prevent duplicates
    assets = db.relationship('Asset', backref='image', lazy='dynamic')

    def __repr__(self):
        return f'<Image {self.filename}>'

class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    inventory_number = db.Column(db.String(128), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('in_use', 'under_repair', 'written_off', name='asset_status_enum'), nullable=False, default='in_use')
    notes = db.Column(db.Text)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id')) # NULLABLE, if photo is optional

    maintenance_logs = db.relationship('MaintenanceLog', backref='asset', lazy='dynamic', cascade="all, delete-orphan")
    responsible_persons = db.relationship('ResponsiblePerson', secondary=asset_responsible_person_association, back_populates='assets')

    def __repr__(self):
        return f'<Asset {self.name} ({self.inventory_number})>'

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False)
    log_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    maintenance_type = db.Column(db.String(128), nullable=False)
    comment = db.Column(db.Text)

    def __repr__(self):
        return f'<MaintenanceLog {self.maintenance_type} for Asset {self.asset_id}>'

class ResponsiblePerson(db.Model):
    __tablename__ = 'responsible_persons'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(256), nullable=False)
    position = db.Column(db.String(128))
    contact_info = db.Column(db.Text)
    assets = db.relationship('Asset', secondary=asset_responsible_person_association, back_populates='responsible_persons')

    def __repr__(self):
        return f'<ResponsiblePerson {self.full_name}>'