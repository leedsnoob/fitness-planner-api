from __future__ import annotations

import httpx

from app.core.config import get_settings
from tests.helpers import auth_headers, generate_plan, register_user, seed_planner_exercises, update_profile


def _prepare_plan(db_client, monkeypatch) -> tuple[str, dict]:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    get_settings.cache_clear()
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    return token, plan


def test_explanation_timeout_retries_and_returns_503(db_client, monkeypatch) -> None:
    token, plan = _prepare_plan(db_client, monkeypatch)
    attempts = {"count": 0}

    def _timeout(*args, **kwargs):
        attempts["count"] += 1
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr("app.services.plan_explanations.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.services.plan_explanations._request_chat_completion", _timeout)

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 503
    assert response.json()["code"] == "provider_timeout"
    assert attempts["count"] == 3


def test_explanation_rate_limit_retries_and_returns_503(db_client, monkeypatch) -> None:
    token, plan = _prepare_plan(db_client, monkeypatch)
    attempts = {"count": 0}

    def _rate_limited(self, *args, **kwargs):
        attempts["count"] += 1
        request = httpx.Request("POST", "https://api.siliconflow.cn/v1/chat/completions")
        response = httpx.Response(429, request=request, json={"message": "slow down"})
        raise httpx.HTTPStatusError("rate limited", request=request, response=response)

    monkeypatch.setattr("app.services.plan_explanations.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.services.plan_explanations._request_chat_completion", _rate_limited)

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 503
    assert response.json()["code"] == "provider_rate_limited"
    assert attempts["count"] == 3


def test_explanation_upstream_5xx_retries_and_returns_503(db_client, monkeypatch) -> None:
    token, plan = _prepare_plan(db_client, monkeypatch)
    attempts = {"count": 0}

    def _server_error(self, *args, **kwargs):
        attempts["count"] += 1
        request = httpx.Request("POST", "https://api.siliconflow.cn/v1/chat/completions")
        response = httpx.Response(502, request=request, json={"message": "bad gateway"})
        raise httpx.HTTPStatusError("bad gateway", request=request, response=response)

    monkeypatch.setattr("app.services.plan_explanations.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.services.plan_explanations._request_chat_completion", _server_error)

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 503
    assert response.json()["code"] == "provider_unavailable"
    assert attempts["count"] == 3


def test_explanation_bad_payload_returns_502(db_client, monkeypatch) -> None:
    token, plan = _prepare_plan(db_client, monkeypatch)

    class _BrokenResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": []}

    monkeypatch.setattr(
        "app.services.plan_explanations._request_chat_completion",
        lambda *_args, **_kwargs: _BrokenResponse(),
    )

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 502
    assert response.json()["code"] == "provider_bad_response"


def test_explanation_empty_text_returns_502(db_client, monkeypatch) -> None:
    token, plan = _prepare_plan(db_client, monkeypatch)

    class _EmptyResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": [{"message": {"content": "   "}}]}

    monkeypatch.setattr(
        "app.services.plan_explanations._request_chat_completion",
        lambda *_args, **_kwargs: _EmptyResponse(),
    )

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 502
    assert response.json()["code"] == "provider_bad_response"
