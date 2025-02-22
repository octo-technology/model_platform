def test_add_event():
    handler = LogEventsHandlerFileAdapter()
    event = Event(action="create_project", user="test_user", entity="test_project")

    mock_file_path = os.path.join(handler.events_folder, f"{event.timestamp}_{event.user}.json")

    with patch("builtins.open", mock_open()) as mocked_file:
        with patch("json.dump") as mocked_json_dump:
            result = handler.add_event(event)

            mocked_file.assert_called_once_with(mock_file_path, "w")
            mocked_json_dump.assert_called_once()
            assert result is True


import os
from unittest.mock import mock_open, patch

from model_platform.domain.entities.event import Event
from model_platform.infrastructure.log_events_handler_json_adapter import LogEventsHandlerFileAdapter


def test_add_event_failure():
    pass


def test_list_events():
    pass
