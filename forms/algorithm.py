from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from flask import flash
import json

from visualization.python_to_low import generate_low_level_from_python


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
    definition_initial_state = TextAreaField('Начальное состояние (JSON)', validators=[Optional()])
    definition_steps = TextAreaField('Шаги (JSON)', validators=[Optional()])

    definition_python = TextAreaField('Python-код описания визуализации', validators=[Optional()])

    # Другие JSON-поля
    input_schema = TextAreaField('Input schema (JSON)', validators=[Optional()])
    default_settings = TextAreaField('Default settings (JSON)', validators=[Optional()])
    default_input_data = TextAreaField('Default input data (JSON)', validators=[Optional()])

    # Режим описания
    definition_mode = SelectField('Режим описания', choices=[
        ('low_level', 'Низкоуровневое JSON-описание'),
        ('python', 'Высокоуровневый Python-код')
    ], default='python', validators=[DataRequired()])

    submit = SubmitField('Сохранить')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливается валидатором definition_python; используется
        # в admin_bp, чтобы не транслировать код повторно.
        self._translated_definition = None

    def _flash_error(self, field_name, message):
        """Единый канал ошибки: и в flash, и в form.<field>.errors.
        Шаблон рендерит errors под полем, layouts/base.html — flash
        в глобальном баннере. Обе точки видны пользователю."""
        flash(f'Ошибка в поле «{field_name}»: {message}', 'danger')
        raise ValidationError(message)

    def validate_definition_python(self, field):
        if self.definition_mode.data != 'python' or not field.data:
            return

        try:
            input_data = json.loads(self.default_input_data.data) \
                if self.default_input_data.data else {}
        except (ValueError, TypeError):
            input_data = {}
        try:
            settings = json.loads(self.default_settings.data) \
                if self.default_settings.data else {}
        except (ValueError, TypeError):
            settings = {}

        try:
            self._translated_definition = generate_low_level_from_python(
                field.data, input_data, settings
            )
        except Exception as e:
            self._flash_error('definition_python', str(e))

    def validate_definition_steps(self, field):
        """Проверка, что steps — валидный JSON"""
        if field.data:
            try:
                json.loads(field.data)
            except json.JSONDecodeError as e:
                self._flash_error('definition_steps', f'Неверный JSON: {e}')

    def validate_definition_initial_state(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError as e:
                self._flash_error('definition_initial_state',
                                  f'Неверный JSON: {e}')

    def validate_input_schema(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError as e:
                self._flash_error('input_schema', f'Неверный JSON: {e}')

    def validate_default_settings(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError as e:
                self._flash_error('default_settings', f'Неверный JSON: {e}')

    def validate_default_input_data(self, field):
        if field.data and field.data.strip():
            try:
                json.loads(field.data)
            except json.JSONDecodeError as e:
                self._flash_error('default_input_data',
                                  f'Неверный JSON: {e}')

    @property
    def translated_definition(self):
        return self._translated_definition
