"""Hlavní vstupní bod FastAPI aplikace."""
from collections.abc import Generator
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from starlette.middleware.sessions import SessionMiddleware

from app.analytics import (
    average_rate,
    convert_to_base,
    strongest_currency,
    weakest_currency,
)
from app.api_client import ExchangeRateClient
from app.auth import require_login, verify_credentials
from app.config import Settings, get_settings
from app.database import get_session, init_db
from app.rate_service import RateService
from app.settings_service import (
    AVAILABLE_CURRENCIES,
    get_or_create_settings,
    update_settings,
)
from app.translations import t


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Inicializace databáze při startu aplikace."""
    init_db()
    yield


app = FastAPI(title="Currency Analyzer", lifespan=lifespan)

settings = get_settings()
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["t"] = t
templates.env.globals["lang"] = "cs"


def get_db_session() -> Generator[Session, None, None]:
    """Vrátí databázovou session pro FastAPI."""
    yield from get_session()


def get_rate_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> RateService:
    """Vrátí RateService s nakonfigurovaným klientem."""
    client = ExchangeRateClient(settings=settings)
    return RateService(client=client, session=session)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Přesměrování podle stavu přihlášení."""
    if request.session.get("user"):
        return RedirectResponse(url="/dashboard", status_code=303)

    return RedirectResponse(url="/login", status_code=303)


@app.get("/health")
async def health():
    """Kontrola stavu aplikace."""
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Zobrazí přihlašovací formulář."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": False},
    )


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    settings: Settings = Depends(get_settings),
):
    """Přihlásí uživatele."""
    if not verify_credentials(username, password, settings):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": True},
            status_code=401,
        )

    request.session["user"] = username
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/logout")
async def logout(request: Request):
    """Odhlásí uživatele."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    symbol: str | None = None,
    period: int = 7,
    _user: str = Depends(require_login),
    session: Session = Depends(get_db_session),
    service: RateService = Depends(get_rate_service),
):
    """Zobrazí aktuální kurzy a graf vývoje."""
    user_settings = get_or_create_settings(session)
    selected = [c for c in user_settings.selected_currencies.split(",") if c]
    base = user_settings.base_currency
    display_symbols = [c for c in selected if c != base]

    # USD se z API netahá, jeho kurz vůči USD je 1.0
    fetch_symbols = list(dict.fromkeys(
        [c for c in display_symbols if c != "USD"]
        + ([base] if base != "USD" else [])
    ))

    api_rates = service.get_live_rates(fetch_symbols) if fetch_symbols else {}
    live_usd = {**api_rates, "USD": 1.0}
    rates_all = convert_to_base(live_usd, base)
    rates = {c: rates_all[c] for c in display_symbols if c in rates_all}

    strongest = strongest_currency(rates) if rates else ""
    weakest = weakest_currency(rates) if rates else ""

    chart_choices = list(rates.keys())
    chart_symbol = symbol if symbol in chart_choices else strongest
    period = period if period in (7, 30, 90) else 7

    end = date.today()
    start = end - timedelta(days=period - 1)

    period_fetch = list(dict.fromkeys(
        ([chart_symbol] if chart_symbol and chart_symbol != "USD" else [])
        + ([base] if base != "USD" else [])
    ))

    api_period = service.get_rates_for_period(start, end, period_fetch) if period_fetch else {}

    # USD doplníme staticky, nevyžaduje API
    period_usd = {d: {**day, "USD": 1.0} for d, day in api_period.items()}
    period_in_base = {d: convert_to_base(day, base) for d, day in period_usd.items()}

    sorted_dates = sorted(period_in_base.keys())
    chart_labels = [d.isoformat() for d in sorted_dates]
    chart_data = [period_in_base[d].get(chart_symbol) for d in sorted_dates]

    chart_average: float | None = None
    if chart_symbol and any(chart_symbol in day for day in period_in_base.values()):
        chart_average = average_rate(period_in_base, chart_symbol)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "base_currency": base,
            "rates": rates,
            "strongest": strongest,
            "weakest": weakest,
            "chart_choices": chart_choices,
            "chart_symbol": chart_symbol,
            "period": period,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "chart_average": chart_average,
        },
    )


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    _user: str = Depends(require_login),
    session: Session = Depends(get_db_session),
):
    """Zobrazí formulář s uživatelským nastavením."""
    user_settings = get_or_create_settings(session)
    selected_list = [c for c in user_settings.selected_currencies.split(",") if c]

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings": user_settings,
            "selected_list": selected_list,
            "available_currencies": AVAILABLE_CURRENCIES,
            "saved": False,
            "error": None,
        },
    )


@app.post("/settings", response_class=HTMLResponse)
async def settings_save(
    request: Request,
    _user: str = Depends(require_login),
    session: Session = Depends(get_db_session),
    base_currency: str = Form(...),
    selected_currencies: list[str] | None = Form(default=None),
):
    """Uloží uživatelské nastavení."""
    selected_currencies = selected_currencies or []

    error = None
    if base_currency not in AVAILABLE_CURRENCIES:
        error = "settings.error_invalid_base"
    elif not selected_currencies:
        error = "settings.error_no_currencies"
    elif any(c not in AVAILABLE_CURRENCIES for c in selected_currencies):
        error = "settings.error_invalid_currency"
    elif not [c for c in selected_currencies if c != base_currency]:
        error = "settings.error_need_non_base"

    if error:
        user_settings = get_or_create_settings(session)
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "settings": user_settings,
                "selected_list": selected_currencies,
                "available_currencies": AVAILABLE_CURRENCIES,
                "saved": False,
                "error": error,
            },
            status_code=400,
        )

    user_settings = update_settings(session, base_currency, selected_currencies)
    selected_list = [c for c in user_settings.selected_currencies.split(",") if c]

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings": user_settings,
            "selected_list": selected_list,
            "available_currencies": AVAILABLE_CURRENCIES,
            "saved": True,
            "error": None,
        },
    )