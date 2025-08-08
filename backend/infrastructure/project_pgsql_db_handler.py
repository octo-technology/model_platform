import logging

import psycopg2

from backend.domain.entities.project import Project
from backend.domain.ports.project_db_handler import ProjectDbHandler
from backend.infrastructure.project_sqlite_db_handler import (
    ProjectAlreadyExistError,
    ProjectDoesntExistError,
    map_rows_to_projects,
)


class ProjectPostgresDBHandler(ProjectDbHandler):
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.db_config["dbname"] = "projects_db"
        self._init_table_project_if_not_exists()

    def _connect(self):
        return psycopg2.connect(**self.db_config)

    def list_projects(self) -> list[Project] | None:
        print("DB CONFIG", self.db_config)
        # TODO ca utilise "users" en dbname et non "projects_db"
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM projects")
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_projects(rows)

    def list_projects_for_user(self, user: str) -> list[Project] | None:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            query = """
                    SELECT *
                    FROM projects
                             JOIN project_users ON projects.name = project_users.project_name
                    WHERE project_users.email = %s \
                    """
            cursor.execute(query, (user,))
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_projects(rows)

    def get_project(self, name) -> Project | None:
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = %s", (name,))
            rows = cursor.fetchall()
        finally:
            connection.close()
        if len(rows) == 1:
            return map_rows_to_projects(rows)[0]
        raise ProjectDoesntExistError(message="Project doesn't exist", name=name)

    def add_project(self, project: Project) -> bool:
        connection = self._connect()
        try:
            self.get_project(name=project.name)
            raise ProjectAlreadyExistError(name=project.name, message="Project with same name already exists")
        except ProjectDoesntExistError:
            logging.info("Project name not used yet, ok")
        try:
            cursor = connection.cursor()
            query = """
                    INSERT INTO projects (name, owner, scope, data_perimeter)
                    VALUES (%s, %s, %s, %s) \
                    """
            cursor.execute(query, (project.name, project.owner, project.scope, project.data_perimeter))
            connection.commit()
        finally:
            connection.close()
            return True

    def remove_project(self, name):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM projects WHERE name = %s", (name,))
            connection.commit()
        finally:
            connection.close()
            return True

    def _init_table_project_if_not_exists(self):
        connection = self._connect()
        try:
            cursor = connection.cursor()
            query = """
                    CREATE TABLE IF NOT EXISTS projects
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        name
                        TEXT
                        NOT
                        NULL,
                        owner
                        TEXT
                        NOT
                        NULL,
                        scope
                        TEXT
                        NOT
                        NULL,
                        data_perimeter
                        TEXT
                        NOT
                        NULL
                    ) \
                    """
            cursor.execute(query)
            connection.commit()
        finally:
            connection.close()
