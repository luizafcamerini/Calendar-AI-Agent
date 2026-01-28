import datetime
import os.path
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class Calendar:
    """Classe para interagir com o Google Calendar API."""

    def __init__(self):
        # If modifying these scopes, delete the file token.json.
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
        ]
        self.service = None

    def connect(self):
        """Connects to the Google Calendar API."""
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
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
            return func(self, *args, **kwargs)

        return wrapper

    @connection_decorator
    def search_next_event(self, days: int = 30) -> str:
        """Searches for the next events in the Google Calendar.

        Args:
            days: Number of days to search for events (default: 30 days).
        """
        logging.info(
            f"Searching for events in the next {days} days in the Google Calendar..."
        )
        now = datetime.datetime.now().isoformat() + "Z"  # 'Z' indicates UTC time
        future = (
            datetime.datetime.now() + datetime.timedelta(days=days)
        ).isoformat() + "Z"
        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=future,
                maxResults=10,
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
    def check_day_hour(self, day: str, hour: str = None) -> str:
        """Verifies if there are scheduled events on a specific day and time in the agenda."""
        logging.info("Verifying events in the Google Calendar...")
        if hour:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=day + "T" + hour + ":00Z",
                    timeMax=day + "T" + hour + ":59Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        else:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=day + "T00:00:00Z",
                    timeMax=day + "T23:59:59Z",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        events = events_result.get("items", [])
        if not events:
            return "No events found."
        formatted_events = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            formatted_events.append(f"{start} - {event.get('summary', 'No title')}")
        return "\n".join(formatted_events)

    @connection_decorator
    def create_event(self, summary: str, start_time: str, end_time: str) -> str:
        """Marks an event in the Google Calendar."""
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": end_time, "timeZone": "America/Sao_Paulo"},
        }
        event = self.service.events().insert(calendarId="primary", body=event).execute()
        return f"Event created: {event.get('htmlLink')}"
