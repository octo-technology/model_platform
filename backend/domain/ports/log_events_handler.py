"""LogEventsHandler port module.

This module defines the abstract base class for the LogEventsHandler port.
"""

from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.entities.event import Event


class LogEventsHandler(ABC):

    @abstractmethod
    def list_events(self, project_name: str) -> Optional[list[Event]]:
        pass

    @abstractmethod
    def add_event(self, event: Event, project_name: str) -> bool:
        pass
