from pydantic import BaseModel

class UserInput(BaseModel):
    email: str
    password: str

    def to_json(self) -> dict:
        return {"email": self.email, "password": self.password}