from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

# UserRole을 문자열 리터럴 타입으로 정의
UserRole = Literal["user", "admin", "super_admin"]

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = "user"

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    """사용자 정보 업데이트 스키마"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None

class UserInDBBase(UserBase):
    """데이터베이스 사용자 기본 스키마"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    """응답용 사용자 스키마"""
    pass

class UserInDB(UserInDBBase):
    """데이터베이스 사용자 스키마"""
    password_hash: str
