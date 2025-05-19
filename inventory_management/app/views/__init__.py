# 뷰 모듈 초기화 파일
# 이 파일은 뷰 패키지를 초기화하는 데 사용됩니다.

# 뷰 라우터 임포트
from . import auth, products, purchases, sales

# 라우터 목록
def get_routers():
    """등록된 모든 라우터를 반환합니다."""
    return [
        auth.router,
        products.router,
        purchases.router,
        sales.router,
    ]
