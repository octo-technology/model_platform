from fastapi import HTTPException


class UserRoleDoesNotExistException(HTTPException):
    """Exception raised when wanting to create a user with a non-existing role"""

    def __init__(self):
        self.message = "Role does not exists"
        super().__init__(status_code=404, detail=self.message)
