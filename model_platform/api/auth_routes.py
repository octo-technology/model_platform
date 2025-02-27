from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from model_platform.domain.use_cases.auth_usecases import get_current_user, login_for_access_token
router = APIRouter()

@router.post("/token")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):

    token_info_dict = await login_for_access_token(form_data)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {token_info_dict .get("access_token")}",
        httponly=True,
        samesite="Strict",  # Protection CSRF
        secure=False  # si True : Indique au navigateur d'envoyer le cookie uniquement sur des connexions HTTPS sécurisées.
    )

    return {"status": "Authentificated"}


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
