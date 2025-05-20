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

class CompanyForm(QWidget):
    """회사 등록/수정 폼 위젯"""
    def __init__(self, parent=None, company=None, is_super_admin=False):
        super().__init__(parent)
        self.company = company
        self.is_super_admin = is_super_admin
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout(self)
        
        # 회사명
        self.name_edit = QLineEdit()
        layout.addRow("회사명*:", self.name_edit)
        
        # 사업자등록번호
        self.business_number_edit = QLineEdit()
        self.business_number_edit.setPlaceholderText("숫자 10자리")
        layout.addRow("사업자등록번호*:", self.business_number_edit)
        
        # 주소
        self.address_edit = QLineEdit()
        layout.addRow("주소:", self.address_edit)
        
        # 전화번호
        self.phone_edit = QLineEdit()
        layout.addRow("전화번호:", self.phone_edit)
        
        # 기존 회사 데이터 로드
        if self.company:
            self.load_company_data()
    
    def load_company_data(self):
        """기존 회사 데이터 로드"""
        if not self.company:
            return
            
        self.name_edit.setText(self.company.get('name', ''))
        self.business_number_edit.setText(self.company.get('business_number', ''))
        self.address_edit.setText(self.company.get('address', ''))
        self.phone_edit.setText(self.company.get('phone', ''))
    
    def get_form_data(self):
        """폼 데이터 가져오기"""
        data = {
            'name': self.name_edit.text().strip(),
            'business_number': self.business_number_edit.text().strip().replace('-', ''),
            'address': self.address_edit.text().strip(),
            'phone': self.phone_edit.text().strip()
        }
        
        # 빈 값은 제외
        return {k: v for k, v in data.items() if v}
    
    def validate(self):
        """폼 유효성 검사"""
        data = self.get_form_data()
        
        if not data.get('name'):
            QMessageBox.warning(self, '입력 오류', '회사명을 입력해주세요.')
            return False
            
        if not data.get('business_number'):
            QMessageBox.warning(self, '입력 오류', '사업자등록번호를 입력해주세요.')
            return False
            
        # 사업자등록번호 유효성 검사 (숫자만 10자리)
        business_number = data.get('business_number', '')
        if not business_number.isdigit() or len(business_number) != 10:
            QMessageBox.warning(self, '입력 오류', '사업자등록번호는 숫자 10자리로 입력해주세요.')
            return False
        
        return True

