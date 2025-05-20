from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QComboBox, QFormLayout, QWidget, QTabWidget,
                             QGroupBox, QGridLayout, QCheckBox, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIntValidator, QIcon

import requests
import json
from datetime import datetime

from app.config import API_BASE_URL, get_auth_header

class UserForm(QWidget):
    """사용자 등록/수정 폼 위젯"""
    def __init__(self, parent=None, user=None, is_super_admin=False):
        super().__init__(parent)
        self.user = user
        self.is_super_admin = is_super_admin
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout(self)
        
        # 사용자명
        self.username_edit = QLineEdit()
        layout.addRow("사용자명*:", self.username_edit)
        
        # 이메일
        self.email_edit = QLineEdit()
        layout.addRow("이메일*:", self.email_edit)
        
        # 비밀번호
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("변경 시에만 입력")
        layout.addRow("비밀번호:", self.password_edit)
        
        # 회사 선택 콤보박스
        self.company_combo = QComboBox()
        self.company_combo.addItem("기본 회사 (자동 생성)", None)  # 기본값 추가
        
        # 역할
        self.role_combo = QComboBox()
        if self.is_super_admin:
            self.role_combo.addItems(["user", "admin", "super_admin"])
            layout.addRow("회사:", self.company_combo)  # 슈퍼 관리자인 경우에만 회사 선택 추가
        else:
            self.role_combo.addItems(["user", "admin"])
        layout.addRow("역할*:", self.role_combo)
        
        # 회사 ID (슈퍼 관리자인 경우에만 표시)
        self.company_id_edit = QLineEdit()
        self.company_id_edit.setPlaceholderText("자동 할당")
        self.company_id_edit.setReadOnly(True)
        
        # 역할 변경 시 이벤트 연결
        self.role_combo.currentTextChanged.connect(self.on_role_changed)
        
        if self.is_super_admin:
            # company_combo는 이미 위에서 추가했으므로 여기서는 company_id_edit만 추가
            layout.addRow("회사 ID:", self.company_id_edit)
        
        # 기존 사용자 데이터 로드
        if self.user:
            self.load_user_data()
    
    def on_role_changed(self, role):
        """역할이 변경될 때 회사 ID 입력 필드 활성화/비활성화"""
        if role == "super_admin":
            self.company_id_edit.setReadOnly(True)
            self.company_id_edit.clear()
        elif self.is_super_admin:
            self.company_id_edit.setReadOnly(False)
    
    def load_user_data(self):
        """기존 사용자 데이터 로드"""
        self.username_edit.setText(self.user.get('username', ''))
        self.email_edit.setText(self.user.get('email', ''))
        
        # 역할 설정
        role_index = self.role_combo.findText(self.user.get('role', ''))
        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)
        
        # 회사 ID 설정
        if 'company_id' in self.user and self.user['company_id']:
            self.company_id_edit.setText(str(self.user['company_id']))
    
    def get_form_data(self):
        """폼 데이터 가져오기"""
        data = {
            'username': self.username_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'role': self.role_combo.currentText(),
        }
        
        # 비밀번호가 입력된 경우에만 포함
        password = self.password_edit.text().strip()
        if password:
            data['password'] = password
        
        # 회사 ID 처리
        if data['role'] != 'super_admin':  # 슈퍼 관리자가 아닌 경우
            if self.is_super_admin:  # 슈퍼 관리자가 사용자를 추가/수정하는 경우
                if hasattr(self, 'company_combo'):
                    company_id = self.company_combo.currentData()
                    if company_id is not None:
                        data['company_id'] = company_id
            elif hasattr(self, 'user') and self.user and 'company_id' in self.user:
                # 기존 사용자 수정 시 회사 ID 유지
                data['company_id'] = self.user['company_id']
        
        return data
    
    def validate(self):
        """폼 유효성 검사"""
        data = self.get_form_data()
        
        if not data['username']:
            QMessageBox.warning(self, '입력 오류', '사용자명을 입력해주세요.')
            return False
            
        if not data['email']:
            QMessageBox.warning(self, '입력 오류', '이메일을 입력해주세요.')
            return False
            
        if not self.user and 'password' not in data:
            QMessageBox.warning(self, '입력 오류', '비밀번호를 입력해주세요.')
            return False
            
        if self.is_super_admin and data['role'] != 'super_admin' and 'company_id' not in data:
            QMessageBox.warning(self, '입력 오류', '회사 ID를 입력해주세요.')
            return False
            
        return True


