"""Загрузка алгоритмов из yaml-фикстур."""
from pathlib import Path

import yaml

from .db import db
from .algorithm import Algorithm, build_definition

FIXTURES_DIR = Path(__file__).resolve().parent / 'fixtures'

REQUIRED_FIELDS = {
    'id', 'name', 'category_id', 'default_input_data',
    'input_schema', 'default_settings', 'definition_python',
}


def load_fixtures():
    items = []
    seen_ids = set()
    for path in sorted(FIXTURES_DIR.glob('**/*.yaml')):
        with open(path, encoding='utf-8') as f:
            item = yaml.safe_load(f)
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f'{path.name}: missing fields {missing}')
        if item['id'] in seen_ids:
            raise ValueError(f'duplicate algorithm id: {item["id"]}')
        seen_ids.add(item['id'])
        items.append(item)
    return items


def init_algorithms():
    allowed = {
        'id', 'name', 'display_name', 'category_id', 'description_short',
        'description_full', 'complexity', 'icon', 'order_index',
        'default_input_data', 'input_schema', 'default_settings',
    }
    for item in load_fixtures():
        python_code = item.pop('definition_python')
        definition_mode = item.pop('definition_mode', 'python')

        extra = set(item) - allowed
        if extra:
            raise ValueError(f'{item["id"]}: unexpected fields in yaml: {extra}')

        definition = build_definition(
            python_code, item['default_input_data'], item['default_settings'])

        new_algo = Algorithm(
            definition=definition,
            definition_python=python_code,
            definition_mode=definition_mode,
            **item,
        )

        existing = db.session.get(Algorithm, new_algo.id)
        if existing:
            for key in ('name', 'display_name', 'category_id', 'description_short',
                        'description_full', 'complexity', 'icon', 'order_index',
                        'default_input_data', 'definition', 'input_schema',
                        'default_settings', 'definition_python', 'definition_mode'):
                setattr(existing, key, getattr(new_algo, key))
        else:
            db.session.add(new_algo)
    db.session.commit()
