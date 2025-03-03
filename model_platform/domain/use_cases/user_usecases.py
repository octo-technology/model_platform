from model_platform.domain.entities.exceptions.user_role_does_not_exist_exception import UserRoleDoesNotExistException
from model_platform.domain.entities.role import Role
from model_platform.domain.ports.user_handler import UserHandler
from model_platform.domain.entities.user import User
from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter

from passlib.context import CryptContext


EVENT_LOGGER = LogEventsHandlerFileAdapter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(user_adapter: UserHandler, email: str, password: str) -> User:
    user = user_adapter.get_user(
        email, 
        password
        )
    return user


def add_user(user_adapter: UserHandler, email: str, password: str, role: str) -> bool:
    if role in (Role.SIMPLE_USER.value, Role.ADMIN.value) : 
        success = user_adapter.add_user(
            email=email,
            hashed_password=pwd_context.hash(password),
            role=role
        )
        return success
    else:
        raise UserRoleDoesNotExistException