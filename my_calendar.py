import os.path
import logging

from datetime import datetime, timedelta
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
        # If modifying these scopes, delete the file token.json.
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
    def search_next_event(self, days: int = 30) -> str:
        """Searches for the next events in the Google Calendar.
        Args:
            days: Number of days to search for events (default: 30 days).
        Returns:
            String containing the events found or an error message.
        """
        logging.info(
            f"Searching for events in the next {days} days in the Google Calendar..."
        )
        now = datetime.now().isoformat() + "Z"
        future = (datetime.now() + timedelta(days=days)).isoformat() + "Z"
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=future,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            return "No events found."
        eventos_formatados = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            eventos_formatados.append(f"{start} - {event.get('summary', 'No title')}")
        return "\n".join(eventos_formatados)

    @connection_decorator
    def check_day_hour(self, day: str, hour: str = "") -> str:
        """Verifies if there are scheduled events on one specific day and time in the agenda.
        Args:
            day: Date in YYYY-MM-DD format.
            hour: Time in HH:MM format (optional, defaults to checking the entire day).

        Returns:
            String containing the events found or no events found."""
        #TODO: for some reason, this method doesnt work
        logging.info(f"Verifying events in the Google Calendar...")

        if hour == "":
            hour = "00:00"
        next_hour = (datetime.strptime(hour, "%H:%M") + timedelta(hours=1)).strftime("%H:%M")
        timemin = f"{day}T{hour}:00Z" if hour else f"{day}T00:00:00Z"
        timemax = f"{day}T{next_hour}:00Z" if hour else f"{day}T23:59:59Z"
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=timemin,
                timeMax=timemax,
                maxResults=1,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        print(events)
        if not events:
            return "No events found."
        return events

    @connection_decorator
    def create_event(self, summary: str, day: str, start_time: str, end_time: str) -> str:
        """Marks an event in the Google Calendar.
        Args:
            summary: Event description.
            day: Date in YYYY-MM-DD format.
            start_time: Event start in HH:MM format.
            end_time: Event end in HH:MM format.
        Returns:
            String with confirmation of the created event or error message."""
        # TODO: Add validation for date and time availability
        availability = self.check_day_hour(day, start_time)
        if availability != "No events found.":
            return "The specified time slot is not available."
        start_time = f"{day}T{start_time}:00"
        end_time = f"{day}T{end_time}:00"
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": end_time, "timeZone": "America/Sao_Paulo"},
        }
        try:
            event = self.service.events().insert(calendarId="primary", body=event).execute()
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
        events_result = (
            self.service.events()
            .list(
                calendarId=HOLIDAY_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", "")
        return str(events)

    @connection_decorator
    def get_event_id(self, day: str, hour: str) -> str:
        """Retrieves the event ID for a specific day and hour.
        Args:
            day: Date in YYYY-MM-DD format.
            hour: Time in HH:MM format.
        Returns:
            Event ID as a string or a message indicating no events found.
        """
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=day + "T" + hour + ":00Z",
                maxResults=1,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            return "No events found."
        else:
            return events[0]['id']

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
        if event_id == "No events found.":
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
