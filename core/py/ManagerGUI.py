#region # 설명 및 목차========================================================================================================
# 파이썬 버전: 3.12.6
# PyQt5: 5.15.11
# Qt: 5.15.2
# 목차:
#   1) 라이브러리 import (PyQt5 위젯/코어/GUI, 표준 모듈)
#   2) 전역변수 및 경로 설정 (isDebugging, assets/icons 경로, package_list_path)
#   3) AHK 실행 파일 경로 조회 (find_ahk_path) 및 ahk_exe_path 바인딩
#   4) PackageManagementGUI 클래스
#       4-1) UI 구성: 커스텀 타이틀바, 버튼(최소화/종료), 본문 레이아웃(좌/중/우 리스트·버튼)
#       4-2) 스타일시트(다크 테마, 스크롤바 커스터마이즈)
#       4-3) 애니메이션 유틸: animateTransfer, moveRight, moveLeft
#       4-4) 타이틀바 드래그: titleMousePress, titleMouseMove
#       4-5) 데이터 I/O: openJson, reloadPkg
#       4-6) 패키지 헬퍼: findInfoByNameInPkgJson, findLibPathByNameInPkgJson,
#                         runPkgByNameInPkgJson(스텁), checkBindingsByNameInPkgJson(스텁)
#   5) 진입점: if __name__ == "__main__" (QApplication 실행)
#endregion #=================================================================================================================

#region imports
import sys, json, os, winreg, threading, subprocess, time, difflib
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QListWidgetItem, QLabel, QFrame, QScroller, QLineEdit, QSpacerItem, QSizePolicy,
    QStyledItemDelegate
)
from util.PyRPC import RPCManager
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon, QColor, QBrush, QPainter
from util.path import ROOT_PATH, DATA_PATH, CONFIG_PATH, RUNTIME_PATH, SCHEMA_PATH, TEMP_PATH, CORE_PATH, ASSETS_PATH, ICONS_PATH, PKGS_PATH

#endregion

isDebugging = True #디버깅 변수

#region Path
package_list_path = os.path.join(SCHEMA_PATH, "package-list.json")
rpc_communication_path = os.path.join(TEMP_PATH, "ipc")

def find_ahk_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"AutoHotkeyScript\Shell\Open\Command")
        value, _ = winreg.QueryValueEx(key, "")
        winreg.CloseKey(key)
        exe_path = value.split('"')[1]  # "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe" "%1"
        return exe_path
    except Exception as e:
        raise FileNotFoundError("Cannot find AutoHotkey executer.") from e

ahk_exe_path = find_ahk_path()
#endregion 


#region 우월한 리스트 위젯
class ToggleList(QListWidget):
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item and item.isSelected():
            item.setSelected(False)
            
            return  # 여기서 이벤트를 소비해서 다시 선택되지 않게 함
        super().mousePressEvent(event)

class SearchableList(ToggleList):
    def __init__(self, search_bar):
        super().__init__()

        self.searchBar = search_bar
        self.searchBar.textChanged.connect(self.highlightAndMove)
        
    def highlightAndMove(self, text):
        text = text.strip().lower()

        # 먼저 모든 아이템 색 초기화
        for i in range(self.count()):
            item = self.item(i)
            item.setForeground(QColor("white"))
            font = item.font()
            font.setBold(False)        # 볼드체 켜기
            # font.setItalic(True)    # 필요시 이탤릭
            item.setFont(font)

        if not text:
            # 검색 없으면 전체 정렬
            self.sortItems(Qt.AscendingOrder)
            return

        matches = []
        for i in range(self.count()):
            item = self.item(i)
            word = item.text().lower()
            # 부분 포함
            if text in word or difflib.SequenceMatcher(None, text, word).ratio() >= 0.60:
                item.setForeground(QColor("#ED7D31"))
                font = item.font()
                font.setBold(True)        # 볼드체 켜기
                # font.setItalic(True)    # 필요시 이탤릭
                item.setFont(font)
                matches.append(item)

        # match 상단으로
        for item in matches:
            row = self.row(item)
            self.takeItem(row)
            self.insertItem(0, item)

        # 나머지 사전순 정렬
        # (matches 그대로)
        count = self.count()
        match_count = len(matches)
        if match_count < count:
            items = [self.item(i).text() for i in range(match_count, count)]
            items.sort(key=lambda s: s.lower())
            for i in range(match_count, count):
                self.item(i).setText(items[i - match_count])
