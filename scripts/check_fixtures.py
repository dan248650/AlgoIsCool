import data.__all_models  # noqa: F401
from data.db import db
from data.algorithm import Algorithm, build_definition
from data.fixtures import load_fixtures


def check(app):
    with app.app_context():
        mismatches = []
        for item in load_fixtures():
            code = item.pop('definition_python')
            fresh = build_definition(code, item['default_input_data'], item['default_settings'])
            old = db.session.get(Algorithm, item['id'])
            if old is None:
                mismatches.append((item['id'], 'нет в базе'))
            elif old.definition != fresh:
                mismatches.append((item['id'], 'definition отличается'))
        for mid, why in mismatches:
            print('MISMATCH:', mid, why)
        else:
            print('OK')
        print(f'Checked {len(load_fixtures()) + len(mismatches)} fixtures')
