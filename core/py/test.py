from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

class Demo(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cursor Demo")
        self.resize(400, 300)
        self.setMouseTracking(True)
        self.margin = 8

    def mouseMoveEvent(self, e):
        r = self.rect(); m = self.margin
        x, y = e.pos().x(), e.pos().y()
        if (x <= m and y <= m) or (x >= r.width()-m and y >= r.height()-m):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (x >= r.width()-m and y <= m) or (x <= m and y >= r.height()-m):
            self.setCursor(Qt.SizeBDiagCursor)
        elif x <= m or x >= r.width()-m:
            self.setCursor(Qt.SizeHorCursor)
        elif y <= m or y >= r.height()-m:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    w = Demo()
    w.show()
    app.exec_()
