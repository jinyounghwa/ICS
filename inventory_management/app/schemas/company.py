from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CompanyBase(BaseModel):
    name: str = Field(..., description="회사명")
    business_number: str = Field(..., description="사업자등록번호")
    address: Optional[str] = Field(None, description="주소")
    phone: Optional[str] = Field(None, description="전화번호")
    
    @field_validator('business_number', mode='before')
    def validate_business_number(cls, v):
        # 사업자등록번호 유효성 검사 (숫자만 10자리)
        if not v.isdigit() or len(v) != 10:
            raise ValueError("유효한 사업자등록번호가 아닙니다. 숫자 10자리를 입력해주세요.")
        return v

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(CompanyBase):
    name: Optional[str] = Field(None, description="회사명")
    business_number: Optional[str] = Field(None, description="사업자등록번호")

class CompanyInDBBase(CompanyBase):
    id: int
    
    class Config:
        from_attributes = True

class CompanyResponse(CompanyInDBBase):
    pass
