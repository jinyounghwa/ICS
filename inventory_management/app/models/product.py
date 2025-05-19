from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, comment='상품명')
    code = Column(String(50), unique=True, nullable=False, comment='상품코드/SKU')
    category = Column(String(50), comment='분류')
    brand = Column(String(100), comment='브랜드')
    model = Column(String(100), comment='모델명')
    description = Column(String(500), comment='상세설명')
    current_stock = Column(Integer, default=0, nullable=False, comment='현재 재고 수량')
    minimum_stock = Column(Integer, default=0, nullable=False, comment='최소 재고 수량')
    price = Column(Float, default=0.0, nullable=False, comment='판매가격')
    cost_price = Column(Float, default=0.0, comment='원가')
    tax_included = Column(Boolean, default=True, comment='부가세 포함 여부')
    created_at = Column(DateTime, default=datetime.now, comment='등록일시')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='수정일시')
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment='회사 ID')
    
    # Relationships
    company = relationship("Company", back_populates="products")
    purchases = relationship("PurchaseInfo", back_populates="product", 
                          cascade="all, delete-orphan")
    sale_records = relationship("SaleRecord", back_populates="product", 
                      cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', code='{self.code}')>"
    
    def to_dict(self):
        """제품 정보를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'brand': self.brand,
            'model': self.model,
            'description': self.description,
            'current_stock': self.current_stock,
            'minimum_stock': self.minimum_stock,
            'price': self.price,
            'cost_price': self.cost_price,
            'tax_included': self.tax_included,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'company_id': self.company_id
        }
