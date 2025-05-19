from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    """제품 기본 스키마"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    current_stock: int = Field(0, ge=0)
    minimum_stock: int = Field(0, ge=0)
    price: float = Field(..., gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    tax_included: bool = Field(True, description="부가세 포함 여부")

class ProductCreate(ProductBase):
    """제품 생성 스키마"""
    pass

class ProductUpdate(BaseModel):
    """제품 업데이트 스키마"""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    current_stock: Optional[int] = Field(None, ge=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, gt=0)
    tax_included: Optional[bool] = Field(None, description="부가세 포함 여부")

class Product(ProductBase):
    """응답용 제품 스키마"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
