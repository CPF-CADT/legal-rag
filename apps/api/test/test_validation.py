from __future__ import annotations


def test_search_rejects_blank_query(client):
    response = client[0].post("/api/search", json={"query": "   "})

    assert response.status_code == 422


def test_search_rejects_top_k_outside_server_bounds(client):
    for top_k in (0, 21):
        response = client[0].post(
            "/api/search", json={"query": "តើច្បាប់មានអ្វីខ្លះ?", "top_k": top_k}
        )
        assert response.status_code == 422


def test_summarize_requires_query(client):
    response = client[0].post("/api/summarize", json={})

    assert response.status_code == 422
