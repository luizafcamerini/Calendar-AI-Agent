import os, agent
from agent import *
from my_calendar import Calendar
from typos import LLMModelConfig
import logging
from dotenv import load_dotenv
from langchain.messages import HumanMessage, ToolMessage, SystemMessage

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
    agente = conecta_llm(llm_config).bind_tools(
        tools=[marca_evento, busca_proximos_evento, check_dia_horario]
    )

    messages = [
        SystemMessage(
            content="Você é um assistente que ajuda os usuários a gerenciar seus eventos no Google Calendar. A data de hoje é "
            + datetime.now().strftime("%Y-%m-%d")
        ),
        HumanMessage(content="Marque no dia 4 de março de 2042 um evento chamado 'Reunião de equipe' das 15:00 às 16:00."),
    ]

    res = agente.invoke(messages)

    while res.tool_calls:
        messages.append(res)

        for tool_call in res.tool_calls:
            selected_tool = {
                "busca_proximos_evento": busca_proximos_evento,
                "check_dia_horario": check_dia_horario,
                "marca_evento": marca_evento,
            }[tool_call["name"]]

            tool_output = selected_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

        res = agente.invoke(messages)

    print(res.content)


if __name__ == "__main__":
    main()
