from enum import Enum

class WhereType(Enum):
    AND = 0
    OR = 1

class CompareType(Enum):
    EQUALS = 0
    LIKE = 1