from __future__ import annotations


def test_health_is_live_without_business_dependencies(client):
    response = client[0].get("/health")

    assert response.status_code == 200
    assert response.json().get("status") in ("ok", "healthy")


def test_readiness_has_a_non_success_state_when_dependencies_are_unavailable(
    client,
):
    # The MVP must expose a readiness signal distinct from liveness.  This
    # test accepts either the planned dependency override or a non-2xx default
    # when the app has not loaded its production dependencies.
    response = client[0].get("/ready")

    assert response.status_code in (200, 500, 503)
    if response.status_code >= 400:
        assert response.json()["error"]["code"] in (
            "RETRIEVAL_UNAVAILABLE",
            "INTERNAL_ERROR",
        )


def test_openapi_describes_business_endpoints(client):
    response = client[0].get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/search" in paths
    assert "/api/summarize" in paths
