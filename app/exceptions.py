"""Vlastní výjimky aplikace."""


class CurrencyAnalyzerError(Exception):
    """Základní výjimka aplikace."""


class ApiError(CurrencyAnalyzerError):
    """Chyba při volání API."""


class ApiResponseError(ApiError):
    """Chybová odpověď z API."""

    def __init__(self, code: int, error_type: str, info: str) -> None:
        self.code = code
        self.error_type = error_type
        self.info = info
        super().__init__(f"API error {code} ({error_type}): {info}")


class ApiConnectionError(ApiError):
    """Chyba při připojení k API."""