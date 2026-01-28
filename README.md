# Calendar AI Agent

Calendar AI Agent is a personal productivity tool that integrates with your calendar to automate scheduling, reminders, and event management using artificial intelligence. The project aims to streamline your daily planning by leveraging AI to understand your preferences, suggest optimal meeting times, and handle routine calendar tasks.

The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.

### Files Overview:
- `agent.py`: This is the main agent file that contains the logic for interacting with the calendar and handling user requests. It defines various tools for searching events, checking availability, and creating new events in the calendar.
- `my_calendar.py`: This file contains functions that interact directly with the Google Calendar API. It includes methods for searching events, checking availability, and creating events.
- `config.py`: This file holds configuration settings for the project, such as API keys, model configurations, and other constants used throughout the application.
- `main.py`: This is the entry point of the application. It initializes the agent, sets up the necessary configurations, and starts the interaction loop with the user.
- `requirements.txt`: This file lists all the Python dependencies required to run the project. It includes libraries for interacting with the Google Calendar API, handling AI models, and other utilities.
- `typos.py`: This file defines data models and types used in the project, such as configurations for the LLM model and other structured data representations.

### What is needed to run the project:
- Python 3.8 or higher
- Google Calendar API credentials (OAuth 2.0 Client ID)
- Cohere API key for language model interactions
