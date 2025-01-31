from typing import Optional

from pydantic import BaseModel


class Project(BaseModel):
    name: str
    owner: str
    scope: str
    data_perimeter: str
    connection_parameters: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "data_perimeter": self.data_perimeter,
            "scope": self.scope,
            "owner": self.owner,
            "name": self.name,
            "connection_parameters": self.connection_parameters,
        }
