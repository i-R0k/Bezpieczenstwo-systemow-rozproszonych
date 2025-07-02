# VetClinic/API/tests/test_config.py
import sys
import importlib
import pytest
import pathlib

MODULE_PATH = "vetclinic_api.core.config"

def unload_module():
    if MODULE_PATH in sys.modules:
        del sys.modules[MODULE_PATH]

@pytest.fixture(autouse=True)
def block_dotenv(monkeypatch):
    # Prevent actual .env loading in tests
    monkeypatch.setenv("DOTENV_PATH", "")
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)


def test_config_file_not_found(monkeypatch):
    unload_module()
    # Always pretend .env does not exist
    monkeypatch.setattr(pathlib.Path, "exists", lambda self: False)
    with pytest.raises(FileNotFoundError):
        importlib.import_module(MODULE_PATH)


def test_config_loads_env_and_defaults(monkeypatch):
    unload_module()
    # Pretend .env exists
    monkeypatch.setattr(pathlib.Path, "exists", lambda self: True)
    # Set environment variables
    monkeypatch.setenv("SECRET_KEY", "my_secret_123")
    monkeypatch.setenv("SMTP_HOST", "smtp.test.pl")
    monkeypatch.setenv("SMTP_PORT", "2527")
    monkeypatch.setenv("SMTP_USER", "user1")
    monkeypatch.setenv("SMTP_PASS", "pass1")
    monkeypatch.setenv("SMTP_FROM", "from@test.pl")
    # Import and reload module to apply monkeypatches
    config = importlib.import_module(MODULE_PATH)
    importlib.reload(config)

    # Default and overridden values
    assert config.API_BASE_URL == "http://127.0.0.1:8000"
    assert config.SECRET_KEY == "my_secret_123"
    assert config.SMTP_HOST == "smtp.test.pl"
    assert isinstance(config.SMTP_PORT, int) and config.SMTP_PORT == 2527
    assert config.SMTP_USER == "user1"
    assert config.SMTP_PASS == "pass1"
    assert config.SMTP_FROM == "from@test.pl"
    assert config.DATABASE_URL.startswith("sqlite:///")
    assert config.DATABASE_URL.endswith("vetclinic.db")
