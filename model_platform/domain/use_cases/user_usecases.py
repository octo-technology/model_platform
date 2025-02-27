
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
    if role == Role.SIMPLE_USER.value : 
        success = user_adapter.add_user(
            email=email,
            hashed_password=pwd_context.hash(password),
            role=Role.SIMPLE_USER.value
        )
    elif role == Role.ADMIN.value:
        success = user_adapter.add_user(
            email=email,
            hashed_password=pwd_context.hash(password),
            role=Role.ADMIN.value
        )
    else:
        success = False
        print("Role doesn't exist")
        #TODO
    return success
