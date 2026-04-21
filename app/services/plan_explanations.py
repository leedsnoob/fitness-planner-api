from __future__ import annotations

import json
import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.enums import ExplanationScope
from app.models.plan import PlanExplanation, PlanRevision, TrainingPlan
from app.models.user import User
from app.services.plan_views import build_plan_detail, build_revision_detail


PROVIDER_NAME = "siliconflow"


class PlanExplanationError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: object = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def create_plan_explanation(db: Session, current_user: User, plan: TrainingPlan) -> PlanExplanation:
    input_snapshot = {
        "scope": ExplanationScope.PLAN.value,
        "plan": build_plan_detail(plan).model_dump(mode="json"),
    }
    output_text, model_name = generate_explanation_text(input_snapshot)
    record = PlanExplanation(
        user_id=current_user.id,
        plan_id=plan.id,
        revision_id=None,
        explanation_scope=ExplanationScope.PLAN,
        provider=PROVIDER_NAME,
        model_name=model_name,
        input_snapshot=input_snapshot,
        output_text=output_text,
    )
    db.add(record)
    db.commit()
    return db.execute(_explanation_query().where(PlanExplanation.id == record.id)).scalar_one()


def create_revision_explanation(
    db: Session,
    current_user: User,
    plan: TrainingPlan,
    revision: PlanRevision,
) -> PlanExplanation:
    input_snapshot = {
        "scope": ExplanationScope.REVISION.value,
        "plan": build_plan_detail(plan).model_dump(mode="json"),
        "revision": build_revision_detail(revision).model_dump(mode="json"),
    }
    output_text, model_name = generate_explanation_text(input_snapshot)
    record = PlanExplanation(
        user_id=current_user.id,
        plan_id=plan.id,
        revision_id=revision.id,
        explanation_scope=ExplanationScope.REVISION,
        provider=PROVIDER_NAME,
        model_name=model_name,
        input_snapshot=input_snapshot,
        output_text=output_text,
    )
    db.add(record)
    db.commit()
    return db.execute(_explanation_query().where(PlanExplanation.id == record.id)).scalar_one()


def list_plan_explanations(
    db: Session,
    user_id: int,
    *,
    plan_id: int,
    revision_id: int | None = None,
) -> list[PlanExplanation]:
    statement = _explanation_query().where(
        PlanExplanation.user_id == user_id,
        PlanExplanation.plan_id == plan_id,
    )
    if revision_id is not None:
        statement = statement.where(PlanExplanation.revision_id == revision_id)
    return list(db.execute(statement).scalars().all())


def _explanation_query():
    return (
        select(PlanExplanation)
        .options(selectinload(PlanExplanation.revision))
        .order_by(PlanExplanation.id.asc())
    )


def generate_explanation_text(input_snapshot: dict) -> tuple[str, str]:
    settings = get_settings()
    if not settings.siliconflow_api_key:
        raise PlanExplanationError(
            status_code=503,
            code="provider_not_configured",
            message="SILICONFLOW_API_KEY is not configured.",
        )

    payload = {
        "model": settings.siliconflow_model,
        "temperature": 0.3,
        "messages": build_explanation_messages(input_snapshot),
    }
    timeout = httpx.Timeout(
        connect=settings.siliconflow_connect_timeout_seconds,
        read=settings.siliconflow_read_timeout_seconds,
        write=settings.siliconflow_read_timeout_seconds,
        pool=settings.siliconflow_connect_timeout_seconds,
    )

    last_error: PlanExplanationError | None = None
    attempts = settings.siliconflow_max_retries + 1
    with httpx.Client(timeout=timeout) as client:
        for attempt in range(attempts):
            try:
                response = _request_chat_completion(client, settings, payload)
                data = response.json()
                content = _extract_explanation_text(data)
                return content, settings.siliconflow_model
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                last_error = PlanExplanationError(
                    status_code=503,
                    code="provider_timeout",
                    message="SiliconFlow explanation request timed out.",
                )
                if attempt < settings.siliconflow_max_retries:
                    _sleep_before_retry(settings, attempt)
                    continue
                raise last_error from exc
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code == 429:
                    last_error = PlanExplanationError(
                        status_code=503,
                        code="provider_rate_limited",
                        message="SiliconFlow rate limited the explanation request.",
                        details=_safe_error_details(exc.response),
                    )
                    if attempt < settings.siliconflow_max_retries:
                        _sleep_before_retry(settings, attempt)
                        continue
                    raise last_error from exc
                if 500 <= status_code < 600:
                    last_error = PlanExplanationError(
                        status_code=503,
                        code="provider_unavailable",
                        message="SiliconFlow is temporarily unavailable.",
                        details=_safe_error_details(exc.response),
                    )
                    if attempt < settings.siliconflow_max_retries:
                        _sleep_before_retry(settings, attempt)
                        continue
                    raise last_error from exc
                raise PlanExplanationError(
                    status_code=502,
                    code="provider_request_failed",
                    message="SiliconFlow rejected the explanation request.",
                    details=_safe_error_details(exc.response),
                ) from exc
            except httpx.HTTPError as exc:
                raise PlanExplanationError(
                    status_code=503,
                    code="provider_unavailable",
                    message="SiliconFlow explanation request failed.",
                ) from exc
            except ValueError as exc:
                raise PlanExplanationError(
                    status_code=502,
                    code="provider_bad_response",
                    message=str(exc),
                ) from exc

    if last_error is not None:
        raise last_error
    raise PlanExplanationError(
        status_code=503,
        code="provider_unavailable",
        message="SiliconFlow explanation request failed.",
    )


def _request_chat_completion(client: httpx.Client, settings: Settings, payload: dict) -> httpx.Response:
    response = client.post(
        f"{settings.siliconflow_base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.siliconflow_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    response.raise_for_status()
    return response


def _extract_explanation_text(data: dict) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("SiliconFlow returned an unexpected response payload.") from exc

    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        content = "\n".join(part for part in text_parts if part)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("SiliconFlow returned empty explanation text.")
    return content.strip()


def _safe_error_details(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return response.text or None


def _sleep_before_retry(settings: Settings, attempt: int) -> None:
    delay = settings.siliconflow_retry_backoff_seconds * (attempt + 1)
    time.sleep(delay)


def build_explanation_messages(input_snapshot: dict) -> list[dict[str, str]]:
    scope = input_snapshot.get("scope", "PLAN")
    if scope == ExplanationScope.REVISION.value:
        task_instruction = (
            "Explain a single revision to a weekly training plan. "
            "Describe why the original exercise was replaced, what constraint triggered the change, "
            "and why the new exercise still matches the training intent."
        )
    else:
        task_instruction = (
            "Explain a full weekly training plan. "
            "Describe the goal, split, major movement choices, and how constraints shaped the final plan."
        )

    return [
        {
            "role": "system",
            "content": (
                "You are explaining outputs from a constraint-aware fitness planning API. "
                "The system is a data-driven web API that generates weekly plans, revises exercises when constraints change, "
                "and stores structured score breakdowns and history. "
                "Use only the provided data, stay concise, explain choices clearly, and do not invent medical claims. "
                "If a detail is not explicitly present in the input, say it is not shown instead of inferring it."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{task_instruction} "
                "Write in clear Chinese for an end user. Mention the training goal, key exercise choices, "
                "constraint handling, and any safety or replacement logic that is explicitly present.\n\n"
                f"{json.dumps(input_snapshot, ensure_ascii=False)}"
            ),
        },
    ]
