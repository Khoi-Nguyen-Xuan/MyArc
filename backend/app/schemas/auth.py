from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class SignupResponse(BaseModel):
    success: bool
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    access_token: str | None = Field(default=None, alias="accessToken")


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # spec's exact (lowercase, no camelCase) key
    newpassword: str
    recovery_code: str = Field(alias="recoveryCode")


class ChangePasswordResponse(BaseModel):
    success: bool
    message: str
