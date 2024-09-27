import re
from logger.log import logger

from exceptions.schema_validation_error import InvalidFormatError, MissingKeyError, EmptyValueError, InvalidKeyError
from validator.base_validator import BaseValidator


class SchemaValidator(BaseValidator):
    def __init__(self, schema_name, schema):
        super().__init__()
        self.schema = schema
        self.schema_name = schema_name

    def validate(self, files=None):
        """Validate the overall schema structure."""
        try:
            self._check_required_keys()
            self._validate_table_info(self.schema['table_info'])
            self._validate_columns(self.schema['columns'])
            logger.info(f"Schema '{self.schema_name}' validation passed!")
        except MissingKeyError as e:
            logger.error(f"Schema '{self.schema_name}' Validation Error: {e}")
        except EmptyValueError as e:
            logger.error(f"Schema '{self.schema_name}' Validation Error: {e}")
        except InvalidFormatError as e:
            logger.error(f"Schema '{self.schema_name}' Validation Error: {e}")
        except InvalidKeyError as e:
            logger.error(f"Schema '{self.schema_name}' Validation Error: {e}")
        except Exception as e:
            logger.exception(f"An unexpected error occurred during schema '{self.schema_name}' validation")

    def _check_required_keys(self):
        """Ensure all required keys are present in the schema."""
        required_keys = ['subject_area', 'table_info', 'columns']
        for key in required_keys:
            if key not in self.schema:
                raise MissingKeyError(key)

    def _validate_columns(self, columns):
        """Validate the structure and values of the columns."""
        if not isinstance(columns, dict):
            raise InvalidFormatError('columns', 'dictionary')

        column_ids = set()
        tables_in_schema = {table['table'] for table in self.schema['table_info']}

        for column_id, column in columns.items():
            if column_id in column_ids:
                raise InvalidKeyError(column_id, "unique column IDs")

            self._validate_column(column_id, column, column_ids, tables_in_schema)
            column_ids.add(column_id)

    def _validate_column(self, column_id, column, column_ids, tables_in_schema):
        """Validate an individual column's structure and values."""
        if not isinstance(column, dict):
            raise InvalidFormatError(column_id, 'dictionary')

        # Check for nested structures
        if any(isinstance(v, dict) for v in column.values()):
            raise InvalidFormatError(column_id, 'no nested dictionaries allowed')

        self._check_unique_column_id(column_id, column_ids)
        self._check_column_format(column_id, column)
        self._check_required_column_keys(column_id, column)
        self._check_indentation(column_id, column)

        # Check 'primary_key' if it exists
        if 'primary_key' in column and not isinstance(column['primary_key'], bool):
            raise InvalidFormatError('primary_key', 'boolean')

        # Validate table reference if it exists
        if 'table' in column:
            self.validate_table_reference(column['table'], tables_in_schema)

    @staticmethod
    def _check_indentation(column_id, column):
        """Check for proper indentation in the column dictionary."""
        keys = list(column.keys())
        expected_keys = ['name', 'type', 'column', 'desc', 'primary_key']

        for key in keys:
            if key not in expected_keys:
                raise InvalidKeyError(key, expected_keys)

        # Check for required keys to have values
        for key in expected_keys:
            if key in column and (column[key] is None or (isinstance(column[key], str) and not column[key].strip())):
                raise EmptyValueError(column_id, key)

    @staticmethod
    def _check_unique_column_id(column_id, column_ids):
        """Ensure column_id is unique."""
        if column_id in column_ids:
            raise InvalidKeyError(column_id, "unique column IDs")
        column_ids.add(column_id)

    @staticmethod
    def _check_column_format(column_id, column):
        """Validate the format of column_id and other properties."""
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', column_id):
            raise InvalidFormatError(column_id, 'valid format')

    @staticmethod
    def _check_required_column_keys(column_id, column):
        """Ensure all required keys in a column are present and non-empty."""
        required_keys = ['name', 'type', 'column', 'desc']
        for key in required_keys:
            if key not in column or not column[key]:
                raise EmptyValueError(column_id, key)

    def _validate_table_info(self, table_info):
        """Validate the structure and values of the table information."""
        if not isinstance(table_info, list):
            raise InvalidFormatError('table_info', 'list')

        for table in table_info:
            self._validate_table_entry(table)

    def _validate_table_entry(self, table):
        """Validate an individual table entry."""
        if not isinstance(table, dict):
            raise InvalidFormatError('table_info entry', 'dictionary')

        # Check for required keys
        if 'table' not in table:
            raise MissingKeyError('table')
        if table['table'] is None:
            raise EmptyValueError('table', 'table_info')
        if 'joins' not in table:
            raise MissingKeyError('joins')

        # Check indentation
        if isinstance(table['joins'], list) and any(isinstance(j, dict) for j in table['joins']):
            raise InvalidFormatError('joins', 'list of strings')

        self._validate_joins(table['joins'], table['table'])

    @staticmethod
    def _validate_joins(joins, table_name):
        """Validate the format of join conditions."""
        if not isinstance(joins, list):
            raise InvalidFormatError('joins', 'list')

        if len(joins) == 0:  # Accept empty joins
            return

        for condition in joins:
            if not isinstance(condition, str) or not re.match(r'^[\w\.]+ = [\w\.]+$', condition):
                raise InvalidFormatError('join condition', 'string of format "table.column = table.column"')

    @staticmethod
    def validate_table_reference(table, tables_in_schema):
        """Validate the table references in columns."""
        if isinstance(table, str):
            if table not in tables_in_schema:
                raise MissingKeyError(table)
        elif isinstance(table, list):
            for t in table:
                if t not in tables_in_schema:
                    raise MissingKeyError(t)
        else:
            raise InvalidFormatError('table', 'string or list of strings')
