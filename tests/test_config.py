import pytest
from autoreviewx.core.config import load_config, ConfigError

def test_load_valid_config():
    config = load_config("config.yaml")
    assert config["framework"] == "PICO"

def test_missing_file():
    with pytest.raises(ConfigError):
        load_config("nonexistent.yaml")
