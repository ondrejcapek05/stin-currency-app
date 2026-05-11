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
        self.admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password: str = os.getenv("ADMIN_PASSWORD", "stin2026")
        self.session_secret: str = os.getenv(
            "SESSION_SECRET",
            "change-me-in-production",
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