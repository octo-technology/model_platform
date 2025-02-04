import uuid
import datetime


class Event():
    action: str
    timestamp: datetime.datetime
    user: uuid.UUID
    entity: str

    def __init__(self, action, user, entity):
        self.action = action
        self.user = user
        self.entity = entity
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

    def to_json(self) -> dict:
        return {
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "user": str(self.user),
            "entity": self.entity,
        }
