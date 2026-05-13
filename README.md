# Currency Analyzer

Webová aplikace pro sledování kurzů měn s denní cache, výpočtem nejsilnější/nejslabší měny a grafem historického vývoje.

## Live demo

[https://stin-currency-app-39mi.onrender.com](https://stin-currency-app-39mi.onrender.com)

## Technologie

- Python 3.13.1, FastAPI
- SQLite přes SQLModel
- Jinja2, Pico.css, Chart.js
- pytest, pytest-cov
- GitHub Actions CI, Render deploy

## Spuštění lokálně

```powershell
git clone https://github.com/ondrejcapek05/stin-currency-app.git
cd stin-currency-app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

V rootu projektu je potřeba vytvořit `.env` soubor s API klíčem pro [exchangerate.host](https://exchangerate.host):
 
```
EXCHANGERATE_API_KEY=tvuj_klic
SESSION_SECRET=tajny_retezec
```
 
Spuštění aplikace:
 
```powershell
uvicorn app.main:app --reload
```
 
Aplikace poběží na `http://localhost:8000`. Výchozí přihlašovací údaje: `admin / stin2026`.
 
## Testy

Aktuální stav: 104 testů, 96 % branch coverage.

```powershell
pytest --cov=app --cov-branch --cov-report=term-missing
```

Testy nevolají reálné API. HTTP klient je testovaný přes mock transport a webové routy používají fake služby přes dependency override.
 
## Architektura
 
- `app/api_client.py` - `ExchangeRateClient` pro komunikaci s API
- `app/rate_service.py` - cache vrstva pro live a historické kurzy
- `app/analytics.py` - výpočty nejsilnější/nejslabší měny, průměru a přepočtu na zvolenou základní měnu
- `app/auth.py` - cookie session a timing-safe porovnání hesla
- `app/settings_service.py` - načítání a ukládání uživatelského nastavení
- `app/logger.py` - logování chyb do databáze
- `app/translations.py` - CS/EN slovníky
- `app/main.py` - hlavní část aplikace, která zpracovává adresy a zobrazuje HTML stránky

## Funkce
 
- Login/logout přes cookie session
- Dashboard: aktuální kurzy, nejsilnější/nejslabší měna, graf 7/30/90 dní, průměr za období
- Settings: výběr základní měny, sledovaných měn a jazyka CS/EN
- Cache 24h pro aktuální kurzy, trvalá cache pro historické kurzy
- Fallback na cache a warning banner při výpadku API
- Chybová stránka, když je cache prázdná a API selže
- Logování API chyb do databáze