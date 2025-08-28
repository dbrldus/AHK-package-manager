#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QPushButton, 
                             QLineEdit, QLabel, QWidget, QMessageBox)
from PyQt5.QtCore import Qt

class ListWidgetExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('QListWidget Items 예제')
        self.setGeometry(300, 300, 500, 400)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)  # 다중 선택 가능
        main_layout.addWidget(self.list_widget)

        # 입력 섹션
        input_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("추가할 텍스트 입력...")
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_item)
        
        input_layout.addWidget(self.line_edit)
        input_layout.addWidget(add_btn)
        main_layout.addLayout(input_layout)
        
        # 버튼 섹션
        button_layout = QHBoxLayout()
        
        # 기본 샘플 아이템 추가
        sample_btn = QPushButton("샘플 추가")
        sample_btn.clicked.connect(self.add_sample_items)
        button_layout.addWidget(sample_btn)
        
        # 모든 아이템 출력
        show_all_btn = QPushButton("모든 아이템 출력")
        show_all_btn.clicked.connect(self.show_all_items)
        button_layout.addWidget(show_all_btn)
        
        # 선택된 아이템 출력
        show_selected_btn = QPushButton("선택된 아이템 출력")
        show_selected_btn.clicked.connect(self.show_selected_items)
        button_layout.addWidget(show_selected_btn)
        
        # 현재 아이템 출력
        show_current_btn = QPushButton("현재 아이템 출력")
        show_current_btn.clicked.connect(self.show_current_item)
        button_layout.addWidget(show_current_btn)
        
        main_layout.addLayout(button_layout)
        
        # 두 번째 버튼 행
        button_layout2 = QHBoxLayout()
        
        # 아이템 검색
        find_btn = QPushButton("'아이템' 검색")
        find_btn.clicked.connect(self.find_items)
        button_layout2.addWidget(find_btn)
        
        # 선택된 아이템 삭제
        delete_selected_btn = QPushButton("선택 삭제")
        delete_selected_btn.clicked.connect(self.delete_selected)
        button_layout2.addWidget(delete_selected_btn)
        
        # 모든 아이템 삭제
        clear_btn = QPushButton("모두 삭제")
        clear_btn.clicked.connect(self.clear_all)
        button_layout2.addWidget(clear_btn)
        
        # 아이템 개수 표시
        count_btn = QPushButton("아이템 개수")
        count_btn.clicked.connect(self.show_count)
        button_layout2.addWidget(count_btn)
        
        main_layout.addLayout(button_layout2)
        
        # 정보 레이블
        self.info_label = QLabel("리스트 위젯 예제 - 다양한 아이템 조작을 테스트해보세요")
        self.info_label.setWordWrap(True)
        main_layout.addWidget(self.info_label)
        
        # Enter 키로 아이템 추가
        self.line_edit.returnPressed.connect(self.add_item)
    
    def add_item(self):
        """텍스트 입력으로 아이템 추가"""
        text = self.line_edit.text().strip()
        if text:
            self.list_widget.addItem(text)
            self.line_edit.clear()
            self.info_label.setText(f"'{text}' 아이템이 추가되었습니다.")
        else:
            self.info_label.setText("텍스트를 입력해주세요.")
    
    def add_sample_items(self):
        """샘플 아이템들 추가"""
        sample_items = ["아이템 1", "아이템 2", "테스트 아이템", "샘플 데이터", "리스트 항목"]
        for item_text in sample_items:
            self.list_widget.addItem(item_text)
        self.info_label.setText(f"{len(sample_items)}개의 샘플 아이템이 추가되었습니다.")
    
    def show_all_items(self):
        """모든 아이템 출력"""
        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item:
                items.append(item.text())
        
        if items:
            items_text = "\\n".join([f"{i+1}. {text}" for i, text in enumerate(items)])
            QMessageBox.information(self, "모든 아이템", f"총 {len(items)}개 아이템:\\n\\n{items_text}")
            self.info_label.setText(f"총 {len(items)}개의 아이템을 출력했습니다.")
        else:
            QMessageBox.information(self, "모든 아이템", "아이템이 없습니다.")
            self.info_label.setText("출력할 아이템이 없습니다.")
    
    def show_selected_items(self):
        """선택된 아이템들 출력"""
        selected_items = self.list_widget.selectedItems()
        
        if selected_items:
            items_text = "\\n".join([f"• {item.text()}" for item in selected_items])
            QMessageBox.information(self, "선택된 아이템", f"선택된 아이템 ({len(selected_items)}개):\\n\\n{items_text}")
            self.info_label.setText(f"{len(selected_items)}개의 선택된 아이템을 출력했습니다.")
        else:
            QMessageBox.information(self, "선택된 아이템", "선택된 아이템이 없습니다.")
            self.info_label.setText("선택된 아이템이 없습니다.")
    
    def show_current_item(self):
        """현재 선택된 아이템 출력"""
        current_item = self.list_widget.currentItem()
        
        if current_item:
            current_row = self.list_widget.currentRow()
            QMessageBox.information(self, "현재 아이템", 
                                  f"현재 아이템: '{current_item.text()}'\\n인덱스: {current_row}")
            self.info_label.setText(f"현재 아이템: '{current_item.text()}' (인덱스: {current_row})")
        else:
            QMessageBox.information(self, "현재 아이템", "현재 선택된 아이템이 없습니다.")
            self.info_label.setText("현재 선택된 아이템이 없습니다.")
    
    def find_items(self):
        """'아이템'이 포함된 항목 찾기"""
        found_items = self.list_widget.findItems("아이템", Qt.MatchContains)
        
        if found_items:
            items_text = "\\n".join([f"• {item.text()}" for item in found_items])
            QMessageBox.information(self, "검색 결과", 
                                  f"'아이템'이 포함된 항목 ({len(found_items)}개):\\n\\n{items_text}")
            
            # 찾은 아이템들 선택
            self.list_widget.clearSelection()
            for item in found_items:
                item.setSelected(True)
            
            self.info_label.setText(f"'아이템'이 포함된 {len(found_items)}개 항목을 찾아 선택했습니다.")
        else:
            QMessageBox.information(self, "검색 결과", "'아이템'이 포함된 항목이 없습니다.")
            self.info_label.setText("'아이템'이 포함된 항목이 없습니다.")
    
    def delete_selected(self):
        """선택된 아이템들 삭제"""
        selected_items = self.list_widget.selectedItems()
        
        if selected_items:
            count = len(selected_items)
            # 역순으로 삭제 (인덱스가 변하지 않도록)
            for item in selected_items:
                row = self.list_widget.row(item)
                self.list_widget.takeItem(row)
            
            self.info_label.setText(f"{count}개의 선택된 아이템을 삭제했습니다.")
        else:
            self.info_label.setText("삭제할 아이템을 선택해주세요.")
    
    def clear_all(self):
        """모든 아이템 삭제"""
        count = self.list_widget.count()
        self.list_widget.clear()
        self.info_label.setText(f"모든 아이템 ({count}개)을 삭제했습니다.")
    
    def show_count(self):
        """아이템 개수 표시"""
        count = self.list_widget.count()
        QMessageBox.information(self, "아이템 개수", f"총 {count}개의 아이템이 있습니다.")
        self.info_label.setText(f"총 {count}개의 아이템이 있습니다.")

def main():
    app = QApplication(sys.argv)
    window = ListWidgetExample()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()