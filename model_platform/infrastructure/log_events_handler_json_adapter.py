"""LogEventsHandler Adapter module.

This module provides an adapter of LogEventsHandler for json file storage.
"""

import json
import pathlib
from os import listdir, path
from typing import Optional

from loguru import logger

from model_platform.domain.entities.event import Event
from model_platform.domain.ports.log_events_handler import LogEventsHandler


class LogEventsHandlerJsonAdapter(LogEventsHandler):
    """Adapter for handling Log Events."""

    # TODO Unit tests
    # TODO Un seul gros fichier de logs / ou un fichier par jour (comme tu préfères)
    def __init__(self, log_folder: str = None):
        """Initialize the LogEventsHandlerAdapter instance."""
        super().__init__()
        self.events_folder = log_folder
        if not path.exists(self.events_folder):
            pathlib.Path(self.events_folder).mkdir(parents=True, exist_ok=True)

    def list_events(self) -> Optional[list[Event]]:
        events = []
        try:
            logger.info("Retrieving events...")
            events_files = [f for f in listdir(self.events_folder)]
            for file in events_files:
                with open(file) as json_data:
                    d = json.loads(json_data)
                    event = Event(
                        d.get("action"),
                        d.get("timestamp"),
                        d.get("user"),
                        d.get("action"),
                    )
                    events.append(event)
                    json_data.close()
            logger.info("All events where retrieved successfully !")
            return events
        except Exception as e:
            logger.error(f"Failed to list events : {e}")

    def add_event(self, event: Event) -> bool:
        j = event.to_json()
        file_name = path.join(self.events_folder, f"{event.timestamp}_{event.user}.json")

        try:
            logger.info(f"Writing event to : {file_name}")
            with open(file_name, "w") as f:
                json.dump(j, f, indent=4)
            logger.info(f"Event written successfully to : {file_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to write event to : {file_name}. {e}")
            return False
