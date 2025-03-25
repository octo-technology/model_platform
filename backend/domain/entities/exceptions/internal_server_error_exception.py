from fastapi import HTTPException


class InternalServerErrorException(HTTPException):
    """Exception raised when something went wrond with the db"""

    def __init__(self):
        self.message = "Internal server error"

        super().__init__(status_code=500, detail=self.message)
