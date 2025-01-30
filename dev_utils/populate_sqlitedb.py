import os.path

from model_platform.domain.entities.project import Project
from model_platform.infrastructure.project_sqlite_db_handler import ProjectSQLiteDBHandler

if __name__ == "__main__":
    db_file_path = "projects.db"
    if os.path.isfile(db_file_path):
        os.remove(db_file_path)
    PROJECT_NAMES = ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta"]

    PROJECTS_INFOS = [
        {
            "name": project_name,
            "owner": project_name.split(" ")[-1] + " team",
            "scope": "A project to revolutionize IA projects",
            "data_perimeter": "All data on earth regarding our clients",
            "connection_parameters": "http://localhost:5000",
        }
        for project_name in PROJECT_NAMES
    ]

    PROJECT_SQLITE_DB_HANDLER = ProjectSQLiteDBHandler(db_file_path)
    for project in PROJECTS_INFOS:
        PROJECT_SQLITE_DB_HANDLER.add_project(Project(**project))
