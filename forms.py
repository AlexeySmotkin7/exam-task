from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DecimalField, DateField, RadioField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from wtforms.widgets import DateInput
from flask_wtf.file import FileField, FileAllowed, FileRequired

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
    # Будет наполняться
    pass


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти', render_kw={"class": "btn btn-primary"}) # Добавим класс Bootstrap