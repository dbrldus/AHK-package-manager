import sys
import os
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class InstallThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_running = True
        
    def run(self):
        tasks = [
            ("설치 환경 확인 중...", 10),
            ("필수 구성 요소 검사 중...", 20),
            ("파일 압축 해제 중...", 35),
            ("AHK 런타임 설치 중...", 50),
            ("패키지 매니저 구성 중...", 65),
            ("레지스트리 항목 생성 중...", 75),
            ("바로 가기 생성 중...", 85),
            ("설치 마무리 중...", 95),
            ("설치 완료!", 100)
        ]
        
        for task, progress in tasks:
            if not self.is_running:
                break
            self.status.emit(task)
            self.progress.emit(progress)
            time.sleep(0.8)  # 더미 지연

class WizardPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWizardPage {
                background-color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit, QTextEdit, QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QCheckBox, QRadioButton {
                color: #2c3e50;
                spacing: 8px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)

class WelcomePage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("AHK Package Manager 설치 마법사")
        self.setSubTitle("")
        
        layout = QVBoxLayout()
        
        # 로고 영역
        logo_label = QLabel()
        logo_label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                color: white;
                font-size: 32px;
                font-weight: bold;
                padding: 40px;
                border-radius: 10px;
            }
        """)
        logo_label.setText("AHK\nPackage Manager")
        logo_label.setAlignment(Qt.AlignCenter)
        
        welcome_text = QLabel(
            "AHK Package Manager v2.5.0 설치를 시작합니다.\n\n"
            "이 프로그램은 AutoHotkey 스크립트를 효율적으로 관리하고\n"
            "실행할 수 있는 통합 패키지 관리 도구입니다.\n\n"
            "설치를 계속하려면 '다음' 버튼을 클릭하십시오."
        )
        welcome_text.setWordWrap(True)
        welcome_text.setStyleSheet("font-size: 12px; line-height: 1.6; padding: 20px 0;")
        
        layout.addWidget(logo_label)
        layout.addWidget(welcome_text)
        layout.addStretch()
        
        self.setLayout(layout)

class LicensePage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("사용권 계약")
        self.setSubTitle("소프트웨어 사용 조건에 동의해 주십시오")
        
        layout = QVBoxLayout()
        
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setPlainText("""AHK Package Manager 최종 사용자 라이선스 계약서

중요 - 주의 깊게 읽어주십시오

본 최종 사용자 라이선스 계약서("계약서")는 AHK Package Manager 소프트웨어("소프트웨어")에 대한 귀하와 개발팀 간의 법적 계약입니다.

1. 라이선스 부여
본 계약서의 조건에 따라, 개발팀은 귀하에게 본 소프트웨어를 사용할 수 있는 비독점적, 양도 불가능한 라이선스를 부여합니다.

2. 사용 제한
귀하는 본 소프트웨어를 리버스 엔지니어링, 디컴파일, 디스어셈블하거나 소스 코드를 추출하려고 시도해서는 안 됩니다.

3. 저작권
본 소프트웨어는 저작권법 및 국제 조약에 의해 보호됩니다. 본 소프트웨어의 모든 권리는 개발팀에 있습니다.

4. 보증 부인
본 소프트웨어는 "있는 그대로" 제공되며, 명시적이든 묵시적이든 어떠한 종류의 보증도 제공되지 않습니다.

5. 책임 제한
어떠한 경우에도 개발팀은 본 소프트웨어의 사용 또는 사용 불능으로 인한 손해에 대해 책임지지 않습니다.

