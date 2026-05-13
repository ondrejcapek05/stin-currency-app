"""Překlady aplikace."""

TRANSLATIONS: dict[str, dict[str, str]] = {
    "cs": {
        "app.title": "Přehled měnových kurzů",
        "nav.dashboard": "Přehled",
        "nav.settings": "Nastavení",
        "nav.logout": "Odhlásit",
        "login.title": "Přihlášení",
        "login.username": "Uživatelské jméno",
        "login.password": "Heslo",
        "login.submit": "Přihlásit",
        "login.error_invalid": "Neplatné přihlašovací údaje",
        "dashboard.title": "Aktuální kurzy",
        "dashboard.strongest": "Nejsilnější měna",
        "dashboard.weakest": "Nejslabší měna",
        "dashboard.chart_title": "Vývoj kurzu",
        "dashboard.currency": "Měna",
        "dashboard.rate": "Kurz",
        "dashboard.period": "Období",
        "dashboard.period_7": "7 dní",
        "dashboard.period_30": "30 dní",
        "dashboard.period_90": "90 dní",
        "dashboard.average": "Průměr za období",
        "settings.title": "Nastavení",
        "settings.base_currency": "Základní měna",
        "settings.selected_currencies": "Sledované měny",
        "settings.save": "Uložit",
        "settings.saved": "Nastavení uloženo",
        "settings.error_no_currencies": "Vyberte alespoň jednu měnu",
        "settings.error_need_non_base": "Vyberte alespoň jednu měnu jinou než základní",
        "settings.error_invalid_base": "Neplatná základní měna",
        "settings.error_invalid_currency": "Neplatná měna ve výběru",
    },
}


def t(key: str, lang: str = "cs") -> str:
    """Vrátí překlad podle klíče."""
    return TRANSLATIONS.get(lang, {}).get(key, key)