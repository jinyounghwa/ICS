import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, MetaData

# 데이터베이스 URL 직접 설정
BASE_DIR = Path(__file__).parent
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/inventory.db"

# 필요한 모델 임포트 (에러 방지를 위해 주석 처리)
# from app.models.base import Base
# from app.models.user import User
# from app.models.product import Product
# from app.models.purchase_info import PurchaseInfo
# from app.models.sale_record import SaleRecord
# from app.models.company import Company

def check_tables():
    # 데이터베이스 엔진 생성
    engine = create_engine(DATABASE_URL)
    
    # 인스펙터 생성
    inspector = inspect(engine)
    
    # 데이터베이스 연결 확인
    with engine.connect() as conn:
        print(f"데이터베이스에 성공적으로 연결되었습니다: {DATABASE_URL}")
    
    # 모든 테이블 이름 가져오기
    tables = inspector.get_table_names()
    
    if not tables:
        print("\n⚠️ 데이터베이스에 테이블이 없습니다.")
        return
    
    print("\n=== 데이터베이스에 있는 테이블 목록 ===")
    for table in tables:
        print(f"\n📋 테이블: {table}")
        
        # 각 테이블의 컬럼 정보 출력
        columns = inspector.get_columns(table)
        print(f"  📌 컬럼:")
        for column in columns:
            # 컬럼 제약 조건 확인
            constraints = []
            if column.get('primary_key'):
                constraints.append("PK")
            if column.get('nullable') is False:
                constraints.append("NOT NULL")
            if column.get('unique'):
                constraints.append("UNIQUE")
                
            constraint_str = f" ({', '.join(constraints)})" if constraints else ""
            default_str = f" DEFAULT {column['default']}" if column.get('default') is not None else ""
            
            print(f"    - {column['name']} ({column['type']}){constraint_str}{default_str}")
        
        # 테이블의 인덱스 정보 출력
        indexes = inspector.get_indexes(table)
        if indexes:
            print(f"  🔍 인덱스:")
            for idx in indexes:
                unique = "UNIQUE " if idx.get('unique') else ""
                print(f"    - {unique}INDEX {idx['name']} ({', '.join(idx['column_names'])})")

if __name__ == "__main__":
    check_tables()
