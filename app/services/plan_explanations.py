from __future__ import annotations

import json

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.enums import ExplanationScope
from app.models.plan import PlanExplanation, PlanRevision, TrainingPlan
from app.models.user import User
from app.services.plan_views import build_plan_detail, build_revision_detail


PROVIDER_NAME = "siliconflow"


class PlanExplanationError(Exception):
    pass


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
    return (
        db.execute(_explanation_query().where(PlanExplanation.id == record.id))
        .scalar_one()
    )


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
    return (
        db.execute(_explanation_query().where(PlanExplanation.id == record.id))
        .scalar_one()
    )


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
        raise PlanExplanationError("SILICONFLOW_API_KEY is not configured.")

    payload = {
        "model": settings.siliconflow_model,
        "temperature": 0.3,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You explain structured fitness plans and revisions. "
                    "Use only the provided data, stay concise, and do not invent medical claims."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Explain this structured fitness planning result in clear Chinese. "
                    "Mention the training goal, key movement choices, and any safety or replacement logic.\n\n"
                    f"{json.dumps(input_snapshot, ensure_ascii=False)}"
                ),
            },
        ],
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{settings.siliconflow_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.siliconflow_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise PlanExplanationError("SiliconFlow explanation request failed.") from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PlanExplanationError("SiliconFlow returned an unexpected response payload.") from exc

    if isinstance(content, list):
        text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
        content = "\n".join(part for part in text_parts if part)
    if not isinstance(content, str) or not content.strip():
        raise PlanExplanationError("SiliconFlow returned empty explanation text.")
    return content.strip(), settings.siliconflow_model
