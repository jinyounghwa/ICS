from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

class ProductController:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_product(self, product_data, company_id):
        """새 제품 생성"""
        from app.models.product import Product
        from app.models.purchase_info import PurchaseInfo
        from app.models.company import Company
        
        try:
            # 회사 존재 여부 확인
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return False, "회사 정보를 찾을 수 없습니다."
            
            # 상품 코드 중복 확인
            existing = self.db.query(Product).filter(
                Product.code == product_data['code'],
                Product.company_id == company_id
            ).first()
            
            if existing:
                return False, "이미 존재하는 상품코드입니다."
            
            # 상품 생성
            product = Product(
                name=product_data['name'],
                code=product_data['code'],
                category=product_data['category'],
                brand=product_data['brand'],
                model=product_data['model'],
                current_stock=product_data['stock'],
                minimum_stock=product_data['min_stock'],
                price=product_data['selling_price'],
                company_id=company_id
            )
            
            self.db.add(product)
            self.db.flush()  # ID를 얻기 위해 flush
            
            # 입고 정보 생성
            if product_data['supplier']['name']:
                purchase = PurchaseInfo(
                    product_id=product.id,
                    supplier_name=product_data['supplier']['name'],
                    supplier_contact="",
                    supplier_address=product_data['supplier']['address'],
                    supplier_phone=product_data['supplier']['phone'],
                    purchase_date=datetime.now(),
                    quantity=product_data['stock'],
                    unit_price=product_data['cost_price'],
                    total_price=product_data['cost_price'] * product_data['stock'],
                    payment_status='PAID' if product_data['cost_price'] > 0 else 'PENDING',
                    notes='초기 재고 등록'
                )
                self.db.add(purchase)
            
            self.db.commit()
            return True, "제품이 성공적으로 등록되었습니다."
            
        except SQLAlchemyError as e:
            self.db.rollback()
            return False, f"데이터베이스 오류: {str(e)}"
        except Exception as e:
            self.db.rollback()
            return False, f"오류가 발생했습니다: {str(e)}"
    
    def update_product(self, product_id, product_data, company_id):
        """기존 제품 수정"""
        from app.models.product import Product
        
        try:
            product = self.db.query(Product).filter(
                Product.id == product_id,
                Product.company_id == company_id
            ).first()
            
            if not product:
                return False, "제품을 찾을 수 없습니다."
            
            # 상품 코드 중복 확인 (자기 자신 제외)
            if product.code != product_data['code']:
                existing = self.db.query(Product).filter(
                    Product.code == product_data['code'],
                    Product.company_id == company_id,
                    Product.id != product_id
                ).first()
                
                if existing:
                    return False, "이미 사용 중인 상품코드입니다."
            
            # 제품 정보 업데이트
            product.name = product_data['name']
            product.code = product_data['code']
            product.category = product_data['category']
            product.brand = product_data['brand']
            product.model = product_data['model']
            product.current_stock = product_data['stock']
            product.minimum_stock = product_data['min_stock']
            product.price = product_data['selling_price']
            
            # 구매처 정보는 별도로 관리되므로 여기서는 업데이트하지 않음
            
            self.db.commit()
            return True, "제품이 성공적으로 수정되었습니다."
            
        except SQLAlchemyError as e:
            self.db.rollback()
            return False, f"데이터베이스 오류: {str(e)}"
        except Exception as e:
            self.db.rollback()
            return False, f"오류가 발생했습니다: {str(e)}"
    
    def get_product(self, product_id, company_id):
        """제품 상세 정보 조회"""
        from app.models.product import Product
        from app.models.purchase_info import PurchaseInfo
        
        try:
            product = self.db.query(Product).filter(
                Product.id == product_id,
                Product.company_id == company_id
            ).first()
            
            if not product:
                return None
            
            # 최근 입고 정보 조회
            purchase = self.db.query(PurchaseInfo).filter(
                PurchaseInfo.product_id == product_id
            ).order_by(PurchaseInfo.purchase_date.desc()).first()
            
            result = {
                'id': product.id,
                'name': product.name,
                'code': product.code,
                'category': product.category,
                'brand': product.brand,
                'model': product.model,
                'stock': product.current_stock,
                'min_stock': product.minimum_stock,
                'cost_price': purchase.unit_price if purchase else 0,
                'selling_price': product.price,
                'tax_included': True,  # 기본값
                'supplier': {
                    'name': purchase.supplier_name if purchase else '',
                    'business_number': '',  # 별도로 관리 필요
                    'address': purchase.supplier_address if purchase else '',
                    'phone': purchase.supplier_phone if purchase else ''
                }
            }
            
            return result
            
        except Exception as e:
            print(f"Error getting product: {str(e)}")
            return None
    
    def delete_product(self, product_id, company_id):
        """제품 삭제"""
        from app.models.product import Product
        
        try:
            product = self.db.query(Product).filter(
                Product.id == product_id,
                Product.company_id == company_id
            ).first()
            
            if not product:
                return False, "제품을 찾을 수 없습니다."
            
            # 판매 내역이 있는지 확인
            if product.sale_records:
                return False, "판매 내역이 있는 제품은 삭제할 수 없습니다."
            
            # 입고 내역 삭제
            for purchase in product.purchases:
                self.db.delete(purchase)
            
            # 제품 삭제
            self.db.delete(product)
            self.db.commit()
            
            return True, "제품이 성공적으로 삭제되었습니다."
            
        except SQLAlchemyError as e:
            self.db.rollback()
            return False, f"데이터베이스 오류: {str(e)}"
        except Exception as e:
            self.db.rollback()
            return False, f"오류가 발생했습니다: {str(e)}"
