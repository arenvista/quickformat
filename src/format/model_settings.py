from enum import Enum

class ModelSettings(Enum):
    LOW = 1
    MEDIUM = 2 
    HIGH = 3

    @property
    def display_name(self) -> str: 
        return self.name.replace('_', ' ').title().lower()
    def __str__(self): 
        return self.display_name
