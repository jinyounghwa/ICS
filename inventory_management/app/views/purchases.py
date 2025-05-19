from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app import get_db
from app.models.purchase_info import PurchaseInfo
from app.models.product import Product
from app.models.user import User
from app.schemas.purchase import Purchase as PurchaseSchema, PurchaseCreate, PurchaseUpdate
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/purchases",
    tags=["구매 관리"],
    responses={404: {"description": "Not found"}},
)

def check_purchase_permission(user: User, db: Session, purchase: PurchaseInfo = None, product_id: int = None):
    """구매 정보 접근 권한 확인"""
    # 관리자는 모든 구매 정보에 접근 가능
    if user.role in ["admin", "super_admin"]:
        return True
    
    # 일반 사용자는 본인 회사의 구매 정보만 접근 가능
    if purchase and purchase.product.company_id != user.company_id:
        return False
    
    # 제품 ID로 권한 확인
    if product_id:
        product = purchase.product if purchase else None
        if not product:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
        if product.company_id != user.company_id:
            return False
    
    return True

@router.get("/", response_model=List[PurchaseSchema])
def list_purchases(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    supplier_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """구매 목록 조회"""
    query = db.query(PurchaseInfo).join(Product)
    
    # 필터링 조건 적용
    if product_id:
        query = query.filter(PurchaseInfo.product_id == product_id)
    if supplier_name:
        query = query.filter(PurchaseInfo.supplier_name.ilike(f"%{supplier_name}%"))
    if start_date:
        query = query.filter(PurchaseInfo.purchase_date >= start_date)
    if end_date:
        query = query.filter(PurchaseInfo.purchase_date <= end_date)
    if payment_status:
        query = query.filter(PurchaseInfo.payment_status == payment_status)
    
    # 권한 확인 및 필터링
    if current_user.role == "user":
        query = query.filter(Product.company_id == current_user.company_id)
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=PurchaseSchema, status_code=201)
def create_purchase(
    purchase: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """새 구매 정보 생성"""
    # 제품 존재 여부 확인
    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_purchase_permission(current_user, db, product_id=product.id):
        raise HTTPException(status_code=403, detail="구매 정보를 생성할 권한이 없습니다.")
    
    # 총 구매 금액 계산
    total_price = purchase.quantity * purchase.unit_price
    if purchase.tax_rate:
        tax_amount = total_price * (purchase.tax_rate / 100)
        if purchase.tax_included:
            total_price += tax_amount
    
    # 새 구매 정보 생성
    db_purchase = PurchaseInfo(
        **purchase.dict(exclude={"tax_included"}),
        total_price=total_price,
        created_by=current_user.id
    )
    
    # 제품 재고 업데이트
    product.current_stock += purchase.quantity
    
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

@router.get("/{purchase_id}", response_model=PurchaseSchema)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """구매 정보 상세 조회"""
    purchase = db.query(PurchaseInfo).filter(PurchaseInfo.id == purchase_id).first()
    if purchase is None:
        raise HTTPException(status_code=404, detail="구매 정보를 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_purchase_permission(current_user, db, purchase):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return purchase

@router.put("/{purchase_id}", response_model=PurchaseSchema)
def update_purchase(
    purchase_id: int,
    purchase_update: PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """구매 정보 수정"""
    # 기존 구매 정보 조회
    db_purchase = db.query(PurchaseInfo).filter(PurchaseInfo.id == purchase_id).first()
    if db_purchase is None:
        raise HTTPException(status_code=404, detail="구매 정보를 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_purchase_permission(current_user, db, db_purchase):
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")
    
    # 제품 재고 조정 (수량이 변경된 경우)
    if purchase_update.quantity is not None and purchase_update.quantity != db_purchase.quantity:
        product = db_purchase.product
        product.current_stock += (purchase_update.quantity - db_purchase.quantity)
    
    # 구매 정보 업데이트
    update_data = purchase_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_purchase, field, value)
    
    # 총 구매 금액 재계산 (필요한 경우)
    if any(field in update_data for field in ['quantity', 'unit_price', 'tax_rate', 'discount']):
        total_price = db_purchase.quantity * db_purchase.unit_price
        if db_purchase.tax_rate:
            tax_amount = total_price * (db_purchase.tax_rate / 100)
            if db_purchase.tax_included:
                total_price += tax_amount
        db_purchase.total_price = total_price
    
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

@router.delete("/{purchase_id}", status_code=204)
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """구매 정보 삭제"""
    # 구매 정보 조회
    purchase = db.query(PurchaseInfo).filter(PurchaseInfo.id == purchase_id).first()
    if purchase is None:
        raise HTTPException(status_code=404, detail="구매 정보를 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_purchase_permission(current_user, db, purchase):
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    
    # 제품 재고 조정 (삭제 시 재고 감소)
    product = purchase.product
    product.current_stock -= purchase.quantity
    
    # 구매 정보 삭제
    db.delete(purchase)
    db.commit()
    return {"ok": True}
