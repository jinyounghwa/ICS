from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class PurchaseInfo(Base):
    __tablename__ = 'purchase_infos'
    
    # 지불 상태 상수
    PAYMENT_PENDING = 'PENDING'
    PAYMENT_PARTIAL = 'PARTIAL'
    PAYMENT_PAID = 'PAID'
    PAYMENT_OVERDUE = 'OVERDUE'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, comment='제품 ID')
    
    # 공급업체 정보
    supplier_name = Column(String(100), nullable=False, comment='공급업체명')
    business_number = Column(String(20), comment='사업자등록번호')
    supplier_contact = Column(String(100), comment='담당자')
    supplier_address = Column(Text, comment='주소')
    supplier_phone = Column(String(20), comment='전화번호')
    supplier_email = Column(String(100), comment='이메일')
    
    # 구매 정보
    invoice_number = Column(String(50), comment='송장번호')
    purchase_date = Column(DateTime, default=datetime.now, nullable=False, comment='구매일자')
    expected_delivery_date = Column(DateTime, comment='예상 납기일')
    actual_delivery_date = Column(DateTime, comment='실제 납기일')
    
    # 수량 및 가격
    quantity = Column(Integer, default=0, nullable=False, comment='수량')
    unit_price = Column(Float, default=0.0, nullable=False, comment='단가')
    tax_rate = Column(Float, default=10.0, comment='세율(%)')
    tax_amount = Column(Float, default=0.0, comment='세액')
    discount = Column(Float, default=0.0, comment='할인금액')
    total_price = Column(Float, default=0.0, nullable=False, comment='총금액')
    
    # 결제 정보
    payment_terms = Column(String(50), comment='결제조건')
    payment_due_date = Column(DateTime, comment='결제기한')
    payment_status = Column(String(20), default=PAYMENT_PENDING, nullable=False, comment='결제상태')
    payment_method = Column(String(50), comment='결제방법')
    paid_amount = Column(Float, default=0.0, comment='결제금액')
    paid_date = Column(DateTime, comment='결제일자')
    
    # 기타 정보
    notes = Column(Text, comment='비고')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='생성일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    created_by = Column(Integer, ForeignKey('users.id'), comment='생성자')
    
    # Relationships
    product = relationship("Product", back_populates="purchases")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<PurchaseInfo(id={self.id}, product_id={self.product_id}, supplier='{self.supplier_name}')>"
    
    def calculate_totals(self):
        """총액 및 세액 계산"""
        subtotal = self.unit_price * self.quantity
        self.tax_amount = subtotal * (self.tax_rate / 100)
        self.total_price = subtotal + self.tax_amount - (self.discount or 0)
        return self.total_price
    
    def update_payment(self, amount, payment_date=None, method=None):
        """결제 정보 업데이트"""
        self.paid_amount = (self.paid_amount or 0) + amount
        
        if payment_date:
            self.paid_date = payment_date
        if method:
            self.payment_method = method
            
        # 결제 상태 업데이트
        if self.paid_amount >= self.total_price:
            self.payment_status = self.PAYMENT_PAID
        elif self.paid_amount > 0:
            self.payment_status = self.PAYMENT_PARTIAL
            
        # 연체 여부 확인
        if self.payment_due_date and datetime.now() > self.payment_due_date and self.payment_status != self.PAYMENT_PAID:
            self.payment_status = self.PAYMENT_OVERDUE
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'supplier_name': self.supplier_name,
            'business_number': self.business_number,
            'supplier_contact': self.supplier_contact,
            'supplier_address': self.supplier_address,
            'supplier_phone': self.supplier_phone,
            'supplier_email': self.supplier_email,
            'invoice_number': self.invoice_number,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'discount': self.discount,
            'total_price': self.total_price,
            'payment_terms': self.payment_terms,
            'payment_due_date': self.payment_due_date.isoformat() if self.payment_due_date else None,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'paid_amount': self.paid_amount,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_totals()
        """총 구매 가격 계산"""
        if self.quantity is not None and self.unit_price is not None:
            self.total_price = self.quantity * self.unit_price
    
    def __repr__(self):
        return f"<PurchaseInfo(id={self.id}, product_id={self.product_id}, supplier={self.supplier_name}, date={self.purchase_date})>"
