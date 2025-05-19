from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Company(Base):
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    business_number = Column(String(20), unique=True, nullable=False)
    address = Column(String(200))
    phone = Column(String(20))
    
    # Relationships
    users = relationship("User", back_populates="company")
    products = relationship("Product", back_populates="company")
    
    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"
