from fastapi import APIRouter, Depends, HTTPException, status, Body
import sqlalchemy
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app import get_db
from app.models.user import User as UserModel
from app.models.company import Company
from app.schemas.user import User, UserCreate, UserUpdate, UserRole
from app.utils.auth import get_current_user, check_super_admin, check_admin, get_password_hash

router = APIRouter(prefix="/api/users", tags=["users"])

def has_company_permission(current_user: UserModel, target_company_id: Optional[int]) -> bool:
    """현재 사용자가 대상 회사에 대한 권한이 있는지 확인"""
    # 슈퍼 관리자는 모든 회사에 접근 가능
    if current_user.role == "super_admin":
        return True
    
    # 회사 관리자/사용자는 자신의 회사만 접근 가능
    if current_user.company_id == target_company_id:
        return True
    
    return False

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """새 사용자 생성"""
    # 사용자명 중복 체크
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다.")
    
    # 이메일 중복 체크
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일 주소입니다.")
    
    # 슈퍼 관리자 생성 권한 확인
    if user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼 관리자만 슈퍼 관리자 계정을 생성할 수 있습니다."
        )
    
    # 슈퍼 관리자인 경우 company_id는 항상 None
    if user.role == "super_admin":
        company_id = None
    else:
        company_id = user.company_id
        
        # 회사 ID가 없는 경우 기본 회사 생성 또는 사용
        if not company_id:
            try:
                # 기본 회사 생성 또는 조회
                default_company = db.query(Company).filter(Company.name == "기본 회사").first()
                if not default_company:
                    print("[기본 회사 생성] 새로운 기본 회사를 생성합니다.")
                    default_company = Company(
                        name="기본 회사",
                        business_number="000-00-00000",  # 사업자번호 추가
                        address="기본 주소",
                        phone="000-0000-0000"
                    )
                    db.add(default_company)
                    db.commit()
                    db.refresh(default_company)
                company_id = default_company.id
                print(f"[기본 회사 사용] 회사 ID: {company_id}")
            except Exception as e:
                print(f"[오류] 기본 회사 생성 중 오류 발생: {str(e)}")
                # 오류가 발생해도 계속 진행하도록 함
                company_id = 1  # 기본값으로 1 사용
        # 회사 권한 확인 (슈퍼 관리자는 모든 회사에 접근 가능)
        elif current_user.role != "super_admin" and not has_company_permission(current_user, company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 회사에 대한 권한이 없습니다."
            )
    
    # 사용자 생성
    hashed_password = get_password_hash(user.password)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        company_id=company_id,  # 위에서 계산한 company_id 사용
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 회사 정보를 다시 로드
    db_user = db.query(UserModel).options(joinedload(UserModel.company)).filter(UserModel.id == db_user.id).first()
    
    # 응답 모델에 맞게 변환
    user_dict = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "company_id": db_user.company_id,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
        "company": {
            "id": db_user.company.id,
            "name": db_user.company.name,
            "business_number": db_user.company.business_number,
            "address": db_user.company.address,
            "phone": db_user.company.phone
        } if db_user.company else None
    }
    
    return user_dict

@router.get("/", response_model=List[User])
def list_users(
    skip: int = 0, 
    limit: int = 100,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """사용자 목록 조회"""
    # 회사 정보를 함께 로드하기 위해 joinedload 사용
    query = db.query(UserModel).options(joinedload(UserModel.company))
    
    # 슈퍼 관리자가 아닌 경우 자신의 회사 사용자만 조회 가능
    if current_user.role != "super_admin":
        query = query.filter(UserModel.company_id == current_user.company_id)
    # 특정 회사 필터링
    elif company_id is not None:
        query = query.filter(UserModel.company_id == company_id)
    
    # 슈퍼 관리자는 모든 사용자 조회, 그 외는 회사 내 사용자만
    if current_user.role != "super_admin":
        query = query.filter(UserModel.role != "super_admin")
    
    # 활성 사용자만 조회
    query = query.filter(UserModel.is_active == True)
    
    # 정렬 (최근 생성일자 순)
    users = query.order_by(UserModel.created_at.desc()).offset(skip).limit(limit).all()
    
    # 응답 모델에 맞게 변환
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "company_id": user.company_id,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "company": {
                "id": user.company.id,
                "name": user.company.name,
                "business_number": user.company.business_number,
                "address": user.company.address,
                "phone": user.company.phone
            } if user.company else None
        }
        result.append(user_dict)
    
    return result

@router.get("/me", response_model=User)
def read_user_me(current_user: UserModel = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return current_user

@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """사용자 상세 조회"""
    # 회사 정보를 함께 로드
    db_user = db.query(UserModel).options(joinedload(UserModel.company)).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    
    # 슈퍼 관리자가 아니고, 자신의 회사 사용자가 아닌 경우 접근 거부
    if current_user.role != "super_admin" and db_user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 사용자에 대한 권한이 없습니다."
        )
    
    # 응답 모델에 맞게 변환
    user_dict = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "company_id": db_user.company_id,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
        "company": {
            "id": db_user.company.id,
            "name": db_user.company.name,
            "business_number": db_user.company.business_number,
            "address": db_user.company.address,
            "phone": db_user.company.phone
        } if db_user.company else None
    }
    
    return user_dict

@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """사용자 정보 수정"""
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 권한 확인
    if not has_company_permission(current_user, db_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 사용자에 대한 수정 권한이 없습니다."
        )
    
    # 슈퍼 관리자 권한 변경 제한
    if db_user.role == "super_admin" and current_user.id != db_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 슈퍼 관리자의 정보는 수정할 수 없습니다."
        )
    
    # 역할 변경 권한 확인
    if user_update.role and user_update.role != db_user.role:
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="사용자 역할을 변경할 권한이 없습니다."
            )
        
        # 슈퍼 관리자로의 역할 변경은 현재 사용자 본인에게는 허용하지 않음
        if user_update.role == "super_admin" and current_user.id == db_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="자신의 역할을 슈퍼 관리자로 변경할 수 없습니다."
            )
    
    # 회사 변경 권한 확인
    if user_update.company_id is not None and user_update.company_id != db_user.company_id:
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="사용자의 소속 회사를 변경할 권한이 없습니다."
            )
        
        # 회사 존재 여부 확인
        company = db.query(Company).filter(Company.id == user_update.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다.")
    
    # 필드 업데이트
    update_data = user_update.dict(exclude_unset=True)
    
    # 비밀번호 업데이트
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    # 슈퍼 관리자는 회사에 속하지 않음
    if update_data.get('role') == 'super_admin':
        update_data['company_id'] = None
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """사용자 삭제"""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신을 삭제할 수 없습니다."
        )
    
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 권한 확인
    if not has_company_permission(current_user, db_user.company_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 사용자를 삭제할 권한이 없습니다."
        )
    
    # 슈퍼 관리자 삭제 제한
    if db_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼 관리자는 삭제할 수 없습니다."
        )
    
    db.delete(db_user)
    db.commit()
    return None
