import logging
import sqlite3

from model_platform.domain.entities.project import Project
from model_platform.domain.ports.project_db_handler import ProjectDbHandler


class ProjectDoesntExistError(Exception):
    def __init__(self, message, name=None):
        super().__init__(message)
        self.project_name = name


class ProjectAlreadyExistError(Exception):
    def __init__(self, message, name=None):
        super().__init__(message)
        self.project_name = name


def map_rows_to_projects(rows: list) -> list[Project]:
    return [Project(name=row[1], owner=row[2], scope=row[3], data_perimeter=row[4]) for row in rows]


class ProjectSQLiteDBHandler(ProjectDbHandler):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_project_if_not_exists()

    def list_projects(self) -> list[Project]:
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM projects")
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_projects(rows)

    def get_project(self, name) -> Project:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM projects where name = ?", (name,))
            rows = cursor.fetchall()
        finally:
            connection.close()
        if len(rows) == 1:
            return map_rows_to_projects(rows)[0]
        raise ProjectDoesntExistError(message="Project doesn't exist", name=name)

    def add_project(self, project: Project) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            self.get_project(name=project.name)
            raise ProjectAlreadyExistError(name=project.name, message="Project with same name already exists")
        except ProjectDoesntExistError:
            logging.info("Project name not used yet, ok")
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO projects (name, owner, scope, data_perimeter)
                VALUES (?, ?, ?, ?)
            """,
                (project.name, project.owner, project.scope, project.data_perimeter),
            )

            connection.commit()
        finally:
            connection.close()
            return True

    def remove_project(self, name):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM projects where name = ?", (name,))
            connection.commit()
        finally:
            connection.close()
            return True

    def _init_table_project_if_not_exists(self):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    data_perimeter TEXT NOT NULL
                )
            """
            )
            connection.commit()
        finally:
            connection.close()
