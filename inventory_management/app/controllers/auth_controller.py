from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import bcrypt

from ..models import User
from .. import SessionLocal

class AuthController:
    def __init__(self):
        self.current_user = None
        self.db = None
        
    def __del__(self):
        if hasattr(self, 'db') and self.db:
            self.db.close()
            self.db = None
        
    def get_db(self) -> Session:
        """새로운 데이터베이스 세션을 반환합니다."""
        if self.db is not None:
            self.db.close()
        self.db = SessionLocal()
        return self.db
    
    def login(self, username: str, password: str) -> tuple[bool, str]:
        """사용자 로그인 처리
        
        Args:
            username: 사용자명
            password: 비밀번호
            
        Returns:
            tuple: (성공 여부, 메시지)
        """
        try:
            print(f"\n=== 로그인 시도 ===")
            print(f"사용자명: {username}")
            
            # 새 세션 생성
            db = self.get_db()
            
            # 사용자 조회
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(f"❌ 사용자를 찾을 수 없음: {username}")
                return False, "사용자명 또는 비밀번호가 일치하지 않습니다."
            
            print(f"✅ 사용자 찾음: {user.username}")
            print(f"저장된 해시: {user.password_hash}")
            
            # 비밀번호 검증
            from app import verify_password
            
            if verify_password(password, user.password_hash):
                print("✅ 비밀번호 검증 성공")
            else:
                print("❌ 비밀번호 불일치")
                return False, "사용자명 또는 비밀번호가 일치하지 않습니다."
            
            # JWT 토큰 생성
            from datetime import datetime, timedelta
            import jwt
            from app.config import SECRET_KEY, ALGORITHM, save_auth_token
            
            print(f"\n=== 토큰 생성 시작 ===")
            print(f"사용자: {user.username}")
            print(f"회사 ID: {user.company_id}")
            
            # 토큰 만료 시간 설정 (예: 24시간)
            access_token_expires = timedelta(hours=24)
            expire = datetime.utcnow() + access_token_expires
            
            # 페이로드 생성
            to_encode = {
                "sub": user.username,
                "exp": expire,
                "company_id": user.company_id  # 회사 ID도 토큰에 포함
            }
            
            print(f"시크릿 키: {SECRET_KEY}")
            print(f"알고리즘: {ALGORITHM}")
            print(f"페이로드: {to_encode}")
            
            try:
                # JWT 토큰 생성
                access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
                print(f"생성된 토큰 타입: {type(access_token)}")
                print(f"생성된 토큰: {access_token}")
                
                # 토큰 저장 (문자열로 변환하여 저장)
                if isinstance(access_token, bytes):
                    token_str = access_token.decode('utf-8')
                    print(f"바이트를 문자열로 디코딩: {token_str}")
                else:
                    token_str = access_token
                
                print(f"저장할 토큰 문자열: {token_str}")
                
                # 토큰 저장 시도
                token_saved = save_auth_token(token_str)
                
                # 저장 후 토큰 확인
                from PySide6.QtCore import QSettings
                settings = QSettings()
                saved_token = settings.value('auth/token', '')
                print(f"저장 후 확인된 토큰: {saved_token}")
                
                if not token_saved:
                    print("❌ 토큰 저장에 실패했습니다.")
                    return False, "토큰 저장에 실패했습니다. 관리자에게 문의해주세요."
                
            except Exception as e:
                print(f"❌ 토큰 생성/저장 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            # 로그인 성공
            self.current_user = user
            return True, "로그인 성공"
            
        except SQLAlchemyError as e:
            return False, f"데이터베이스 오류가 발생했습니다: {str(e)}"
        except Exception as e:
            return False, f"오류가 발생했습니다: {str(e)}"
    
    def register_user(self, username: str, password: str, email: str, 
                     company_name: str, business_number: str, 
                     role: str = "user") -> tuple[bool, str]:
        """새 사용자 등록
        
        Args:
            username: 사용자명
            password: 비밀번호
            email: 이메일
            company_name: 회사명
            business_number: 사업자등록번호
            role: 사용자 역할 (기본값: USER)
            
        Returns:
            tuple: (성공 여부, 메시지)
        """
        db = self.get_db()
        try:
            # 사용자명 중복 확인
            if db.query(User).filter(User.username == username).first():
                return False, "이미 사용 중인 사용자명입니다."
                
            # 이메일 중복 확인
            if db.query(User).filter(User.email == email).first():
                return False, "이미 사용 중인 이메일입니다."
                
            # 회사 조회 또는 생성
            company = db.query(Company).filter(
                Company.business_number == business_number
            ).first()
            
            if not company:
                # 새 회사 생성
                company = Company(
                    name=company_name,
                    business_number=business_number,
                    address="",
                    phone=""
                )
                db.add(company)
                db.commit()
                db.refresh(company)
            
            # 비밀번호 해시 생성
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # 사용자 생성
            user = User(
                username=username,
                password_hash=hashed_password,
                email=email,
                role=role,
                company_id=company.id
            )
            
            db.add(user)
            db.commit()
            
            return True, "회원가입이 완료되었습니다."
            
        except SQLAlchemyError as e:
            db.rollback()
            return False, f"데이터베이스 오류가 발생했습니다: {str(e)}"
        except Exception as e:
            db.rollback()
            return False, f"오류가 발생했습니다: {str(e)}"
    
    def logout(self):
        """사용자 로그아웃 처리"""
        self.current_user = None
    
    def change_password(self, current_password: str, new_password: str) -> tuple[bool, str]:
        """비밀번호 변경
        
        Args:
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            tuple: (성공 여부, 메시지)
        """
        if not self.current_user:
            return False, "로그인이 필요합니다."
            
        try:
            # 현재 비밀번호 확인
            if not pwd_context.verify(current_password, self.current_user.password_hash):
                return False, "현재 비밀번호가 일치하지 않습니다."
            
            # 새 비밀번호로 업데이트
            self.current_user.password_hash = pwd_context.hash(new_password)
            self.db.commit()
            
            return True, "비밀번호가 성공적으로 변경되었습니다."
            
        except SQLAlchemyError as e:
            self.db.rollback()
            return False, f"데이터베이스 오류가 발생했습니다: {str(e)}"
        except Exception as e:
            self.db.rollback()
            return False, f"오류가 발생했습니다: {str(e)}"
