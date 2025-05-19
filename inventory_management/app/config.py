import os
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

# 세션 설정
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# PDF 출력 설정
PDF_OUTPUT_DIR = DATA_DIR / 'pdf'
STAMP_IMAGE_PATH = DATA_DIR / 'stamp.png'

# 필요한 디렉토리 생성
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
