import sqlalchemy
from sqlalchemy import orm
from data.db import db
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import JSON
from datetime import datetime


class Algorithm(db.Model):
    __tablename__ = 'algorithms'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.Text, nullable=False)

    # foreign key
    category_id = db.Column(db.String(50), db.ForeignKey('categories.id'))

    # relationship
    category_rel = db.relationship('Category', backref='algorithms')

    display_name = db.Column(db.String(100))          # Отображаемое имя в каталоге
    description_short = db.Column(db.String(200))     # Краткое описание (для каталога)
    description_full = db.Column(db.Text)             # Полное описание
    complexity = db.Column(db.String(50))             # Оценка сложности
    icon = db.Column(db.String(10))
    order_index = db.Column(db.Integer, default=0)    # Порядок для пагинации
    default_input_data = db.Column(JSON)              # Данные по умолчанию

    definition = db.Column(JSON, nullable=False)      # Сгенерированное low-level описание
    input_schema = db.Column(JSON)
    default_settings = db.Column(JSON)

    definition_python = db.Column(db.Text, nullable=True)  # Python-код алгоритма
    definition_mode = db.Column(db.String(20), default='python')  # 'low_level' или 'python'


def build_definition(python_code, default_input, default_settings):
    """Сгенерировать low-level definition из python-кода алгоритма."""
    from visualization.python_to_low import generate_low_level_from_python
    return generate_low_level_from_python(python_code, default_input, default_settings)
