from agent import *
from my_calendar import Calendar
from typos import LLMModelConfig
from langchain.messages import HumanMessage, ToolMessage, SystemMessage
from datetime import datetime
from dotenv import load_dotenv
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import MemorySaver
import os, agent
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
    model = connect_llm(llm_config)
    checkpoint = MemorySaver()
    agente = create_agent(
        model=model,
        tools=[
            search_next_event,
            check_day_hour,
            create_event,
            is_holiday,
            remove_event,
        ],
        checkpointer=checkpoint,
    )

    while True:
        message = input(">> ")
        if not message:
            break

        messages = [
            SystemMessage(
                content=f"""Você é um assistente que ajuda os usuários a gerenciar seus eventos no Google Calendar.
            A data de hoje é {datetime.now().strftime("%Y-%m-%d")}. Caso o ano não for especificado em uma data, utilize o ano atual.
            Caso o horário não especifique manhã ou tarde (ou formato 24 horas), considere o horário para o período da tarde.
            Utilize as ferramentas disponíveis para buscar eventos, verificar horários disponíveis e criar novos eventos na agenda."""
            ),
            HumanMessage(content=message),
        ]

        res = agente.invoke(
            {
                "messages": messages,
            },
            config={"thread_id": "user_session_1"},
        )

        # while res["messages"][-1].tool_calls:
        #     ai_message = res["messages"][-1]
        #     messages.append(ai_message)
        #     for tool_call in res.tool_calls:
        #         selected_tool = {
        #             "search_next_event": search_next_event,
        #             "check_day_hour": check_day_hour,
        #             "create_event": create_event,
        #             "is_holiday": is_holiday,
        #             "remove_event": remove_event,
        #         }[tool_call["name"]]

        #         tool_output = selected_tool.invoke(tool_call["args"])

        #         messages.append(
        #             ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
        #         )

        #     res = agente.invoke({"messages": messages})

        print(res["messages"][-1].content)
    print(messages)

    agent.calendar.disconnect()
