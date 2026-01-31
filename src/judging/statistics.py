from src.crud.judgment import judgment_crud
from src.crud.sample import samples_crud


class JudgementStatistics:
    def __init__(self):
        self.judgment = judgment_crud
        self.sample = samples_crud
