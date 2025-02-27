from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from model_platform.domain.use_cases import user_usecases
from model_platform.domain.ports.user_handler import UserHandler

from model_platform.domain.use_cases.auth_usecases import get_current_admin, get_current_user, get_user_adapter

router = APIRouter()

@router.get("/get")
def get_user(
    email: str,
    password: str,
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    user = user_usecases.get_user(user_adapter, email, password)
    return JSONResponse(
        content={
            "email": user.email, 
            "role": user.role
        },
        media_type="application/json"
    )
    

@router.post("/add")
async def create_user(
        email: str,
        password: str,
        role: str,
        user_adapter: UserHandler = Depends(get_user_adapter),
        current_admin: dict = Depends(get_current_admin)
    ) -> JSONResponse :
    
    success = user_usecases.add_user(
        user_adapter=user_adapter,
        email=email,
        password=password,
        role=role
    )
    return JSONResponse(
        content={
            "status":success
        },
        media_type="application/json"
    )