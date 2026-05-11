"""Autentizace aplikace."""
import secrets

from fastapi import HTTPException, Request, status

from app.config import Settings


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    """Ověří přihlašovací údaje."""
    user_ok = secrets.compare_digest(username, settings.admin_username)
    pass_ok = secrets.compare_digest(password, settings.admin_password)
    return user_ok and pass_ok


def require_login(request: Request) -> str:
    """Vrátí přihlášeného uživatele."""
    username = request.session.get("user")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return username