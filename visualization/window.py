class Window:
    def __init__(self, window_id: str, title: str = ""):
        self.id = window_id
        self.title = title or window_id
        self.structures = []       # список структур, порядок задаёт порядок отображения
        self.visible = False

    def add_structure(self, structure):
        """Прикрепить структуру к окну. Структура запоминает окно у себя."""
        structure.window = self
        self.structures.append(structure)

    def remove_structure(self, structure):
        if structure in self.structures:
            self.structures.remove(structure)
        if structure.window is self:
            structure.window = None

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def clear(self):
        for s in self.structures:
            if s.window is self:
                s.window = None
        self.structures = []

    def is_visible(self) -> bool:
        return self.visible and len(self.structures) > 0

    def build_snapshot_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'visible': self.visible,
            'structureNames': [s.name for s in self.structures],
        }
