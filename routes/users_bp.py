from flask import Blueprint, render_template, redirect, flash, request, abort, jsonify
from utils.auth import login_required
from data.db import db
from data.__all_models import User, Role
from forms.user import UserForm, ChangePasswordForm
from flask_security import current_user

user_bp = Blueprint('user_bp', __name__, template_folder='templates')


@user_bp.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not (current_user.is_admin() or current_user.id == id):
        flash('У вас нет прав для редактирования этого пользователя', 'danger')
        return redirect('/admin/dashboard' if current_user.is_admin() else '/')

    form = UserForm()
    form.submit.label.text = 'Сохранить изменения'

    user = db.session.query(User).get(id)
    if not user:
        abort(404)

    if request.method == 'GET':
        form.surname.data = user.surname
        form.name.data = user.name
        form.age.data = user.age
        form.address.data = user.address
        form.email.data = user.email
        form.background_image.data = user.get_settings()['background_image']
        form.roles.data = [r.id for r in user.roles]
        form.active.data = user.active

    if form.validate_on_submit():
        existing = db.session.query(User).filter(
            User.email == form.email.data,
            User.id != id
        ).first()
        if existing:
            return render_template('users/user.html',
                                   title='Редактирование пользователя',
                                   form=form,
                                   message='Пользователь с таким email уже существует',
                                   action='edit',
                                   user_id=id,
                                   return_url='/admin/dashboard' if current_user.is_admin() else '/')

        user.surname = form.surname.data
        user.name = form.name.data
        user.age = form.age.data
        user.address = form.address.data
        user.email = form.email.data
        user.update_settings(background_image=form.background_image.data)
        user.active = form.active.data

        if current_user.is_admin() and form.roles.data:
            roles = db.session.query(Role).filter(Role.id.in_(form.roles.data)).all()
            user.roles = roles

        db.session.commit()
        flash('Пользователь успешно обновлен!', 'success')
        return redirect('/admin/dashboard' if current_user.is_admin() else '/')

    return render_template('users/user.html',
                           title='Редактирование пользователя',
                           form=form,
                           action='edit',
                           user_id=id,
                           return_url='/admin/dashboard' if current_user.is_admin() else '/')


@user_bp.route('/delete_user/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin():
        flash('У вас нет прав для удаления пользователей', 'danger')
        return redirect('/')

    user = db.session.query(User).get(id)
    if not user:
        abort(404)

    if user.id == current_user.id:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect('/admin/dashboard')

    db.session.delete(user)
    db.session.commit()

    flash('Пользователь успешно удален!', 'success')
    return redirect('/admin/dashboard')


@user_bp.route('/change_password/<int:id>', methods=['GET', 'POST'])
@login_required
def change_password(id):
    if not (current_user.is_admin() or current_user.id == id):
        flash('У вас нет прав для изменения пароля', 'danger')
        return redirect('/')

    form = ChangePasswordForm()
    form.submit.label.text = 'Изменить пароль'

    user = db.session.query(User).get(id)
    if not user:
        abort(404)

    if form.validate_on_submit():
        if not current_user.is_admin():
            if not user.check_password(form.current_password.data):
                return render_template('users/change_password.html',
                                       title='Изменение пароля',
                                       form=form,
                                       message='Неверный текущий пароль',
                                       user_id=id)

        if form.new_password.data != form.confirm_password.data:
            return render_template('users/change_password.html',
                                   title='Изменение пароля',
                                   form=form,
                                   message='Пароли не совпадают',
                                   user_id=id)

        user.set_password(form.new_password.data)
        db.session.commit()

        flash('Пароль успешно изменен!', 'success')
        return redirect('/admin/dashboard' if current_user.is_admin() else '/')

    return render_template('users/change_password.html',
                           title='Изменение пароля',
                           form=form,
                           user_id=id)


@user_bp.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    allowed_keys = set(User.DEFAULT_SETTINGS.keys())
    clean = {k: v for k, v in data.items() if k in allowed_keys}
    if not clean:
        return jsonify({'error': 'No valid keys'}), 400

    current_user.update_settings(**clean)
    db.session.commit()
    return jsonify({'success': True, 'settings': current_user.get_settings()})
