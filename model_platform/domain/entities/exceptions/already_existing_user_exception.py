from fastapi import HTTPException


class AlreadyExistingUserException(HTTPException):
    """Exception raised when an email is already used by another already registered user"""

    def __init__(self):
        self.message = "Email is already used by another user"

        super().__init__(status_code=404, detail=self.message)
