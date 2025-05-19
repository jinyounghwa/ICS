# 재고관리 시스템 (Inventory Management System)

PySide6 기반의 재고관리 시스템입니다. 제품의 입출고, 재고 관리, 판매 내역 등의 기능을 제공합니다.

## 개발 현황 (2025.05.19 개발 시작)

### 구현 완료 기능
- 사용자 인증 (로그인/회원가입)
  - 회원 등급: 최고관리자, 회사관리자, 사용자
- 제품 관리
  - 제품 등록/수정/삭제
  - 재고 현황 조회

### 개발 중인 기능
- 제품 관리
  - 제품 검색 및 필터링
- 판매 관리
  - 판매 내역 기록
  - 일/월/년 판매량 통계
- 구매처 관리
  - 구매처 정보 등록/관리
  - 구매 내역 추적

### 향후 개발 예정 기능
- AI 기반 판매 예측 (Gemini API 연동)
- 보고서 생성
  - 재고 현황 보고서
  - 판매 실적 보고서
  - PDF 형식의 견적서 발행

## 개발 환경

- Python 3.8+
- PySide6
- SQLAlchemy (SQLite)
- FastAPI (API 서버)
- JWT 인증

## 설치 방법

1. 저장소 복제
```bash
git clone https://github.com/jinyounghwa/ICS.git
cd inventory_management
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정하세요:
```
# 데이터베이스 설정
DATABASE_URL=sqlite:///data/inventory.db

# JWT 시크릿 키
SECRET_KEY=your_secret_key

```

4. 데이터베이스 초기화
```bash
python -c "from app import init_db; init_db()"
```

## 실행 방법

```bash
python run.py
```

### 기본 계정
- 관리자: admin / admin123
- 일반 사용자: user1 / user123

## 기능 사용법

### 제품 관리
1. 제품 추가: "추가" 버튼을 클릭하여 새 제품 정보를 입력합니다.
2. 제품 수정: 목록에서 제품을 선택한 후 "수정" 버튼을 클릭합니다.
3. 제품 삭제: 목록에서 제품을 선택한 후 "삭제" 버튼을 클릭합니다.

## 문제 해결

오류가 발생하면 다음 절차를 시도해보세요:

1. 로그 파일 확인: `logs/app.log`
2. 데이터베이스 연결 확인
3. 애플리케이션 재시작

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.
