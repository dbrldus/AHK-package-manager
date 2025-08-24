import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("QVBoxLayout - 수직 배치")

layout1 = QVBoxLayout()
layout1.addWidget(QLabel("첫 번째"))
layout1.addWidget(QPushButton("두 번째"))
layout1.addWidget(QPushButton("세 번째"))
layout2 = QVBoxLayout()
# layout2.addWidget(QLabel("e 번째"))
layout2.addWidget(QPushButton("r 번째"))
layout2.addWidget(QPushButton("f 번째"))
layoutm = QHBoxLayout()
layoutm.addLayout(layout1)
layoutm.addLayout(layout2)
window.setLayout(layoutm)
window.show()
sys.exit(app.exec_())
