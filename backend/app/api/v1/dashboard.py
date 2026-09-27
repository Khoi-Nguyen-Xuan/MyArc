from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardCurrentStateResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/current-state", response_model=DashboardCurrentStateResponse)
def current_state(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return dashboard_service.get_current_state(db, user.id)
