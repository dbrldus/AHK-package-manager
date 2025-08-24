import sys, json, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QPushButton, QListWidgetItem, QLabel, QFrame, QScroller
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon

isDebugging = True

assetsPath = os.path.join(os.path.dirname(__file__), "..", "assets")
iconsPath = os.path.join(assetsPath, "icons")
pluginListPath = os.path.join(os.path.dirname(__file__),"plugin-list.json")

class PluginManagementGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(200, 200, 500, 350)
        self.plgJson = self.openJson(pluginListPath)
        self.plg_names = [_.get("name") for _ in self.plgJson]
        if isDebugging:
            print(self.plg_names)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        #region 커스텀 타이틀바
        titleBar = QFrame()
        titleBar.setFixedHeight(40)
        titleBar.setStyleSheet("background-color: #5E81AC;")
        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(10, 0, 10, 0)

        self.titleLabel = QLabel("AHK Plugins Manager")
        self.titleLabel.setStyleSheet("color: white; font-weight: bold;")
        self.titleLabel.setFont(QFont("Segoe UI", 8))

        btnMin = QPushButton(QIcon(os.path.join(iconsPath, "frame_.svg")),"")
        btnMin.setFixedSize(30, 24)
        btnMin.clicked.connect(self.showMinimized)
        
        btnClose = QPushButton(QIcon(os.path.join(iconsPath, "frameX.svg")),"")
        btnClose.setFixedSize(30, 24)
        btnClose.clicked.connect(self.close)

        for b in (btnMin, btnClose):
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

        titleLayout.addWidget(self.titleLabel)
        titleLayout.addStretch()
        titleLayout.addWidget(btnMin)
        titleLayout.addWidget(btnClose)
        titleBar.setLayout(titleLayout)
        #endregion

        # ===== 본문 =====
        bodyLayout = QHBoxLayout()
        bodyLayout.setContentsMargins(10, 10, 10, 10)

        leftListLayout = QVBoxLayout()
        self.leftList = QListWidget()
        self.leftListTitle = QLabel("대기중인 플러그인")
        leftListLayout.addWidget(self.leftListTitle)
        leftListLayout.addWidget(self.leftList)
        self.leftList.addItems(self.plg_names)
        bodyLayout.addLayout(leftListLayout)
        
        # 버튼
        btnLayout = QVBoxLayout()
        self.btnRight = QPushButton(QIcon(os.path.join(iconsPath, "arrowR.svg")), "")
        self.btnLeft = QPushButton(QIcon(os.path.join(iconsPath, "arrowL.svg")), "")
        self.btnReload = QPushButton(QIcon(os.path.join(iconsPath, "reloadbtn1.svg")), "")
        # 버튼설정
        self.btnRight.clicked.connect(self.moveRight)
        self.btnLeft.clicked.connect(self.moveLeft)
        self.btnReload.clicked.connect(self.reLoadPlg)

        btnLayout.addStretch()
        btnLayout.addWidget(self.btnRight)
        btnLayout.addWidget(self.btnLeft)
        btnLayout.addWidget(self.btnReload)
        btnLayout.addStretch()
        bodyLayout.addLayout(btnLayout)

        rightListLayout = QVBoxLayout()
        self.rightList = QListWidget()
        self.rightListTitle = QLabel("작동중인 플러그인")
        rightListLayout.addWidget(self.rightListTitle)
        rightListLayout.addWidget(self.rightList)
        bodyLayout.addLayout(rightListLayout)

        bodyFrame = QFrame()
        bodyFrame.setLayout(bodyLayout)

        mainLayout.addWidget(titleBar)
        mainLayout.addWidget(bodyFrame)
        self.setLayout(mainLayout)

        # 스타일시트
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
        # self.btnReload.setStyleSheet("""
        #     QPushButton {
        #         background-color: #5E81AC;
        #         border-radius: 8px;
        #         padding: 6px 12px;
        #     }
        #     QPushButton:hover {
        #         background-color: #88C0D0;
        #     }
        # """)
        self.btnReload.setStyleSheet("QPushButton { qproperty-iconSize: 24px 24px; }")
        self.btnRight.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")
        self.btnLeft.setStyleSheet("QPushButton { qproperty-iconSize: 20px 20px; }")


        # 타이틀바 드래그
        self.offset = QPoint()
        titleBar.mousePressEvent = self.title_mousePress
        titleBar.mouseMoveEvent = self.title_mouseMove

    # ===== 애니메이션 =====
    def animateTransfer(self, text, start_pos, end_pos, callbackA, callbackB):
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

    def moveRight(self):
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

    def moveLeft(self):
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


    # ===== 타이틀바 드래그 =====
    def title_mousePress(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPos() - self.frameGeometry().topLeft()

    def title_mouseMove(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)
    
    #정보통신
    def openJson(self, path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
            
    def reLoadPlg(self): # 플러그인 json에서 플러그인 이름 받아서 만약 추가되
        if isDebugging:
            print("Reloadbtn pushed!")
        new_plg_json = self.openJson(pluginListPath)
        new_plg_names = [_.get("name") for _ in new_plg_json]
        for name in set(new_plg_names) - set(self.plg_names):
            if isDebugging:
                print(set(new_plg_names) - set(self.plg_names))
                
            self.plg_names.append(name)
            self.leftList.addItem(name)
            
    def RunAHK(self, plg):
        return None
    def isEnabled(self, plg):
        return None
    def checkHotKey(self, plg):
        return None
    def findByName(self, data, name, target):
        return next((i[target] for i in data if i.get("name") == name), None)
        
        
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PluginManagementGUI()
    window.show()
    sys.exit(app.exec_())
