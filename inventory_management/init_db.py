import os
import sys
import traceback
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = str(Path(__file__).resolve().parent)
sys.path.append(project_root)

def init_database():
    """데이터베이스 초기화"""
    try:
        print("데이터베이스 초기화를 시작합니다...")
        
        # 데이터베이스 파일이 존재하면 삭제
        db_path = os.path.join(project_root, 'data', 'inventory.db')
        if os.path.exists(db_path):
            print(f"기존 데이터베이스 파일을 삭제합니다: {db_path}")
            os.remove(db_path)
        
        # 데이터 디렉토리 생성
        data_dir = os.path.join(project_root, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 데이터베이스 초기화
        from app import init_db
        init_db()
        
        print("\n✅ 데이터베이스 초기화가 완료되었습니다.")
        print("\n애플리케이션을 실행하려면 다음 명령어를 입력하세요:")
        print("  python run.py")
        
    except Exception as e:
        print("\n❌ 오류가 발생했습니다:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()
