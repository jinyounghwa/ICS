from pydantic import BaseModel, EmailStr, Field, field_validator, validator
from typing import Optional, Literal, List, Any, Dict
from datetime import datetime

# UserRole을 문자열 리터럴 타입으로 정의
UserRole = Literal["user", "admin", "super_admin"]

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명 (3~50자)")
    email: EmailStr = Field(..., description="이메일 주소")
    role: UserRole = Field("user", description="사용자 역할: user, admin, super_admin")
    company_id: Optional[int] = Field(None, description="소속 회사 ID (슈퍼 관리자는 제외 가능)")

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=6, description="비밀번호 (6자 이상)")
    
    @validator('company_id')
    def validate_company_id(cls, v, values):
        # 슈퍼 관리자는 company_id가 없을 수 있음
        if values.get('role') == 'super_admin' and v is None:
            return v
            
        # 일반 사용자와 관리자는 반드시 company_id가 있어야 함
        if v is None:
            raise ValueError("회사 ID는 필수입니다.")
        return v
        
    @validator('role')
    def validate_role(cls, v, values):
        # 슈퍼 관리자 생성은 슈퍼 관리자만 가능 (API 레벨에서 검증)
        return v

class UserUpdate(BaseModel):
    """사용자 정보 업데이트 스키마"""
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    password: Optional[str] = Field(None, min_length=6, description="비밀번호 (6자 이상)")
    role: Optional[UserRole] = Field(None, description="사용자 역할: user, admin, super_admin")
    company_id: Optional[int] = Field(None, description="소속 회사 ID (슈퍼 관리자만 수정 가능)")
    
    @validator('company_id')
    def validate_company_id(cls, v, values):
        # role이 제공된 경우에만 검증
        if 'role' in values and values['role'] == 'super_admin' and v is not None:
            # 슈퍼 관리자는 company_id가 없어야 함
            raise ValueError("슈퍼 관리자는 회사에 소속될 수 없습니다.")
        return v
        
    @validator('role')
    def validate_role(cls, v, values):
        # role이 super_admin으로 변경되는 경우 company_id는 None이어야 함
        if v == 'super_admin' and values.get('company_id') is not None:
            values['company_id'] = None
        return v

class UserInDBBase(UserBase):
    """데이터베이스 사용자 기본 스키마"""
    id: int
    is_active: bool = Field(..., description="계정 활성화 여부")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    class Config:
        from_attributes = True

class CompanyBase(BaseModel):
    """회사 기본 스키마"""
    id: int
    name: str
    
    class Config:
        from_attributes = True

class User(UserInDBBase):
    """응답용 사용자 스키마"""
    company: Optional[CompanyBase] = None
    
    class Config:
        from_attributes = True

class UserInDB(UserInDBBase):
    """데이터베이스 사용자 스키마"""
    password_hash: str
