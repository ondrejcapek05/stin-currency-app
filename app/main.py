"""Hlavní vstupní bod FastAPI aplikace."""
from fastapi import FastAPI

app = FastAPI(title="Currency Analyzer")


@app.get("/")
def read_root():
    """Úvodní stránka"""
    return {"message": "Currency Analyzer is running."}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}