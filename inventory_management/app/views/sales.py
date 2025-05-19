from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app import get_db
from app.models.sale_record import SaleRecord
from app.models.product import Product
from app.models.user import User
from app.schemas.sale import Sale as SaleSchema, SaleCreate, SaleUpdate
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/sales",
    tags=["판매 관리"],
    responses={404: {"description": "Not found"}},
)

def check_sale_permission(user: User, db: Session, sale: SaleRecord = None, product_id: int = None):
    """판매 정보 접근 권한 확인"""
    # 관리자는 모든 판매 정보에 접근 가능
    if user.role in ["admin", "super_admin"]:
        return True
    
    # 일반 사용자는 본인 회사의 판매 정보만 접근 가능
    if sale and sale.product.company_id != user.company_id:
        return False
    
    # 제품 ID로 권한 확인
    if product_id:
        product = sale.product if sale else None
        if not product:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
        if product.company_id != user.company_id:
            return False
    
    return True

@router.get("/", response_model=List[SaleSchema])
def list_sales(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """판매 목록 조회"""
    query = db.query(SaleRecord).join(Product)
    
    # 필터링 조건 적용
    if product_id:
        query = query.filter(SaleRecord.product_id == product_id)
    if customer_name:
        query = query.filter(SaleRecord.customer_name.ilike(f"%{customer_name}%"))
    if start_date:
        query = query.filter(SaleRecord.sale_date >= start_date)
    if end_date:
        # 종료일은 해당일 자정까지 포함
        end_date = end_date.replace(hour=23, minute=59, second=59)
        query = query.filter(SaleRecord.sale_date <= end_date)
    if status:
        query = query.filter(SaleRecord.status == status)
    if payment_status:
        query = query.filter(SaleRecord.payment_status == payment_status)
    
    # 권한 확인 및 필터링
    if current_user.role == "user":
        query = query.filter(Product.company_id == current_user.company_id)
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=SaleSchema, status_code=201)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """새 판매 정보 생성"""
    # 제품 존재 여부 확인
    product = db.query(Product).filter(Product.id == sale.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_sale_permission(current_user, db, product_id=product.id):
        raise HTTPException(status_code=403, detail="판매 정보를 생성할 권한이 없습니다.")
    
    # 재고 확인
    if product.current_stock < sale.quantity:
        raise HTTPException(status_code=400, detail="재고가 부족합니다.")
    
    # 총 판매 금액 계산
    total_price = sale.quantity * sale.unit_price
    
    # 새 판매 정보 생성
    db_sale = SaleRecord(
        **sale.dict(),
        total_price=total_price,
        created_by=current_user.id
    )
    
    # 제품 재고 감소
    product.current_stock -= sale.quantity
    
    # 판매 상태가 '완료'이고 결제 상태가 '결제완료'인 경우에만 재고 업데이트
    if sale.status == 'completed' and sale.payment_status == 'paid':
        product.current_stock -= sale.quantity
    
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.get("/{sale_id}", response_model=SaleSchema)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """판매 정보 상세 조회"""
    sale = db.query(SaleRecord).filter(SaleRecord.id == sale_id).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="판매 정보를 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_sale_permission(current_user, sale):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return sale

@router.put("/{sale_id}", response_model=SaleSchema)
def update_sale(
    sale_id: int,
    sale_update: SaleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """판매 정보 수정"""
    # 기존 판매 정보 조회
    db_sale = db.query(SaleRecord).filter(SaleRecord.id == sale_id).first()
    if db_sale is None:
        raise HTTPException(status_code=404, detail="판매 정보를 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_sale_permission(current_user, db, db_sale):
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")
    
    # 제품 재고 조정 (수량이 변경된 경우)
    if sale_update.quantity is not None and sale_update.quantity != db_sale.quantity:
        product = db_sale.product
        # 이전 수량만큼 재고 복구
        product.current_stock += db_sale.quantity
        # 새로운 수량만큼 재고 차감 (유효성 검사 포함)
        if product.current_stock < sale_update.quantity:
            db.rollback()  # 변경 사항 롤백
            raise HTTPException(status_code=400, detail="재고가 부족합니다.")
        product.current_stock -= sale_update.quantity
    
    # 판매 정보 업데이트
    update_data = sale_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sale, field, value)
    
    # 총 판매 금액 재계산 (수량이나 단가가 변경된 경우)
    if any(field in update_data for field in ['quantity', 'unit_price']):
        db_sale.total_price = db_sale.quantity * db_sale.unit_price
    
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.delete("/{sale_id}", status_code=204)
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """판매 정보 삭제"""
    # 판매 정보 조회
    sale = db.query(SaleRecord).filter(SaleRecord.id == sale_id).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="판매 정보를 찾을 수 없습니다.")
    
    # 권한 확인
    if not check_sale_permission(current_user, sale):
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")
    
    # 제품 재고 복구 (판매 취소 시 재고 증가)
    product = sale.product
    product.current_stock += sale.quantity
    
    # 판매 정보 삭제
    db.delete(sale)
    db.commit()
    return {"ok": True}
