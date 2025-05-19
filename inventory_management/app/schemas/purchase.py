from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date

class PurchaseBase(BaseModel):
    """구매 기본 스키마"""
    product_id: int
    supplier_name: str = Field(..., max_length=100)
    business_number: Optional[str] = Field(None, max_length=20)
    supplier_contact: Optional[str] = Field(None, max_length=100)
    supplier_address: Optional[str] = None
    supplier_phone: Optional[str] = Field(None, max_length=20)
    supplier_email: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=50)
    purchase_date: datetime = Field(default_factory=datetime.now)
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    tax_rate: float = Field(10.0, ge=0, le=100)
    tax_included: bool = Field(True, description="부가세 포함 여부")
    discount: float = Field(0.0, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    payment_due_date: Optional[date] = None
    payment_status: str = Field("unpaid", max_length=20)
    payment_method: Optional[str] = Field(None, max_length=50)
    paid_amount: Optional[float] = Field(None, ge=0)
    paid_date: Optional[datetime] = None
    notes: Optional[str] = None

    @field_validator('payment_status')
    def validate_payment_status(cls, v):
        valid_statuses = ['unpaid', 'partial', 'paid', 'cancelled', 'refunded']
        if v not in valid_statuses:
            raise ValueError(f"결제 상태는 다음 중 하나여야 합니다: {', '.join(valid_statuses)}")
        return v

class PurchaseCreate(PurchaseBase):
    """구매 생성 스키마"""
    pass

class PurchaseUpdate(BaseModel):
    """구매 업데이트 스키마"""
    supplier_name: Optional[str] = Field(None, max_length=100)
    business_number: Optional[str] = Field(None, max_length=20)
    supplier_contact: Optional[str] = Field(None, max_length=100)
    supplier_address: Optional[str] = None
    supplier_phone: Optional[str] = Field(None, max_length=20)
    supplier_email: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=50)
    purchase_date: Optional[datetime] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    tax_included: Optional[bool] = Field(None, description="부가세 포함 여부")
    discount: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    payment_due_date: Optional[date] = None
    payment_status: Optional[str] = Field(None, max_length=20)
    payment_method: Optional[str] = Field(None, max_length=50)
    paid_amount: Optional[float] = Field(None, ge=0)
    paid_date: Optional[datetime] = None
    notes: Optional[str] = None

class Purchase(PurchaseBase):
    """응답용 구매 스키마"""
    id: int
    total_price: float
    created_at: datetime
    updated_at: datetime
    created_by: int

    class Config:
        from_attributes = True
