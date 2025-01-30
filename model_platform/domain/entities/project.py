from pydantic import BaseModel


class Project(BaseModel):
    name: str
    owner: str
    scope: str
    data_perimeter: str

    def to_json(self) -> dict:
        return {"data_perimeter": self.data_perimeter, "scope": self.scope, "owner": self.owner, "name": self.name}
