from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def register_error_handlers(app: FastAPI) -> None:
    """Register all global error handlers on the app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Return a human-readable 429 with reset info from the Retry-After header."""
        if exc.status_code == 429:
            retry_after = exc.headers.get("Retry-After", "3600") if exc.headers else "3600"
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
                headers=dict(exc.headers) if exc.headers else {},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(_request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
