from abc import ABC


class BaseValidator(ABC):
    def __init__(self):
        ...

    def validate(self, files = None):
        ...

    def _check_required_keys(self):
        ...