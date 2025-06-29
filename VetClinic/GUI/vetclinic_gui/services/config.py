from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # URL do lokalnego node'a blockchain (Ganache/Hardhat)
    BLOCKCHAIN_URL: str = "http://127.0.0.1:8545"
    # Adres i ABI kontraktu MedicalRecord (nadpisywane plikiem JSON)
    CONTRACT_ADDRESS: str = ""
    CONTRACT_ABI_PATH: str = ""

    class Config:
        # Wczytuj zmienne z .env, bez prefiksu
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_prefix = ""

# Instancja ustawień
settings = Settings()