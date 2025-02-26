import logging
import sqlite3

from model_platform.domain.entities.role import Role
from model_platform.domain.entities.user import User
from model_platform.domain.ports.user_handler import UserHandler
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserSqliteDbAdapter(UserHandler):

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_users_if_not_exists()

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

    def get_user(self, email: str, password: str) -> User:
        try:
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            print(row["hashed_password"])
            if pwd_context.verify(password, row["hashed_password"]) :

                print(f"showing the row : {row}")
                user = User(
                    id=row["id"],
                    email=row["email"],
                    hashed_password=row["hashed_password"],
                    role=row["role"],
                )
                print(user)
            else:
                print("Wrond password") #TODO
        except Exception as e:
            user = None
            print("\n\n\n there error is :", e, "\n\n\n\n") 

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
                """
                ,
                (email,)
            )
            row = cursor.fetchone()
            if row :
                print("utilisateur existant") #TODO
                success = False
            else : 
                cursor.execute(
                    """
                    INSERT INTO users (email, hashed_password, role)
                    VALUES (?, ?, ?)
                    """,
                    (email, str(hashed_password), role,),
                )
                connection.commit()
                success = True
        except Exception as e:
            print(e) #TODO
            success = False
        finally:
            connection.close()
        return success