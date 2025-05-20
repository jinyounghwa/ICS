from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)  # 이름으로 자주 검색되므로 인덱스 추가
    business_number = Column(String(20), unique=True, nullable=False, index=True)
    address = Column(String(200))
    phone = Column(String(20))
    
    # 복합 인덱스 추가 (자주 함께 조회되는 필드)
    __table_args__ = (
        Index('idx_company_name_business', 'name', 'business_number'),
    )
    
    # Relationships
    users = relationship("User", back_populates="company")
    products = relationship("Product", back_populates="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"
