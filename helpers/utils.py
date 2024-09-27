import os
import yaml
from logger.log import logger

class DuplicateKeyLoader(yaml.Loader):
    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        if len(mapping) != len(node.value):
            raise yaml.YAMLError(f"Duplicate keys found in YAML file: {node}")
        return mapping

def load_yaml_file(file_path):
    """Load a single YAML file and return its content."""
    try:
        with open(file_path, 'r') as file:
            return yaml.load(file, Loader=DuplicateKeyLoader)
    except yaml.YAMLError as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None  # Return None if there's an error

def _load_files_from_assets(assets_directory):
    """Load all YAML files from the given assets directory."""
    if not os.path.exists(assets_directory):
        logger.error(f"Directory does not exist: {assets_directory}")
        return []

    files = []
    for filename in os.listdir(assets_directory):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            file_path = os.path.join(assets_directory, filename)
            content = load_yaml_file(file_path)
            if content is not None:
                files.append((filename, content))
    return files

def load_schemas_from_assets(base_location):
    """Load all YAML schema files from the specified assets directory."""
    schema_assets_path = os.path.join(base_location, 'schema', 'assets')
    return _load_files_from_assets(schema_assets_path)

def load_semantics_from_assets(base_location):
    """Load all YAML semantics files from the specified assets directory."""
    semantics_assets_path = os.path.join(base_location, 'semantics', 'assets')
    return _load_files_from_assets(semantics_assets_path)