from fastapi import Header, HTTPException

from app.config import load_settings


def verify_api_key(authorization: str | None) -> None:
    settings = load_settings()
    if not settings.get("require_auth"):
        return

    expected = settings.get("api_key") or ""
    if not expected:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": {"message": "Missing or invalid Authorization header"}},
        )

    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(
            status_code=401,
            detail={"error": {"message": "Invalid API key"}},
        )
