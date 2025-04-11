import enum


class DjangoEnvironment(enum.Enum):
    """Django 환경"""

    LOCAL = "local"
    DEVELOP = "develop"
    STAGE = "stage"
    PROD = "prod"
    TEST = "test"
