from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from model_platform.domain.entities.role import Role
from model_platform.domain.ports.user_handler import UserHandler
from model_platform.domain.use_cases import user_usecases
from model_platform.domain.use_cases.auth_usecases import get_current_user, get_user_adapter

router = APIRouter()


@router.get("/get")
def get_user(
    email: str,
    password: str,
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
):
    user = user_usecases.get_user(user_adapter, email, password)
    if user is None:
        raise HTTPException(status_code=403, detail="User does not exist")
    return JSONResponse(content={"email": user.email, "role": user.role}, media_type="application/json")


@router.post("/add")
async def create_user(
    email: str,
    password: str,
    role: str,
    user_adapter: UserHandler = Depends(get_user_adapter),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    if current_user["role"] != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can add users")
    success = user_usecases.add_user(user_adapter=user_adapter, email=email, password=password, role=role)
    if success:
        return JSONResponse(content={"status": success}, media_type="application/json")
    else:
        raise HTTPException(status_code=403, detail="Unexpected error has occurred")
