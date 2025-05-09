import os
import sys
import time
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QMessageBox, QProgressBar, QApplication, QStyleFactory,
    QFileDialog, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QGroupBox, QScrollArea, QFrame, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette

from ui.file_cleanup_tab import FileCleanupTab
from ui.process_manager_tab import ProcessManagerTab
from ui.battery_monitor_tab import BatteryMonitorTab

class MainWindow(QMainWindow):
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.setWindowTitle("Laptop Optimizer")
        self.setMinimumSize(800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        self.file_cleanup_tab = FileCleanupTab(self.controller)
        self.process_manager_tab = ProcessManagerTab(self.controller)
        self.battery_monitor_tab = BatteryMonitorTab(self.controller)
        
        self.tabs.addTab(self.file_cleanup_tab, "File Cleanup")
        self.tabs.addTab(self.process_manager_tab, "Process Manager")
        self.tabs.addTab(self.battery_monitor_tab, "Battery Health")
        
        self.status_bar = self.statusBar()
        self.status_bar_label = QLabel()
        self.status_bar.addWidget(self.status_bar_label)
        
        self.update_status("Ready")
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_current_tab)
        self.refresh_timer.start(5000)
        
        self.on_tab_changed(0)
    
    def update_status(self, message):
        self.status_bar_label.setText(message)
    
    def on_tab_changed(self, index):
        tab_name = self.tabs.tabText(index)
        self.update_status(f"Viewing {tab_name}")
        
        self.refresh_current_tab()
    
    def refresh_current_tab(self):
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'refresh_data'):
            current_widget.refresh_data()
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()