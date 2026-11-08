from __future__ import annotations


def test_summarize_returns_grounded_summary_and_sources(client):
    response = client[0].post(
        "/api/summarize", json={"query": "តើនិយោជកមានកាតព្វកិច្ចអ្វីខ្លះ?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]
    assert body["has_sufficient_evidence"] is True
    assert len(body["sources"]) == 1
    assert body["sources"][0]["article_text"] == (
        "COMPLETE ARTICLE BODY, including the non-matching paragraphs."
    )


def test_summarize_insufficient_evidence_is_empty_and_not_fabricated(client):
    client[2].insufficient = True

    response = client[0].post("/api/summarize", json={"query": "សំណួរមិនមានភស្តុតាង"})

    assert response.status_code == 200
    assert response.json() == {
        "query": "សំណួរមិនមានភស្តុតាង",
        "summary": None,
        "sources": [],
        "has_sufficient_evidence": False,
    }


def test_summarize_provider_failure_is_stable_and_non_sensitive(client):
    client[2].should_fail = True

    response = client[0].post("/api/summarize", json={"query": "សំណួរ"})

    assert response.status_code in (500, 502, 503)
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "LLM_UNAVAILABLE"
    assert "provider response" not in response.text.lower()
    assert "traceback" not in response.text.lower()
