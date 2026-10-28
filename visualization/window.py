"""
Окно визуализации.

На этом шаге окно содержит одну структуру. В будущем — список,
когда понадобится объединять несколько структур в одном окне.
"""


class Window:
    def __init__(self, window_id: str, title: str = ""):
        self.id = window_id
        self.title = title or window_id
        self.structure = None      # на этом шаге — одна структура
        self.visible = True

    def add_structure(self, structure):
        """Прикрепить структуру к окну. Структура запоминает окно у себя."""
        self.remove_structure()
        structure.attach_to(self)

    def remove_structure(self):
        if self.structure is not None:
            self.structure.detach()

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def clear(self):
        self.structure = None

    def is_visible(self) -> bool:
        return self.visible and self.structure is not None

    def build_snapshot_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'visible': self.visible,
            'structureName': self.structure.name if self.structure else None,
        }
