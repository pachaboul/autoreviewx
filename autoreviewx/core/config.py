# autoreviewx/core/config.py
import yaml
import os


class ConfigError(Exception):
    """Custom error for config issues."""
    pass


def validate_config(config: dict):
    schema = {
        "title": str,
        "framework": str,
        "inclusion_criteria": list,
        "exclusion_criteria": list,
        "output_format": str,
        "citation_style": str,
        "databases": list,
        "tools_of_interest": list,
        "modalities": list,
        "learning_outcomes": list
    }

    for key, expected_type in schema.items():
        if key not in config:
            raise ConfigError(f"Missing required key: {key}")
        if not isinstance(config[key], expected_type):
            raise ConfigError(f"Key '{key}' must be of type {expected_type.__name__}")

    return True



def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load and validate the review protocol configuration file.

    Args:
        config_path (str): Path to YAML config file.

    Returns:
        dict: Parsed config content.

    Raises:
        ConfigError: If file not found or schema invalid.
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        try:
            config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML parsing error: {e}")

    # Minimal validation
    required_fields = ["title", "framework", "inclusion_criteria", "exclusion_criteria"]
    for field in required_fields:
        if field not in config:
            raise ConfigError(f"Missing required field in config: {field}")

    validate_config(config)
    return config
