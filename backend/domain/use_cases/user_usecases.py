from fastapi import HTTPException
from passlib.context import CryptContext

from backend.domain.entities.exceptions.user_role_does_not_exist_exception import UserRoleDoesNotExistException
from backend.domain.entities.role import PROJECT_ACTIONS_MINIMUM_LEVEL, ProjectRole, Role
from backend.domain.entities.user import User
from backend.domain.ports.user_handler import UserHandler
from backend.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter
from backend.infrastructure.user_sqlite_db_adapter import UserSqliteDbAdapter

EVENT_LOGGER = LogEventsHandlerFileAdapter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(user_adapter: UserHandler, email: str, password: str) -> User:
    user = user_adapter.get_user(email, password)
    return user


def get_all_users(user_adapter: UserHandler) -> list:
    users = user_adapter.get_all_users()
    return users


def add_user(user_adapter: UserHandler, email: str, password: str, role: str) -> bool:
    try:
        role = Role(role.upper())
        success = user_adapter.add_user(email=email, hashed_password=pwd_context.hash(password), role=role)
        return success
    except ValueError:
        raise UserRoleDoesNotExistException


def add_user_to_project(user_adapter: UserHandler, email: str, project_name: str, role: str) -> bool:
    try:
        role = ProjectRole(role.upper())
        success = user_adapter.add_project_user(project_name=project_name, email=email, role=role)
        return success
    except ValueError:
        raise UserRoleDoesNotExistException


def remove_user_from_project(user_adapter: UserHandler, email: str, project_name: str) -> bool:
    success = user_adapter.delete_project_user(project_name=project_name, email=email)
    return success


def get_user_role_for_project(email: str, project_name: str, user_adapter: UserSqliteDbAdapter):
    role = user_adapter.get_users_role_for_project(email, project_name)
    return role


def get_users_for_project(project_name: str, user_adapter: UserSqliteDbAdapter):
    users = user_adapter.get_users_for_project(project_name)
    return users


def user_can_perform_action_for_project(
    current_user: dict, project_name: str, action_name: str, user_adapter: UserSqliteDbAdapter
) -> None:
    role: ProjectRole = get_user_role_for_project(
        email=current_user["email"], project_name=project_name, user_adapter=user_adapter
    )
    role_authorized_actions = PROJECT_ACTIONS_MINIMUM_LEVEL[role]

    if (action_name not in role_authorized_actions) and (current_user["role"] != Role.ADMIN):
        message_project = f"for project {project_name}" if project_name != "" else ""
        raise HTTPException(status_code=403, detail=f"User cannot perform this {action_name} {message_project}")


def change_user_role_for_project(email: str, project_name: str, role: str, user_adapter: UserSqliteDbAdapter):
    try:
        print(role)
        role = ProjectRole(role.upper())
        success = user_adapter.change_user_role_for_project(email, project_name, role)
        return success
    except ValueError:
        raise UserRoleDoesNotExistException
