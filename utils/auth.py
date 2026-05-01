from functools import wraps
from flask import redirect, flash
from flask_security import current_user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Необходимо войти в систему', 'warning')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function
