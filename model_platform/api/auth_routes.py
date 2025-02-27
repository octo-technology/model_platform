from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from .auth import get_current_admin, get_current_user, login_for_access_token, get_user_adapter

from model_platform.domain.use_cases import user_usecases
from model_platform.domain.entities.user_input import UserInput
from model_platform.domain.ports.user_handler import UserHandler

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


@router.get("/user/get")
def get_user(
    email: str,
    password: str,
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    user_input = UserInput(
        email = email,
        password = password
    )
    user = user_usecases.get_user(user_adapter, user_input)
    return JSONResponse(
        content={"email": user.email, "role": user.role},
        media_type="application/json"
    )
    

@router.post("/user/add")
async def create_user(
        email: str,
        password: str,
        role: str,
        user_adapter: UserHandler = Depends(get_user_adapter),
        current_admin: dict = Depends(get_current_admin)
    ) -> JSONResponse :
    user_input = UserInput(
        email = email,
        password = password
    )
    success = user_usecases.add_user(
        user_adapter=user_adapter,
        user_input=user_input,
        role=role
    )
    return JSONResponse(
        content={"status":success},
        media_type="application/json"
    )