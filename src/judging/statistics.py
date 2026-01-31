from src.repositories.judgment import judgment_repository
from src.repositories.sample import samples_repository


class JudgementStatistics:
    def __init__(self):
        self.judgment = judgment_repository
        self.sample = samples_repository
