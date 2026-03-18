from typing import Optional

from pydantic import BaseModel


class Project(BaseModel):
    name: str
    owner: str
    scope: str
    data_perimeter: str
    batch_enabled: bool = False
    connection_parameters: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "data_perimeter": self.data_perimeter,
            "scope": self.scope,
            "owner": self.owner,
            "name": self.name,
            "batch_enabled": self.batch_enabled,
        }
