import os
from logger.log import logger, log_file_path

from helpers.utils import load_schemas_from_assets, load_semantics_from_assets
from validator import SchemaValidator, SemanticsValidator

def validate_schemas(schemas):
    for filename, schema in schemas:
        logger.info(f"----------------------------------------------------------------")
        logger.info(f"Validating schema from {filename}...")
        try:
            validator = SchemaValidator(filename, schema)
            validator.validate()
        except Exception as e:
            logger.error(f"Schema validation failed for {filename}: {e}")
            logger.info(f"----------------------------------------------------------------")


def validate_semantics(semantics_files, schema_files):
    """Validate each semantics file and log results."""
    for filename, semantics in semantics_files:
        logger.info(f"----------------------------------------------------------------")
        logger.info(f"Validating semantics from {filename}...")
        try:
            validator = SemanticsValidator(filename, semantics)
            validator.validate(schema_files)
            logger.info(f"{filename} semantics is valid.")
        except Exception as e:
            logger.error(f"Semantics validation failed for {filename}: {e}")
        logger.info(f"----------------------------------------------------------------")


def load_metadata_files(metadata_directory) -> tuple[dict, dict]:
    """Load schemas and semantics from the given metadata directory."""
    # Check if the metadata directory exists
    if not os.path.exists(metadata_directory):
        logger.error(f"Directory does not exist: {metadata_directory}")
        raise FileNotFoundError(f"Directory does not exist: {metadata_directory}")

    logger.info("Extracting schemas files...")
    schemas_files = load_schemas_from_assets(metadata_directory)
    logger.info("Extraction completed. Following schema files are found: ")
    if schemas_files is not None:
        for i, file in enumerate(schemas_files):
            logger.info(f"- {file[0]}")

    logger.info("Extracting semantics files...")
    semantics_files = load_semantics_from_assets(metadata_directory)
    logger.info("Extraction completed. Following semantics files are found: ")
    if semantics_files is not None:
        for i, file in enumerate(semantics_files):
            logger.info(f"- {file[0]}")


    logger.info(f"Loaded {len(schemas_files)} schema(s) and {len(semantics_files)} semantics file(s) from {metadata_directory}.")
    return schemas_files, semantics_files

def main():
    logger.info("Inteliome Metadata Validator: Starting metadata validation...")
    metadata_directory = '_metadata/hrm'
    try:
        schemas_files, semantics_files = load_metadata_files(metadata_directory)
        validate_schemas(schemas_files)
        validate_semantics(semantics_files, schemas_files)
        logger.info("\u2714 \u2714 \u2714 Validation completed! Check the logs for details. \u2714 \u2714 \u2714")
        logger.info(f"Log file is {log_file_path}")
    except Exception as e:
        logger.error(f"\u274C \u274C \u274C Validation failed - An error occurred: {e} \u274C \u274C \u274C")

if __name__ == "__main__":
    main()
