from typing import Optional

import psycopg2
from passlib.context import CryptContext

from backend.domain.entities.exceptions.already_existing_user_exception import AlreadyExistingUserException
from backend.domain.entities.exceptions.not_existing_user_exception import NotExistingUserException
from backend.domain.entities.role import ProjectRole, Role
from backend.domain.entities.user import User
from backend.domain.ports.user_handler import UserHandler

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserPgsqlDbAdapter(UserHandler):
    def __init__(self, db_config: dict, admin_config: dict = None):
        self.db_config = db_config
        self.admin_config = admin_config
        self.db_config["dbname"] = "model_platform_db"
        self._init_table_users_if_not_exists()
        self._init_table_project_users_if_not_exists()
        if admin_config is not None:
            self.create_admin_user_if_not_exists()

    def _get_connection(self):
        return psycopg2.connect(**self.db_config)

    def _init_table_users_if_not_exists(self):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    email
                    TEXT
                    NOT
                    NULL
                    UNIQUE,
                    hashed_password
                    TEXT
                    NOT
                    NULL,
                    role
                    TEXT
                    NOT
                    NULL
                )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def _init_table_project_users_if_not_exists(self):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS project_users
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    email
                    TEXT
                    NOT
                    NULL,
                    project_name
                    TEXT
                    NOT
                    NULL,
                    role
                    TEXT
                    NOT
                    NULL,
                    UNIQUE
                (
                    email,
                    project_name
                )
                    )
                """
            )
            connection.commit()
        finally:
            connection.close()

    def add_project_user(self, project_name: str, email: str, role: ProjectRole):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            user_row = cursor.fetchone()
            if not user_row:
                raise NotExistingUserException

            cursor.execute(
                """
                SELECT *
                FROM project_users
                WHERE email = %s
                  and project_name = %s
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
                    VALUES (%s, %s, %s)
                    """,
                    (email, project_name, role.value),
                )
                connection.commit()
                success = True
        finally:
            connection.close()
        return success

    def delete_project_user(self, email: str, project_name: str):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                DELETE
                FROM project_users
                WHERE email = %s
                  AND project_name = %s
                """,
                (email, project_name),
            )
            connection.commit()
            success = True
        finally:
            connection.close()
        return success

    def get_user(self, email: str, password: str) -> Optional[User]:
        user = None
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
            if row and pwd_context.verify(password, row[2]):
                user = User(
                    id=row[0],
                    email=row[1],
                    hashed_password=row[2],
                    role=row[3],
                )
            else:
                print("Wrong password")  # TODO
        finally:
            connection.close()
        return user

    def add_user(self, email: str, hashed_password: str, role: Role) -> bool:
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
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
                    VALUES (%s, %s, %s)
                    """,
                    (
                        email,
                        str(hashed_password),
                        role.value,
                    ),
                )
                connection.commit()
                success = True
        finally:
            connection.close()
        return success

    def get_users_role_for_project(self, email, project_name):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT role
                FROM project_users
                WHERE email = %s
                  and project_name = %s
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
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT email FROM users")
            users = cursor.fetchall()
            users = [user[0] for user in users]
        finally:
            connection.close()
        return users

    def get_users_for_project(self, project_name: str) -> list[dict]:
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT email, role
                FROM project_users
                WHERE project_name = %s
                """,
                (project_name,),
            )
            users = cursor.fetchall()
            users = [{"email": user[0], "role": user[1]} for user in users]
        finally:
            connection.close()
        return users

    def change_user_role_for_project(self, email: str, project_name: str, role: ProjectRole):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE project_users
                SET role = %s
                WHERE email = %s
                  AND project_name = %s
                """,
                (role.value, email, project_name),
            )
            connection.commit()
            success = True
        finally:
            connection.close()
        return success

    def create_admin_user_if_not_exists(self):
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            email = self.admin_config["email"]
            password = self.admin_config["password"]
            hashed_password = pwd_context.hash(password)
            cursor.execute(
                """
                INSERT INTO users (email, hashed_password, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (email) DO NOTHING
                """,
                (email, hashed_password, Role.ADMIN.value),
            )
            connection.commit()
        finally:
            connection.close()
