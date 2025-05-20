import os
import json
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'

# 데이터베이스 설정
DATABASE_URL = f"sqlite:///{DATA_DIR}/inventory.db"

# 애플리케이션 설정
APP_NAME = "Inventory Management System"
VERSION = "1.0.0"

# API 설정
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# 세션 설정
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
TOKEN_KEY = 'inventory_auth_token'

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# PDF 출력 설정
PDF_OUTPUT_DIR = DATA_DIR / 'pdf'
STAMP_IMAGE_PATH = DATA_DIR / 'stamp.png'

# 필요한 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

def get_auth_header():
    """인증 헤더 생성"""
    from PySide6.QtCore import QSettings, QCoreApplication
    
    try:
        # QSettings 초기화 (애플리케이션 이름과 조직 이름 설정)
        QCoreApplication.setOrganizationName("ICS")
        QCoreApplication.setApplicationName("InventoryManagement")
        
        # QSettings 인스턴스 생성 (파일 기반 저장소 사용)
        settings = QSettings("ICS", "InventoryManagement")
        token = settings.value('auth/token', '')
        
        print(f"\n=== 인증 헤더 생성 ===")
        print(f"초기 토큰 값 타입: {type(token)}")
        print(f"초기 토큰 값: {token}")
        
        if not token:
            print("❌ 토큰이 없어 인증 헤더를 생성할 수 없습니다.")
            return {}
        
        # 토큰이 bytes 타입인 경우 문자열로 디코딩
        if isinstance(token, bytes):
            try:
                token = token.decode('utf-8')
                print(f"바이트에서 디코딩된 토큰: {token}")
            except UnicodeDecodeError:
                print("❌ 토큰 디코딩 실패")
                return {}
        
        # 토큰이 문자열로 감싸져 있는 경우 제거
        if isinstance(token, str):
            token = token.strip()
            if (token.startswith("b'") and token.endswith("'")) or \
               (token.startswith('"') and token.endswith('"')):
                token = token[1:-1]
                print(f"따옴표 제거 후 토큰: {token}")
        
        # 토큰 유효성 검사 (기본적인 형식 확인)
        if not isinstance(token, str) or len(token) < 10:  # 최소한의 길이 확인
            print(f"❌ 유효하지 않은 토큰 형식: {token}")
            return {}
            
        print(f"✅ 최종 토큰: {token[:10]}... (총 길이: {len(token)})")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        print(f"생성된 헤더: {headers}")
        return headers
        
    except Exception as e:
        print(f"❌ 인증 헤더 생성 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def save_auth_token(token: str):
    """인증 토큰 저장"""
    from PySide6.QtCore import QSettings, QCoreApplication, QStandardPaths
    import os
    
    print(f"\n=== 토큰 저장 시도 ===")
    print(f"저장할 토큰: {token}")
    print(f"저장할 토큰 타입: {type(token)}")
    
    try:
        # QSettings 초기화 (애플리케이션 이름과 조직 이름 설정)
        QCoreApplication.setOrganizationName("ICS")
        QCoreApplication.setApplicationName("InventoryManagement")
        
        # 저장 디렉토리 생성 (필요한 경우)
        config_dir = os.path.join(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation), "ICS")
        os.makedirs(config_dir, exist_ok=True)
        
        print(f"설정 파일 경로: {config_dir}")
        
        # QSettings 인스턴스 생성 (파일 기반 저장소 사용)
        settings = QSettings("ICS", "InventoryManagement")
        
        # 토큰이 bytes 타입인지 확인하고 문자열로 변환
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            print(f"바이트를 문자열로 변환: {token}")
        
        # 토큰이 이미 문자열로 감싸져 있는지 확인하고 제거
        token = token.strip()
        if (token.startswith("'") and token.endswith("'")) or \
           (token.startswith('"') and token.endswith('"')):
            token = token[1:-1]
            print(f"따옴표 제거 후 토큰: {token}")
        
        # 토큰 유효성 검사
        if not token or len(token) < 10:
            print("❌ 유효하지 않은 토큰 형식")
            return False
        
        # 토큰 저장
        settings.setValue('auth/token', token)
        settings.sync()  # 설정값을 즉시 저장
        
        # 저장된 토큰 확인
        settings = QSettings("ICS", "InventoryManagement")  # 새 인스턴스로 확인
        saved_token = settings.value('auth/token', '')
        
        print(f"저장된 토큰 확인: {saved_token}")
        print(f"저장된 토큰 타입: {type(saved_token)}")
        
        # 저장 여부 확인
        if not saved_token or (isinstance(saved_token, str) and not saved_token.strip()):
            print("❌ 토큰이 비어있습니다.")
            return False
            
        # 토큰 비교 (타입 변환 후 비교)
        saved_str = str(saved_token).strip()
        token_str = str(token).strip()
        
        if saved_str != token_str:
            print(f"❌ 토큰 불일치. 저장된: '{saved_str}', 예상: '{token_str}'")
            return False
            
        print("✅ 토큰 저장 성공")
        return True
        
    except Exception as e:
        print(f"❌ 토큰 저장 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def clear_auth_token():
    """인증 토큰 삭제"""
    from PySide6.QtCore import QSettings, QCoreApplication
    
    try:
        # QSettings 초기화 (애플리케이션 이름과 조직 이름 설정)
        QCoreApplication.setOrganizationName("ICS")
        QCoreApplication.setApplicationName("InventoryManagement")
        
        # QSettings 인스턴스 생성 (파일 기반 저장소 사용)
        settings = QSettings("ICS", "InventoryManagement")
        
        # 토큰 삭제
        settings.remove('auth/token')
        settings.sync()  # 변경사항 즉시 적용
        
        # 삭제 확인
        token = settings.value('auth/token', '')
        if not token:
            print("✅ 토큰 삭제 성공")
        else:
            print("❌ 토큰 삭제 실패")
            
    except Exception as e:
        print(f"❌ 토큰 삭제 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
