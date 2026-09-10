"""
A small LangGraph agent that answers engineering questions ("why is my ArgoCD app stuck
OutOfSync?") by retrieving relevant chunks from a local runbook/docs folder and generating a
grounded answer, escalating to "ask a human" when nothing relevant is found.

This runs fully offline by default (no API key required) using a template-based generator built
from the retrieved text. Plugging in a real LLM for the generate step is a couple of lines â see
`llm_generate()` below and the README.

Graph shape:

    retrieve --> generate --> decide_escalate --> END

State flows through a single TypedDict so each node is a small, testable pure-ish function.
"""

from __future__ import annotations

import os
from typing import TypedDict

from langgraph.graph import StateGraph, END

from retrieval import Chunk, load_chunks, retrieve

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")

# Below this score, we don't trust the retrieval enough to answer confidently.
CONFIDENCE_THRESHOLD = 0.35


class AgentState(TypedDict, total=False):
    query: str
    hits: list[tuple[Chunk, float]]
    answer: str
    confidence: float
    escalate: bool


def retrieve_node(state: AgentState) -> AgentState:
    chunks = load_chunks(DOCS_DIR)
    hits = retrieve(state["query"], chunks, top_k=2)
    confidence = hits[0][1] if hits else 0.0
    return {**state, "hits": hits, "confidence": confidence}


def template_generate(query: str, hits: list[tuple[Chunk, float]]) -> str:
    """Default, offline generator: stitches the top retrieved chunk into a direct answer."""
    if not hits or hits[0][1] < CONFIDENCE_THRESHOLD:
        return "I couldn't find anything relevant in the docs for that question."
    top_chunk, _ = hits[0]
    return (
        f"Based on {top_chunk.source} -> \"{top_chunk.heading}\":\n\n{top_chunk.text}"
    )


def llm_generate(query: str, hits: list[tuple[Chunk, float]]) -> str:
    """
    Optional real-LLM generator. Only used if an LLM client is configured (see README) â
    otherwise `generate_node` falls back to `template_generate`. Kept separate so swapping in a
    real model doesn't touch the graph wiring at all.
    """
    from langchain_core.messages import HumanMessage, SystemMessage  # local import: optional dep

    context = "\n\n".join(f"[{c.source} - {c.heading}]\n{c.text}" for c, _ in hits)
    system = SystemMessage(
        content=(
            "You are an internal engineering assistant. Answer only from the provided context. "
            "If the context doesn't cover the question, say so plainly instead of guessing."
        )
    )
    human = HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")

    provider = os.environ.get("LLM_PROVIDER", "").lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model=os.environ.get("LLM_MODEL", "gpt-4o-mini"))
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        model = ChatAnthropic(model=os.environ.get("LLM_MODEL", "claude-3-5-sonnet-latest"))
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider!r}")

    response = model.invoke([system, human])
    return response.content


def generate_node(state: AgentState) -> AgentState:
    use_llm = bool(os.environ.get("LLM_PROVIDER"))
    if use_llm:
        answer = llm_generate(state["query"], state["hits"])
    else:
        answer = template_generate(state["query"], state["hits"])
    return {**state, "answer": answer}


def decide_escalate_node(state: AgentState) -> AgentState:
    escalate = state.get("confidence", 0.0) < CONFIDENCE_THRESHOLD
    if escalate:
        answer = (
            state.get("answer", "")
            + "\n\n(Low retrieval confidence â flagging for a human to double-check rather than "
            "answering confidently on thin evidence.)"
        )
        return {**state, "escalate": True, "answer": answer}
    return {**state, "escalate": False}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("decide_escalate", decide_escalate_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "decide_escalate")
    graph.add_edge("decide_escalate", END)

    return graph.compile()


def ask(query: str) -> AgentState:
    app = build_graph()
    return app.invoke({"query": query})


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Why is my ArgoCD application stuck OutOfSync?"
    result = ask(question)
    print(f"Q: {question}\n")
    print(f"A: {result['answer']}\n")
    print(f"[confidence={result['confidence']:.2f}, escalate={result['escalate']}]")
