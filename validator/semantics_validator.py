import re
from logger.log import logger
from pathlib import Path

from exceptions.semamtic_validation_error import MissingKeyError, EmptyValueError, InvalidFormatError, InvalidKeyError
from validator.base_validator import BaseValidator# Set

class SemanticsValidator(BaseValidator):
    def __init__(self, filename, semantics):
        super().__init__()
        self.filename = filename
        self.semantics = semantics

    def _check_required_keys(self):
        """Ensure all required keys are present in the semantics."""
        required_keys = ['folder', 'type']
        for key in required_keys:
            if key not in self.semantics:
                logger.error(f"Missing required key: '{key}' in the semantics.")
                raise ValueError(f"Missing required key: '{key}' in the semantics.")

        # Ensure at least one of attributes or metrics is present
        if not self.semantics.get('attributes') and not self.semantics.get('metrics'):
            logger.error("At least one of 'attributes' or 'metrics' must be present.")
            raise MissingKeyError("At least one of 'attributes' or 'metrics' must be present.")

    def validate(self, files=None):
        """Validate the semantics against the relevant schema."""
        if files is None:
            logger.error("No schema files initialized yet.")
            raise MissingKeyError("No schema files initialized yet.")

        source = self.semantics.get('source')
        if source is None:
            logger.error("No source specified in semantics.")
            raise MissingKeyError("No source specified in semantics.")

        logger.info("Scanning sourced schema...")
        schema_references = list(source.keys())
        if not schema_references:
            logger.error("No schema reference found.")
            raise MissingKeyError("No schema reference found.")

        logger.info(f"Found {schema_references} schemas in semantics")
        for schema_key in schema_references:
            schema = schema_key.split('.')[1]

            relevant_schema = next((content for s, content in files if Path(s).stem == schema), None)
            if relevant_schema is None:
                logger.error(f"Schema '{schema}' referenced in source '{schema_key}' not found.")
                raise MissingKeyError(f"Schema '{schema}' referenced in source '{schema_key}' not found.")

            # extract the sourced columns from schema_key
            referenced_columns = source[schema_key]['columns']

            self.validate_referenced_columns(schema, relevant_schema, referenced_columns)
            self._validate_attributes(self.semantics.get('attributes', {}), schema)
            self._validate_metrics(self.semantics.get('metrics', {}), schema)

            self.validate_semantics(schema_key)

    def validate_referenced_columns(self, schema_name, schema, referenced_columns):
        """Validate that all columns referenced in the semantics exist in the schema."""
        schema_columns = schema.get('columns', [])
        missing_columns = [col for col in referenced_columns if col not in schema_columns]

        if missing_columns:
            logger.error(f"The following columns are referenced but not found in schema: {missing_columns}")
            raise MissingKeyError(f"Columns missing in schema: {', '.join(missing_columns)}")

        logger.info(f"All column references are verified in {schema_name}.yml schema file.")

    def validate_semantics(self, schema):
        """Validate the overall semantics structure."""
        try:
            self._check_required_keys()
            self._validate_source(self.semantics.get('source'))
            logger.info(f"Semantics {self.filename} validation passed!")
        except ValueError as e:
            logger.error(f"Validation Error: {e}")
        except Exception as e:
            logger.exception("An unexpected error occurred")

    def _validate_source(self, source):
        """Validate the source key."""
        if source is not None:
            if not isinstance(source, dict):
                logger.error("Source must be a dictionary.")
                raise InvalidFormatError('source', 'dictionary')

            for key, value in source.items():
                if not re.match(r'^schema\.\w+$', key):
                    logger.error(f"Invalid key format: {key}. Expected format 'schema.<name>'.")
                    raise InvalidKeyError(key, "Expected format 'schema.<name>'")

                if not isinstance(value, dict) or 'columns' not in value:
                    logger.error(f"Key '{key}' must be a dictionary containing a 'columns' key.")
                    raise InvalidFormatError(key, "must be a dictionary containing a 'columns' key")

                columns = value['columns']
                if not isinstance(columns, list) or not all(isinstance(col, str) for col in columns):
                    logger.error(f"'columns' for source {key} must be a list of strings.")
                    raise InvalidFormatError('columns', 'a list of strings for source ' + key)

    def _validate_attributes(self, attributes, schema):
        """Validate the structure and values of the attributes."""
        if not isinstance(attributes, dict):
            logger.error("Attributes must be a dictionary.")
            raise InvalidFormatError(attributes, 'dictionary')

        for key, value in attributes.items():
            self._validate_attribute(key, value, schema)

    def _validate_attribute(self, attr_key, attribute, schema):
        """Validate an individual semantic attribute's structure and values."""
        if not isinstance(attribute, dict):
            logger.error(f"Attribute {attr_key} must be a dictionary.")
            raise InvalidFormatError(attr_key, 'dictionary')

        if 'name' in attribute and not attribute['name']:
            logger.error(f"Attribute {attr_key} must have a non-empty 'name'.")
            raise EmptyValueError(attr_key, 'name')
        if 'desc' in attribute and not attribute['desc']:
            logger.error(f"Attribute {attr_key} must have a non-empty 'desc'.")
            raise EmptyValueError(attr_key, 'desc')
        if 'calculation' in attribute and not attribute['calculation']:
            logger.error(f"Attribute {attr_key} must have a non-empty 'calculation'.")
            raise EmptyValueError(attr_key, 'calculation')

        if 'calculation' in attribute:
            self._validate_calculation(attribute['calculation'])

        if 'filter' in attribute:
            self._validate_filters(attribute['filter'])

    def _validate_calculation(self, calculation):
        """Validate calculation format against defined patterns."""

        if not isinstance(calculation, str):
            logger.error(f"Calculation must be a string. Got: {type(calculation).__name__}")
            raise InvalidFormatError(calculation, 'string')

        # Patterns for basic expressions and operators
        basic_expr_pattern = r'[\w\s\[\]\+\-\*\/\(\)]+'
        logical_pattern = self._build_pattern(["AND", "OR", "NOT"])
        comparison_pattern = self._build_pattern(["=", "!=", "<", ">", "<=", ">="])
        function_pattern = self._build_function_pattern(basic_expr_pattern)

        # Complete regex pattern for calculations
        complete_pattern = self._build_complete_pattern(
            function_pattern, basic_expr_pattern, comparison_pattern, logical_pattern
        )

        if not re.match(complete_pattern, calculation, re.IGNORECASE):
            logger.error(f"Calculation format is invalid for: {calculation}")
            raise InvalidFormatError('calculation', 'valid calculation format')

    def _build_function_pattern(self, basic_expr_pattern):
        """Build the regex pattern for supported functions."""
        supported_functions = {
            "aggregate": ["SUM", "AVG", "COUNT", "MAX", "MIN"],
            "string": ["UPPER", "LOWER", "CONCAT", "SUBSTRING", "TRIM", "LENGTH"],
            "date": ["NOW", "DATE"],
            "math": ["ROUND"],
            "conditional": ["CASE", "COALESCE", "NULLIF"]
        }

        function_pattern = r'\s*(' + r'|'.join(
            [f"{func}\\s*\\(\\s*{basic_expr_pattern}\\s*\\)" for funcs in supported_functions.values() for func in funcs]
        ) + r')\s*'

        return function_pattern

    def _build_complete_pattern(self, function_pattern, basic_expr_pattern, comparison_pattern, logical_pattern):
        """Construct the final regex pattern for calculations."""
        nested_function_pattern = r'(' + function_pattern + r'|' + basic_expr_pattern + r')'
        return (
                r'^' +
                r'(' + nested_function_pattern +
                r'(\s*' + comparison_pattern + nested_function_pattern + r')*' +
                r'(\s*' + logical_pattern + nested_function_pattern + r')*$' +
                r')$'
        )

    def _build_pattern(self, operators):
        """Helper method to build regex pattern for operators."""
        return r'\s*(' + r'|'.join(operators) + r')\s*'

    def _validate_filters(self, filters):
        """Validate filters format."""
        if not isinstance(filters, list):
            logger.error("Filters must be a list.")
            raise InvalidFormatError('filter', 'list')

        for condition in filters:
            if not isinstance(condition, str):
                logger.error(f"Filter condition must be a string. Got: {type(condition).__name__}")
                raise InvalidFormatError('filter condition', 'string')

    def _validate_attribute_keys(self, attr_key, attribute):
        """Check for valid attribute keys."""
        valid_keys = ['name', 'desc', 'calculation', 'filter', 'function', 'synonym']
        for key in attribute.keys():
            if key not in valid_keys:
                logger.error(f"Invalid key '{key}' found in attribute {attr_key}. Valid keys are: {valid_keys}.")
                raise InvalidKeyError(key, valid_keys)

    def _validate_metrics(self, metrics, schema):
        """Validate the structure and values of the metrics."""
        if not isinstance(metrics, dict):
            logger.error("Metrics must be a dictionary.")
            raise InvalidFormatError(metrics, 'dictionary')

        for key, value in metrics.items():
            self._validate_metric(key, value, schema)

    def _validate_metric(self, metric_key, metric, schema):
        """Validate an individual metrics structure and values."""
        if not isinstance(metric, dict):
            logger.error(f"Metric {metric_key} must be a dictionary.")
            raise InvalidFormatError(metric_key, 'dictionary')

        if 'name' not in metric or 'calculation' not in metric:
            if metric_key not in schema['columns']:
                logger.error(f"Metric {metric_key} must contain 'name' or 'calculation' but it's missing.")
                raise MissingKeyError('name or calculation')

        if 'name' in metric and not metric['name']:
            logger.error(f"Metric {metric_key} must have a non-empty 'name'.")
            raise EmptyValueError(metric_key, 'name')
        if 'calculation' in metric and not metric['calculation']:
            logger.error(f"Metric {metric_key} must have a non-empty 'calculation'.")
            raise EmptyValueError(metric_key, 'calculation')

        if 'function' in metric and not isinstance(metric['function'], str):
            logger.error(f"Metric {metric_key} function must be a string.")
            raise EmptyValueError(metric_key, 'function')

        self._validate_calculation(metric['calculation'])
        self._validate_metric_keys(metric_key, metric)

    def _validate_metric_keys(self, metric_key, metric):
        """Check for valid metric keys."""
        valid_keys = ['name', 'calculation', 'function', 'desc', 'filter', 'synonym']
        for key in metric.keys():
            if key not in valid_keys:
                logger.error(f"Invalid key '{key}' found in metric {metric_key}. Valid keys are: {valid_keys}.")
                raise InvalidKeyError(key, valid_keys)
