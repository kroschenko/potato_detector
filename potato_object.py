class PotatoObject:
    def __init__(self, _id: int):
        self.id = _id
        self.first_section_scanned = False
        self.second_section_scanned = False
        self.third_section_scanned = False
        self.bounds = None
