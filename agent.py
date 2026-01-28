import os


from langchain.tools import tool
from langchain_cohere import ChatCohere
from typos import LLMModelConfig
from datetime import datetime


calendar = None


@tool(response_format="content")
def search_next_event(days: int) -> str:
    """Search for the next event in the Google Calendar within a specified number of days.
    Args:
        days: Number of days to look ahead for the next event.
    Returns:
        String containing the next event details or an error message.
    """
    result = calendar.busca_proximo_evento(days)
    return str(result)


@tool(response_format="content")
def check_day_hour(day: str, hour: str = "") -> str:
    """Verifies if there are scheduled events on a specific day and time in the agenda.
    Args:
        day: Date in YYYY-MM-DD format. If not provided, call the 'dia_atual' tool to get the current date.
        hour: Time in HH:MM format (optional, defaults to checking the entire day).
    Returns:
        String containing the events found or an error message.
    """
    result = calendar.check_dia_horario(day, hour if hour else None)
    return str(result)


@tool(response_format="content")
def create_event(
    summary: str,
    start_time: str,
    end_time: str,
) -> str:
    """Creates an event in the Google Calendar.
    Args:
        summary: Event description.
        start_time: Event start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        end_time: Event end time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
    Returns:
        String with confirmation of the created event or error message
    """
    result = calendar.marca_evento(summary, start_time, end_time)
    return str(result)


def conect_llm(llm_config: LLMModelConfig) -> ChatCohere:
    """Connects to the Cohere LLM model using the provided configuration.
    Args:
        llm_config: Configuration object containing model details and API token.
    Returns:
        An instance of ChatCohere connected to the specified model."""
    api_token = llm_config.api_token
    if not api_token:
        raise ValueError("API token for LLM model is not provided.")
    return ChatCohere(
        cohere_api_key=api_token,
        model=llm_config.model_name,
        temperature=llm_config.temperature,
    )
