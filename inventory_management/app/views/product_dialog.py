from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal

class ProductDialog(QDialog):
    product_saved = Signal(dict)  # 제품 저장 시그널
    
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle('제품 등록' if not product else '제품 수정')
        self.setMinimumWidth(500)
        
        self.init_ui()
        if product:
            self.load_product_data()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        
        # 기본 정보
        self.name_input = QLineEdit()
        self.code_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(['전자제품', '사무용품', '생활용품', '기타'])
        self.brand_input = QLineEdit()
        self.model_input = QLineEdit()
        
        # 재고/가격 정보
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 999999)
        self.cost_price_spin = QDoubleSpinBox()
        self.cost_price_spin.setRange(0, 999999999)
        self.cost_price_spin.setPrefix('₩ ')
        self.selling_price_spin = QDoubleSpinBox()
        self.selling_price_spin.setRange(0, 999999999)
        self.selling_price_spin.setPrefix('₩ ')
        self.tax_check = QCheckBox('부가세 포함')
        
        # 구매처 정보
        self.supplier_name = QLineEdit()
        self.business_number = QLineEdit()
        self.supplier_address = QLineEdit()
        self.supplier_phone = QLineEdit()
        
        # 폼에 위젯 추가
        form_layout.addRow('상품명 *', self.name_input)
        form_layout.addRow('상품코드 *', self.code_input)
        form_layout.addRow('분류', self.category_combo)
        form_layout.addRow('브랜드', self.brand_input)
        form_layout.addRow('모델명', self.model_input)
        
        form_layout.addRow(QLabel('\n재고/가격 정보'))
        form_layout.addRow('현재 재고 수량', self.stock_spin)
        form_layout.addRow('최소 재고 수량', self.min_stock_spin)
        form_layout.addRow('단가 (입고가)', self.cost_price_spin)
        form_layout.addRow('판매가', self.selling_price_spin)
        form_layout.addRow('', self.tax_check)
        
        form_layout.addRow(QLabel('\n구매처 정보'))
        form_layout.addRow('구매처 사업자명', self.supplier_name)
        form_layout.addRow('사업자등록번호', self.business_number)
        form_layout.addRow('주소', self.supplier_address)
        form_layout.addRow('전화번호', self.supplier_phone)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        save_btn = QPushButton('저장')
        save_btn.clicked.connect(self.save_product)
        cancel_btn = QPushButton('취소')
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        # 메인 레이아웃에 추가
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_product_data(self):
        """기존 제품 데이터를 폼에 로드"""
        if not self.product:
            return
            
        self.name_input.setText(self.product.get('name', ''))
        self.code_input.setText(self.product.get('code', ''))
        
        category = self.product.get('category', '')
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
            
        self.brand_input.setText(self.product.get('brand', ''))
        self.model_input.setText(self.product.get('model', ''))
        self.stock_spin.setValue(self.product.get('stock', 0))
        self.min_stock_spin.setValue(self.product.get('min_stock', 0))
        self.cost_price_spin.setValue(self.product.get('cost_price', 0))
        self.selling_price_spin.setValue(self.product.get('selling_price', 0))
        self.tax_check.setChecked(self.product.get('tax_included', False))
        
        # 구매처 정보
        supplier = self.product.get('supplier', {})
        self.supplier_name.setText(supplier.get('name', ''))
        self.business_number.setText(supplier.get('business_number', ''))
        self.supplier_address.setText(supplier.get('address', ''))
        self.supplier_phone.setText(supplier.get('phone', ''))
    
    def validate_inputs(self):
        """입력 유효성 검사"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, '입력 오류', '상품명을 입력해주세요.')
            return False
            
        if not self.code_input.text().strip():
            QMessageBox.warning(self, '입력 오류', '상품코드를 입력해주세요.')
            return False
            
        return True
    
    def get_product_data(self):
        """폼 데이터를 딕셔너리로 반환"""
        return {
            'name': self.name_input.text().strip(),
            'code': self.code_input.text().strip(),
            'category': self.category_combo.currentText(),
            'brand': self.brand_input.text().strip(),
            'model': self.model_input.text().strip(),
            'stock': self.stock_spin.value(),
            'min_stock': self.min_stock_spin.value(),
            'cost_price': self.cost_price_spin.value(),
            'selling_price': self.selling_price_spin.value(),
            'tax_included': self.tax_check.isChecked(),
            'supplier': {
                'name': self.supplier_name.text().strip(),
                'business_number': self.business_number.text().strip(),
                'address': self.supplier_address.text().strip(),
                'phone': self.supplier_phone.text().strip()
            }
        }
    
    def save_product(self):
        """제품 저장"""
        if not self.validate_inputs():
            return
            
        product_data = self.get_product_data()
        self.product_saved.emit(product_data)
        self.accept()
