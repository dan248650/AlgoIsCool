from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
import json


class AlgorithmForm(FlaskForm):
    # Основные поля
    name = StringField('Название (ID)', validators=[DataRequired(), Length(max=50)])
    display_name = StringField('Отображаемое имя', validators=[Optional(), Length(max=100)])
    category_id = StringField('Категория', validators=[Optional(), Length(max=50)])
    order_index = IntegerField('Порядок', validators=[Optional(), NumberRange(min=0)])

    # Описание
    description_short = StringField('Краткое описание', validators=[Optional(), Length(max=200)])
    description_full = TextAreaField('Полное описание', validators=[Optional()])
    complexity = StringField('Сложность', validators=[Optional(), Length(max=50)])

    # Definition (разбит на отдельные поля)
    definition_type = SelectField('Тип алгоритма', choices=[
        ('array', 'array (массив)'),
        ('graph', 'graph (граф)')
    ], validators=[DataRequired()])
    definition_initial_state = TextAreaField('Начальное состояние (JSON)', validators=[Optional()])
    definition_steps = TextAreaField('Шаги (JSON)', validators=[DataRequired()])

    definition_python = TextAreaField('Python-код описания визуализации', validators=[Optional()])

    # Другие JSON-поля
    input_schema = TextAreaField('Input schema (JSON)', validators=[Optional()])
    default_settings = TextAreaField('Default settings (JSON)', validators=[Optional()])
    default_input_data = TextAreaField('Default input data (JSON)', validators=[Optional()])

    # Режим описания
    definition_mode = SelectField('Режим описания', choices=[
        ('low_level', 'Низкоуровневое JSON-описание'),
        ('python', 'Высокоуровневый Python-код')
    ], default='low_level', validators=[DataRequired()])

    submit = SubmitField('Сохранить')

    def validate_definition_python(self, field):
        if self.definition_mode.data == 'python' and field.data:
            try:
                compile(field.data, '<string>', 'exec')
            except SyntaxError as e:
                raise ValidationError(f'Синтаксическая ошибка в Python-коде: {e}')

    def validate_definition_steps(self, field):
        """Проверка, что steps — валидный JSON"""
        if field.data:
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValueError('Неверный JSON в поле steps')

    def validate_definition_initial_state(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValueError('Неверный JSON в начальном состоянии')

    def validate_input_schema(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValueError('Неверный JSON в input_schema')

    def validate_default_settings(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValueError('Неверный JSON в default_settings')

    def validate_default_input_data(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError:
                raise ValueError('Неверный JSON в default_input_data')
