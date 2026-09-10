import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import ask, DOCS_DIR, CONFIDENCE_THRESHOLD  # noqa: E402
from retrieval import load_chunks, retrieve  # noqa: E402


def test_docs_load_into_chunks():
    chunks = load_chunks(DOCS_DIR)
    assert len(chunks) > 0
    assert any("Sev1" in c.text or "Sev1" in c.heading for c in chunks)


def test_retrieve_finds_relevant_chunk_for_argocd_question():
    chunks = load_chunks(DOCS_DIR)
    hits = retrieve("Why is my ArgoCD application stuck OutOfSync?", chunks, top_k=2)
    assert len(hits) > 0
    top_chunk, score = hits[0]
    assert "OutOfSync" in top_chunk.heading or "argo" in top_chunk.text.lower()
    assert score > 0


def test_retrieve_returns_nothing_for_unrelated_query():
    chunks = load_chunks(DOCS_DIR)
    hits = retrieve("what is the best recipe for banana bread", chunks, top_k=2)
    assert hits == []


def test_agent_answers_grounded_question():
    os.environ.pop("LLM_PROVIDER", None)  # force offline template mode for this test
    result = ask("Why is my ArgoCD application stuck OutOfSync?")
    assert result["answer"]
    assert result["confidence"] > 0
    assert "escalate" in result


def test_agent_escalates_on_unrelated_question():
    os.environ.pop("LLM_PROVIDER", None)
    result = ask("what should I have for lunch")
    assert result["escalate"] is True
    assert "flagging for a human" in result["answer"]


def test_confidence_threshold_is_reasonable():
    # sanity check that the threshold is a real probability-like value, not left at a placeholder
    assert 0 < CONFIDENCE_THRESHOLD < 1
