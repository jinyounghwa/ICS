from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt

class RegisterDialog(QDialog):
    def __init__(self, auth_controller, parent=None):
        super().__init__(parent)
        self.auth_controller = auth_controller
        self.setWindowTitle('회원가입')
        self.setFixedSize(400, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목 라벨
        title_label = QLabel('회원가입')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 18px; font-weight: bold; margin: 10px 0;')
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 사용자명 입력 필드
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('사용자명을 입력하세요')
        
        # 비밀번호 입력 필드
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('비밀번호를 입력하세요')
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # 비밀번호 확인 필드
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText('비밀번호를 다시 입력하세요')
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        # 이메일 입력 필드
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('이메일을 입력하세요')
        
        # 회사명 입력 필드
        self.company_name_input = QLineEdit()
        self.company_name_input.setPlaceholderText('회사명을 입력하세요')
        
        # 사업자등록번호 입력 필드
        self.business_number_input = QLineEdit()
        self.business_number_input.setPlaceholderText('사업자등록번호를 입력하세요 (선택사항)')
        
        # 역할 선택
        self.role_combo = QComboBox()
        self.role_combo.addItem("사용자", "user")
        self.role_combo.addItem("관리자", "admin")
        
        # 폼에 위젯 추가
        form_layout.addRow('사용자명:', self.username_input)
        form_layout.addRow('비밀번호:', self.password_input)
        form_layout.addRow('비밀번호 확인:', self.confirm_password_input)
        form_layout.addRow('이메일:', self.email_input)
        form_layout.addRow('회사명:', self.company_name_input)
        form_layout.addRow('사업자등록번호:', self.business_number_input)
        form_layout.addRow('역할:', self.role_combo)
        
        # 등록 버튼
        register_btn = QPushButton('가입하기')
        register_btn.clicked.connect(self.handle_register)
        
        # 취소 버튼
        cancel_btn = QPushButton('취소')
        cancel_btn.clicked.connect(self.reject)
        
        # 레이아웃에 위젯 추가
        layout.addWidget(title_label)
        layout.addLayout(form_layout)
        layout.addWidget(register_btn)
        layout.addWidget(cancel_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def handle_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        email = self.email_input.text().strip()
        company_name = self.company_name_input.text().strip()
        business_number = self.business_number_input.text().strip()
        role = self.role_combo.currentData()
        
        # 입력 검증
        if not all([username, password, confirm_password, email, company_name]):
            QMessageBox.warning(self, '입력 오류', '모든 필수 항목을 입력해주세요.')
            return
            
        if password != confirm_password:
            QMessageBox.warning(self, '입력 오류', '비밀번호가 일치하지 않습니다.')
            return
            
        # 회원가입 처리
        success, message = self.auth_controller.register_user(
            username=username,
            password=password,
            email=email,
            company_name=company_name,
            business_number=business_number,
            role=role
        )
        
        if success:
            QMessageBox.information(self, '회원가입 성공', '회원가입이 완료되었습니다. 로그인해주세요.')
            self.accept()
        else:
            QMessageBox.critical(self, '회원가입 실패', message)
