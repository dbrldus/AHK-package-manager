#========================================================================================================
# 파이썬 버전: 3.12.6
# PyQt5: 5.15.11
# Qt: 5.15.2
# 목차:
#   1) 라이브러리 import (PyQt5 위젯/코어/GUI, 표준 모듈)
#   2) 전역변수 및 경로 설정 (isDebugging, assets/icons 경로, package_list_path)
#   3) AHK 실행 파일 경로 조회 (find_ahk_path) 및 ahk_exe 바인딩
#   4) PackageManagementGUI 클래스
#       4-1) UI 구성: 커스텀 타이틀바, 버튼(최소화/종료), 본문 레이아웃(좌/중/우 리스트·버튼)
#       4-2) 스타일시트(다크 테마, 스크롤바 커스터마이즈)
#       4-3) 애니메이션 유틸: animateTransfer, moveRight, moveLeft
#       4-4) 타이틀바 드래그: titleMousePress, titleMouseMove
#       4-5) 데이터 I/O: openJson, reloadPkg
#       4-6) 패키지 헬퍼: findInfoByNameInPkgJson, findLibPathByNameInPkgJson,
#                         runPkgByNameInPkgJson(스텁), checkBindingsByNameInPkgJson(스텁)
#   5) 진입점: if __name__ == "__main__" (QApplication 실행)
#========================================================================================================

#region imports
import sys, json, os, winreg, threading, subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QListWidgetItem, QLabel, QFrame, QScroller
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon

#endregion

isDebugging = True #디버깅 변수

#region Path
assets_path = os.path.join(os.path.dirname(__file__), "..", "assets")
icons_path = os.path.join(assets_path, "icons")
package_list_path = os.path.join(os.path.dirname(__file__),"package-list.json")
#endregion

def find_ahk_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"AutoHotkeyScript\Shell\Open\Command")
        value, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)
        exe_path = value.split('"')[1]  # "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe" "%1"
        return exe_path
    except Exception as e:
        raise FileNotFoundError("Cannot find AutoHotkey executer.") from e

ahk_exe = find_ahk_path()


class PackageManagementGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(200, 200, 500, 350)
        self.pkgJson = self.openJson(package_list_path)
        self.pkgNames = [_.get("name") for _ in self.pkgJson]
        if isDebugging:
            print(self.pkgNames)
            
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        #region 커스텀 타이틀바
        
            #region 타이틀 레이아웃 기본 설정
        titleBar = QFrame()
        titleBar.setFixedHeight(40)
        titleBar.setStyleSheet("background-color: #5E81AC;")
        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(10, 0, 10, 0)
        #endregion 
        
            #region 타이틀에 적을 것들
        self.titleLabel = QLabel("AHK packages Manager")
        self.titleLabel.setStyleSheet("color: white; font-weight: bold;")
        self.titleLabel.setFont(QFont("Segoe UI", 8))
        #endregion 
        
            #region 타이틀에 놓일 버튼 (최소화, 나가기(종료), 디자인 포함)
        btnMin = QPushButton(QIcon(os.path.join(icons_path, "frame_.svg")),"")
        btnMin.setFixedSize(30, 24)
        btnMin.clicked.connect(self.showMinimized)
        
        btnClose = QPushButton(QIcon(os.path.join(icons_path, "frameX.svg")),"")
        btnClose.setFixedSize(30, 24)
        btnClose.clicked.connect(self.close)

        for b in (btnMin, btnClose): # 버튼 visual 관련
            b.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #88C0D0;
                }
            """)
        #endregion 

        #요소 배치
        titleLayout.addWidget(self.titleLabel)
        titleLayout.addStretch()
        titleLayout.addWidget(btnMin)
        titleLayout.addWidget(btnClose)
        titleBar.setLayout(titleLayout)
        
        # 타이틀바 드래그 기능
        self.offset = QPoint()
        titleBar.mousePressEvent = self.titleMousePress
        titleBar.mouseMoveEvent = self.titleMouseMove
        
        #endregion

        #region 레이아웃 구조 설명
        # body (전체, 수평으로 원소 배치)
        # body 아래, 세 개의 레이아웃 존재. 각각의 레이아웃은 리스트(설명 딸림)
        # 각각의 레이아웃 명칭은 leftListLayout, btnLayout, rightListLayout
        #endregion 
        
        #body 설정
        bodyLayout = QHBoxLayout()
        bodyLayout.setContentsMargins(10, 10, 10, 10)
        
        #region 좌측 리스트 leftList
        leftListLayout = QVBoxLayout()
        self.leftList = QListWidget()
        self.leftListTitle = QLabel("대기중인 패키지")
        leftListLayout.addWidget(self.leftListTitle)
        leftListLayout.addWidget(self.leftList)
        self.leftList.addItems(self.pkgNames)
        bodyLayout.addLayout(leftListLayout)
        #endregion 
        
        #region  본문 버튼 설정, 배치, 디자인
        btnLayout = QVBoxLayout()
        self.btnRight = QPushButton(QIcon(os.path.join(icons_path, "arrowR.svg")), "")
        self.btnLeft = QPushButton(QIcon(os.path.join(icons_path, "arrowL.svg")), "")
        self.btnReload = QPushButton(QIcon(os.path.join(icons_path, "reloadbtn1.svg")), "")
        
        # 버튼설정
        self.btnRight.clicked.connect(self.runPkg)
        self.btnLeft.clicked.connect(self.stopPkg)
        self.btnReload.clicked.connect(self.reloadPkg)
        
        # 버튼 배치
        btnLayout.addStretch()
        btnLayout.addWidget(self.btnRight)
        btnLayout.addWidget(self.btnLeft)
        btnLayout.addWidget(self.btnReload)
        btnLayout.addStretch()
        bodyLayout.addLayout(btnLayout)
        
        #버튼 디자인        
        self.btnReload.setStyleSheet("QPushButton { qproperty-iconSize: 24px 24px; }")
        self.btnRight.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")
        self.btnLeft.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")
        #endregion 
        
        #region 우측 리스트(작동중인 패키지) rightList
        rightListLayout = QVBoxLayout()
        self.rightList = QListWidget()
        self.rightListTitle = QLabel("작동중인 패키지")
        rightListLayout.addWidget(self.rightListTitle)
        rightListLayout.addWidget(self.rightList)
        bodyLayout.addLayout(rightListLayout)
        #endregion 
        
        #region 최종 화면 설정. body와는 다름
        bodyFrame = QFrame()
        bodyFrame.setLayout(bodyLayout)

        mainLayout.addWidget(titleBar)
        mainLayout.addWidget(bodyFrame)
        self.setLayout(mainLayout)
        #endregion 
        
        #region 스타일시트
        self.setStyleSheet("""
        QWidget {
            background-color: #2E3440;
            color: #ECEFF4;
            font-family: 'Segoe UI';
            font-size: 14px;
        }
        QListWidget {
            border: 2px solid #4C566A;
            border-radius: 8px;
            padding: 5px;
            background-color: #3B4252;
        }
        QListWidget::item {
            padding: 6px;
        }
        QListWidget::item:selected {
            background-color: #81A1C1;
            color: white;
        }
        QPushButton {
            background-color: #5E81AC;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #88C0D0;
        }
        QPushButton:pressed {
            background-color: #4C566A;
        }

        /* ===== 스크롤바 커스터마이즈 ===== */
        QScrollBar:vertical {
            background: #3B4252;
            width: 12px;
            margin: 2px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background: #81A1C1;
            min-height: 20px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background: #88C0D0;
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: none;
            height: 0px;
        }
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: none;
        }
    """)
    #endregion 

    #region  ===== 애니메이션 관련 =====
    def animateTransfer(self, text, start_pos, end_pos, callbackA, callbackB): #딱히 수정 필요없음. 순수 애니메이팅. A 위치에서 B 위치로 이동하는 기능
        label = QLabel(text, self)
        label.setStyleSheet("background-color: #81A1C1; color: white; padding: 4px; border-radius: 4px;")
        label.adjustSize()
        callbackA()
        label.move(start_pos)
        label.show()

        anim = QPropertyAnimation(label, b"pos")
        anim.setDuration(400)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def onFinished():
            label.deleteLater()
            callbackB()

        anim.finished.connect(onFinished)
        anim.start()
        # PyQt GC 방지 → 객체를 변수에 붙여둠
        self._anim = anim

    def moveRight(self): #수정 불필요. 애니메이팅 보조 기능
        for item in self.leftList.selectedItems():
            text = item.text()
            start = self.leftList.mapToGlobal(self.leftList.visualItemRect(item).topLeft())
            end = self.rightList.mapToGlobal(self.rightList.rect().topLeft())
            start = self.mapFromGlobal(start)
            end = self.mapFromGlobal(end)

            def beforeMoveing():
                self.leftList.takeItem(self.leftList.row(item))
            def finish():
                self.rightList.addItem(text)
            self.animateTransfer(text, start, end, beforeMoveing ,finish)

    def moveLeft(self): #수정 불필요. 애니메이팅 보조 기능
        for item in self.rightList.selectedItems():
            text = item.text()
            start = self.rightList.mapToGlobal(self.rightList.visualItemRect(item).topLeft())
            end = self.leftList.mapToGlobal(self.leftList.rect().topLeft())
            start = self.mapFromGlobal(start)
            end = self.mapFromGlobal(end)

            def beforeMoveing():
                self.rightList.takeItem(self.rightList.row(item))
            def finish():
                self.leftList.addItem(text)
            self.animateTransfer(text, start, end, beforeMoveing, finish)

    #endregion 
    
    # ===== 타이틀바 드래그 =====
    def titleMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPos() - self.frameGeometry().topLeft()

    def titleMouseMove(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
    
    #정보통신. json을 열고, 읽고, (쓸 수는 없음), 각종 ahk실행 및 
    def openJson(self, path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
            
    def reloadPkg(self): # 패키지 json에서 패키지 이름 받아서 만약 추가되
        if isDebugging:
            print("Reloadbtn pushed!")
        new_pkg_json = self.openJson(package_list_path)
        new_pkgNames = [_.get("name") for _ in new_pkg_json]
        for name in set(new_pkgNames) - set(self.pkgNames):
            if isDebugging:
                print(set(new_pkgNames) - set(self.pkgNames))
                
            self.pkgNames.append(name)
            self.leftList.addItem(name)
        
            
    def findInfoByNameInPkgJson(self, name, target): # data는 package-list.json 의 원형(딕셔너리를 원소로 갖는 리스트). name은 말 그대로 패키지 "이름"(name, id 아님). target은 찾고 싶은 패키지의 인자. id, path, version 등. 
        return next((i[target] for i in self.pkgJson if i.get("name") == name), None)
    def findLibPathByNameInPkgJson(self, name):
        return os.path.join(os.path.dirname(__file__), "..", self.findInfoByNameInPkgJson(name, "path"))
    def runPkgByNameInPkgJson(self, pkg, name): # 인자 pkg라 함은 core 디렉토리의 package-list.json의 최외곽 리스트의 각 딕셔너리 타입 원소를 의미한다. 
        pkg_path = self.findLibPathByNameInPkgJson(name)
        
    def checkBindingsByNameInPkgJson(self, pkg):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PackageManagementGUI()
    window.show()
    sys.exit(app.exec_())