class UserManagementDialog(QDialog):
    """사용자 관리 다이얼로그"""
    def __init__(self, parent=None, is_super_admin=False, current_user_id=None):
        super().__init__(parent)
        self.is_super_admin = is_super_admin
        self.current_user_id = current_user_id
        self.users = []
        self.companies = []
        
        self.setWindowTitle("사용자 관리")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_companies()
        self.load_users()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 상단 버튼 그룹
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("새로고침")
        # self.refresh_btn.setIcon(QIcon(":/icons/refresh.png"))  # 아이콘 파일이 없으므로 주석 처리
        self.refresh_btn.clicked.connect(self.load_users)
        
        self.add_btn = QPushButton("사용자 추가")
        # self.add_btn.setIcon(QIcon(":/icons/add.png"))  # 아이콘 파일이 없으므로 주석 처리
        self.add_btn.clicked.connect(self.add_user)
        
        self.edit_btn = QPushButton("수정")
        # self.edit_btn.setIcon(QIcon(":/icons/edit.png"))  # 아이콘 파일이 없으므로 주석 처리
        self.edit_btn.clicked.connect(self.edit_user)
        
        self.delete_btn = QPushButton("삭제")
        # self.delete_btn.setIcon(QIcon(":/icons/delete.png"))  # 아이콘 파일이 없으므로 주석 처리
        self.delete_btn.clicked.connect(self.delete_user)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 사용자 테이블
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["ID", "사용자명", "이메일", "역할", "회사"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.doubleClicked.connect(self.edit_user)
        
        layout.addWidget(self.user_table)
        
        # 상태바
        self.status_bar = QLabel("준비 완료")
        layout.addWidget(self.status_bar)
    
    def load_companies(self):
        """회사 목록 로드"""
        try:
            # 기본 회사 옵션 추가 (슈퍼 관리자인 경우에만)
            if self.is_super_admin and hasattr(self, 'company_combo'):
                self.company_combo.clear()
                self.company_combo.addItem("기본 회사 (자동 생성)", None)
                
                # 회사 목록 로드
                response = requests.get(
                    f"{API_BASE_URL}/companies/",
                    headers=get_auth_header()
                )
                
                if response.status_code == 200:
                    self.companies = response.json()
                    for company in self.companies:
                        self.company_combo.addItem(company['name'], company['id'])
                else:
                    QMessageBox.warning(self, '경고', '회사 목록을 불러오는 중 오류가 발생했습니다.')
                    self.companies = []
        except Exception as e:
            QMessageBox.critical(self, '오류', f'회사 목록을 불러오는 중 오류가 발생했습니다.\n{str(e)}')
            self.companies = []
            return
            
        try:
            print("\n=== 회사 목록 로드 시도 ===")
            headers = get_auth_header()
            print(f"요청 헤더: {headers}")
            
            response = requests.get(
                f"{API_BASE_URL}/api/companies/",
                headers=headers
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text[:200]}...")
            
            if response.status_code == 200:
                self.companies = response.json()
                print(f"로드된 회사 수: {len(self.companies)}")
            else:
                print(f"회사 목록 로드 실패: {response.status_code} - {response.text}")
                QMessageBox.critical(self, '오류', f'회사 목록을 불러오는 중 오류가 발생했습니다: {response.status_code}')
        except Exception as e:
            print(f"회사 목록 로드 중 예외 발생: {str(e)}")
            QMessageBox.critical(self, '오류', f'회사 목록을 불러오는 중 오류가 발생했습니다: {str(e)}')
    
    def load_users(self):
        """사용자 목록 로드"""
        try:
            print("\n=== 사용자 목록 로드 시도 ===")
            headers = get_auth_header()
            print(f"요청 헤더: {headers}")
            
            response = requests.get(
                f"{API_BASE_URL}/api/users/",
                headers=headers
            )
            
            print(f"응답 상태 코드: {response.status_code}")
            print(f"응답 내용: {response.text[:200]}...")
            
            if response.status_code == 200:
                self.users = response.json()
                print(f"로드된 사용자 수: {len(self.users)}")
                self.update_user_table()
            else:
                print(f"사용자 목록 로드 실패: {response.status_code} - {response.text}")
                QMessageBox.critical(self, '오류', f'사용자 목록을 불러오는 중 오류가 발생했습니다: {response.status_code}')
        except Exception as e:
            print(f"사용자 목록 로드 중 예외 발생: {str(e)}")
            QMessageBox.critical(self, '오류', f'사용자 목록을 불러오는 중 오류가 발생했습니다: {str(e)}')
    
    def update_user_table(self):
        """사용자 테이블 업데이트"""
        self.user_table.setRowCount(0)
        
        for user in self.users:
            row = self.user_table.rowCount()
            self.user_table.insertRow(row)
            
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
            self.user_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
            self.user_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
            self.user_table.setItem(row, 3, QTableWidgetItem(user.get('role', '')))
            
            # 회사명 표시
            company_name = user.get('company', {}).get('name', '') if user.get('company') else ''
            self.user_table.setItem(row, 4, QTableWidgetItem(company_name))
    
    def get_selected_user(self):
        """선택된 사용자 반환"""
        selected = self.user_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, '선택 필요', '수정할 사용자를 선택해주세요.')
            return None
            
        row = selected[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        
        # 현재 로그인한 사용자와 동일한지 확인
        if user_id == self.current_user_id:
            QMessageBox.warning(self, '오류', '자기 자신은 수정할 수 없습니다.')
            return None
            
        # 사용자 찾기
        for user in self.users:
            if user['id'] == user_id:
                return user
                
        return None
    
    def add_user(self):
        """사용자 추가"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("사용자 추가")
            
            form = UserForm(is_super_admin=self.is_super_admin)
            
            # 회사 콤보박스가 있는 경우 회사 목록 로드
            if hasattr(form, 'company_combo'):
                form.company_combo.clear()
                form.company_combo.addItem("기본 회사 (자동 생성)", None)
                
                # 기존 회사 목록 추가
                for company in self.companies:
                    form.company_combo.addItem(company['name'], company['id'])
            
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            
            layout = QVBoxLayout()
            layout.addWidget(form)
            layout.addWidget(btn_box)
            dialog.setLayout(layout)
            
            if dialog.exec() == QDialog.Accepted:
                if not form.validate():
                    return
                    
                user_data = form.get_form_data()
                print(f"[사용자 추가] 사용자 데이터: {user_data}")
                
                # 슈퍼 관리자가 아니고 회사가 선택되지 않은 경우 기본 회사로 설정
                if user_data.get('role') != 'super_admin' and 'company_id' not in user_data:
                    user_data['company_id'] = None  # 서버에서 기본 회사로 자동 생성
                    print("[사용자 추가] 기본 회사로 설정")
                
                # 슈퍼 관리자인 경우 company_id 제거
                if user_data.get('role') == 'super_admin' and 'company_id' in user_data:
                    del user_data['company_id']
                    print("[사용자 추가] 슈퍼 관리자에서 company_id 제거")
                
                try:
                    print(f"[사용자 추가] API 요청: {user_data}")
                    response = requests.post(
                        f"{API_BASE_URL}/api/users/",
                        json=user_data,
                        headers=get_auth_header()
                    )
                    
                    if response.status_code == 201:
                        QMessageBox.information(self, '성공', '사용자가 추가되었습니다.')
                        self.load_users()
                    else:
                        try:
                            error_detail = response.json().get('detail', {})
                            if isinstance(error_detail, dict):
                                error_msg = '\n'.join([f"{k}: {v}" for k, v in error_detail.items()])
                            else:
                                error_msg = str(error_detail)
                        except:
                            error_msg = response.text or '사용자 추가 중 오류가 발생했습니다.'
                        
                        QMessageBox.warning(self, '오류', f'사용자 추가에 실패했습니다.\n\n{error_msg}')
                except Exception as e:
                    import traceback
                    error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
                    QMessageBox.critical(self, '오류', f'사용자 추가 중 오류가 발생했습니다.\n\n{error_detail}')
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
            QMessageBox.critical(self, '오류', f'사용자 추가 화면 로드 중 오류가 발생했습니다.\n\n{error_detail}')
    
    def edit_user(self):
        """사용자 수정"""
        user = self.get_selected_user()
        if not user:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("사용자 수정")
        
        form = UserForm(user=user, is_super_admin=self.is_super_admin)
        
        # 회사 콤보박스가 있는 경우 기존 회사 목록 로드
        if hasattr(form, 'company_combo'):
            form.company_combo.clear()
            form.company_combo.addItem("기본 회사 (자동 생성)", None)
            
            # 기존 회사 목록 추가
            for company in self.companies:
                form.company_combo.addItem(company['name'], company['id'])
                
            # 현재 사용자의 회사 선택
            if 'company_id' in user and user['company_id']:
                index = form.company_combo.findData(user['company_id'])
                if index >= 0:
                    form.company_combo.setCurrentIndex(index)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(form)
        layout.addWidget(btn_box)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            if not form.validate():
                return
                
            user_data = form.get_form_data()
            
            # 슈퍼 관리자가 아니고 회사가 선택되지 않은 경우 기본 회사로 설정
            if user_data.get('role') != 'super_admin' and 'company_id' not in user_data:
                user_data['company_id'] = None  # 서버에서 기본 회사로 자동 생성
            
            # 슈퍼 관리자인 경우 company_id 제거
            if user_data.get('role') == 'super_admin' and 'company_id' in user_data:
                del user_data['company_id']
            
            try:
                response = requests.put(
                    f"{API_BASE_URL}/api/users/{user['id']}",
                    json=user_data,
                    headers=get_auth_header()
                )
                
                if response.status_code == 200:
                    QMessageBox.information(self, '성공', '사용자 정보가 수정되었습니다.')
                    self.load_users()
                else:
                    try:
                        error_detail = response.json().get('detail', {})
                        if isinstance(error_detail, dict):
                            error_msg = '\n'.join([f"{k}: {v}" for k, v in error_detail.items()])
                        else:
                            error_msg = str(error_detail)
                    except:
                        error_msg = response.text or '사용자 수정 중 오류가 발생했습니다.'
                    
                    QMessageBox.warning(self, '오류', f'사용자 수정에 실패했습니다.\n\n{error_msg}')
            except Exception as e:
                import traceback
                error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
                QMessageBox.critical(self, '오류', f'사용자 수정 중 오류가 발생했습니다.\n\n{error_detail}')
    
    def delete_user(self):
        """사용자 삭제"""
        user = self.get_selected_user()
        if not user:
            return
            
        reply = QMessageBox.question(
            self,
            '사용자 삭제',
            f'정말로 "{user["username"]}" 사용자를 삭제하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/api/users/{user['id']}",
                    headers=get_auth_header()
                )
                
                if response.status_code == 204:
                    QMessageBox.information(self, '성공', '사용자가 삭제되었습니다.')
                    self.load_users()
                else:
                    try:
                        error_detail = response.json().get('detail', {})
                        if isinstance(error_detail, dict):
                            error_msg = '\n'.join([f"{k}: {v}" for k, v in error_detail.items()])
                        else:
                            error_msg = str(error_detail)
                    except:
                        error_msg = response.text or '사용자 삭제 중 오류가 발생했습니다.'
                    
                    QMessageBox.warning(self, '오류', f'사용자 삭제에 실패했습니다.\n\n{error_msg}')
            except Exception as e:
                import traceback
                error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
                QMessageBox.critical(self, '오류', f'사용자 삭제 중 오류가 발생했습니다.\n\n{error_detail}')
