from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import get_settings

_bearer = HTTPBearer(auto_error=False)
_jwks_client: PyJWKClient | None = None


def _unauthorized(message: str, code: str = "UNAUTHORIZED") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"message": message, "code": code},
    )


def _claims_from_apigw(request: Request) -> dict | None:
    event = request.scope.get("aws.event") or {}
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims")
    )
    return claims if isinstance(claims, dict) and claims else None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    settings = get_settings()
    if not settings.cognito_user_pool_id:
        raise _unauthorized("Cognito user pool is not configured")
    if _jwks_client is None:
        jwks_url = (
            f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
            f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
        )
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def _verify_cognito_token(token: str) -> dict:
    settings = get_settings()
    if not settings.cognito_user_pool_id or not settings.cognito_client_id:
        raise _unauthorized("Cognito is not configured for local JWT validation")

    issuer = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}"
    )
    signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.cognito_client_id,
        issuer=issuer,
        options={"verify_at_hash": False},
    )


def _user_id_from_claims(claims: dict) -> UUID:
    sub = claims.get("sub")
    if not sub:
        raise _unauthorized("Token missing subject claim")
    try:
        return UUID(str(sub))
    except ValueError as exc:
        raise _unauthorized("Token subject is not a valid UUID") from exc


def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UUID:
    """
    Resolve the authenticated Cognito user id (sub).

    - On Lambda behind API Gateway JWT authorizer: use injected claims.
    - Locally (uvicorn): validate the Bearer ID token against Cognito JWKS.
    """
    claims = _claims_from_apigw(request)
    if claims:
        return _user_id_from_claims(claims)

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Missing or invalid authorization header")

    try:
        payload = _verify_cognito_token(credentials.credentials)
        return _user_id_from_claims(payload)
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("Token has expired", code="TOKEN_EXPIRED") from exc
    except jwt.PyJWTError as exc:
        raise _unauthorized("Invalid access token") from exc
