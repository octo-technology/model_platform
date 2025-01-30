import json  # Pour convertir le dictionnaire en chaîne JSON
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
    return [
        Project(name=row[1], owner=row[2], scope=row[3], data_perimeter=row[4], connection_parameters=row[5])
        for row in rows
    ]


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

    def add_project(
        self,
        project: Project,
    ) -> None:
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
                INSERT INTO projects (name, owner, scope, data_perimeter, connection_parameters)
                VALUES (?, ?, ?, ?, ?)
            """,
                (project.name, project.owner, project.scope, project.data_perimeter, project.connection_parameters),
            )

            connection.commit()

        finally:
            # Fermeture de la connexion
            connection.close()

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
                    data_perimeter TEXT NOT NULL,
                    connection_parameters TEXT
                )
            """
            )
            connection.commit()
        finally:
            connection.close()

    def get_project_connection_params(self, project_name: str) -> dict:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT connection_parameters FROM projects WHERE name = ?", (project_name,))
            row = cursor.fetchone()
        finally:
            connection.close()

        if row and row[0]:
            # Si des paramètres de connexion sont trouvés, on les retourne sous forme de dictionnaire
            return json.loads(row[0])  # Convertir la chaîne JSON en dictionnaire
        else:
            return {}
