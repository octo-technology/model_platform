import sqlite3
from typing import Optional

from passlib.context import CryptContext

from model_platform.domain.entities.exceptions.already_existing_user_exception import AlreadyExistingUserException
from model_platform.domain.entities.exceptions.internal_server_error_exception import InternalServerErrorException
from model_platform.domain.entities.exceptions.not_existing_user_exception import NotExistingUserException
from model_platform.domain.entities.role import ProjectRole, Role
from model_platform.domain.entities.user import User
from model_platform.domain.ports.user_handler import UserHandler

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserSqliteDbAdapter(UserHandler):

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_users_if_not_exists()
        self._init_table_project_users_if_not_exists()

    def _init_table_users_if_not_exists(self):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            """
            )
            connection.commit()
        finally:
            connection.close()

    def _init_table_project_users_if_not_exists(self):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS project_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    UNIQUE(email, project_name)
                )
            """
            )
            connection.commit()
        finally:
            connection.close()

    def add_project_user(self, project_name: str, email: str, role: ProjectRole):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT * FROM users WHERE email = ?
                """,
                (email,),
            )
            user_row = cursor.fetchone()
            if not user_row:
                raise NotExistingUserException

            cursor.execute(
                """
                SELECT * FROM project_users WHERE email = ?
                and project_name = ?
                """,
                (email, project_name),
            )
            row = cursor.fetchone()
            if row:
                raise AlreadyExistingUserException
            else:
                cursor.execute(
                    """
                    INSERT INTO project_users (email, project_name, role)
                    VALUES (?, ?, ?)
                    """,
                    (email, project_name, role.value),
                )
                connection.commit()
                success = True
        finally:
            connection.close()
        return success

    def delete_project_user(self, email: str, project_name: str):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                DELETE FROM project_users WHERE email = ? AND project_name = ?
                """,
                (email, project_name),
            )
            connection.commit()
            success = True
        finally:
            connection.close()
        return success

    def get_user(self, email: str, password: str) -> Optional[User]:
        try:
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if pwd_context.verify(password, row["hashed_password"]):
                user = User(
                    id=row["id"],
                    email=row["email"],
                    hashed_password=row["hashed_password"],
                    role=row["role"],
                )
            else:
                print("Wrond password")  # TODO
        finally:
            connection.close()
        return user

    def add_user(self, email: str, hashed_password: str, role: Role) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT * FROM users WHERE email = ?
                """,
                (email,),
            )
            row = cursor.fetchone()
            if row:
                raise AlreadyExistingUserException
            else:
                cursor.execute(
                    """
                    INSERT INTO users (email, hashed_password, role)
                    VALUES (?, ?, ?)
                    """,
                    (
                        email,
                        str(hashed_password),
                        role.value,
                    ),
                )
                connection.commit()
                success = True
        except Exception:
            raise InternalServerErrorException
        finally:
            connection.close()
        return success

    def get_users_role_for_project(self, email, project_name):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT role FROM project_users WHERE email = ? and project_name = ?
                """,
                (email, project_name),
            )
            row = cursor.fetchone()
            if row is None:
                return ProjectRole.NO_ROLE

            role = ProjectRole[row[0].upper()]
        finally:
            connection.close()
        return role

    def get_all_users(self) -> list[str]:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT email FROM users")
            users = cursor.fetchall()
            users = [user[0] for user in users]
        finally:
            connection.close()
        return users

    def get_users_for_project(self, project_name: str) -> list[dict]:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT email, role FROM project_users WHERE project_name = ?
                """,
                (project_name,),
            )
            users = cursor.fetchall()
            users = [{"email": user[0], "role": user[1]} for user in users]
        finally:
            connection.close()
        return users

    def change_user_role_for_project(self, email: str, project_name: str, role: ProjectRole):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE project_users SET role = ? WHERE email = ? AND project_name = ?
                """,
                (role.value, email, project_name),
            )
            connection.commit()
            success = True
        finally:
            connection.close()
        return success
