from pydantic import BaseModel

class Token(BaseModel):
    """액세스 토큰 응답 스키마"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    username: str | None = None
