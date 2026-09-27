from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_salt,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordResponse,
    LoginResponse,
    SignupResponse,
)


def signup(db: Session, email: str, password: str) -> SignupResponse:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return SignupResponse(success=False, message="An account with this email already exists.")

    salt = generate_salt()
    user = User(
        email=email,
        salt=salt,
        hash_password=hash_password(password, salt),
    )
    db.add(user)
    db.commit()

    return SignupResponse(success=True, message="Account created successfully.")


def login(db: Session, email: str, password: str) -> LoginResponse:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return LoginResponse(success=False, message="Account not found.")

    if not verify_password(password, user.salt, user.hash_password):
                return LoginResponse(success=False, message="Invalid email or password.")

    token = create_access_token(user.id, user.email)
    return LoginResponse(success=True, message="Logged in successfully.", accessToken=token)


def change_password(db: Session, recovery_code: str, new_password: str) -> ChangePasswordResponse:
    user = db.query(User).filter(User.recovery_code == recovery_code).first()
    if not user:
        return ChangePasswordResponse(success=False, message="Invalid or expired recovery code.")

    salt = generate_salt()
    user.salt = salt
    user.hash_password = hash_password(new_password, salt)
    user.recovery_code = None  # single-use: invalidate after success
    db.commit()

    return ChangePasswordResponse(success=True, message="Password changed successfully.")
