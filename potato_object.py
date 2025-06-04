from torch import Tensor


class PotatoObject:
    def __init__(self, _id: int):
        self.id = _id
        self.section_0_scanned = False
        self.section_1_scanned = False
        self.section_2_scanned = False
        self.section_3_scanned = False
        self.section_4_scanned = False
        self.section_5_scanned = False
        self.section_6_scanned = False
        self.section_7_scanned = False
        self.section_8_scanned = False
        self.bounds = None
        self.evaluation_results = Tensor([[0, 0]])
        self.final_evaluation_complete = False
