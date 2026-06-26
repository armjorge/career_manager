import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.config import get_settings

router = APIRouter(tags=["auth"])


class SignInBody(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class SignUpBody(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=8)


def _auth_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                return message
    except Exception:
        pass
    return "Authentication failed"


def _looks_like_jwt(token: str) -> bool:
    return token.count(".") == 2


async def _fetch_jwt(client: httpx.AsyncClient, auth_url: str) -> str:
    session_resp = await client.get(f"{auth_url}/get-session")
    if session_resp.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Failed to establish session", "code": "UNAUTHORIZED"},
        )

    jwt_header = session_resp.headers.get("set-auth-jwt")
    if jwt_header and _looks_like_jwt(jwt_header):
        return jwt_header

    try:
        payload = session_resp.json()
    except Exception:
        payload = None

    if isinstance(payload, dict):
        session = payload.get("session")
        if isinstance(session, dict):
            token = session.get("token")
            if isinstance(token, str) and _looks_like_jwt(token):
                return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": "No JWT returned from auth provider", "code": "UNAUTHORIZED"},
    )


def _map_user(raw: dict) -> dict:
    return {
        "id": str(raw.get("id", "")),
        "email": str(raw.get("email", "")),
        "name": raw.get("name") if isinstance(raw.get("name"), str) else None,
        "emailVerified": bool(raw.get("emailVerified")),
    }


@router.post("/auth/sign-in")
async def sign_in(body: SignInBody) -> dict:
    settings = get_settings()
    auth_url = settings.neon_auth_url.rstrip("/")

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.post(
            f"{auth_url}/sign-in/email",
            json={"email": body.email, "password": body.password},
        )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail={"message": _auth_error_message(response), "code": "SIGN_IN_FAILED"},
            )

        payload = response.json()
        user = payload.get("user") if isinstance(payload, dict) else None
        if not isinstance(user, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"message": "Sign in failed", "code": "SIGN_IN_FAILED"},
            )

        token = await _fetch_jwt(client, auth_url)
        return {"token": token, "user": _map_user(user)}


@router.post("/auth/sign-up")
async def sign_up(body: SignUpBody) -> dict:
    settings = get_settings()
    auth_url = settings.neon_auth_url.rstrip("/")

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.post(
            f"{auth_url}/sign-up/email",
            json={"name": body.name, "email": body.email, "password": body.password},
        )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail={"message": _auth_error_message(response), "code": "SIGN_UP_FAILED"},
            )

        payload = response.json()
        user = payload.get("user") if isinstance(payload, dict) else None
        if not isinstance(user, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Sign up failed", "code": "SIGN_UP_FAILED"},
            )

        token = await _fetch_jwt(client, auth_url)
        return {"token": token, "user": _map_user(user)}
