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


if __name__ == "__main__":
    llm_config = LLMModelConfig(
        api_token=os.getenv("COHERE_API_KEY"),
        model_name=os.getenv("MODEL_NAME"),
        temperature=float(os.getenv("TEMPERATURE", 0.5)),
        max_tokens=int(os.getenv("MAX_TOKENS", 1000)),
    )
    agent.calendar = Calendar()
    agent.calendar.connect()
    agente = connect_llm(llm_config).bind_tools(
        tools=[create_event, search_next_event, check_day_hour, is_holiday],
    )

    messages = [
        SystemMessage(
            content=f"""Você é um assistente que ajuda os usuários a gerenciar seus eventos no Google Calendar.
            A data de hoje é {datetime.now().strftime("%Y-%m-%d")}. Caso o ano não for especificado em uma data, utilize o ano atual.
            Utilize as ferramentas disponíveis para buscar eventos, verificar horários disponíveis e criar novos eventos na agenda."""
        ),
        HumanMessage(content="Verifique se o dia 18/02 é um feriado"),
    ]

    res = agente.invoke(messages)

    while res.tool_calls:
        messages.append(res)

        for tool_call in res.tool_calls:
            selected_tool = {
                "search_next_event": search_next_event,
                "check_day_hour": check_day_hour,
                "create_event": create_event,
                "is_holiday": is_holiday,
            }[tool_call["name"]]

            tool_output = selected_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

        res = agente.invoke(messages)

    print(res.content)
