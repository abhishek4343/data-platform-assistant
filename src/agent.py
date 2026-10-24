"""A LangGraph agent that decides, per question, whether to search the docs, query the
pipeline_runs table, or both, and then answers with sources.

Graph:  START -> agent --(tool calls?)--> tools -> agent ... -> END

Run:  python src/agent.py "Which pipeline failed most in the last 30 days, and what does the runbook say about that error?"
"""
import operator
import sys
from typing import Annotated, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, require
from tools import TOOL_SPECS, call_tool

MAX_TURNS = 6  # safety limit on agent <-> tools round trips

SYSTEM_PROMPT = """You are a data platform assistant for data engineers.
You have two tools:
- search_docs: runbooks, incident reports and standards (how-to, policy, root cause).
- run_sql: read-only SQL on the pipeline_runs table (counts, trends, failures, volumes).
Decide which tool(s) each question needs; use both when it mixes data and process.
If a SQL query errors, read the error and fix the query.
Answer concisely. Cite documents as (doc_name > section) and show the key numbers from SQL.
If neither tool gives the answer, say so."""

client = anthropic.Anthropic(api_key=require(ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY"))


class State(TypedDict):
    messages: Annotated[list, operator.add]  # each node appends; LangGraph merges the lists
    turns: Annotated[int, operator.add]


def agent_node(state: State) -> dict:
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        tools=TOOL_SPECS,
        messages=state["messages"],
    )
    # Keep only the fields the API needs when this message is sent back on the next turn.
    content = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
    return {"messages": [{"role": "assistant", "content": content}], "turns": 1}


def tools_node(state: State) -> dict:
    last = state["messages"][-1]
    results = []
    for block in last["content"]:
        if block.get("type") == "tool_use":
            print(f"  -> {block['name']}: {block['input']}")
            output = call_tool(block["name"], block["input"])
            results.append({"type": "tool_result", "tool_use_id": block["id"], "content": output})
    return {"messages": [{"role": "user", "content": results}]}


def route(state: State) -> str:
    last = state["messages"][-1]
    wants_tools = any(b.get("type") == "tool_use" for b in last["content"])
    if wants_tools and state["turns"] < MAX_TURNS:
        return "tools"
    return END


def build_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def ask(question: str) -> str:
    final = build_graph().invoke({"messages": [{"role": "user", "content": question}], "turns": 0})
    last = final["messages"][-1]
    text = "".join(b.get("text", "") for b in last["content"] if b.get("type") == "text")
    return text or f"Stopped after {MAX_TURNS} steps without a final answer."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which pipeline failed most in the last 30 days, and what does the runbook say about that error?"
    print(f"Question: {q}\n")
    answer = ask(q)
    print(f"\n{answer}")
