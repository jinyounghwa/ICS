from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import Product as ProductSchema, ProductCreate, ProductUpdate
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/products",
    tags=["제품"],
    responses={404: {"description": "Not found"}},
)

def check_admin(user: User):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=403,
            detail="관리자 권한이 필요합니다."
        )

@router.get("/", response_model=List[ProductSchema])
def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """제품 목록 조회"""
    query = db.query(Product)
    
    # 검색어가 있는 경우
    if search:
        search = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search)) |
            (Product.code.ilike(search)) |
            (Product.brand.ilike(search)) |
            (Product.model.ilike(search)) |
            (Product.description.ilike(search))
        )
    
    # 관리자가 아니면 본인 회사 제품만 조회
    if current_user.role == "user":
        query = query.filter(Product.company_id == current_user.company_id)
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=ProductSchema, status_code=201)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """새 제품 생성"""
    # 관리자 권한 확인
    check_admin(current_user)
    
    # 제품 코드 중복 확인
    db_product = db.query(Product).filter(Product.code == product.code).first()
    if db_product:
        raise HTTPException(status_code=400, detail="이미 존재하는 제품 코드입니다.")
    
    # 새 제품 생성
    db_product = Product(
        **product.dict(),
        company_id=current_user.company_id  # 사용자의 회사 ID로 설정
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """제품 상세 조회"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    
    # 관리자가 아니면 본인 회사 제품만 조회 가능
    if current_user.role == "user" and db_product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return db_product

@router.put("/{product_id}", response_model=ProductSchema)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """제품 정보 수정"""
    # 관리자 권한 확인
    check_admin(current_user)
    
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    
    # 관리자가 아니면 본인 회사 제품만 수정 가능
    if current_user.role == "user" and db_product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")
    
    # 제품 정보 업데이트
    update_data = product.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """제품 삭제"""
    # 관리자 권한 확인
    check_admin(current_user)
    
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    
    # 관리자가 아니면 본인 회사 제품만 삭제 가능
    if current_user.role == "user" and db_product.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    
    db.delete(db_product)
    db.commit()
    return {"ok": True}
