from abc import ABC, abstractmethod

from swagger_to_uml.model import Diagram


class DiagramRenderer(ABC):
    @abstractmethod
    def render(self, diagram: Diagram) -> str:
        pass
