from data.db import db
from sqlalchemy_serializer import SerializerMixin


class Category(db.Model, SerializerMixin):
    __tablename__ = 'categories'

    id = db.Column(db.String(50), primary_key=True)  # 'sorting', 'search', 'graph'
    name = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(10), default='algo')
    order_index = db.Column(db.Integer, default=0)


def init_categories():
    categories = [
        {'id': 'sorting', 'name': 'Sorting Algorithms', 'display_name': 'Алгоритмы сортировки', 'order_index': 10},
        {'id': 'search', 'name': 'Search Algorithms', 'display_name': 'Алгоритмы поиска', 'order_index': 20},
        {'id': 'graph', 'name': 'Graph Algorithms', 'display_name': 'Графовые алгоритмы', 'order_index': 30},
        {'id': 'linear', 'name': 'Linear Algorithms', 'display_name': 'Линейные алгоритмы', 'order_index': 40},
        {'id': 'tree', 'name': 'Tree Algorithms', 'display_name': 'Алгоритмы на деревьях', 'order_index': 50},
        {'id': 'string', 'name': 'String Algorithms', 'display_name': 'Строковые алгоритмы', 'order_index': 60},
        {'id': 'dynamics', 'name': 'Dynamic Programming', 'display_name': 'Динамическое программирование', 'order_index': 70},
        {'id': '2d-dynamics', 'name': '2D Dynamic Programming', 'display_name': 'Двумерная динамика', 'order_index': 80},
        {'id': 'tests', 'name': 'Тестирование', 'display_name': 'Тесты', 'order_index': 200}
    ]

    for cat_data in categories:
        existing = Category.query.get(cat_data['id'])
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)
    db.session.commit()
