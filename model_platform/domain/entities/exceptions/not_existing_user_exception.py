from fastapi import HTTPException


class NotExistingUserException(HTTPException):
    def __init__(self):
        self.message = "This user does not exists"

        super().__init__(status_code=404, detail=self.message)
