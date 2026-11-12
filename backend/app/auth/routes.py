"""Auth API: /api/auth/*"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.dependencies import CurrentUser, get_current_user
from app.auth.jwt import JwtConfigurationError, create_access_token
from app.auth.mongodb import get_auth_db
from app.auth.permissions import permissions_for_roles
from app.auth.rate_limit import check_login_rate_limit, client_ip_from_request
from app.auth.refresh_tokens import RefreshTokenService
from app.auth.schemas import LoginRequest, TokenResponse, UserMeResponse
from app.auth.service import AuthenticationError, OrgAccessError, authenticate_user, create_session_tokens
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, settings: Settings, raw_token: str) -> None:
    max_age = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path="/api/auth/refresh",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.AUTH_REFRESH_COOKIE_NAME,
        path="/api/auth/refresh",
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    ip = client_ip_from_request(dict(request.headers), request.client.host if request.client else None)
    check_login_rate_limit(ip)

    db = get_auth_db(settings)
    try:
        ctx = authenticate_user(db, body.email, body.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except OrgAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    try:
        access, expires_in, refresh_raw = create_session_tokens(
            db,
            settings,
            user=ctx["user"],
            membership=ctx["membership"],
            org=ctx["org"],
            device_id=request.headers.get("x-device-id") or str(uuid4()),
        )
    except JwtConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    _set_refresh_cookie(response, settings, refresh_raw)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    raw = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    db = get_auth_db(settings)
    refresh_svc = RefreshTokenService(db, settings)
    device_id = request.headers.get("x-device-id") or str(uuid4())

    try:
        new_raw, session_id, _family, user_id = refresh_svc.rotate(raw, device_id=device_id)
    except ValueError as exc:
        _clear_refresh_cookie(response, settings)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db["users"].find_one({"_id": user_id})
    if not user or user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    membership = db["org_memberships"].find_one({"user_id": user_id, "status": "active"})
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active organization")

    roles = list(membership.get("roles") or [])
    permissions = permissions_for_roles(roles)
    try:
        access, expires_in = create_access_token(
            settings,
            user_id=user_id,
            org_id=membership["org_id"],
            roles=roles,
            permissions=permissions,
            session_id=session_id,
        )
    except JwtConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    _set_refresh_cookie(response, settings, new_raw)
    return TokenResponse(access_token=access, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    raw = request.cookies.get(settings.AUTH_REFRESH_COOKIE_NAME)
    if raw:
        RefreshTokenService(get_auth_db(settings), settings).revoke_token(raw)
    _clear_refresh_cookie(response, settings)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    response: Response,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    RefreshTokenService(get_auth_db(settings), settings).revoke_all_for_user(user.user_id)
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserMeResponse)
def me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserMeResponse:
    db = get_auth_db(settings)
    org = db["organizations"].find_one({"_id": user.org_id})
    return UserMeResponse(
        user_id=user.user_id,
        email=user.email,
        org_id=user.org_id,
        org_name=org.get("name", "") if org else "",
        roles=user.roles,
        permissions=user.permissions,
        status="active",
    )
