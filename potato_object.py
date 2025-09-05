class PotatoObject:
    def __init__(self, _id: int):
        self.id = _id
        self.sections_scanned = []
        self.bounds = None
        self.final_evaluation_complete = False
        self.img_patches = []
        self.added_to_queue = False
