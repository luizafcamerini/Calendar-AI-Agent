import os.path
import logging

from datetime import datetime, timedelta, timezone
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Load holiday calendar configuration from JSON file
with open("config/holiday_calendar.json", "r", encoding="utf-8") as f:
    holiday_config = json.load(f)


HOLIDAY_CALENDAR_ID = holiday_config["id"]
CREDENTIALS_PATH = "config/credentials.json"


class Calendar:
    """Class to interact with Google Calendar API."""

    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
        ]
        self.service = None

    def connect(self):
        """Connects to the Google Calendar API."""
        creds = None
        if os.path.exists("config/token.json"):
            creds = Credentials.from_authorized_user_file(
                "config/token.json", self.scopes
            )
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "config/credentials.json", self.scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("config/token.json", "w") as token:
                token.write(creds.to_json())
        try:
            self.service = build("calendar", "v3", credentials=creds)
        except HttpError as error:
            print(f"An error occurred: {error}")

    def disconnect(self):
        """Disconnects from the Google Calendar API."""
        logging.info("Disconnecting from the Google Calendar API...")
        self.service = None

    def connection_decorator(func):
        """Decorator to ensure connection before executing API methods."""

        def wrapper(self, *args, **kwargs):
            if not self.service:
                self.connect()
            try:
                result = func(self, *args, **kwargs)
            finally:
                self.disconnect()
            return result

        return wrapper

    @connection_decorator
    def list_events(
        self,
        timeMin: str,
        timeMax: str,
        calendarId: str = "primary",
        max_results: int = 100,
        singleEvents: bool = True,
    ) -> list:
        """Lists the upcoming events in the specified Google Calendar.
        Args:
            timeMin: The time after which to list events (ISO 8601 format).
            timeMax: The time before which to list events (ISO 8601 format).
            calendarId: ID of the calendar to list events from (default: primary).
            max_results: Maximum number of events to retrieve (default: 100).
            singleEvents: Whether to expand recurring events into instances (default: True).
        Returns:
            List of events found. If no events are found, returns an empty list.
        """
        events_result = (
            self.service.events()
            .list(
                calendarId=calendarId,
                timeMin=timeMin,
                timeMax=timeMax,
                maxResults=max_results,
                singleEvents=singleEvents,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            return []
        return events

    def stringify_events(self, events: list) -> str:
        """Converts a list of events into a readable string format.
        Args:
            events: List of event objects.
        Returns:
            String representation of the events. If no events, returns an empty string.
        """
        event_strings = []
        if not events:
            return ""
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            event_strings.append(f"{start}: {event.get('summary', 'No Title')}")
        return "\n".join(event_strings)

    def search_next_event(self, days: int = 30) -> str:
        """Searches for the next events in the Google Calendar.
        Args:
            days: Number of days to search for events (default: 30 days).
        Returns:
            String containing the events found. If no events, returns an empty string.
        """
        now = datetime.now().isoformat() + "Z"
        future = (datetime.now() + timedelta(days=days)).isoformat() + "Z"
        return self.stringify_events(self.list_events(timeMin=now, timeMax=future))

    def check_day_hour(self, day: str, hour: str = "") -> str:
        """Verifies if there are scheduled events on one specific day and time in the agenda.
        Args:
            day: Date in YYYY-MM-DD format.
            hour: Time in HH:MM format (optional, defaults to checking the entire day).

        Returns:
            String containing the events found. If no events, returns an empty string.
        """
        # TODO: for some reason, this method doesnt work
        logging.info(f"Verifying events in the Google Calendar...")
        if not hour:
            start = datetime.fromisoformat(f"{day}T00:00").replace(tzinfo=timezone.utc)
            end = start + timedelta(days=1)
        else:
            start = datetime.fromisoformat(f"{day}T{hour}").replace(tzinfo=timezone.utc)
            end = start + timedelta(hours=1)
        timemin = start.isoformat()
        timemax = end.isoformat()
        return self.stringify_events(self.list_events(timeMin=timemin, timeMax=timemax))

    @connection_decorator
    def create_event(
        self, summary: str, day: str, start_time: str, end_time: str = ""
    ) -> str:
        """Creates an event in the Google Calendar.
        Args:
            summary: Event description.
            day: Date in YYYY-MM-DD format.
            start_time: Event start in HH:MM format.
            end_time: Event end in HH:MM format (optional, default is one hour after start_time).
        Returns:
            String with confirmation of the created event or error message."""
        availability = not self.check_day_hour(day, start_time) and not self.is_holiday(
            day
        )
        if not availability:
            return "The specified time slot is not available."
        start_time = f"{day}T{start_time}:00"
        if not end_time:
            end_time = (
                datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)
            ).strftime("%H:%M")
        end_time = f"{day}T{end_time}:00"
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": end_time, "timeZone": "America/Sao_Paulo"},
        }
        try:
            event = (
                self.service.events().insert(calendarId="primary", body=event).execute()
            )
            return f"Event created: {event.get('htmlLink')}"
        except HttpError as error:
            return f"An error occurred: {error}"

    @connection_decorator
    def is_holiday(self, date: str) -> str:
        """Checks if a given date is a holiday using the holiday calendar.
        Args:
            date: Date in YYYY-MM-DD format.
        Returns:
            String indicating the name of the holiday. If not a holiday, returns ''.
        """
        time_min = f"{date}T00:00:00Z"
        time_max = f"{date}T23:59:59Z"
        return self.stringify_events(
            self.list_events(
                timeMin=time_min, timeMax=time_max, calendarId=HOLIDAY_CALENDAR_ID
            )
        )

    @connection_decorator
    def get_event_id(self, day: str, hour: str) -> str:
        """Retrieves the event ID for a specific day and hour.
        Args:
            day: Date in YYYY-MM-DD format.
            hour: Time in HH:MM format.
        Returns:
            Event ID as a string or an empty string if no events are found.
        """
        event = self.list_events(
            timeMin=day + "T" + hour + ":00Z",
        )
        return event.get("items")[0]["id"] if event else ""

    @connection_decorator
    def remove_event(self, day: str, hour: str) -> str:
        """Removes an event from the Google Calendar.
        Args:
            day: Date in YYYY-MM-DD format.
            hour: Time in HH:MM format.
        Returns:
            String confirming the deletion of the event or reporting an error.
        """
        event_id = self.get_event_id(day, hour)
        if event_id == "":
            return "No event found to delete."
        else:
            try:
                self.service.events().delete(
                    calendarId="primary", eventId=event_id
                ).execute()
                return f"Event with ID {event_id} has been deleted."
            except HttpError as error:
                return f"An error occurred: {error}"


if __name__ == "__main__":
    cal = Calendar()
    cal.connect()
    print(cal.check_day_hour("2026-01-29", "19:00"))
