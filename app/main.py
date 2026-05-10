"""Hlavní vstupní bod FastAPI aplikace."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializace databáze při startu aplikace."""
    init_db()
    yield


app = FastAPI(title="Currency Analyzer", lifespan=lifespan)


@app.get("/")
def read_root():
    """Úvodní stránka"""
    return {"message": "Currency Analyzer is running."}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}