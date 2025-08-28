#region # 설명 및 목차========================================================================================================
# 파이썬 버전: 3.12.6
# PyQt5: 5.15.11
# Qt: 5.15.2
# 수정사항: 창 크기 가변, 왼쪽 사이드바 추가
#endregion #=================================================================================================================

#region imports
import sys, json, os, winreg, shutil, threading, subprocess, time, difflib
from typing import *
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QListWidgetItem, QLabel, QFrame, QScroller, QLineEdit, QSpacerItem, QSizePolicy,
    QStyledItemDelegate, QSplitter, QFileDialog
)
from util.PyRPC2 import RPCManager
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRectF, pyqtSignal, QObject, QRect, QEvent
from PyQt5.QtGui import QFont, QIcon, QColor, QBrush, QPainter, QCursor
from util.path import ROOT_PATH, DATA_PATH, CONFIG_PATH, RUNTIME_PATH, SCHEMA_PATH, TEMP_PATH, CORE_PATH, ASSETS_PATH, ICONS_PATH, PKGS_PATH

#endregion

isDebugging = True #디버깅 변수

#region Path
package_list_path = os.path.join(SCHEMA_PATH, "package-list.json")
rpc_communication_path = os.path.join(TEMP_PATH, "ipc")
hub_status_path = os.path.join(RUNTIME_PATH,"hub-status.json")

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
    reloadGuiSig = pyqtSignal()  
    hubStatusSig = pyqtSignal()

class PackageManagementGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 창 크기 가변으로 변경 - setGeometry 대신 resize 사용
        self.resize(800, 500)  # 초기 크기만 설정
        self.setMinimumSize(600, 400)  # 최소 크기 설정
        self.offset = QPoint()
        self.resize_margin = 8
        self.resizing = False
        self.resize_direction = set()  # {'left','right','top','bottom'}
        self.resize_start_pos = None
        self.resize_start_geo = None
        self.setMouseTracking(True)  # 버튼 안 눌러도 move 이벤트 받기
        
        QApplication.instance().installEventFilter(self)
        
        self.pkgJson = self.openJson(package_list_path)
        self.pkgInfos : list[tuple[str,str]] = [ (item.get("id"), item.get("name")) for item in self.pkgJson]
        self.activePkgIds = set()
        self.pkgNames : list[str] = [_.get("name") for _ in self.pkgJson]
        if isDebugging:
            print(self.pkgNames)
        self._anims = [] #텍스트 여러 개 옮길 때 애니메이션 각각 저장하기 위함
        
        #region RPC 통신용 셋업

        self.client = RPCManager(rpc_communication_path)
        self.bridge = UiBridge()
        self.bridge.reloadGuiSig.connect(self.reloadGUI, Qt.QueuedConnection)
        self.bridge.hubStatusSig.connect(self.checkHubStatus, Qt.QueuedConnection)
        self.client.regist(self._rpc_run_wrapper, "reloadGui")
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
        
        # 타이틀바 드래그 기능 + 리사이즈 기능 추가
        
        titleBar.mousePressEvent = self.titleMousePress
        titleBar.mouseMoveEvent = self.titleMouseMove
        
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
        
        #region 새로운 전체 body (사이드바 + 기존 body)
        fullBodyLayout = QHBoxLayout()
        fullBodyLayout.setContentsMargins(0, 0, 0, 0)
        fullBodyLayout.setSpacing(0)
        
        #region 왼쪽 사이드바 추가
        sideBar = QFrame()
        sideBar.setFixedWidth(60)
        sideBar.setStyleSheet("""
            QFrame {
                background-color: #2E3440;
                border-right: 2px solid #4C566A;
            }
        """)
        
        sideBarLayout = QVBoxLayout()
        sideBarLayout.setContentsMargins(5, 10, 5, 10)
        sideBarLayout.setSpacing(5)
        #endregion 
        #region 사이드바 버튼들
        sideBarButtons = []
        sideBarIcons = ["🏠", "📦", "⚙️", "➕", "❓"]  # 이모지 대신 실제 아이콘 파일 사용 가능
        sideBarTooltips = ["Home", "Packages", "Settings", "Add", "Help"]
        
        for i, (icon, tooltip) in enumerate(zip(sideBarIcons, sideBarTooltips)):
            btn = QPushButton(icon)
            btn.setFixedSize(50, 50)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B4252;
                    border: none;
                    border-radius: 8px;
                    color: #D8DEE9;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: #4C566A;
                }
                QPushButton:pressed {
                    background-color: #5E81AC;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.onSideBarClick(idx))
            sideBarLayout.addWidget(btn)
            sideBarButtons.append(btn)
        
        sideBarLayout.addStretch()
        sideBar.setLayout(sideBarLayout)
        #endregion
        
        #region body 설정 (기존 body)
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

        self.reloadGUI()
        #endregion
        
        #region 최종 화면 설정. 
        bodyFrame = QFrame()
        bodyFrame.setLayout(bodyLayout)
        
        # 사이드바와 body를 fullBodyLayout에 추가
        fullBodyLayout.addWidget(sideBar)
        fullBodyLayout.addWidget(bodyFrame, 1)  # stretch factor 1로 body가 늘어나도록

        mainLayout.addWidget(titleBar)
        mainLayout.addLayout(searchLayout)
        mainLayout.addLayout(fullBodyLayout)
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
    
    # 사이드바 버튼 클릭 핸들러
    def onSideBarClick(self, index):
        buttons = ["Home", "Packages", "Settings", "Add", "Help"]
        print(f"Clicked: {buttons[index]}")
        if(index == 3):
            self.addPkg()
        
    #region 창 크기변경 관련
    def _hit_edges(self, pos):
        rect = self.rect()
        m = self.resize_margin
        on_left   = pos.x() <= m
        on_right  = pos.x() >= rect.width()  - m
        on_top    = pos.y() <= m
        on_bottom = pos.y() >= rect.height() - m
        return on_left, on_right, on_top, on_bottom

    # ---- 마우스 이벤트 ----
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)

        pos = event.pos()
        on_left, on_right, on_top, on_bottom = self._hit_edges(pos)
        dir_set = set()
        if on_left: dir_set.add("left")
        if on_right: dir_set.add("right")
        if on_top: dir_set.add("top")
        if on_bottom: dir_set.add("bottom")

        if dir_set:
            self.resizing = True
            self.resize_direction = dir_set
            self.resize_start_pos = event.globalPos()
            # 시작 지오메트리는 반드시 "복사"
            self.resize_start_geo = QRect(self.geometry())
        else:
            self.resizing = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # --- 리사이즈 동작 ---
        if not self.resizing:
            return
        r = self.rect()

        delta = event.globalPos() - self.resize_start_pos
        start = self.resize_start_geo
        r = QRect(start)  # 복사본

        if "left" in self.resize_direction:
            new_left = start.left() + delta.x()
            min_w = self.minimumWidth()
            new_left = min(new_left, start.right() - (min_w - 1))
            r.setLeft(new_left)
        elif "right" in self.resize_direction:
            new_right = start.right() + delta.x()
            min_w = self.minimumWidth()
            new_right = max(new_right, start.left() + (min_w - 1))
            r.setRight(new_right)

        if "top" in self.resize_direction:
            new_top = start.top() + delta.y()
            min_h = self.minimumHeight()
            new_top = min(new_top, start.bottom() - (min_h - 1))
            r.setTop(new_top)
        elif "bottom" in self.resize_direction:
            new_bot = start.bottom() + delta.y()
            min_h = self.minimumHeight()
            new_bot = max(new_bot, start.top() + (min_h - 1))
            r.setBottom(new_bot)

        self.setGeometry(r.normalized())
        
    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.MouseMove:
            gp = QCursor.pos()
            lp = self.mapFromGlobal(gp)
            r = self.rect(); m = 10
            x, y = lp.x(), lp.y()

            # 대각선 우선
            if (x <= m and y <= m) or (x >= r.width()-m and y >= r.height()-m):
                self.setCursor(Qt.SizeFDiagCursor)   # ↘︎↖︎
            elif (x >= r.width()-m and y <= m) or (x <= m and y >= r.height()-m):
                self.setCursor(Qt.SizeBDiagCursor)   # ↗︎↙︎
            elif x <= m or x >= r.width()-m:
                self.setCursor(Qt.SizeHorCursor)     # ↔︎
            elif y <= m or y >= r.height()-m:
                self.setCursor(Qt.SizeVerCursor)     # ↕︎
            else:
                self.setCursor(Qt.ArrowCursor)       # 기본 화살표
        return super().eventFilter(obj, ev)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.resizing:
            self.resizing = False
            self.resize_direction.clear()
        return super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
    # 마우스가 위젯 밖으로 나가면 커서 복구
        if not self.resizing:
            self.unsetCursor()
        return super().leaveEvent(event)
    #endregion 
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
            
        for item in selected:
            self.leftList.takeItem(self.leftList.row(item))
            
        for item in selected:
            text = item.text()
            start = self.leftList.mapToGlobal(self.leftList.visualItemRect(item).topLeft())
            end = self.rightList.mapToGlobal(self.rightList.rect().topLeft())
            start = self.mapFromGlobal(start)
            end = self.mapFromGlobal(end)

            def finish(item=item):
                self.rightList.addItem(item)

            self.animateTransfer(text, start, end, finish)
        
    def moveLeft(self, item = None):
        selected = list(self.rightList.selectedItems())
        if item != None:
            selected = [item]
        else:
            selected = list(self.rightList.selectedItems())

        for item in selected:
            self.rightList.takeItem(self.rightList.row(item)) #
            
        for item in selected:
            text = item.text()
            start = self.rightList.mapToGlobal(self.rightList.visualItemRect(item).topLeft()) #
            end = self.leftList.mapToGlobal(self.leftList.rect().topLeft())
            start = self.mapFromGlobal(start)
            end = self.mapFromGlobal(end)

            def finish(item=item):
                self.leftList.addItem(item)

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
    def genListWidgetItemWithId(self, id : str, title : str) :
        listItem = QListWidgetItem(title)
        listItem.setData(Qt.UserRole, id)
        return listItem

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
    
    def addPkg(self):
        home_dir = str(os.path.join(Path.home(), "Downloads"))
        dir_path = QFileDialog.getExistingDirectory(None, '패키지 폴더 선택', home_dir, QFileDialog.ShowDirsOnly)
        if dir_path:
            fileName = dir_path.split("/")[-1]
            for f in ["init.ahk", f"{fileName}.ahk", "package.json", "bindings.json"]:
                p = Path(os.path.join(dir_path, f))
                if not p.is_file():
                    print(f"Selected Directory({dir_path}) is not a proper ahk package")
                    print(f"{f} does not exist in selected package")
                    break
            else:
                print("AHK Package Confirmed")
                try:
                    shutil.copytree(dir_path, os.path.join(PKGS_PATH, fileName))
                    pkgList = self.openJson(package_list_path)
                    currentPkgInfo = self.openJson(os.path.join(PKGS_PATH, fileName, "package.json"))
                    pkgList.append(currentPkgInfo)
                    with open(package_list_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(pkgList, indent=4, ensure_ascii=False, sort_keys=True))
                        self.reloadPkg()
                    print("Add Package Completed")
                except FileExistsError:
                    print("Error : Package Already Exists")
                except FileNotFoundError:
                    print("Error : Could Not Find Selected Package")
        else:
            print("Fail to import package.")
            
    def reloadPkg(self): # 패키지 json에서 패키지 이름 받아서 만약 추가되면 리스트에도 추가.
        if isDebugging:
            print("Reloadbtn pushed!")
        new_pkg_json = self.openJson(package_list_path)
        new_pkgInfos : list[tuple[str,str]] = [ (item.get("id"), item.get("name")) for item in new_pkg_json]
        self.pkgInfos = new_pkgInfos
        self.checkActivePkg()
        self.reloadGUIwithAnimation()

    def reloadGUI(self):
        self.leftList.clear()
        self.rightList.clear()
        for id, name in self.pkgInfos:
            listItem = self.genListWidgetItemWithId(id, name)
            if id in self.activePkgIds: #active #animation?
                self.rightList.addItem(listItem)
            else: #not active
                self.leftList.addItem(listItem)
    
    def reloadGUIwithAnimation(self):
        leftIds = [self.leftList.item(i).data(Qt.UserRole) for i in range(self.leftList.count())]
        rightIds = [self.rightList.item(i).data(Qt.UserRole) for i in range(self.rightList.count())]

        for id, _ in self.pkgInfos:
            if id in self.activePkgIds and id in leftIds: #active #animation?
                self.moveItemRightById(id)
            elif id in rightIds: #not active
                self.moveItemLeftById(id)

    def checkActivePkg(self):
        pkgStatus = self.openJson(os.path.join(RUNTIME_PATH, "package-status.json"))
        activePkgIdList = []
        for singlePkg in pkgStatus:
            try:
                if(singlePkg.get("status", "dummy") == "running"):
                    activePkgIdList.append(pkgStatus["id"])
            except:
                print("Invalid Package Status")
        self.activePkgIds = set(activePkgIdList)

    def runPkgById(self, id): # 인자 pkg라 함은 core 디렉토리의 package-list.json의 최외곽 리스트의 각 딕셔너리 타입 원소를 의미한다. 
        if(not self.client.request("runPkgInit",[id])):
            return 0
        else:
            return 1
    
    def runPkgCall(self):
        selected = list(self.leftList.selectedItems())
        ids = [item.data(Qt.UserRole) for item in selected]
        for id in ids:
            self.runPkgById(id)
        
    def stopPkgCall(self):
        pass
        
    def _rpc_run_wrapper(self, *args):
        self.checkActivePkg()
        self.bridge.reloadGuiSig.emit()
        return 0
    
    def findItemById(self, qlist:QListWidget, id):
        for i in range(qlist.count()):
            item = qlist.item(i)
            if item.data(Qt.UserRole) == id:
                return item
    
    def moveItemRightById(self, id):
        target_item = self.findItemById(self.leftList, id)
        self.moveRight(item=target_item)
        return 0
    
    def moveItemLeftById(self, id):
        target_item = self.findItemById(self.rightList, id)
        self.moveLeft(item=target_item)
        return 0

    #region HUB ON/OFF 관련
    def _check_hub(self, *args):
        self.bridge.hubStatusSig.emit()
        return "Hub_checked, this res is from PyGui"
    
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
            creation_flags = subprocess.DETACHED_PROCESS | 0x01000000

            # 표준 입출력을 완전히 분리하여 더욱 안정적으로 만듭니다.
            subprocess.Popen(
                [ahk_exe_path, os.path.join(CORE_PATH, "ahk", "shutdown.ahk")],
                creationflags=creation_flags,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("off hub!!")
        elif(data["is_active"] == "False"):
            creation_flags = subprocess.DETACHED_PROCESS | 0x01000000

            # 표준 입출력을 완전히 분리하여 더욱 안정적으로 만듭니다.
            proc = subprocess.Popen(
                [ahk_exe_path, os.path.join(CORE_PATH, "ahk", "Hub.ahk")],
                creationflags=creation_flags,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            

    #endregion 
    #endregion 
    #endregion 
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PackageManagementGUI()
    window.show()
    window.checkHubStatus()
    sys.exit(app.exec_())