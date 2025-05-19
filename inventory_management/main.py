import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# 애플리케이션 초기화
app = FastAPI(
    title="재고 관리 시스템 API",
    description="재고 관리를 위한 API 서비스",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 도메인을 지정하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from app.views import get_routers

# 모든 라우터 등록
for router in get_routers():
    app.include_router(router)

# 루트 엔드포인트
@app.get("/")
async def root():
    return {
        "message": "재고 관리 시스템 API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    # 데이터베이스 초기화
    from app import init_db
    init_db()
    
    # 개발 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )
