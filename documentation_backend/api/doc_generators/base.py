# doc_generators/base.py
from abc import ABC, abstractmethod

class DocGenerator(ABC):
    @abstractmethod
    def generate(self, repo_path: str) -> str:
        """
        Генерирует документацию для проекта в repo_path.
        Возвращает путь к сгенерированной документации.
        """
        pass
