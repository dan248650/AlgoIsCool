import sqlalchemy
from sqlalchemy import orm
from data.db import db
from werkzeug.security import generate_password_hash, check_password_hash
from data.associations import user_role
from datetime import datetime
from flask_security import UserMixin
from sqlalchemy import event
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.mutable import MutableDict


class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    serialize_rules = (
        '-hashed_password',
        '-fs_uniquifier',
        '-roles.users',
    )

    DEFAULT_SETTINGS = {
        'background_image': 'tree.jpg',
    }

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    age = sqlalchemy.Column(sqlalchemy.Integer)
    address = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)
    active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    city_from = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    settings = sqlalchemy.Column(
        MutableDict.as_mutable(sqlalchemy.JSON),
        default=DEFAULT_SETTINGS
    )

    fs_uniquifier = sqlalchemy.Column(sqlalchemy.String, unique=True)

    roles = orm.relationship('Role', secondary='user_role', back_populates='users',
                             cascade='all, delete')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def is_admin(self):
        return any(role.name == 'admin' for role in self.roles)

    def get_settings(self):
        result = dict(self.DEFAULT_SETTINGS)
        if self.settings:
            result.update(self.settings)
        return result

    def update_settings(self, **kwargs):
        current = self.get_settings()
        current.update(kwargs)
        self.settings = current

    def __repr__(self):
        return f'<User {self.id}: {self.name} {self.surname}>'


@event.listens_for(User, 'after_insert')
def add_default_role(mapper, connection, target):
    from data.__all_models import Role

    role = connection.execute(
        Role.__table__.select().where(Role.name == 'user')
    ).first()

    if role:
        connection.execute(
            user_role.insert().values(
                user_id=target.id,
                role_id=role.id
            )
        )
