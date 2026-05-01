from flask import Blueprint, render_template, redirect, flash, request
from flask_security import login_user, logout_user, current_user
from utils.auth import login_required
from data.__all_models import User
from data.db import db
from forms.user import LoginForm

login_bp = Blueprint('login_bp', __name__, template_folder='templates')


@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db.session
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and user.check_password(form.password.data):
            if not user.active:
                return render_template('auth/login.html',
                                       title='Авторизация',
                                       form=form,
                                       message="Аккаунт деактивирован")

            login_user(user, remember=form.remember_me.data)
            flash('Вы успешно вошли в систему!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect("/")
        else:
            return render_template('auth/login.html',
                                   title='Авторизация',
                                   form=form,
                                   message="Неправильный email или пароль")

    return render_template('auth/login.html',
                           title='Авторизация',
                           form=form)


@login_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect("/")
