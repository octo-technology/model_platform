from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from model_platform.domain.use_cases.auth_usecases import get_current_user, login_for_access_token
router = APIRouter()

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await login_for_access_token(form_data)


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
