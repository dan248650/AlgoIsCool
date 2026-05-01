import sqlalchemy
from sqlalchemy import orm
from data.db import db
from data.associations import user_role
from flask_security import RoleMixin
from sqlalchemy_serializer import SerializerMixin


class Role(db.Model, RoleMixin, SerializerMixin):
    __tablename__ = 'roles'

    serialize_rules = (
        '-users.roles',
    )

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)

    users = orm.relationship('User', secondary='user_role', back_populates='roles')

    def __repr__(self):
        return f'<Role {self.id}: {self.name}>'
