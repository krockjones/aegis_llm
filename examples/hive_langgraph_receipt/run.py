"""Run one LangGraph turn through AegisLLM and mint a Hive receipt.

The Hive callback receives metadata and SHA-256 hashes only; prompts and model
outputs stay local to this process and the configured AegisLLM/Ollama stack.
"""

from __future__ import annotations

import os
import time
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_hive import HiveCallbackHandler
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def main() -> None:
    base_url = os.getenv("AEGISLLM_OPENAI_BASE_URL", "http://127.0.0.1:8765/v1")
    model = os.getenv("AEGISLLM_MODEL", "llama3.2")
    client_key = os.getenv("AEGISLLM_CLIENT_API_KEY", "aegis-local-demo")
    bounty_tag = os.getenv("HIVE_BOUNTY_TAG", "aegis-langgraph-hive-demo")
    prompt = os.getenv(
        "AEGISLLM_DEMO_PROMPT",
        "In one sentence, explain why a local LLM gateway benefits from verifiable execution receipts.",
    )

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=client_key,
        temperature=0,
    )
    hive = HiveCallbackHandler(tag=bounty_tag, verbose=True)

    def call_model(state: AgentState) -> AgentState:
        return {"messages": [llm.invoke(state["messages"])]}

    builder = StateGraph(AgentState)
    builder.add_node("call_model", call_model)
    builder.add_edge(START, "call_model")
    builder.add_edge("call_model", END)
    graph = builder.compile()

    result = graph.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={"callbacks": [hive]},
    )
    final = result["messages"][-1]
    print(f"\nAegisLLM response:\n{final.content}\n")

    # Hive intentionally posts receipts on a daemon thread so receipt telemetry
    # can never block the agent. Keep this short-lived demo alive long enough for
    # the free receipt call to finish and print its public verification URL.
    time.sleep(5)
    print("If Hive returned a receipt, its https://thehiveryiq.com/verify/?id=... URL is printed above.")


if __name__ == "__main__":
    main()
