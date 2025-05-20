# 뷰 모듈 초기화 파일
# 이 파일은 뷰 패키지를 초기화하는 데 사용됩니다.

# 뷰 라우터 임포트
from . import auth, products, purchases, sales

# API 라우터 임포트
from app.api import user as user_api
from app.api import company as company_api

# 뷰 컴포넌트 임포트
from .user_management_dialog import UserManagementDialog

# 라우터 목록
def get_routers():
    """등록된 모든 라우터를 반환합니다."""
    return [
        auth.router,
        products.router,
        purchases.router,
        sales.router,
        user_api.router,      # 사용자 관리 API
        company_api.router,   # 회사 관리 API
    ]

# 공개할 모듈 목록
__all__ = [
    'UserManagementDialog',
    # 기타 필요한 컴포넌트들...
]
