from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from app.config import DATABASE_URL, DATA_DIR
import os
import bcrypt

# 데이터베이스 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)


# 데이터베이스 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """데이터베이스 세션을 생성하는 함수"""
    return SessionLocal()

# 모델 임포트 (SQLAlchemy가 모델을 인식하도록)
from app.models import *

def create_password_hash(password: str) -> str:
    """비밀번호 해시 생성"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def init_db():
    """데이터베이스 테이블 생성 및 초기 데이터 삽입"""
    from app.models.base import Base
    import bcrypt
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 초기 데이터 삽입
    db = SessionLocal()
    try:
        # 테스트용 비밀번호 해시 생성 및 검증
        test_password = "admin123"
        hashed_password = create_password_hash(test_password)
        
        print(f"\n=== 해시 생성 및 검증 테스트 ===")
        print(f"비밀번호: {test_password}")
        print(f"생성된 해시: {hashed_password}")
        
        if verify_password(test_password, hashed_password):
            print("✅ 해시 검증 성공")
        else:
            print("❌ 해시 검증 실패")
            raise ValueError("해시 검증에 실패했습니다.")
        
        # 기본 회사가 있는지 확인
        company = db.query(Company).filter(Company.business_number == "123-45-67890").first()
        if not company:
            # 기본 회사 생성
            company = Company(
                name="테스트 회사",
                business_number="123-45-67890",
                address="서울시 강남구 테헤란로",
                phone="02-123-4567"
            )
            db.add(company)
            db.commit()
            db.refresh(company)
        
        # 관리자 계정이 있는지 확인
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            # 관리자 사용자 생성
            admin = User(
                username="admin",
                password_hash=hashed_password,
                email="admin@example.com",
                role="super_admin",
                company_id=company.id
            )
            db.add(admin)
            
            # 테스트 사용자 생성
            test_user_password = "user123"
            user_hashed_password = create_password_hash(test_user_password)
            
            print(f"\n=== 테스트 사용자 계정 ===")
            print(f"사용자명: user1")
            print(f"비밀번호: {test_user_password}")
            print(f"해시: {user_hashed_password}")
            
            if not verify_password(test_user_password, user_hashed_password):
                raise ValueError("테스트 사용자 비밀번호 해시 검증에 실패했습니다.")
            
            test_user = User(
                username="user1",
                password_hash=user_hashed_password,
                email="user1@example.com",
                role="user",
                company_id=company.id
            )
            db.add(test_user)
            
            db.commit()
            print("데이터베이스 초기화가 완료되었습니다.")
            print(f"관리자 계정: admin / admin123")
            print(f"일반 사용자 계정: user1 / user123")
        
    except Exception as e:
        db.rollback()
        print(f"데이터베이스 초기화 중 오류가 발생했습니다: {e}")
        raise
    finally:
        db.close()
