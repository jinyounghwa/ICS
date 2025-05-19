from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout
)

from .main_window import MainWindow
from PySide6.QtCore import Qt

class LoginWindow(QWidget):
    def __init__(self, auth_controller):
        super().__init__()
        self.auth_controller = auth_controller
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('로그인')
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 제목 라벨
        title_label = QLabel('재고관리 시스템')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet('font-size: 24px; font-weight: bold; margin: 20px 0;')
        
        # 폼 레이아웃
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # 사용자명 입력 필드
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('사용자명을 입력하세요')
        
        # 비밀번호 입력 필드
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('비밀번호를 입력하세요')
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # 폼에 위젯 추가
        form_layout.addRow('사용자명:', self.username_input)
        form_layout.addRow('비밀번호:', self.password_input)
        
        # 로그인 버튼
        login_btn = QPushButton('로그인')
        login_btn.clicked.connect(self.handle_login)
        login_btn.setStyleSheet('')
        
        # 회원가입 버튼
        register_btn = QPushButton('회원가입')
        register_btn.clicked.connect(self.show_register_dialog)
        
        # 레이아웃에 위젯 추가
        layout.addWidget(title_label)
        layout.addLayout(form_layout)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, '입력 오류', '사용자명과 비밀번호를 모두 입력해주세요.')
            return
            
        success, message = self.auth_controller.login(username, password)
        if success:
            self.main_window = MainWindow(self.auth_controller)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.critical(self, '로그인 실패', message)
    
    def show_register_dialog(self):
        # 회원가입 다이얼로그 표시
        from .register_dialog import RegisterDialog
        dialog = RegisterDialog(self.auth_controller, self)
        dialog.exec()
