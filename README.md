# Currency Analyzer

Webová aplikace pro práci s měnovými kurzy z REST API exchangerate.host.

**Live demo:** https://stin-currency-app-39mi.onrender.com/

## Technologie
- Python 3.13
- FastAPI
- pytest

## Lokální spuštění

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev app/main.py
```

Aplikace poběží na http://localhost:8000

## Testy

```bash
pytest --cov=app --cov-branch --cov-report=term-missing
```