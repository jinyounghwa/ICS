from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

# UserRole을 문자열로 정의
USER_ROLES = ["super_admin", "admin", "user"]

__all__ = ["User", "USER_ROLES"]

class User(BaseModel):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), default="user", nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="users")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