본 계약서에 동의하시면 아래 체크박스를 선택하고 '다음'을 클릭하십시오.""")
        
        self.accept_checkbox = QCheckBox("사용권 계약 조건에 동의합니다")
        self.accept_checkbox.toggled.connect(self.check_accept)
        
        layout.addWidget(QLabel("라이선스 계약서:"))
        layout.addWidget(license_text)
        layout.addWidget(self.accept_checkbox)
        
        self.setLayout(layout)
        
        # 필수 필드 등록
        self.registerField("licenseAccepted*", self.accept_checkbox)
        
    def check_accept(self):
        self.completeChanged.emit()
        
    def isComplete(self):
        return self.accept_checkbox.isChecked()

class InstallDirPage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("설치 위치 선택")
        self.setSubTitle("AHK Package Manager를 설치할 폴더를 선택하십시오")
        
        layout = QVBoxLayout()
        
        # 설치 경로
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit("C:\\Program Files\\AHK Package Manager")
        self.browse_btn = QPushButton("찾아보기...")
        self.browse_btn.clicked.connect(self.browse_folder)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        
        # 디스크 공간 정보
        space_info = QGroupBox("디스크 공간 정보")
        space_layout = QVBoxLayout()
        space_layout.addWidget(QLabel("필요한 공간: 45.2 MB"))
        space_layout.addWidget(QLabel("사용 가능한 공간: 238.4 GB"))
        space_info.setLayout(space_layout)
        space_info.setStyleSheet("""
            QGroupBox {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout.addWidget(QLabel("설치 폴더:"))
        layout.addLayout(path_layout)
        layout.addWidget(space_info)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 필드 등록
        self.registerField("installPath", self.path_edit)
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "설치 폴더 선택")
        if folder:
            self.path_edit.setText(folder)

class ComponentsPage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("구성 요소 선택")
        self.setSubTitle("설치할 구성 요소를 선택하십시오")
        
        layout = QVBoxLayout()
        
        # 구성 요소 목록
        self.components_tree = QTreeWidget()
        self.components_tree.setHeaderLabel("구성 요소")
        self.components_tree.setRootIsDecorated(False)
        
        # 주요 구성 요소
        main_item = QTreeWidgetItem(["AHK Package Manager (필수)"])
        main_item.setCheckState(0, Qt.Checked)
        main_item.setFlags(main_item.flags() & ~Qt.ItemIsUserCheckable)
        main_item.setIcon(0, self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 추가 구성 요소
        items = [
            ("스크립트 편집기", Qt.Checked, QStyle.SP_FileDialogDetailedView),
            ("디버깅 도구", Qt.Checked, QStyle.SP_FileDialogListView),
            ("샘플 스크립트", Qt.Checked, QStyle.SP_DirOpenIcon),
            ("온라인 리포지토리 연동", Qt.Unchecked, QStyle.SP_DriveNetIcon),
            ("개발자 도구", Qt.Unchecked, QStyle.SP_ComputerIcon)
        ]
        
        self.components_tree.addTopLevelItem(main_item)
        
        for name, state, icon in items:
            item = QTreeWidgetItem([name])
            item.setCheckState(0, state)
            item.setIcon(0, self.style().standardIcon(icon))
            self.components_tree.addTopLevelItem(item)
        
        # 설명
        self.description_label = QLabel("구성 요소를 선택하면 여기에 설명이 표시됩니다.")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                min-height: 60px;
            }
        """)
        
        layout.addWidget(self.components_tree)
        layout.addWidget(QLabel("설명:"))
        layout.addWidget(self.description_label)
        
        self.setLayout(layout)

class StartupPage(WizardPage):
    def __init__(self, ahk_file_path=""):
        super().__init__()
        self.ahk_file_path = ahk_file_path
        self.setTitle("추가 옵션")
        self.setSubTitle("시작 프로그램 및 추가 옵션을 설정하십시오")
        
        layout = QVBoxLayout()
        
        # 시작 프로그램 옵션
        startup_group = QGroupBox("시작 프로그램")
        startup_layout = QVBoxLayout()
        
        self.startup_checkbox = QCheckBox("Windows 시작 시 AHK Package Manager 자동 실행")
        self.startup_checkbox.setChecked(True)
        
        self.startup_minimized = QCheckBox("시작 시 최소화 상태로 실행")
        self.startup_minimized.setEnabled(True)
        
        startup_layout.addWidget(self.startup_checkbox)
        startup_layout.addWidget(self.startup_minimized)
        startup_group.setLayout(startup_layout)
        
        # 바로 가기 옵션
        shortcut_group = QGroupBox("바로 가기")
        shortcut_layout = QVBoxLayout()
        
        self.desktop_shortcut = QCheckBox("바탕화면에 바로 가기 만들기")
        self.desktop_shortcut.setChecked(True)
        
        self.startmenu_shortcut = QCheckBox("시작 메뉴에 바로 가기 만들기")
        self.startmenu_shortcut.setChecked(True)
        
        self.quicklaunch_shortcut = QCheckBox("빠른 실행에 바로 가기 만들기")
        
        shortcut_layout.addWidget(self.desktop_shortcut)
        shortcut_layout.addWidget(self.startmenu_shortcut)
        shortcut_layout.addWidget(self.quicklaunch_shortcut)
        shortcut_group.setLayout(shortcut_layout)
        
        # AHK 파일 경로 표시 (있을 경우)
        if self.ahk_file_path:
            ahk_group = QGroupBox("등록할 AHK 파일")
            ahk_layout = QVBoxLayout()
            ahk_label = QLabel(f"파일 경로: {self.ahk_file_path}")
            ahk_label.setWordWrap(True)
            ahk_layout.addWidget(ahk_label)
            ahk_group.setLayout(ahk_layout)
            layout.addWidget(ahk_group)
        
        layout.addWidget(startup_group)
        layout.addWidget(shortcut_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 필드 등록
        self.registerField("addToStartup", self.startup_checkbox)
        self.registerField("startMinimized", self.startup_minimized)

class ReadyPage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("설치 준비 완료")
        self.setSubTitle("설치를 시작할 준비가 되었습니다")
        
        layout = QVBoxLayout()
        
        ready_label = QLabel(
            "설치를 시작하려면 '설치' 버튼을 클릭하십시오.\n"
            "설정을 변경하려면 '이전' 버튼을 클릭하십시오."
        )
        ready_label.setWordWrap(True)
        
        # 설치 요약
        summary_group = QGroupBox("설치 요약")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        
        summary_layout.addWidget(self.summary_text)
        summary_group.setLayout(summary_layout)
        
        layout.addWidget(ready_label)
        layout.addWidget(summary_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def initializePage(self):
        # 설치 요약 정보 업데이트
        install_path = self.field("installPath")
        license_accepted = self.field("licenseAccepted")
        add_to_startup = self.field("addToStartup")
        
        summary = f"""설치 위치: {install_path}
