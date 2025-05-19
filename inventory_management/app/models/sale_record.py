from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class SaleStatus:
    PENDING = 'pending'  # 주문 접수
    PROCESSING = 'processing'  # 처리 중
    SHIPPED = 'shipped'  # 배송 중
    DELIVERED = 'delivered'  # 배송 완료
    CANCELLED = 'cancelled'  # 취소됨
    RETURNED = 'returned'  # 반품됨

class SaleRecord(Base):
    __tablename__ = 'sale_records'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    sale_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    customer_name = Column(String(100))
    customer_contact = Column(String(100))
    customer_email = Column(String(100))
    status = Column(
        Enum(
            SaleStatus.PENDING, 
            SaleStatus.PROCESSING, 
            SaleStatus.SHIPPED,
            SaleStatus.DELIVERED,
            SaleStatus.CANCELLED,
            SaleStatus.RETURNED,
            name='sale_status'
        ),
        default=SaleStatus.PENDING,
        nullable=False
    )
    payment_method = Column(String(50))  # 'credit_card', 'bank_transfer', 'cash', etc.
    payment_status = Column(String(20), default='unpaid')  # 'paid', 'unpaid', 'partial'
    notes = Column(Text)
    
    # Relationships
    product = relationship("Product", back_populates="sale_records")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_total()
    
    def calculate_total(self):
        """총 판매 가격 계산"""
        if self.quantity is not None and self.unit_price is not None:
            self.total_price = self.quantity * self.unit_price
    
    def update_inventory(self, session):
        """판매 시 재고 업데이트"""
        if self.product:
            if self.product.current_stock >= self.quantity:
                self.product.current_stock -= self.quantity
                session.add(self.product)
                return True
            return False
        return False
    
    def __repr__(self):
        return f"<SaleRecord(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, total={self.total_price})>"
