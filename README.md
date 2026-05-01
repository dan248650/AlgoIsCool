# AlgoIsCool — интерактивная визуализация алгоритмов

**AlgoIsCool** — веб-приложение для наглядного изучения алгоритмов через анимацию. Платформа поддерживает массивы, графы, пользовательские алгоритмы, администрирование и гибкую систему визуализации.

---

## Особенности

- **Визуализация алгоритмов** в реальном времени (массивы, графы).
- **Каталог алгоритмов** с сортировкой по категориям.
- **Ролевая модель** (администратор, пользователь).
- **Адаптивный интерфейс** с регулировкой скорости, размера элементов и раскладки.
- **Расширяемая архитектура** — легко добавлять новые алгоритмы через JSON-определение.
- **Админ-панель** с метриками, управлением пользователями и алгоритмами.
- **REST API** для управления и выполнения алгоритмов.

---

## Быстрый старт

### Предварительные требования

- Python 3.8 или новее
- pip (менеджер пакетов)

### Запуск на Windows

Просто дважды кликните по файлу:

```batch
AlgoIsCool.bat
```

Скрипт автоматически:
- создаст виртуальное окружение `.venv`
- установит все зависимости из `requirements.txt`
- освободит порт 2109
- запустит сервер на `http://localhost:2109`

> При первом запуске будет создана база данных `users.db` и сгенерирован пароль для администратора (выводится в консоль).  
> **Учётные данные администратора по умолчанию:**  
> Email: `admin@algoiscool.ru`  
> Пароль: см. в консоли.

### Запуск на Linux/macOS

```bash
# Клонируйте репозиторий
git clone https://github.com/dan248650/AlgoIsCool.git
cd AlgoIsCool

# Создайте и активируйте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS

# Установите зависимости
pip install -r requirements.txt

# Запустите сервер
python server.py
```

Сервер будет доступен по адресу `http://localhost:2109`.

---

## Использование

1. **Главная страница** – краткое описание, кнопки входа/регистрации.
2. **Каталог алгоритмов** – доступен по `/algo/catalog` после авторизации (публичный просмотр возможен и без входа).
3. **Визуализация** – выберите алгоритм → введите данные → наблюдайте анимацию по шагам.
4. **Админ-панель** – доступна только для `admin` по адресу `/admin/dashboard`.  
   В ней можно:
   - просматривать статистику системы
   - добавлять/редактировать/удалять алгоритмы
   - управлять пользователями (изменять роли, блокировать)

---

## Структура проекта

```
AlgoIsCool/
├── data/                     # Модели БД и инициализация
│   ├── __all_models.py
│   ├── algorithm.py
│   ├── category.py
│   ├── user.py, role.py, associations.py
│   └── db.py
├── forms/                    # WTForms для пользователей и алгоритмов
├── routes/                   # Blueprints (admin, api, algo, auth, static)
├── static/                   # Статические файлы
│   ├── js/utils/             # Ядро визуализации
│   │   ├── base_renderer.js
│   │   ├── array_renderer.js
│   │   ├── graph_renderer.js
│   │   ├── player.js
│   │   └── input_form_handler.js
│   └── styles/               # CSS (core, auth, admin, algorithm)
├── templates/                # HTML-шаблоны Jinja2
├── utils/                    # Вспомогательные модули (auth, slugify, error_handlers)
├── visualization/            # Интерпретаторы алгоритмов (array_interpreter, graph_interpreter)
├── config.py                 # Настройки приложения
├── server.py                 # Точка входа
├── requirements.txt          # Зависимости Python
├── AlgoIsCool.bat            # Автоматический запуск на Windows
└── README.md
```

---

## Добавление нового алгоритма

Алгоритмы описываются JSON-определением и сохраняются в таблице `algorithms`.  
Через админ-панель можно добавить любой алгоритм, указав:

- **definition** – набор шагов (create_elements, for_each, condition, highlight, swap и т.д.)
- **input_schema** – типы входных данных (array, number, graph_nodes и т.д.)
- **default_input_data** – пример данных для демонстрации

### Пример шагов для линейного поиска (упрощённо)

```json
{
  "steps": [
    {
      "name": "Создать массив",
      "commands": [
        {"component": "create_elements", "params": {"array": "input_array"}}
      ]
    },
    {
      "name": "Поиск",
      "commands": [
        {
          "component": "for_each",
          "items": "range(0, n)",
          "variable": "i",
          "commands": [
            {"component": "highlight", "params": {"element_ids": ["elem_{{i}}"], "color": "colors.current"}},
            {"component": "condition", "condition": "array[i] == target", "then": [
                {"component": "highlight", "params": {"element_ids": ["elem_{{i}}"], "color": "colors.found"}}
            ]}
          ]
        }
      ]
    }
  ]
}
```

Поддерживаемые команды: `create_elements`, `swap_elements`, `highlight`, `unhighlight`, `move_straight`, `set_variable`, `while_loop`, `for_each`, `condition`, `wait`.  
Для графов: `highlight_node`, `highlight_edge`, `set_node_label` и другие.

---

## API

Базовый URL: `/api`

| Эндпоинт | Метод | Описание | Требуется admin |
|----------|-------|----------|----------------|
| `/check-auth` | GET | Проверка авторизации | нет |
| `/admin/algorithms` | GET | Список всех алгоритмов | да |
| `/admin/algorithms` | POST | Создать алгоритм | да |
| `/admin/algorithms/<id>` | GET, PUT, DELETE | Получить, обновить, удалить | да |

Также доступны публичные эндпоинты (`/algo/api/...`):

- `GET /algo/api/algorithms` – список алгоритмов
- `GET /algo/api/algorithm/<id>` – детали алгоритма
- `POST /algo/api/visualize` – выполнить алгоритм и получить команды для рендеринга

Пример запроса к `/algo/api/visualize`:

```json
{
  "algorithm_id": "linear-search",
  "input_data": {"input_array": [1,3,5], "target": 5},
  "settings": {"speed_factor": 1.5}
}
```

---

## Технологии

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Security, SQLite
- **Frontend**: ES6 модули, Canvas API, CSS Grid/Flexbox
- **Визуализация**: два рендерера (ArrayRenderer, GraphRenderer) + интерпретаторы команд
- **Планирование**: python-igraph для графовых раскладок
- **Управление паролями**: werkzeug.security, генератор случайных паролей

---

## Презентация

Презентация проекта: `docs/presentation.pptx`.

---

*AlgoIsCool — изучай алгоритмы с удовольствием!*  
Связь: [daniel.dan.pavlov@gmail.com](mailto:daniel.dan.pavlov@gmail.com)
