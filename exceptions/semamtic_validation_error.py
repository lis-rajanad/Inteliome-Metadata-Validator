class SemanticValidationError(Exception):
    """Base class for all semantic validation exceptions."""
    pass

class MissingKeyError(SemanticValidationError):
    def __init__(self, key):
        """
        Initialize a MissingKeyError with the given key.

        Args:
            key (str): The missing key.
        """
        super().__init__(f"Missing required key: '{key}'.")

class EmptyValueError(SemanticValidationError):
    def __init__(self, attribute, key):
        """
        Initialize an EmptyValueError with the given key.

        Args:
            attribute (str): The attribute with the missing or empty value.
            key (str): The key with the missing or empty value.
        """
        super().__init__(f"Missing or empty value for: '{key}' in {attribute}.")

class InvalidFormatError(SemanticValidationError):
    def __init__(self, key, expected_type):
        """
        Initialize an InvalidFormatError with the given key and expected type.

        Args:
            key (str): The key with the invalid format.
            expected_type (str): The expected type of the value for the given key.
        """
        super().__init__(f"Invalid format for key '{key}'. Expected type: '{expected_type}'.")

class InvalidKeyError(SemanticValidationError):
    def __init__(self, key: str, valid_keys: str):
        """
        Initialize an InvalidKeyError with the given key and valid keys.

        Args:
            key (str): The invalid key.
            valid_keys (str): The valid key.
        """
        super().__init__(f"Invalid key '{key}'. Expected one of: {valid_keys}.")
