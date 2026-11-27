"""Одноразовый скрипт: выгружает фикстуры из add_* функций в YAML.

Запуск: python -m scripts.dump_fixtures
После выгрузки add-функции в algorithm.py можно удалить.
"""
from pathlib import Path

import yaml
from flask import Flask

from config import Config
from data.db import db
import data.category  # noqa: F401
import data.algorithm as algo_mod

from scripts.check_fixtures import check

FIXTURES_DIR = Path(__file__).resolve().parent.parent / 'data' / 'fixtures'

# Всё, что попадает в yaml, кроме definition (генерируется при загрузке)
FIELDS = [
    'id', 'name', 'display_name', 'category_id',
    'description_short', 'description_full', 'complexity',
    'icon', 'order_index', 'default_input_data', 'input_schema',
    'default_settings', 'definition_mode', 'definition_python',
]


def _literal_str(dumper, text):
    """Многострочные строки пишем блочным скаляром |, остальные — как обычно."""
    if '\n' in text:
        return dumper.represent_scalar('tag:yaml.org,2002:str', text, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', text)


yaml.SafeDumper.add_representer(str, _literal_str)


def main():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)  # минимальный app: без create_app, чтобы не трогать БД и Security

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    add_fns = [
        fn for name, fn in sorted(vars(algo_mod).items())
        if name.startswith('add_') and callable(fn)
    ]

    with app.app_context():
        for fn in add_fns:
            algo = fn()
            data = {key: getattr(algo, key) for key in FIELDS}
            path = FIXTURES_DIR / f'{algo.id}.yaml'
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=100)
            print(f'written: {path.name}')

    print(f'\nTotal: {len(add_fns)} fixtures in {FIXTURES_DIR}')

    check(app)


if __name__ == '__main__':
    main()
