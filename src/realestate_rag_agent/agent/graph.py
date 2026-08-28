from functools import lru_cache

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from realestate_rag_agent.agent.llm import get_chat_model
from realestate_rag_agent.agent.tools import AGENT_TOOLS

SYSTEM_PROMPT = """Você é um assistente especializado em busca de imóveis em \
Florianópolis (venda e locação).

Regras:
- Sempre use as ferramentas para encontrar imóveis. Nunca invente imóveis, \
preços ou bairros.
- Só mencione imóveis que vieram no resultado de uma ferramenta nesta conversa.
- Escolha a ferramenta certa: `search_properties` quando o usuário descreve o \
que quer em linguagem natural; `filter_properties` para consultas puramente \
objetivas; `get_property_details` para detalhar um imóvel específico.
- Extraia filtros estruturados da pergunta (operação, faixa de preço, número de \
quartos, bairro, tipo, comodidades) e passe-os para a ferramenta.
- Responda em português, de forma concisa. Para cada imóvel recomendado, cite \
título, bairro, preço e 1-2 características relevantes.
- Se nada for encontrado, diga isso claramente e sugira relaxar algum filtro.
"""


def _agent_node(state: MessagesState) -> dict:
    model = get_chat_model().bind_tools(AGENT_TOOLS)
    reply = model.invoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
    return {"messages": [reply]}


def _should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


def build_agent_graph(checkpointer=None):
    graph = StateGraph(MessagesState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(AGENT_TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer or InMemorySaver())


@lru_cache
def get_agent_graph():
    return build_agent_graph()
