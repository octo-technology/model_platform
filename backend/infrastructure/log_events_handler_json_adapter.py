"""LogEventsHandler Adapter module.

This module provides an adapter of LogEventsHandler for json file storage.
"""

import csv
import os
import pathlib
from os import listdir, path
from typing import Optional

from loguru import logger

from backend.domain.entities.event import Event
from backend.domain.ports.log_events_handler import LogEventsHandler


class LogEventsHandlerFileAdapter(LogEventsHandler):
    """Adapter for handling Log Events."""

    def __init__(self):
        """Initialize the LogEventsHandlerAdapter instance."""
        super().__init__()
        self.events_folder = os.environ["PATH_LOG_EVENTS"]
        if not path.exists(self.events_folder):
            pathlib.Path(self.events_folder).mkdir(parents=True, exist_ok=True)

    def list_events(self, project_name: str) -> Optional[list]:
        project_event_log_folder = path.join(self.events_folder, project_name)
        events = []
        try:
            logger.info(f"Retrieving events from {project_event_log_folder}...")
            events_files = [f for f in listdir(project_event_log_folder) if f.endswith(".csv")]
            for file in events_files:
                with open(path.join(project_event_log_folder, file), newline="") as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        events.append(row)
            logger.info("All events were retrieved successfully!")
            return events
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return None

    def add_event(self, event: Event, project_name: str) -> bool:
        event_to_log = event.to_json()
        current_date = str(event.timestamp).split(" ")[0]
        project_event_log_folder = path.join(self.events_folder, project_name)
        if not os.path.exists(project_event_log_folder):
            pathlib.Path(project_event_log_folder).mkdir(parents=True, exist_ok=True)
        file_name = path.join(project_event_log_folder, f"events_logs_{current_date}.csv")
        try:
            logger.info(f"Writing event to : {file_name}")
            with open(file_name, "a", newline="") as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow(event_to_log.keys())  # Write header if file is empty
                writer.writerow(event_to_log.values())
            logger.info(f"Event written successfully to : {file_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to write event to : {file_name}. {e}")
            return False
