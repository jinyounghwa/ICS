# 재고관리 시스템 (Inventory Management System)

PySide6 기반의 재고관리 시스템입니다. 제품의 입출고, 재고 관리, 판매 예측 등의 기능을 제공합니다.

## 주요 기능

- 사용자 인증 (로그인/회원가입)
  - 회원 등급: 최고관리자, 회사관리자, 사용자
- 제품 관리
  - 제품 등록/수정/삭제
  - 재고 현황 조회
  - 제품 검색 및 필터링
- 판매 관리
  - 판매 내역 기록
  - 일/월/년 판매량 통계
  - AI 기반 판매 예측 (Gemini API 연동)
- 구매처 관리
  - 구매처 정보 등록/관리
  - 구매 내역 추적
- 보고서 생성
  - 재고 현황 보고서
  - 판매 실적 보고서
  - PDF 형식의 견적서 발행

## 개발 환경

- Python 3.8+
- PySide6
- SQLAlchemy (SQLite)
- Gemini API (AI 예측)
- WeasyPrint (PDF 생성)

## 설치 방법

1. 저장소 클론
```bash
git clone [저장소 주소]
cd inventory_management
```

2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:
```
# 데이터베이스 설정
DATABASE_URL=sqlite:///data/inventory.db

# Gemini API 키 (선택사항)
GEMINI_API_KEY=your_gemini_api_key

# 애플리케이션 시크릿 키
SECRET_KEY=your_secret_key
```

5. 데이터베이스 초기화
```bash
python -c "from app import init_db; init_db()"
```

## 실행 방법

```bash
python run.py
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.
