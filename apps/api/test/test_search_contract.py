from __future__ import annotations


def test_search_maps_complete_article_and_hides_server_paths(client):
    response = client[0].post(
        "/api/search", json={"query": "តើនិយោជកមានកាតព្វកិច្ចអ្វីខ្លះ?", "top_k": 5}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "តើនិយោជកមានកាតព្វកិច្ចអ្វីខ្លះ?"
    assert body["count"] == 1
    item = body["items"][0]
    assert item["rank"] == 1
    assert item["article_number"] == "7"
    assert item["article_text"] == (
        "COMPLETE ARTICLE BODY, including the non-matching paragraphs."
    )
    serialized = response.text
    assert "local_pdf_path" not in serialized
    assert "source_text_path" not in serialized
    assert "/srv/legal-rag" not in serialized


def test_search_returns_stable_retrieval_error_without_internal_details(
    client, monkeypatch
):
    client[1].should_fail = True

    response = client[0].post("/api/search", json={"query": "សំណួរ"})

    assert response.status_code in (500, 503)
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "RETRIEVAL_UNAVAILABLE"
    assert "chroma" not in response.text.lower()
    assert "/srv/legal-rag" not in response.text
    assert "traceback" not in response.text.lower()
