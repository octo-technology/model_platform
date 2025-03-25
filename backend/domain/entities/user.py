from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str
    hashed_password: str
    role: str  # TODO

    def to_json(self) -> dict:
        return {"id": self.id, "email": self.email, "hashed_password": self.hashed_password, "role": self.role}