class CompanyManagementDialog(QDialog):
    """회사 관리 다이얼로그"""
    def __init__(self, parent=None, is_super_admin=False):
        super().__init__(parent)
        self.is_super_admin = is_super_admin
        self.companies = []
        self.init_ui()
        self.load_companies()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("회사 관리")
        self.resize(800, 600)
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        
        # 회사 목록 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "회사명", "사업자등록번호", "주소", "전화번호"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self.add_company)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("수정")
        self.edit_btn.clicked.connect(self.edit_company)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.clicked.connect(self.delete_company)
        button_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.load_companies)
        button_layout.addWidget(self.refresh_btn)
        
        # 슈퍼 관리자가 아니면 추가/수정/삭제 버튼 비활성화
        if not self.is_super_admin:
            self.add_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
        
        # 레이아웃에 위젯 추가
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
    
    def load_companies(self):
        """회사 목록 로드"""
        try:
            print("[회사 관리] 회사 목록 로드 시도")
            
            # 인증 헤더 디버깅
            headers = get_auth_header()
            print(f"[회사 관리] 인증 헤더: {headers}")
            
            # API 요청
            api_url = f"{API_BASE_URL}/api/companies/"
            print(f"[회사 관리] API URL: {api_url}")
            
            # 페이징 파라미터 추가
            params = {
                'skip': 0,
                'limit': 100  # 한 번에 가져올 최대 항목 수
            }
            
            response = requests.get(
                api_url,
                headers=headers,
                params=params
            )
            
            print(f"[회사 관리] 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                # items 필드에서 회사 목록을 가져옴
                if isinstance(response_data, dict) and 'items' in response_data:
                    self.companies = response_data['items']
                    print(f"[회사 관리] 불러온 회사 수: {len(self.companies)}")
                    self.update_table()
                else:
                    print(f"[회사 관리] 잘못된 응답 형식: {response_data}")
                    QMessageBox.warning(self, '오류', '잘못된 응답 형식입니다.')
            else:
                error_msg = response.text
                print(f"[회사 관리] 오류 응답: {error_msg}")
                QMessageBox.warning(self, '오류', f'회사 목록을 불러오는데 실패했습니다.\n\n상태 코드: {response.status_code}\n\n{error_msg}')
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
            print(f"[회사 관리] 예외 발생: {error_detail}")
            QMessageBox.critical(self, '오류', f'회사 목록을 불러오는 중 오류가 발생했습니다.\n\n{error_detail}')
    
    def update_table(self):
        """테이블 업데이트"""
        self.table.setRowCount(0)
        
        for company in self.companies:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(company.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(company.get('name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(company.get('business_number', '')))
            self.table.setItem(row, 3, QTableWidgetItem(company.get('address', '')))
            self.table.setItem(row, 4, QTableWidgetItem(company.get('phone', '')))
    
    def get_selected_company(self):
        """선택된 회사 가져오기"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, '선택 오류', '회사를 선택해주세요.')
            return None
            
        row = selected_rows[0].row()
        company_id = int(self.table.item(row, 0).text())
        
        for company in self.companies:
            if company['id'] == company_id:
                return company
                
        return None
    
    def add_company(self):
        """회사 추가"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("회사 추가")
            
            form = CompanyForm(is_super_admin=self.is_super_admin)
            
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
                    
                company_data = form.get_form_data()
                print(f"[회사 추가] 회사 데이터: {company_data}")
                
                try:
                    print(f"[회사 추가] API 요청: {company_data}")
                    response = requests.post(
                        f"{API_BASE_URL}/api/companies/",
                        json=company_data,
                        headers=get_auth_header()
                    )
                    
                    if response.status_code == 201:
                        QMessageBox.information(self, '성공', '회사가 추가되었습니다.')
                        self.load_companies()
                    else:
                        try:
                            error_detail = response.json().get('detail', {})
                            if isinstance(error_detail, dict):
                                error_msg = '\n'.join([f"{k}: {v}" for k, v in error_detail.items()])
                            else:
                                error_msg = str(error_detail)
                        except:
                            error_msg = response.text or '회사 추가 중 오류가 발생했습니다.'
                        
                        QMessageBox.warning(self, '오류', f'회사 추가에 실패했습니다.\n\n{error_msg}')
                except Exception as e:
                    import traceback
                    error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
                    QMessageBox.critical(self, '오류', f'회사 추가 중 오류가 발생했습니다.\n\n{error_detail}')
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
            QMessageBox.critical(self, '오류', f'회사 추가 화면 로드 중 오류가 발생했습니다.\n\n{error_detail}')
    
    def edit_company(self):
        """회사 수정"""
        company = self.get_selected_company()
        if not company:
            return
            
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("회사 수정")
            
            form = CompanyForm(company=company, is_super_admin=self.is_super_admin)
            
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
                    
                company_data = form.get_form_data()
                print(f"[회사 수정] 회사 데이터: {company_data}")
                
                try:
                    print(f"[회사 수정] API 요청: {company_data}")
                    response = requests.put(
                        f"{API_BASE_URL}/api/companies/{company['id']}",
                        json=company_data,
                        headers=get_auth_header()
                    )
                    
                    if response.status_code == 200:
                        QMessageBox.information(self, '성공', '회사 정보가 수정되었습니다.')
                        self.load_companies()
                    else:
                        try:
                            error_detail = response.json().get('detail', {})
                            if isinstance(error_detail, dict):
                                error_msg = '\n'.join([f"{k}: {v}" for k, v in error_detail.items()])
                            else:
                                error_msg = str(error_detail)
                        except:
                            error_msg = response.text or '회사 수정 중 오류가 발생했습니다.'
                        
                        QMessageBox.warning(self, '오류', f'회사 수정에 실패했습니다.\n\n{error_msg}')
                except Exception as e:
                    import traceback
                    error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
                    QMessageBox.critical(self, '오류', f'회사 수정 중 오류가 발생했습니다.\n\n{error_detail}')
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
            QMessageBox.critical(self, '오류', f'회사 수정 화면 로드 중 오류가 발생했습니다.\n\n{error_detail}')
    
    def delete_company(self):
        """회사 삭제"""
        company = self.get_selected_company()
        if not company:
            return
            
        # 삭제 확인
        reply = QMessageBox.question(
            self, '삭제 확인', 
            f"'{company['name']}' 회사를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            print(f"[회사 삭제] 삭제 요청 - 회사 ID: {company['id']}, 회사명: {company['name']}")
            
            # 인증 헤더 디버깅
            headers = get_auth_header()
            print(f"[회사 삭제] 인증 헤더: {headers}")
            
            # API 요청
            api_url = f"{API_BASE_URL}/api/companies/{company['id']}"
            print(f"[회사 삭제] API URL: {api_url}")
            
            response = requests.delete(
                api_url,
                headers=headers
            )
            
            print(f"[회사 삭제] 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    message = result.get('message', '회사가 삭제되었습니다.')
                    print(f"[회사 삭제] 성공 - {message}")
                except:
                    message = '회사가 삭제되었습니다.'
                
                QMessageBox.information(self, '성공', message)
                self.load_companies()
            else:
                try:
                    error_detail = response.json().get('detail', {})
                    if isinstance(error_detail, dict):
                        error_msg = '\n'.join([f"{k}: {v}" for k, v in error_detail.items()])
                    else:
                        error_msg = str(error_detail)
                except:
                    error_msg = response.text or '회사 삭제 중 오류가 발생했습니다.'
                
                print(f"[회사 삭제] 오류 - {error_msg}")
                QMessageBox.warning(self, '오류', f'회사 삭제에 실패했습니다.\n\n{error_msg}')
        except Exception as e:
            import traceback
            error_detail = f'{str(e)}\n\n{traceback.format_exc()}'
            print(f"[회사 삭제] 예외 발생 - {error_detail}")
            QMessageBox.critical(self, '오류', f'회사 삭제 중 오류가 발생했습니다.\n\n{error_detail}')
