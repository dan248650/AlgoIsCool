from flask_wtf import FlaskForm
from wtforms import (PasswordField, StringField, IntegerField, SubmitField, EmailField,
                     BooleanField, SelectMultipleField)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from data.db import db
from data.__all_models import Role


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    age = IntegerField('Возраст', validators=[DataRequired(), NumberRange(min=10, max=100)])
    address = StringField('Адрес', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class UserForm(FlaskForm):
    surname = StringField('Фамилия', validators=[DataRequired(), Length(min=2, max=50)])
    name = StringField('Имя', validators=[DataRequired(), Length(min=2, max=50)])
    age = IntegerField('Возраст', validators=[DataRequired(), NumberRange(min=10, max=100)])
    address = StringField('Адрес', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    roles = SelectMultipleField('Роли', coerce=int, validators=[Optional()])
    active = BooleanField('Активен', default=True)
    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.roles.choices = [
            (role.id, role.name)
            for role in db.session.query(Role).all()
        ]


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = StringField('Подтвердите пароль', validators=[DataRequired()])
    submit = SubmitField('Изменить пароль')
