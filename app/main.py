"""Hlavní vstupní bod FastAPI aplikace."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from starlette.middleware.sessions import SessionMiddleware

from app.auth import require_login, verify_credentials
from app.config import Settings, get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializace databáze při startu aplikace."""
    init_db()
    yield


app = FastAPI(title="Currency Analyzer", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(SessionMiddleware, secret_key=_settings.session_secret)


@app.get("/")
def read_root():
    """Úvodní stránka"""
    return {"message": "Currency Analyzer is running."}


@app.get("/health")
def health_check():
    """Kontrola stavu aplikace."""
    return {"status": "ok"}


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    settings: Settings = Depends(get_settings),
):
    """Přihlásí uživatele."""
    if not verify_credentials(username, password, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    request.session["user"] = username
    return {"status": "logged_in"}


@app.post("/logout")
def logout(request: Request):
    """Odhlásí uživatele."""
    request.session.clear()
    return {"status": "logged_out"}
 

@app.get("/protected")
def protected(user: str = Depends(require_login)):
    """Vrátí přihlášeného uživatele."""
    return {"user": user}