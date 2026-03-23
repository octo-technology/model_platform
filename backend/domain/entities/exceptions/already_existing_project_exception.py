# Philippe Stepniewski
from fastapi import HTTPException


class AlreadyExistingProjectException(HTTPException):
    """Exception raised when a project with the same name already exists"""

    def __init__(self, project_name: str):
        self.message = f"A project with the name '{project_name}' already exists"

        super().__init__(status_code=409, detail=self.message)
