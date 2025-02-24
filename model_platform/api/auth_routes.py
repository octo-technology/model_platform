from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from .auth import get_current_admin, get_current_user, login_for_access_token

router = APIRouter()


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await login_for_access_token(form_data)


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/admin-only")
async def admin_only_route(current_admin: dict = Depends(get_current_admin)):
    return {"message": "Bienvenue Admin !"}
