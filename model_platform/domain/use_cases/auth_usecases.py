from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from model_platform.domain.entities.role import Role
from model_platform.domain.use_cases.config import Config
from model_platform.domain.use_cases import user_usecases
from model_platform.infrastructure.user_sqlite_db_adapter import UserSqliteDbAdapter

# Clé secrète et algorithme JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Gestion des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 avec bearer token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
    )

# Vérification de l'utilisateur
def authenticate_user(username: str, password: str):
    user_adapter = UserSqliteDbAdapter(db_path=Config().db_path)
    user = user_usecases.get_user(
        user_adapter=user_adapter, 
        email=username, 
        password=password
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User doesn't exist")
    if not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    return user

# Création du token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    token_jwt = jwt.encode(
        to_encode, 
        Config().jwt_secret, 
        algorithm=Config().jwt_algorithm
        )
    return token_jwt

# Endpoint pour obtenir un token
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Could not authenticate")
    access_token = create_access_token(
        {
            "sub": user.email, 
            "role": user.role
        }, 
        timedelta(minutes=Config().jwt_access_token_expiration_time)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Vérifier et extraire l'utilisateur depuis le token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token, 
            Config().jwt_secret, 
            algorithms=[Config().jwt_algorithm]
        )
        email = payload.get("sub")
        role = payload.get("role")
        if email is None or role is None:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token"
                )
        return {
            "email": email,
            "role": role
            }
    except JWTError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token"
            )


# Gestion des rôles
def get_current_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != Role.ADMIN.value :
        raise HTTPException(
            status_code=403, 
            detail="Unauthorized access"
            )
    return current_user


def get_user_adapter(request: Request):
    return request.app.state.user_adapter