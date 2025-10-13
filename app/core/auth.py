import os
from fastapi import Header, HTTPException, status


API_KEY_ENV = "API_KEY"
DEFAULT_API_KEY = "oneal_demo_token"


def get_expected_api_key() -> str:
    return os.getenv(API_KEY_ENV, DEFAULT_API_KEY)


async def api_key_auth(x_api_key: str = Header(default=None, alias="X-API-Key")) -> None:
    expected = get_expected_api_key()
    if x_api_key is None or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
