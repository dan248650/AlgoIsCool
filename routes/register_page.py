from flask import Blueprint, render_template, redirect, flash
from flask_security import current_user
from data.__all_models import User, Role
from data.db import db
from forms.user import RegisterForm
import uuid

register_bp = Blueprint('register_bp', __name__, template_folder='templates')


@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('auth/register.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")

        db_sess = db.session

        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('auth/register.html',
                                   title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")

        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            address=form.address.data,
            email=form.email.data,
            fs_uniquifier=str(uuid.uuid4()),
            active=True
        )

        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()

        flash('Регистрация прошла успешно! Теперь вы можете войти', 'success')
        return redirect('/login')

    return render_template('auth/register.html', title='Регистрация', form=form)
