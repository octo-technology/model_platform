import sqlite3

from backend.domain.entities.project import Project
from backend.domain.ports.project_db_handler import ProjectDbHandler


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
        Project(
            name=row[1],
            owner=row[2],
            scope=row[3],
            data_perimeter=row[4],
            batch_enabled=bool(row[5]) if len(row) > 5 else False,
        )
        for row in rows
    ]


class ProjectSQLiteDBHandler(ProjectDbHandler):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table_project_if_not_exists()

    def list_projects(self) -> list[Project] | None:
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM projects")
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_projects(rows)

    def list_projects_for_user(self, user: str) -> list[Project] | None:
        try:
            connection = sqlite3.connect(self.db_path)
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM projects JOIN project_users ON projects.name = project_users.project_name "
                "WHERE project_users.email = ?",
                (user,),
            )
            rows = cursor.fetchall()
        finally:
            connection.close()
        return map_rows_to_projects(rows)

    def get_project(self, name) -> Project | None:
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
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO projects (name, owner, scope, data_perimeter, batch_enabled)
                VALUES (?, ?, ?, ?, ?)
            """,
                (project.name, project.owner, project.scope, project.data_perimeter, project.batch_enabled),
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

    def update_batch_enabled(self, name: str, batch_enabled: bool) -> bool:
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE projects SET batch_enabled = ? WHERE name = ?", (batch_enabled, name))
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
                    data_perimeter TEXT NOT NULL,
                    batch_enabled BOOLEAN DEFAULT FALSE
                )
            """
            )
            # Migration: add batch_enabled column if missing
            cursor.execute("PRAGMA table_info(projects)")
            columns = [col[1] for col in cursor.fetchall()]
            if "batch_enabled" not in columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN batch_enabled BOOLEAN DEFAULT FALSE")
            connection.commit()
        finally:
            connection.close()
