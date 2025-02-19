"""LogEventsHandler Adapter module.

This module provides an adapter of LogEventsHandler for json file storage.
"""

import json
import os
import pathlib
from os import listdir, path
from typing import Optional

from loguru import logger

from model_platform.domain.entities.event import Event
from model_platform.domain.ports.log_events_handler import LogEventsHandler


class LogEventsHandlerJsonAdapter(LogEventsHandler):
    """Adapter for handling Log Events."""

    def __init__(self):
        """Initialize the LogEventsHandlerAdapter instance."""
        super().__init__()
        self.events_folder = os.environ["PATH_LOG_EVENTS"]
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
        current_date = str(event.timestamp).split(" ")[0]
        file_name = path.join(self.events_folder, f"events_logs_{current_date}.json")
        try:
            logger.info(f"Writing event to : {file_name}")
            if path.exists(file_name):
                with open(file_name, "r+") as f:
                    data = json.load(f)
                    data.append(j)
                    f.seek(0)
                    json.dump(data, f, indent=4)
            else:
                with open(file_name, "w") as f:
                    json.dump([j], f, indent=4)
            logger.info(f"Event written successfully to : {file_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to write event to : {file_name}. {e}")
            return False