프로그램 유형: 전체 설치
구성 요소: 모든 구성 요소
시작 프로그램 등록: {'예' if add_to_startup else '아니오'}
바로 가기 생성: 바탕화면, 시작 메뉴
예상 설치 시간: 약 2-3분
필요한 디스크 공간: 45.2 MB"""
        
        self.summary_text.setPlainText(summary)

class InstallPage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("설치 중")
        self.setSubTitle("AHK Package Manager를 설치하고 있습니다...")
        
        layout = QVBoxLayout()
        
        # 진행 상태
        self.status_label = QLabel("설치 준비 중...")
        self.status_label.setStyleSheet("font-weight: bold; color: #2980b9;")
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        
        # 상세 로그
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("설치 로그:"))
        layout.addWidget(self.log_text)
        layout.addStretch()
        
        self.setLayout(layout)
        
        self.install_thread = None
        
    def initializePage(self):
        # 설치 시작
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "설치 중...")
        self.wizard().button(QWizard.BackButton).setEnabled(False)
        self.wizard().button(QWizard.CommitButton).setEnabled(False)
        
        # 설치 스레드 시작
        self.install_thread = InstallThread()
        self.install_thread.progress.connect(self.update_progress)
        self.install_thread.status.connect(self.update_status)
        self.install_thread.finished.connect(self.installation_finished)
        
        # 초기 로그
        self.log_text.append("[INFO] 설치 프로세스 시작")
        self.log_text.append(f"[INFO] 설치 경로: {self.field('installPath')}")
        
        QTimer.singleShot(500, self.install_thread.start)
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def update_status(self, status):
        self.status_label.setText(status)
        self.log_text.append(f"[INFO] {status}")
        
    def installation_finished(self):
        self.log_text.append("[SUCCESS] 설치가 성공적으로 완료되었습니다!")
        self.wizard().button(QWizard.NextButton).setEnabled(True)
        self.completeChanged.emit()
        
    def isComplete(self):
        return self.progress_bar.value() == 100

class CompletePage(WizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("설치 완료")
        self.setSubTitle("")
        
        layout = QVBoxLayout()
        
        # 완료 아이콘과 메시지
        complete_icon = QLabel()
        complete_icon.setPixmap(self.style().standardPixmap(QStyle.SP_DialogApplyButton).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        complete_icon.setAlignment(Qt.AlignCenter)
        
        complete_msg = QLabel(
            "AHK Package Manager가 성공적으로 설치되었습니다!\n\n"
            "이제 AutoHotkey 스크립트를 효율적으로 관리하고\n"
            "실행할 수 있습니다."
        )
        complete_msg.setAlignment(Qt.AlignCenter)
        complete_msg.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        
        # 옵션
        self.launch_checkbox = QCheckBox("AHK Package Manager 지금 실행")
        self.launch_checkbox.setChecked(True)
        
        self.readme_checkbox = QCheckBox("README 파일 보기")
        
        # 추가 정보
        info_group = QGroupBox("설치 정보")
        info_layout = QVBoxLayout()
        info_text = QLabel(
            "• 프로그램 위치: C:\\Program Files\\AHK Package Manager\n"
            "• 시작 메뉴: 시작 > 모든 프로그램 > AHK Package Manager\n"
            "• 제어판에서 언제든지 제거할 수 있습니다."
        )
        info_text.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        
        layout.addWidget(complete_icon)
        layout.addWidget(complete_msg)
        layout.addSpacing(20)
        layout.addWidget(self.launch_checkbox)
        layout.addWidget(self.readme_checkbox)
        layout.addWidget(info_group)
        layout.addStretch()
        
        self.setLayout(layout)

class InstallWizard(QWizard):
    def __init__(self, ahk_file_path=""):
        super().__init__()
        self.ahk_file_path = ahk_file_path
        
        self.setWindowTitle("AHK Package Manager 설치 마법사")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setFixedSize(650, 500)
        
        # 윈도우 스타일
        self.setStyleSheet("""
            QWizard {
                background-color: #f8f9fa;
            }
            QWizard QPushButton {
                min-width: 80px;
                padding: 6px 12px;
            }
        """)
        
        # 아이콘 설정
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        
        # 페이지 추가
        self.addPage(WelcomePage())
        self.addPage(LicensePage())
        self.addPage(InstallDirPage())
        self.addPage(ComponentsPage())
        self.addPage(StartupPage(ahk_file_path))
        self.addPage(ReadyPage())
        self.addPage(InstallPage())
        self.addPage(CompletePage())
        
        # 버튼 텍스트 한글화
        self.setButtonText(QWizard.BackButton, "< 이전")
        self.setButtonText(QWizard.NextButton, "다음 >")
        self.setButtonText(QWizard.CommitButton, "설치")
        self.setButtonText(QWizard.FinishButton, "완료")
        self.setButtonText(QWizard.CancelButton, "취소")
        
        # 로고 추가
        logo = QPixmap(100, 100)
        logo.fill(Qt.transparent)
        painter = QPainter(logo)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(0, 0, 100, 100)
        gradient.setColorAt(0, QColor("#3498db"))
        gradient.setColorAt(1, QColor("#2980b9"))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(10, 10, 80, 80, 10, 10)
        
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(logo.rect(), Qt.AlignCenter, "AHK\nPM")
        painter.end()
        
        self.setPixmap(QWizard.LogoPixmap, logo)
        
    def accept(self):
        # 설치 완료 시 동작 (더미이므로 실제 동작 없음)
        print("설치 마법사 완료!")
        if self.ahk_file_path:
            print(f"시작 프로그램 등록 예정 파일: {self.ahk_file_path}")
        super().accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 여기에 시작프로그램에 등록할 AHK 파일 경로를 입력하세요
    ahk_file_path = "C:\\Users\\YourName\\Scripts\\example.ahk"  # 이 경로를 원하는 경로로 변경
    
    wizard = InstallWizard(ahk_file_path)
    wizard.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()