#endregion 

class UiBridge(QObject):
    movePkgRightSig = pyqtSignal()  
    hubStatusSig = pyqtSignal()

class PackageManagementGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(200, 200, 500, 350)
        
        self.pkgJson = self.openJson(package_list_path)
        self.pkgNames = [_.get("name") for _ in self.pkgJson]
        if isDebugging:
            print(self.pkgNames)
        self._anims = [] #텍스트 여러 개 옮길 때 애니메이션 각각 저장하기 위함
        
        #region RPC 통신용 셋업

        self.client = RPCManager(rpc_communication_path)
        self.bridge = UiBridge()
        self.bridge.movePkgRightSig.connect(self.moveRight, Qt.QueuedConnection)
        self.bridge.hubStatusSig.connect(self.checkHubStatus, Qt.QueuedConnection)
        self.client.regist(self._rpc_run_wrapper, "MovePkgRight")
        self.client.regist(self._check_hub, "doCheckHubStatus")
        self.client.spin()
        #endregion 

        #region 눈에보이는거
        #region 메인 레이아웃 설정
        mainLayout = QVBoxLayout()
        
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        
        #endregion 
        
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
        btnMin = QPushButton(QIcon(os.path.join(ICONS_PATH, "frame_.svg")),"")
        btnMin.setFixedSize(30, 24)
        btnMin.clicked.connect(self.showMinimized)
        
        btnClose = QPushButton(QIcon(os.path.join(ICONS_PATH, "frameX.svg")),"")
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
        
        #region 검색바
        
        searchLayout = QHBoxLayout()
        searchBar = QLineEdit()
        searchLayout.setContentsMargins(10, 5, 10, 5) 

        leftSpacer  = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        rightSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Search Pkg...")
        searchBar.setFixedWidth(200)  # 폭 고정
        
        searchLayout.addItem(leftSpacer)
        searchLayout.addWidget(searchBar)
        searchLayout.addItem(rightSpacer)
        
        #endregion 
        
        #region body 설정
        bodyLayout = QHBoxLayout()
        bodyLayout.setContentsMargins(10, 10, 10, 10)
        #endregion 
        
        #region 좌측 리스트 leftList
        leftListLayout = QVBoxLayout()
        self.leftList = SearchableList(search_bar=searchBar)
        
        self.leftList.setSelectionMode(ToggleList.ExtendedSelection)
        self.leftList.itemClicked.connect(self.delRightSelectedItems)
        self.leftListTitle = QLabel("Ready")
        leftListLayout.addWidget(self.leftListTitle)
        leftListLayout.addWidget(self.leftList)
        self.leftList.addItems(self.pkgNames)
        bodyLayout.addLayout(leftListLayout)
        #endregion 
        
        #region  본문 버튼 설정, 배치, 디자인
        btnLayout = QVBoxLayout()
        self.btnRight = QPushButton(QIcon(os.path.join(ICONS_PATH, "arrowR.svg")), "")
        self.btnLeft = QPushButton(QIcon(os.path.join(ICONS_PATH, "arrowL.svg")), "")
        self.btnReload = QPushButton(QIcon(os.path.join(ICONS_PATH, "reloadbtn1.svg")), "")
        self.btnOnOffHub = QPushButton(QIcon(os.path.join(ICONS_PATH, "onOff.svg")), "")
        self.hubStatusLable = QLabel(text="Hub: Off")
        self.hubStatusLable.setStyleSheet("color: red;")
        
        
        # 버튼설정
        self.btnRight.clicked.connect(self.runPkgCall)
        self.btnLeft.clicked.connect(self.moveLeft)
        self.btnReload.clicked.connect(self.reloadPkg)
        self.btnOnOffHub.clicked.connect(self.hubOnOff)
        
        # 버튼 배치
        btnLayout.addStretch()
        btnLayout.addWidget(self.btnOnOffHub)
        btnLayout.addWidget(self.hubStatusLable)
        btnLayout.addWidget(self.btnRight)
        btnLayout.addWidget(self.btnLeft)
        btnLayout.addWidget(self.btnReload)
        btnLayout.addStretch()
        bodyLayout.addLayout(btnLayout)
        
        #버튼 디자인        
        self.btnReload.setStyleSheet("QPushButton { qproperty-iconSize: 24px 24px; }")
        self.btnRight.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")
        self.btnLeft.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")
        self.btnOnOffHub.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")
        #endregion 
        
        #region 우측 리스트(작동중인 패키지) rightList
        rightListLayout = QVBoxLayout()
        self.rightList = SearchableList(search_bar=searchBar)
        self.rightList.setSelectionMode(ToggleList.ExtendedSelection)
        self.rightList.itemClicked.connect(self.delLeftSelectedItems)
        self.rightListTitle = QLabel("Active")
        rightListLayout.addWidget(self.rightListTitle)
        rightListLayout.addWidget(self.rightList)
        bodyLayout.addLayout(rightListLayout)
        #endregion 
        
        #region 최종 화면 설정. body와는 다름
        bodyFrame = QFrame()
        bodyFrame.setLayout(bodyLayout)

        mainLayout.addWidget(titleBar)
        mainLayout.addLayout(searchLayout)
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
        #endregion 

    #region 함수 영역
    #region  ===== 애니메이션 관련 =====
    def animateTransfer(self, text, start_pos, end_pos, callback):
        label = QLabel(text, self)
        label.setStyleSheet("background-color: #81A1C1; color: white; padding: 4px; border-radius: 4px;")
        label.adjustSize()
        label.move(start_pos)
        label.show()

        anim = QPropertyAnimation(label, b"pos")
        anim.setDuration(400)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def onFinished():
            label.deleteLater()
            callback()   # 여기서 지우기

        anim.finished.connect(onFinished)
        anim.start()
        if not hasattr(self, "_anims"):
            self._anims = []
        self._anims.append(anim)


    def moveRight(self, item = None):
        selected = list(self.leftList.selectedItems())
        if item != None:
            selected = [item]
        else:
            selected = list(self.leftList.selectedItems())
            
        texts = [item.text() for item in selected]
        for item in selected:
            self.leftList.takeItem(self.leftList.row(item))
            
        for text in texts:
            start = self.leftList.mapToGlobal(self.leftList.visualItemRect(item).topLeft())
            end = self.rightList.mapToGlobal(self.rightList.rect().topLeft())
            start = self.mapFromGlobal(start)
            end = self.mapFromGlobal(end)

            def finish(text=text):
                self.rightList.addItem(text)

            self.animateTransfer(text, start, end, finish)
        
    def moveLeft(self):
        selected = list(self.leftList.selectedItems())
        texts = [item.text() for item in selected]
        for item in selected:
            self.rightList.takeItem(self.rightList.row(item)) #
            
        for text in texts:
            start = self.rightList.mapToGlobal(self.rightList.visualItemRect(item).topLeft()) #
            end = self.leftList.mapToGlobal(self.leftList.rect().topLeft())
            start = self.mapFromGlobal(start)
            end = self.mapFromGlobal(end)

            def finish(text=text):
                self.leftList.addItem(text)

            self.animateTransfer(text, start, end, finish)

    #endregion 
    
    #region ===== 타이틀바 드래그 =====
    def titleMousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPos() - self.frameGeometry().topLeft()

    def titleMouseMove(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
    #endregion 
    
    #region ===== 리스트 관련 함수 =====
    def delRightSelectedItems(self, _):
        if len(self.rightList.selectedItems()):
            self.rightList.clearSelection()
    def delLeftSelectedItems(self, _):
        if len(self.leftList.selectedItems()):
            self.leftList.clearSelection()
    #endregion 
    
    #region 정보통신. json을 열고, 읽고, (쓸 수는 없음), 각종 ahk실행 및 
    
    def openJson(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def reloadPkg(self): # 패키지 json에서 패키지 이름 받아서 만약 추가되면 리스트에도 추가.
        if isDebugging:
            print("Reloadbtn pushed!")
        new_pkg_json = self.openJson(package_list_path)
        new_pkgNames = [_.get("name") for _ in new_pkg_json]
        for name in set(new_pkgNames) - set(self.pkgNames):
            if isDebugging:
                print(set(new_pkgNames) - set(self.pkgNames))
                
            if name in [item.text() for item in list(self.leftList.Items())]:
                self.leftList.takeItem(self.leftList.row(name))
            self.pkgNames.append(name)
            self.leftList.addItem(name)
        
    def findInfoByNameInPkgJson(self, name, target): # data는 package-list.json 의 원형(딕셔너리를 원소로 갖는 리스트). name은 말 그대로 패키지 "이름"(name, id 아님). target은 찾고 싶은 패키지의 인자. id, path, version 등. 
        return next((i[target] for i in self.pkgJson if i.get("name") == name), None)
    
    def findInstallDirByNameInPkgJson(self, name):
        return os.path.join(PKGS_PATH, self.findInfoByNameInPkgJson(name, "id"))
    
    def runPkgByNameInPkgJson(self, name): # 인자 pkg라 함은 core 디렉토리의 package-list.json의 최외곽 리스트의 각 딕셔너리 타입 원소를 의미한다. 
        pkg_init_path = os.path.join(self.findInstallDirByNameInPkgJson(name), "init.ahk")
        print(f"pkg_init_path is {pkg_init_path}!!")
        if(not self.client.request("runPkgInit",[pkg_init_path])):
            return 0
        else:
            return 1
    
    def runPkgCall(self):
        selected = list(self.leftList.selectedItems())
        # print(selected)
        texts = [item.text() for item in selected]
        print(texts)
        for text in texts:
            self.runPkgByNameInPkgJson(text)
        
    def stopPkgCall(self):
        pass
        
    def _rpc_run_wrapper(self, *args):
        self.bridge.movePkgRightSig.emit()
        return 0
    
    
    def findItemByName(self, qlist:QListWidget, name):
        obj = list(qlist.items())
        for item in obj:
            if item.text() == name:
                return item
    
    def moveItemRightByName(self, name):
        target_item = self.findItemByName(self.leftList, name)
        self.moveRight(item=target_item)
        return 0
    
    def moveItemLeftByName(self, name):
        target_item = self.findItemByName(self.leftList, name)
        self.moveRight(item=target_item)
        return 0
    #region HUB ON/OFF 관련
    def _check_hub(self, *args):
        self.bridge.hubStatusSig.emit()
        return 0
    
    def checkHubStatus(self):
        path = os.path.join(RUNTIME_PATH, "hub-status.json")
        data = self.openJson(path)
        print("checking hub state...")
        if(data["is_active"] == "True"):
            self.hubStatusLable.setStyleSheet("color: green;")
            self.hubStatusLable.setText("Hub status: On")
        else:
            self.hubStatusLable.setStyleSheet("color: red;")
            self.hubStatusLable.setText("Hub status: Off")
    
    def hubOnOff(self):
        path = os.path.join(RUNTIME_PATH, "hub-status.json")
        data = self.openJson(path)

        if data["is_active"] == "True":
            # 현재 켜져 있으니 종료 실행
            subprocess.Popen([ahk_exe_path, os.path.join(CORE_PATH, "ahk", "shutdown.ahk")])
        else:
            # 현재 꺼져 있으니 초기화 실행
            subprocess.Popen([ahk_exe_path, os.path.join(CORE_PATH, "ahk", "init.ahk")])
    #endregion 
    #endregion 
    #endregion 
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PackageManagementGUI()
    window.show()
    window.checkHubStatus()
    sys.exit(app.exec_())
