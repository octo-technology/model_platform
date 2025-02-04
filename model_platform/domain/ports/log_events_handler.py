"""LogEventsHandler port module.

This module defines the abstract base class for the LogEventsHandler port.
"""
from abc import ABC, abstractmethod
from typing import Optional

from model_platform.domain.entities.event import Event


class LogEventsHandler(ABC):

    @abstractmethod
    def list_events(self) -> Optional[list[Event]]:
        pass

    @abstractmethod
    def add_event(self, event: Event) -> bool:
        pass
