from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = "Strategic Member"
    location: Optional[str] = "India"

class UserCreate(UserBase):
    password: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr

class PasswordLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class GoogleAuth(BaseModel):
    token: str
    name: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
