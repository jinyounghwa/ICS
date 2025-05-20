from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTabWidget, QLabel, QStatusBar,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QFormLayout, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QDateEdit, QTextEdit, QFileDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QAction, QIcon, QPixmap

from ..controllers.product_controller import ProductController
from .product_dialog import ProductDialog
from .user_management_dialog import UserManagementDialog
from .company_management_dialog import CompanyManagementDialog
from ..models.user import User as UserModel

class ProductTableWidget(QWidget):
    def __init__(self, db_session, company_id, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.company_id = company_id
        self.product_controller = ProductController(db_session)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 버튼 바
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton('추가')
        self.add_btn.clicked.connect(self.add_product)
        
        self.edit_btn = QPushButton('수정')
        self.edit_btn.clicked.connect(self.edit_product)
        
        self.delete_btn = QPushButton('삭제')
        self.delete_btn.clicked.connect(self.delete_product)
        
        self.refresh_btn = QPushButton('새로고침')
        self.refresh_btn.clicked.connect(self.load_products)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)
        
        # 테이블 위젯
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            'ID', '상품코드', '상품명', '분류', '브랜드', '모델명', 
            '현재재고', '최소재고', '판매가', '등록일'
        ])
        
        # 테이블 속성 설정
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # 레이아웃에 위젯 추가
        layout.addLayout(button_layout)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # 데이터 로드
        self.load_products()
    
    def load_products(self):
        """제품 목록 로드"""
        from ..models import Product
        
        try:
            # 테이블 초기화
            self.table.setRowCount(0)
            
            # 제품 조회
            # 이미 세션 객체를 가지고 있으므로 직접 사용
            session = self.db_session
            products = session.query(Product).filter(
                Product.company_id == self.company_id
            ).order_by(Product.created_at.desc()).all()
            
            for row, product in enumerate(products):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(product.id)))
                self.table.setItem(row, 1, QTableWidgetItem(product.code))
                self.table.setItem(row, 2, QTableWidgetItem(product.name))
                self.table.setItem(row, 3, QTableWidgetItem(product.category or ''))
                self.table.setItem(row, 4, QTableWidgetItem(product.brand or ''))
                self.table.setItem(row, 5, QTableWidgetItem(product.model or ''))
                self.table.setItem(row, 6, QTableWidgetItem(str(product.current_stock)))
                self.table.setItem(row, 7, QTableWidgetItem(str(product.minimum_stock)))
                self.table.setItem(row, 8, QTableWidgetItem(f"{product.price:,.0f}원"))
                self.table.setItem(row, 9, QTableWidgetItem(product.created_at.strftime('%Y-%m-%d') if product.created_at else ''))
            
            # 컬럼 너비 조정
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'제품 목록을 불러오는 중 오류가 발생했습니다: {str(e)}')
    
    def add_product(self):
        """제품 추가"""
        dialog = ProductDialog()
        
        # 제품 저장 시그널 연결
        dialog.product_saved.connect(self.on_product_saved)
        
        if dialog.exec() == QDialog.Accepted:
            # 제품 추가 로직은 on_product_saved에서 처리됨
            pass
    
    def on_product_saved(self, product_data):
        """제품 데이터 저장"""
        try:
            from ..models import Product
            
            # 이미 세션 객체를 가지고 있으므로 직접 사용
            session = self.db_session
            
            # 새 제품 객체 생성
            new_product = Product(
                name=product_data['name'],
                code=product_data['code'],
                category=product_data['category'],
                brand=product_data['brand'],
                model=product_data['model'],
                current_stock=product_data['stock'],
                minimum_stock=product_data['min_stock'],
                price=product_data['selling_price'],
                tax_included=product_data['tax_included'],
                company_id=self.company_id
            )
            
            # 데이터베이스에 추가
            session.add(new_product)
            session.commit()
            
            QMessageBox.information(self, '성공', '제품이 성공적으로 등록되었습니다.')
            
            # 제품 목록 새로고침
            self.load_products()
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'제품 등록 중 오류가 발생했습니다: {str(e)}')
            # 오류 로그 출력
            import traceback
            print(f"\n제품 등록 오류: {str(e)}")
            print(traceback.format_exc())
    
    def edit_product(self):
        """제품 수정"""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, '경고', '수정할 제품을 선택해주세요.')
            return
            
        product_id = int(self.table.item(selected[0].row(), 0).text())
        
        # 제품 정보 조회
        from ..models import Product
        
        # 이미 세션 객체를 가지고 있으므로 직접 사용
        session = self.db_session
        product = session.query(Product).get(product_id)
        if not product:
            QMessageBox.warning(self, '경고', '선택한 제품을 찾을 수 없습니다.')
            return
            
        # 제품 정보를 딕셔너리로 변환
        product_data = product.to_dict()
        
        # 구매 정보 조회 (가장 최근 입고 정보)
        if product.purchases:
            purchase = product.purchases[0]
            product_data.update({
                'cost_price': purchase.unit_price,
                'supplier': {
                    'name': purchase.supplier_name,
                    'business_number': purchase.business_number or '',
                    'address': purchase.supplier_address or '',
                    'phone': purchase.supplier_phone or ''
                }
            })
        
        # 다이얼로그 열기
        dialog = ProductDialog(product=product_data)
        
        # 제품 저장 시그널 연결
        dialog.product_saved.connect(lambda data: self.on_product_updated(product.id, data))
        
        if dialog.exec() == QDialog.Accepted:
            # 제품 수정 로직은 on_product_updated에서 처리됨
            pass
    
    def on_product_updated(self, product_id, product_data):
        """제품 데이터 업데이트"""
        try:
            from ..models import Product
            
            # 이미 세션 객체를 가지고 있으므로 직접 사용
            session = self.db_session
            
            # 제품 조회
            product = session.query(Product).get(product_id)
            if not product:
                QMessageBox.warning(self, '경고', '선택한 제품을 찾을 수 없습니다.')
                return
            
            # 제품 정보 업데이트
            product.name = product_data['name']
            product.code = product_data['code']
            product.category = product_data['category']
            product.brand = product_data['brand']
            product.model = product_data['model']
            product.current_stock = product_data['stock']
            product.minimum_stock = product_data['min_stock']
            product.price = product_data['selling_price']
            product.tax_included = product_data['tax_included']
            
            # 변경사항 저장
            session.commit()
            
            QMessageBox.information(self, '성공', '제품이 성공적으로 수정되었습니다.')
            
            # 제품 목록 새로고침
            self.load_products()
            
        except Exception as e:
            QMessageBox.critical(self, '오류', f'제품 수정 중 오류가 발생했습니다: {str(e)}')
            # 오류 로그 출력
            import traceback
            print(f"\n제품 수정 오류: {str(e)}")
            print(traceback.format_exc())
    
    def delete_product(self):
        """제품 삭제"""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, '경고', '삭제할 제품을 선택해주세요.')
            return
            
        product_id = int(self.table.item(selected[0].row(), 0).text())
        product_name = self.table.item(selected[0].row(), 2).text()
        
        reply = QMessageBox.question(
            self, '확인', 
            f'"{product_name}" 제품을 정말 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 제품 삭제 로직
                from ..models import Product
                
                # 이미 세션 객체를 가지고 있으므로 직접 사용
                session = self.db_session
                product = session.query(Product).get(product_id)
                if product:
                    session.delete(product)
                    session.commit()
                    QMessageBox.information(self, '성공', '제품이 삭제되었습니다.')
                    self.load_products()
                else:
                    QMessageBox.warning(self, '경고', '선택한 제품을 찾을 수 없습니다.')
                        
            except Exception as e:
                QMessageBox.critical(self, '오류', f'제품 삭제 중 오류가 발생했습니다: {str(e)}')

class MainWindow(QMainWindow):
    def __init__(self, auth_controller):
        super().__init__()
        self.auth_controller = auth_controller
        self.current_user = auth_controller.current_user
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('재고관리 시스템')
        self.setMinimumSize(1024, 768)
        
        # 메뉴바 숨기기
        self.menuBar().setVisible(False)
        
        # 메인 위젯 및 레이아웃
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 헤더 영역
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f'환영합니다, {self.current_user.username}님!')
        welcome_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        
        logout_btn = QPushButton('로그아웃')
        logout_btn.clicked.connect(self.handle_logout)
        
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        header_layout.addWidget(logout_btn)
        
        # 탭 위젯 생성
        self.tabs = QTabWidget()
        
        # 재고 관리 탭
        self.inventory_tab = QWidget()
        self.setup_inventory_tab()
        
        # 판매 관리 탭
        self.sales_tab = QWidget()
        self.setup_sales_tab()
        
        # 구매처 관리 탭
        self.supplier_tab = QWidget()
        self.setup_supplier_tab()
        
        # 사용자 관리 탭 (관리자용)
        if self.current_user.role in ['super_admin', 'company_admin']:
            self.user_tab = QWidget()
            self.setup_user_tab()
            self.tabs.addTab(self.user_tab, '사용자 관리')
        
        # 레이아웃에 위젯 추가
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.tabs)
        
        self.setCentralWidget(main_widget)
        
        # 상태바
        self.statusBar().showMessage('준비 완료')
    
    def create_menubar(self):
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        
        logout_action = QAction('로그아웃', self)
        logout_action.triggered.connect(self.handle_logout)
        
        exit_action = QAction('종료', self)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(logout_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu('도구')
        
        settings_action = QAction('설정', self)
        settings_action.triggered.connect(self.show_settings)
        
        tools_menu.addAction(settings_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말')
        
        about_action = QAction('정보', self)
        about_action.triggered.connect(self.show_about)
        
        help_menu.addAction(about_action)
    
    def setup_inventory_tab(self):
        """재고 관리 탭 설정"""
        layout = QVBoxLayout()
        
        # 제품 관리 위젯 추가
        self.product_table = ProductTableWidget(
            db_session=self.auth_controller.db,
            company_id=self.current_user.company_id,
            parent=self
        )
        
        layout.addWidget(self.product_table)
        self.inventory_tab.setLayout(layout)
        layout = QVBoxLayout()
        
        # 제품 목록 테이블 (나중에 구현)
        self.product_table = QLabel('제품 목록이 여기에 표시됩니다.')
        self.product_table.setAlignment(Qt.AlignCenter)
        
        # 버튼 그룹
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton('제품 추가')
        edit_btn = QPushButton('제품 수정')
        delete_btn = QPushButton('제품 삭제')
        refresh_btn = QPushButton('새로고침')
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        
        layout.addWidget(self.product_table)
        layout.addLayout(btn_layout)
        
        self.inventory_tab.setLayout(layout)
        self.tabs.addTab(self.inventory_tab, '재고 관리')
    
    def setup_sales_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel('판매 관리 탭 (구현 중...)'))
        self.sales_tab.setLayout(layout)
        self.tabs.addTab(self.sales_tab, '판매 관리')
    
    def setup_supplier_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel('구매처 관리 탭 (구현 중...)'))
        self.supplier_tab.setLayout(layout)
        self.tabs.addTab(self.supplier_tab, '구매처 관리')
    
    def setup_user_tab(self):
        layout = QVBoxLayout()
        
        # 사용자 관리 버튼
        btn_manage_users = QPushButton('사용자 관리')
        btn_manage_users.clicked.connect(self.manage_users)
        layout.addWidget(btn_manage_users)
        
        # 회사 관리 버튼 (슈퍼 관리자인 경우에만 활성화)
        btn_manage_companies = QPushButton('회사 관리')
        btn_manage_companies.clicked.connect(self.manage_companies)
        layout.addWidget(btn_manage_companies)
        
        # 슈퍼 관리자가 아닌 경우 버튼 비활성화
        if self.current_user.role != 'super_admin':
            btn_manage_companies.setEnabled(False)
            btn_manage_companies.setToolTip('슈퍼 관리자만 회사를 관리할 수 있습니다.')
        
        layout.addStretch()
        
        self.user_tab.setLayout(layout)
    
    def manage_users(self):
        """사용자 관리 다이얼로그 열기"""
        dialog = UserManagementDialog(
            parent=self,
            is_super_admin=self.current_user.role == 'super_admin',
            current_user_id=self.current_user.id
        )
        dialog.exec()
    
    def manage_companies(self):
        """회사 관리 다이얼로그 열기"""
        if self.current_user.role != 'super_admin':
            QMessageBox.warning(self, '권한 없음', '슈퍼 관리자만 회사를 관리할 수 있습니다.')
            return
            
        dialog = CompanyManagementDialog(
            parent=self,
            is_super_admin=self.current_user.role == 'super_admin'
        )
        dialog.exec()
    
    def handle_logout(self):
        reply = QMessageBox.question(
            self, '로그아웃', '정말 로그아웃 하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_controller.logout()
            self.close()
    
    def show_settings(self):
        QMessageBox.information(self, '설정', '설정 대화상자 (구현 중...)')
    
    def show_about(self):
        QMessageBox.about(
            self, 
            '재고관리 시스템 정보',
            '재고관리 시스템 v1.0\n\n'
            '제품의 입출고 및 재고 관리를 위한 통합 솔루션입니다.\n\n'
            '© 2025 재고관리 시스템. All rights reserved.'
        )
    
    def closeEvent(self, event):
        # 애플리케이션 종료 전 처리
        event.accept()
