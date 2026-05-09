"""Konfigurace aplikace"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Konfigurace aplikace načtená z environment proměnných."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("EXCHANGERATE_API_KEY", "")
        self.api_base_url: str = os.getenv(
            "EXCHANGERATE_API_URL",
            "https://api.exchangerate.host",
        )

    def validate(self) -> None:
        """Ověří, že povinné proměnné jsou nastavené."""
        if not self.api_key:
            raise ValueError(
                "EXCHANGERATE_API_KEY není nastaven. "
                "Vytvoř .env soubor podle .env.example."
            )


def get_settings() -> Settings:
    """Vrátí nastavení aplikace."""
    return Settings()