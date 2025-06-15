import enum


class DjangoEnvironment(enum.Enum):
    """Django environment"""

    LOCAL = "local"
    DEVELOP = "develop"
    STAGE = "stage"
    PROD = "prod"
    TEST = "test"
