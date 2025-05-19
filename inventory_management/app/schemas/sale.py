from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date

class SaleBase(BaseModel):
    """판매 기본 스키마"""
    product_id: int
    customer_name: str = Field(..., max_length=100)
    customer_contact: Optional[str] = Field(None, max_length=100)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=50)
    sale_date: datetime = Field(default_factory=datetime.now)
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    tax_rate: float = Field(10.0, ge=0, le=100)
    discount: float = Field(0.0, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    payment_due_date: Optional[date] = None
    payment_status: str = Field("unpaid", max_length=20)
    payment_method: Optional[str] = Field(None, max_length=50)
    paid_amount: Optional[float] = Field(None, ge=0)
    paid_date: Optional[datetime] = None
    status: str = Field("pending", max_length=20)  # pending, processing, shipped, delivered, cancelled, returned
    tracking_number: Optional[str] = Field(None, max_length=100)
    shipping_carrier: Optional[str] = Field(None, max_length=50)
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_zipcode: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

    @field_validator('payment_status')
    def validate_payment_status(cls, v):
        valid_statuses = ['unpaid', 'partial', 'paid', 'cancelled', 'refunded']
        if v not in valid_statuses:
            raise ValueError(f"결제 상태는 다음 중 하나여야 합니다: {', '.join(valid_statuses)}")
        return v
    
    @field_validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
        if v not in valid_statuses:
            raise ValueError(f"주문 상태는 다음 중 하나여야 합니다: {', '.join(valid_statuses)}")
        return v

class SaleCreate(SaleBase):
    """판매 생성 스키마"""
    pass

class SaleUpdate(BaseModel):
    """판매 업데이트 스키마"""
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_contact: Optional[str] = Field(None, max_length=100)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=50)
    sale_date: Optional[datetime] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    discount: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    payment_due_date: Optional[date] = None
    payment_status: Optional[str] = Field(None, max_length=20)
    payment_method: Optional[str] = Field(None, max_length=50)
    paid_amount: Optional[float] = Field(None, ge=0)
    paid_date: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=20)
    tracking_number: Optional[str] = Field(None, max_length=100)
    shipping_carrier: Optional[str] = Field(None, max_length=50)
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_zipcode: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class Sale(SaleBase):
    """응답용 판매 스키마"""
    id: int
    total_price: float
    created_at: datetime
    updated_at: datetime
    created_by: int

    class Config:
        from_attributes = True
