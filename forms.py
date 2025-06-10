from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DecimalField, DateField, RadioField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from wtforms.widgets import DateInput
from flask_wtf.file import FileField, FileAllowed, FileRequired
from models import Category # Импортируем, чтобы получить список категорий

# Временные заглушки, будут наполняться
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class AssetForm(FlaskForm):
    # Будет наполняться
    pass

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