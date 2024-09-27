class SchemaValidationError(Exception):
    """Base class for all schema validation exceptions."""
    pass

class MissingKeyError(SchemaValidationError):
    def __init__(self, key):
        super().__init__(f"Missing required key: '{key}'.")

class EmptyValueError(SchemaValidationError):
    def __init__(self, attribute, key):
        super().__init__(f"Missing or empty value for: '{key}' in {attribute}.")

class InvalidFormatError(SchemaValidationError):
    def __init__(self, key, expected_type):
        super().__init__(f"Invalid format for key '{key}'. Expected type: '{expected_type}'.")

class InvalidKeyError(SchemaValidationError):
    def __init__(self, key: str, valid_keys: list[str]|str):
        super().__init__(f"Invalid key '{key}'. Expected one of: {valid_keys}.")
