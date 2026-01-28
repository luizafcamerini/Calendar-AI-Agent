import os, agent
from agent import *
from my_calendar import Calendar
from typos import LLMModelConfig
from dotenv import load_dotenv
from langchain.messages import HumanMessage, ToolMessage, SystemMessage
from datetime import datetime
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)


def main():
    llm_config = LLMModelConfig(
        api_token=os.getenv("COHERE_API_KEY"),
        model_name=os.getenv("MODEL_NAME"),
        temperature=float(os.getenv("TEMPERATURE", 0.5)),
        max_tokens=int(os.getenv("MAX_TOKENS", 1000)),
    )
    agent.calendar = Calendar()
    agent.calendar.connect()
    agente = connect_llm(llm_config).bind_tools(
        tools=[create_event, search_next_event, check_day_hour]
    )

    messages = [
        SystemMessage(
            content=f"""Você é um assistente que ajuda os usuários a gerenciar seus eventos no Google Calendar.
            A data de hoje é {datetime.now().strftime("%Y-%m-%d")}.
            Utilize as ferramentas disponíveis para buscar eventos, verificar horários disponíveis e criar novos eventos na agenda.
            Caso necessário, utilize ferramentas em sequência para completar a tarefa do usuário."""
        ),
        HumanMessage(content="Me diga os eventos no dia 8/12/2025"),
    ]

    res = agente.invoke(messages)

    while res.tool_calls:
        messages.append(res)

        for tool_call in res.tool_calls:
            selected_tool = {
                "search_next_event": search_next_event,
                "check_day_hour": check_day_hour,
                "create_event": create_event,
            }[tool_call["name"]]

            tool_output = selected_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

        res = agente.invoke(messages)

    print(res.content)


if __name__ == "__main__":
    main()
