# AI Agent LangGraph Demo â Engineering Docs Assistant

A small [LangGraph](https://github.com/langchain-ai/langgraph) agent that answers engineering
questions by retrieving relevant context from a local folder of runbooks and docs, then
generating a grounded answer â escalating to "ask a human" instead of guessing when nothing
relevant is found. Modeled on the kind of debugging/onboarding assistant pattern I've built
internal agentic tooling around before.

**Runs fully offline out of the box** â no API key required. The graph's `generate` step
defaults to a template-based generator built from the retrieved doc text, so the whole thing is
runnable and testable with zero external dependencies beyond `langgraph` itself. A real LLM
(OpenAI or Anthropic) can be swapped in with an environment variable, without touching the graph.

## Graph shape

```
retrieve --> generate --> decide_escalate --> END
```

- **retrieve**: keyword-overlap search over `docs/*.md`, split into per-section chunks (see
  `retrieval.py`)
- **generate**: builds an answer from the top retrieved chunk (template mode), or calls a
  configured LLM (LLM mode)
- **decide_escalate**: if retrieval confidence is below a threshold, flags the answer for human
  follow-up instead of answering confidently on thin evidence

## Usage

```bash
pip install -r requirements.txt
python agent.py "Why is my ArgoCD application stuck OutOfSync?"
```

```
Q: Why is my ArgoCD application stuck OutOfSync?

A: Based on incident-response-runbook.md (Triage steps) -> "...":

Check Argo CD sync status for the affected Application. An out-of-sync or failed sync can
leave a service running a stale or partially-applied configuration.

[confidence=0.62, escalate=False]
```

Ask something the docs don't cover and the agent says so, rather than making something up:

```bash
python agent.py "what should I have for lunch"
```

```
A: I couldn't find anything relevant in the docs for that question.

(Low retrieval confidence â flagging for a human to double-check rather than answering
confidently on thin evidence.)

[confidence=0.00, escalate=True]
```

## Running the tests

```bash
pip install -r requirements.txt
pytest tests/
```

## Using a real LLM instead of the offline template

Set `LLM_PROVIDER` before running:

```bash
export LLM_PROVIDER=openai        # or anthropic
export OPENAI_API_KEY=...         # or ANTHROPIC_API_KEY
pip install langchain-openai      # or langchain-anthropic
python agent.py "Why is my ArgoCD application stuck OutOfSync?"
```

`generate_node` checks `LLM_PROVIDER` and routes to `llm_generate()` instead of
`template_generate()` â the retrieval step and the escalation logic don't change either way.

## Project structure

```
agent.py       # LangGraph StateGraph: retrieve -> generate -> decide_escalate
retrieval.py   # dependency-light keyword-overlap retriever over docs/
docs/          # small internal-style knowledge base (onboarding, incident response, debugging)
tests/         # pytest coverage for retrieval and the full agent graph
```

## Why offline-by-default

A lot of agent demos are impossible to actually run without paying for API access, which makes
them hard to evaluate quickly. Keeping retrieval and a baseline generator fully local means
anyone can clone this and run it in under a minute, while the LLM hook shows the pattern for
plugging in a real model when quality needs to go up.
