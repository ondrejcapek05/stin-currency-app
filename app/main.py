"""Hlavní vstupní bod FastAPI aplikace."""
from collections.abc import Generator
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
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
from app.exceptions import ApiConnectionError, ApiResponseError
from app.logger import log_error
from app.models import ExchangeRate
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
        {"lang": "cs", "error": False},
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
            {"lang": "cs", "error": True},
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
    lang = user_settings.language
    selected = [c for c in user_settings.selected_currencies.split(",") if c]
    base = user_settings.base_currency
    display_symbols = [c for c in selected if c != base]

    # USD se z API netahá, jeho kurz vůči USD je 1.0
    fetch_symbols = list(dict.fromkeys(
        [c for c in display_symbols if c != "USD"]
        + ([base] if base != "USD" else [])
    ))

    fallback_warning: str | None = None
    api_rates: dict[str, float] = {}

    if fetch_symbols:
        try:
            api_rates = service.get_live_rates(fetch_symbols)
        except (ApiConnectionError, ApiResponseError) as exc:
            log_error(session, f"API failure on live rates: {exc}")
            api_rates, last_date = _load_cached_live(session, fetch_symbols)
            # Bez base měny nejde přepočítat fallback data
            missing_base = base != "USD" and base not in api_rates
            if not api_rates or missing_base or last_date is None:
                return templates.TemplateResponse(
                    request,
                    "error.html",
                    {"lang": lang},
                    status_code=503,
                )
            fallback_warning = t("dashboard.fallback_warning", lang).format(
                date=last_date.isoformat()
            )

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

    api_period: dict[date, dict[str, float]] = {}
    if period_fetch:
        try:
            api_period = service.get_rates_for_period(start, end, period_fetch)
        except (ApiConnectionError, ApiResponseError) as exc:
            log_error(session, f"API failure on period rates: {exc}")
            api_period = _load_cached_period(session, period_fetch, start, end)

    # Doplnění USD staticky, nevyžaduje API
    period_usd = {d: {**day, "USD": 1.0} for d, day in api_period.items()}

    # přeskočení dnů bez kurzu základní měny (jinak by convert_to_base spadl)
    period_in_base: dict[date, dict[str, float]] = {}
    for day, day_rates in period_usd.items():
        if base == "USD" or base in day_rates:
            period_in_base[day] = convert_to_base(day_rates, base)

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
            "lang": lang,
            "fallback_warning": fallback_warning,
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


def _load_cached_live(
    session: Session,
    symbols: list[str],
) -> tuple[dict[str, float], date | None]:
    """Načte poslední dostupné kurzy z cache."""
    rows = session.exec(
        select(ExchangeRate)
        .where(ExchangeRate.base == "USD", ExchangeRate.target.in_(symbols))
        .order_by(ExchangeRate.date.desc())
    ).all()

    rates: dict[str, float] = {}
    last_date: date | None = None
    for row in rows:
        if row.target not in rates:
            rates[row.target] = row.rate
            if last_date is None or row.date > last_date:
                last_date = row.date
    return rates, last_date


def _load_cached_period(
    session: Session,
    symbols: list[str],
    start: date,
    end: date,
) -> dict[date, dict[str, float]]:
    """Načte kurzy za období z cache."""
    rows = session.exec(
        select(ExchangeRate).where(
            ExchangeRate.base == "USD",
            ExchangeRate.target.in_(symbols),
            ExchangeRate.date >= start,
            ExchangeRate.date <= end,
        )
    ).all()

    result: dict[date, dict[str, float]] = {}
    for row in rows:
        result.setdefault(row.date, {})[row.target] = row.rate
    return result


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
            "lang": user_settings.language,
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
    language: str = Form(...),
):
    """Uloží uživatelské nastavení."""
    selected_currencies = selected_currencies or []

    error = None
    if language not in ("cs", "en"):
        error = "settings.error_invalid_language"
    elif base_currency not in AVAILABLE_CURRENCIES:
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
                "lang": user_settings.language,
                "settings": user_settings,
                "selected_list": selected_currencies,
                "available_currencies": AVAILABLE_CURRENCIES,
                "saved": False,
                "error": error,
            },
            status_code=400,
        )

    user_settings = update_settings(
        session, base_currency, selected_currencies, language
    )
    selected_list = [c for c in user_settings.selected_currencies.split(",") if c]

    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "lang": user_settings.language,
            "settings": user_settings,
            "selected_list": selected_list,
            "available_currencies": AVAILABLE_CURRENCIES,
            "saved": True,
            "error": None,
        },
    )