import sys
from PySide6.QtWidgets import QApplication
from app.views.login_window import LoginWindow
from app.controllers.auth_controller import AuthController

def main():
    app = QApplication(sys.argv)
    
    # 인증 컨트롤러 초기화
    auth_controller = AuthController()
    
    # 로그인 창 표시
    login_window = LoginWindow(auth_controller)
    login_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
