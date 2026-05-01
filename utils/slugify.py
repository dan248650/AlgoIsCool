import re


def slugify(name: str) -> str:
    """Генерирует id из названия"""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s_-]+', '-', name)
    return name.strip('-')
