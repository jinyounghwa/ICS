import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, Query
from sqlalchemy import text
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

from app import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.utils.auth import get_current_user, check_super_admin, check_admin

# 쿼리 실행 시간을 측정하는 데코레이터
def log_query_time(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            logger.info(f"{func.__name__} 쿼리 실행 시간: {end_time - start_time:.4f}초")
    return wrapper

def _execute_query(query: Query, skip: int, limit: int) -> Tuple[List[Dict[str, Any]], int]:
    """실제 쿼리를 실행하고 결과를 반환하는 헬퍼 함수"""
    # 총 개수 조회 (COUNT 쿼리 최적화를 위해 서브쿼리 사용)
    count_query = query.with_entities(Company.id).statement.with_only_columns([text('COUNT(1)')])
    total = query.session.execute(count_query).scalar() or 0
    
    # EXPLAIN ANALYZE를 사용하여 쿼리 실행 계획 확인
    explain_sql = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    explain_query = f"EXPLAIN ANALYZE {explain_sql}"
    
    try:
        # 실행 계획 로깅 (DEBUG 레벨에서만 출력)
        if logger.isEnabledFor(logging.DEBUG):
            explain_result = query.session.execute(text(explain_query)).fetchall()
            logger.debug("\n" + "\n".join([str(row) for row in explain_result]))
    except Exception as e:
        logger.warning(f"쿼리 실행 계획 조회 실패: {e}")
    
    # 실제 쿼리 실행 (필요한 필드만 선택적으로 로드)
    companies = query.offset(skip).limit(limit).all()
    
    # 결과를 딕셔너리로 변환
    result = [
        {
            "id": id,
            "name": name,
            "business_number": business_number,
            "address": address,
            "phone": phone
        }
        for id, name, business_number, address, phone in companies
    ]
    
    return result, total

router = APIRouter(prefix="/api/companies", tags=["companies"])

@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """새 회사 생성 (슈퍼 관리자만 가능)"""
    check_super_admin(current_user)
    
    # 회사명 중복 체크
    db_company = db.query(Company).filter(Company.name == company.name).first()
    if db_company:
        raise HTTPException(status_code=400, detail="이미 존재하는 회사명입니다.")
    
    # 사업자등록번호 중복 체크
    db_company = db.query(Company).filter(Company.business_number == company.business_number).first()
    if db_company:
        raise HTTPException(status_code=400, detail="이미 등록된 사업자등록번호입니다.")
    
    db_company = Company(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/", response_model=Dict[str, Any])
@log_query_time
def get_companies(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    회사 목록 조회 (슈퍼 관리자는 전체, 일반 관리자/사용자는 자신의 회사만)
    
    - **skip**: 건너뛸 레코드 수 (페이징용)
    - **limit**: 반환할 최대 레코드 수 (페이징용)
    - **search**: 회사명 또는 사업자등록번호로 검색 (선택사항)
    """
    try:
        logger.info(f"[회사 목록 조회] 사용자 역할: {current_user.role}, 회사 ID: {current_user.company_id}")
        start_time = time.time()
        
        # 필요한 필드만 선택적으로 로드
        query = db.query(
            Company.id,
            Company.name,
            Company.business_number,
            Company.address,
            Company.phone
        )
        
        # 검색어가 있는 경우 필터링
        if search:
            search = f"%{search}%"
            query = query.filter(
                (Company.name.ilike(search)) | 
                (Company.business_number.ilike(search))
            )
        
        # 정렬 (인덱스가 있는 필드로 정렬)
        query = query.order_by(Company.name.asc())
        
        # 사용자 역할에 따라 쿼리 필터링
        if current_user.role != "super_admin":
            # 일반 사용자/관리자는 자신의 회사만 조회
            query = query.filter(Company.id == current_user.company_id)
            total = 1  # 일반 사용자는 자신의 회사 1개만 조회 가능
            companies = query.all()
            
            # 결과를 딕셔너리로 변환
            result = [
                {
                    "id": id,
                    "name": name,
                    "business_number": business_number,
                    "address": address,
                    "phone": phone
                }
                for id, name, business_number, address, phone in companies
            ]
        else:
            # 슈퍼 관리자는 모든 회사 조회 (페이징 적용)
            result, total = _execute_query(query, skip, limit)
        
        # 응답 메타데이터 추가
        response = {
            "items": result,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + len(result)) < total if total > 0 else False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 실행 시간 로깅
        execution_time = time.time() - start_time
        logger.info(f"회사 목록 조회 완료: {len(result)}개 항목, 소요시간: {execution_time:.4f}초")
        
        return response
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[오류] 회사 목록 조회 중 오류 발생: {error_detail}")
        raise HTTPException(status_code=500, detail=f"회사 목록 조회 중 오류 발생: {str(e)}")

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """회사 상세 조회 (슈퍼 관리자 또는 해당 회사 관리자만 가능)"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    
    if current_user.role != "super_admin" and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    
    return company

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """회사 정보 수정 (슈퍼 관리자만 가능)"""
    check_super_admin(current_user)
    
    db_company = db.query(Company).filter(Company.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    
    # 업데이트할 필드만 추출 (None인 필드는 제외)
    update_data = company.model_dump(exclude_unset=True)
    
    # 회사명 중복 체크
    if 'name' in update_data and update_data['name'] != db_company.name:
        existing_company = db.query(Company).filter(Company.name == update_data['name']).first()
        if existing_company:
            raise HTTPException(status_code=400, detail="이미 존재하는 회사명입니다.")
    
    # 사업자등록번호 중복 체크
    if 'business_number' in update_data and update_data['business_number'] != db_company.business_number:
        existing_company = db.query(Company).filter(Company.business_number == update_data['business_number']).first()
        if existing_company:
            raise HTTPException(status_code=400, detail="이미 등록된 사업자등록번호입니다.")
    
    for key, value in update_data.items():
        setattr(db_company, key, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """회사 삭제 (슈퍼 관리자만 가능)"""
    try:
        print(f"[회사 삭제] 삭제 요청 - 회사 ID: {company_id}, 사용자: {current_user.username}")
        
        # 슈퍼 관리자 권한 확인
        check_super_admin(current_user)
        
        # 회사 조회
        db_company = db.query(Company).filter(Company.id == company_id).first()
        if not db_company:
            print(f"[회사 삭제] 오류 - 회사 ID {company_id}를 찾을 수 없음")
            raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
        
        # 연관된 사용자 확인
        user_count = db.query(User).filter(User.company_id == company_id).count()
        print(f"[회사 삭제] 회사에 속한 사용자 수: {user_count}")
        
        if user_count > 0:
            print(f"[회사 삭제] 오류 - 회사에 속한 사용자가 있어 삭제 불가")
            raise HTTPException(
                status_code=400, 
                detail="회사에 속한 사용자가 있어 삭제할 수 없습니다. 먼저 모든 사용자를 삭제해주세요."
            )
        
        # 회사 삭제
        company_name = db_company.name
        db.delete(db_company)
        db.commit()
        
        print(f"[회사 삭제] 성공 - 회사 '{company_name}' 삭제 완료")
        return {"message": f"회사 '{company_name}'가 삭제되었습니다."}
    except HTTPException as e:
        # HTTP 예외는 그대로 전파
        raise e
    except Exception as e:
        import traceback
        print(f"[오류] 회사 삭제 중 예외 발생: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"회사 삭제 중 오류 발생: {str(e)}")
