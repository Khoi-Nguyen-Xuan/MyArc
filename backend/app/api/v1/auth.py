from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    return auth_service.signup(db, payload.email, payload.password)


@router.post("/login", response_model=LoginResponse, response_model_by_alias=True)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.login(db, payload.email, payload.password)


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db)):
    return auth_service.change_password(db, payload.recovery_code, payload.newpassword)
