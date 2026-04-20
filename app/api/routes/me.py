from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.profile import ProfilePayload, UpdateProfileRequest, UserResponse

router = APIRouter(prefix="/me", tags=["me"])


def _build_user_response(user: User) -> UserResponse:
    return UserResponse(
        email=user.email,
        profile=ProfilePayload.model_validate(user.profile),
    )


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    return _build_user_response(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    profile = current_user.profile
    profile.display_name = payload.display_name
    profile.training_level = payload.training_level
    profile.preferred_environment = payload.preferred_environment
    profile.primary_goal = payload.primary_goal
    db.add(profile)
    db.commit()
    db.refresh(current_user)
    return _build_user_response(current_user)

