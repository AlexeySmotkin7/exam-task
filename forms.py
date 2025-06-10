from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DecimalField, DateField, RadioField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from wtforms.widgets import DateInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
from models import Category, ResponsiblePerson # Импортируем, чтобы получить список категорий

# Временные заглушки, будут наполняться
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class AssetForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(min=2, max=256)])
    inventory_number = StringField('Инвентарный номер', validators=[DataRequired(), Length(min=1, max=128)])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    purchase_date = DateField('Дата покупки', format='%Y-%m-%d', validators=[DataRequired()], widget=DateInput())
    cost = DecimalField('Стоимость', validators=[DataRequired(), NumberRange(min=0.01)])
    status = RadioField('Статус', choices=[
        ('in_use', 'В эксплуатации'), 
        ('under_repair', 'На ремонте'), 
        ('written_off', 'Списано')
    ], validators=[DataRequired()], default='in_use')
    notes = TextAreaField('Примечание', validators=[Length(max=5000)])
    photo = FileField('Фотография', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')])
    # MultiSelectField можно использовать для ответственных лиц, но для простоты пока пропустим.
    # Или используем простой SelectMultipleField и передаем id
    responsible_persons = SelectField('Ответственные лица', coerce=int, multiple=True)

    submit = SubmitField('Сохранить', render_kw={"class": "btn btn-primary"})

    def __init__(self, *args, **kwargs):
        super(AssetForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        # Добавляем пустой выбор, если категория может быть необязательной, или если нужен placeholder
        # self.category_id.choices.insert(0, (0, 'Выберите категорию')) 

        self.responsible_persons.choices = [(p.id, p.full_name) for p in ResponsiblePerson.query.order_by(ResponsiblePerson.full_name).all()]

class MaintenanceLogForm(FlaskForm):
    # Будет наполняться
    pass

class AssetFilterForm(FlaskForm):
    category = SelectField('Категория', coerce=lambda x: int(x) if x else None)
    status = SelectField('Статус', choices=[('', 'Все'), ('in_use', 'В эксплуатации'), ('under_repair', 'На ремонте'), ('written_off', 'Списано')])
    purchase_date_start = DateField('Дата покупки (от)', format='%Y-%m-%d', widget=DateInput())
    purchase_date_end = DateField('Дата покупки (до)', format='%Y-%m-%d', widget=DateInput())
    submit = SubmitField('Применить фильтры', render_kw={"class": "btn btn-outline-secondary"})

    def __init__(self, *args, **kwargs):
        super(AssetFilterForm, self).__init__(*args, **kwargs)
        # Динамическое заполнение категорий
        self.category.choices = [('', 'Все')] + [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти', render_kw={"class": "btn btn-primary"}) # Добавим класс Bootstrap


class MaintenanceLogForm(FlaskForm):
    log_date = DateField('Дата обслуживания', format='%Y-%m-%d', validators=[DataRequired()], widget=DateInput())
    maintenance_type = StringField('Тип обслуживания', validators=[DataRequired(), Length(min=2, max=128)])
    comment = TextAreaField('Комментарий', validators=[DataRequired(), Length(min=5, max=5000)])
    submit = SubmitField('Добавить запись', render_kw={"class": "btn btn-success"})