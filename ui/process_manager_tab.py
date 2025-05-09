import os
import time
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox, QDoubleSpinBox, 
    QGroupBox, QScrollArea, QSplitter, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush

class ProcessManagerTab(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.main_layout = QVBoxLayout(self)
        self.active_task = None
        
        self._setup_ui()
        self._connect_signals()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(5000)
        
        QTimer.singleShot(500, self.refresh_data)
    
    def auto_refresh(self):
        if self.active_task or not self.isVisible():
            return
        
        self.refresh_data()
    
    def _setup_ui(self):
        controls_group = QGroupBox("Process Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        upper_controls = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Now")
        self.high_cpu_btn = QPushButton("Show High CPU Usage")
        self.high_mem_btn = QPushButton("Show High Memory Usage")
        self.show_all_btn = QPushButton("Show All Processes")
        
        upper_controls.addWidget(self.refresh_btn)
        upper_controls.addWidget(self.high_cpu_btn)
        upper_controls.addWidget(self.high_mem_btn)
        upper_controls.addWidget(self.show_all_btn)
        
        filter_options = QHBoxLayout()
        
        self.cpu_threshold_label = QLabel("CPU Threshold (%):")
        self.cpu_threshold_spin = QDoubleSpinBox()
        self.cpu_threshold_spin.setRange(0.1, 100.0)
        self.cpu_threshold_spin.setValue(5.0)
        self.cpu_threshold_spin.setSingleStep(0.1)
        
        self.mem_threshold_label = QLabel("Memory Threshold (MB):")
        self.mem_threshold_spin = QSpinBox()
        self.mem_threshold_spin.setRange(10, 10000)
        self.mem_threshold_spin.setValue(500)
        
        filter_options.addWidget(self.cpu_threshold_label)
        filter_options.addWidget(self.cpu_threshold_spin)
        filter_options.addWidget(self.mem_threshold_label)
        filter_options.addWidget(self.mem_threshold_spin)
        filter_options.addStretch()
        
        controls_layout.addLayout(upper_controls)
        controls_layout.addLayout(filter_options)
        
        table_group = QGroupBox("Running Processes")
        table_layout = QVBoxLayout(table_group)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory (MB)", "Status", "User", "Path"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.process_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.process_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        table_actions = QHBoxLayout()
        self.terminate_btn = QPushButton("Terminate Process")
        self.force_terminate_btn = QPushButton("Force Terminate")
        self.terminate_btn.setEnabled(False)
        self.force_terminate_btn.setEnabled(False)
        
        table_actions.addWidget(self.terminate_btn)
        table_actions.addWidget(self.force_terminate_btn)
        table_actions.addStretch()
        
        table_layout.addWidget(self.process_table)
        table_layout.addLayout(table_actions)
        
        startup_group = QGroupBox("Startup Applications")
        startup_layout = QVBoxLayout(startup_group)
        
        self.startup_table = QTableWidget()
        self.startup_table.setColumnCount(4)
        self.startup_table.setHorizontalHeaderLabels([
            "Name", "Status", "Location", "Command"
        ])
        self.startup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.startup_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.startup_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        startup_actions = QHBoxLayout()
        self.refresh_startup_btn = QPushButton("Refresh Startup Items")
        self.disable_startup_btn = QPushButton("Disable Selected Item")
        self.disable_startup_btn.setEnabled(False)
        
        startup_actions.addWidget(self.refresh_startup_btn)
        startup_actions.addWidget(self.disable_startup_btn)
        startup_actions.addStretch()
        
        startup_layout.addWidget(self.startup_table)
        startup_layout.addLayout(startup_actions)
        
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_label, 1)
        
        splitter = QSplitter(Qt.Vertical)
        
        processes_widget = QWidget()
        processes_layout = QVBoxLayout(processes_widget)
        processes_layout.addWidget(controls_group)
        processes_layout.addWidget(table_group)
        
        startup_widget = QWidget()
        startup_layout_main = QVBoxLayout(startup_widget)
        startup_layout_main.addWidget(startup_group)
        
        splitter.addWidget(processes_widget)
        splitter.addWidget(startup_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        self.main_layout.addWidget(splitter)
        self.main_layout.addLayout(status_layout)
    
    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.high_cpu_btn.clicked.connect(self.show_high_cpu)
        self.high_mem_btn.clicked.connect(self.show_high_memory)
        self.show_all_btn.clicked.connect(self.show_all_processes)
        
        self.process_table.itemSelectionChanged.connect(self.process_selection_changed)
        
        self.terminate_btn.clicked.connect(lambda: self.terminate_process(False))
        self.force_terminate_btn.clicked.connect(lambda: self.terminate_process(True))
        
        self.refresh_startup_btn.clicked.connect(self.refresh_startup_items)
        self.startup_table.itemSelectionChanged.connect(self.startup_selection_changed)
        self.disable_startup_btn.clicked.connect(self.disable_startup_item)
    
    def refresh_data(self):
        if self.active_task:
            return
        
        self.active_task = "refresh_processes"
        self._set_status("Refreshing process list...")
        self.progress_bar.setVisible(True)
        
        self._set_buttons_enabled(False)
        
        QApplication.processEvents()
        
        self.controller.run_task_in_background(
            task_id="refresh_processes",
            func=lambda stop_event: self.controller.get_running_processes(),
            callback=self._on_processes_loaded
        )
    
    def _on_processes_loaded(self, processes):
        if processes is None:
            self._set_status("Error loading process data.")
        else:
            self._display_processes(processes)
            self._set_status(f"Found {len(processes)} processes.")
        
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.active_task = None
    
    def show_high_cpu(self):
        if self.active_task:
            return
            
        self.active_task = "high_cpu_processes"
        cpu_threshold = self.cpu_threshold_spin.value()
        
        self._set_status(f"Finding processes using more than {cpu_threshold}% CPU...")
        self.progress_bar.setVisible(True)
        
        self._set_buttons_enabled(False)
        
        QApplication.processEvents()
        
        self.controller.run_task_in_background(
            task_id="high_cpu_processes",
            func=lambda stop_event: self.controller.get_high_resource_processes(
                cpu_threshold=cpu_threshold, memory_threshold_mb=0
            ),
            callback=lambda processes: self._on_high_cpu_loaded(processes, cpu_threshold)
        )
    
    def _on_high_cpu_loaded(self, processes, threshold):
        if processes is None:
            self._set_status("Error loading high CPU processes.")
        else:
            self._display_processes(processes)
            self._set_status(f"Found {len(processes)} processes using more than {threshold}% CPU.")
        
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.active_task = None
    
    def show_high_memory(self):
        if self.active_task:
            return
            
        self.active_task = "high_memory_processes"
        memory_threshold = self.mem_threshold_spin.value()
        
        self._set_status(f"Finding processes using more than {memory_threshold} MB memory...")
        self.progress_bar.setVisible(True)
        
        self._set_buttons_enabled(False)
        
        QApplication.processEvents()
        
        self.controller.run_task_in_background(
            task_id="high_memory_processes",
            func=lambda stop_event: self.controller.get_high_resource_processes(
                cpu_threshold=0, memory_threshold_mb=memory_threshold
            ),
            callback=lambda processes: self._on_high_memory_loaded(processes, memory_threshold)
        )
    
    def _on_high_memory_loaded(self, processes, threshold):
        if processes is None:
            self._set_status("Error loading high memory processes.")
        else:
            self._display_processes(processes)
            self._set_status(f"Found {len(processes)} processes using more than {threshold} MB memory.")
        
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.active_task = None
        
    def show_all_processes(self):
        if self.active_task:
            return
            
        self.active_task = "all_processes"
        self._set_status("Loading all processes...")
        self.progress_bar.setVisible(True)
        
        self._set_buttons_enabled(False)
        
        QApplication.processEvents()
        
        self.controller.run_task_in_background(
            task_id="all_processes",
            func=lambda stop_event: self.controller.get_running_processes(),
            callback=self._on_all_processes_loaded
        )
    
    def _on_all_processes_loaded(self, processes):
        if processes is None:
            self._set_status("Error loading process data.")
        else:
            self._display_processes(processes)
            self._set_status(f"Found {len(processes)} processes.")
        
        self._set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        self.active_task = None
    
    def refresh_startup_items(self):
        self._set_status("Loading startup items...")
        self.progress_bar.setVisible(True)
        
        self.controller.run_task_in_background(
            task_id="refresh_startup",
            func=lambda stop_event: self.controller.get_startup_items(),
            callback=self._on_startup_items_loaded
        )
    
    def _on_startup_items_loaded(self, startup_items):
        self._display_startup_items(startup_items)
        self._set_status(f"Found {len(startup_items)} startup items.")
        self.progress_bar.setVisible(False)
    
    def process_selection_changed(self):
        selected_items = self.process_table.selectedItems()
        
        if selected_items and len(selected_items) > 0:
            row = selected_items[0].row()
            pid_item = self.process_table.item(row, 0)
            name_item = self.process_table.item(row, 1)
            
            if pid_item and name_item:
                pid = int(pid_item.text())
                name = name_item.text()
                
                is_system = False
                for col in range(self.process_table.columnCount()):
                    item = self.process_table.item(row, col)
                    if item and item.background().color() == QColor(255, 200, 200):
                        is_system = True
                        break
                
                self.terminate_btn.setEnabled(not is_system)
                self.force_terminate_btn.setEnabled(not is_system)
                
                if is_system:
                    self._set_status(f"Process {name} (PID: {pid}) is a system process and cannot be terminated.")
                else:
                    self._set_status(f"Selected process: {name} (PID: {pid})")
            else:
                self.terminate_btn.setEnabled(False)
                self.force_terminate_btn.setEnabled(False)
        else:
            self.terminate_btn.setEnabled(False)
            self.force_terminate_btn.setEnabled(False)
    
    def terminate_process(self, force: bool = False):
        selected_items = self.process_table.selectedItems()
        
        if not selected_items or len(selected_items) == 0:
            return
        
        row = selected_items[0].row()
        pid_item = self.process_table.item(row, 0)
        name_item = self.process_table.item(row, 1)
        
        if not pid_item or not name_item:
            return
        
        pid = int(pid_item.text())
        name = name_item.text()
        
        message = f"Are you sure you want to {'' if not force else 'force '}terminate process {name} (PID: {pid})?"
        if force:
            message += "\n\nWarning: Force termination may cause data loss if the process is writing to disk."
        
        reply = QMessageBox.question(
            self, f"Confirm {'Force ' if force else ''}Termination",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self._set_status(f"{'Force t' if force else 'T'}erminating process {name} (PID: {pid})...")
        self.progress_bar.setVisible(True)
        
        try:
            success, error = self.controller.terminate_process(pid, force)
            
            if success:
                self._set_status(f"Successfully {'force ' if force else ''}terminated process {name} (PID: {pid}).")
                self.refresh_data()
            else:
                self._set_status(f"Failed to terminate process: {error}")
                QMessageBox.critical(self, "Error", f"Failed to terminate process: {error}")
        except Exception as e:
            self._set_status(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to terminate process: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def startup_selection_changed(self):
        selected_items = self.startup_table.selectedItems()
        
        if selected_items and len(selected_items) > 0:
            row = selected_items[0].row()
            name_item = self.startup_table.item(row, 0)
            status_item = self.startup_table.item(row, 1)
            
            if name_item and status_item:
                name = name_item.text()
                status = status_item.text()
                
                self.disable_startup_btn.setEnabled(status.lower() == "enabled")
                
                self._set_status(f"Selected startup item: {name} ({status})")
            else:
                self.disable_startup_btn.setEnabled(False)
        else:
            self.disable_startup_btn.setEnabled(False)
    
    def disable_startup_item(self):
        selected_items = self.startup_table.selectedItems()
        
        if not selected_items or len(selected_items) == 0:
            return
        
        row = selected_items[0].row()
        name_item = self.startup_table.item(row, 0)
        location_item = self.startup_table.item(row, 2)
        
        if not name_item or not location_item:
            return
        
        name = name_item.text()
        location = location_item.text()
        
        reply = QMessageBox.question(
            self, "Confirm Disable Startup Item",
            f"Are you sure you want to disable startup item '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self._set_status(f"Disabling startup item '{name}'...")
        self.progress_bar.setVisible(True)
        
        try:
            success, error = self.controller.disable_startup_item(name, location)
            
            if success:
                self._set_status(f"Successfully disabled startup item '{name}'.")
                status_item = self.startup_table.item(row, 1)
                if status_item:
                    status_item.setText("Disabled")
                    status_item.setForeground(QBrush(QColor(150, 150, 150)))
                    
                self.disable_startup_btn.setEnabled(False)
            else:
                self._set_status(f"Failed to disable startup item: {error}")
                QMessageBox.critical(self, "Error", f"Failed to disable startup item: {error}")
        except Exception as e:
            self._set_status(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to disable startup item: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def _display_processes(self, processes):
        self.process_table.setRowCount(0)
        
        if not processes:
            return
        
        self.process_table.setUpdatesEnabled(False)
        self.process_table.setRowCount(len(processes))
        
        for row, process in enumerate(processes):
            pid_item = QTableWidgetItem(str(process['pid']))
            self.process_table.setItem(row, 0, pid_item)
            
            name_item = QTableWidgetItem(process['name'])
            self.process_table.setItem(row, 1, name_item)
            
            cpu_item = QTableWidgetItem(f"{process['cpu_percent']:.1f}")
            self.process_table.setItem(row, 2, cpu_item)
            
            memory_item = QTableWidgetItem(f"{process['memory_mb']:.1f}")
            self.process_table.setItem(row, 3, memory_item)
            
            status_item = QTableWidgetItem(process['status'])
            self.process_table.setItem(row, 4, status_item)
            
            user_item = QTableWidgetItem(process['username'])
            self.process_table.setItem(row, 5, user_item)
            
            path_item = QTableWidgetItem(process.get('exe', 'Unknown'))
            self.process_table.setItem(row, 6, path_item)
            
            if process.get('is_system', False):
                for col in range(self.process_table.columnCount()):
                    item = self.process_table.item(row, col)
                    if item:
                        item.setBackground(QBrush(QColor(255, 200, 200)))
            
            if process['cpu_percent'] > 20:
                cpu_item.setForeground(QBrush(QColor(200, 0, 0)))
            elif process['cpu_percent'] > 10:
                cpu_item.setForeground(QBrush(QColor(200, 100, 0)))
                
            if process['memory_mb'] > 1000:
                memory_item.setForeground(QBrush(QColor(200, 0, 0)))
            elif process['memory_mb'] > 500:
                memory_item.setForeground(QBrush(QColor(200, 100, 0)))
        
        self.process_table.setUpdatesEnabled(True)
        self.process_table.resizeColumnsToContents()
        self.process_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        
        QApplication.processEvents()
    
    def _display_startup_items(self, startup_items):
        self.startup_table.setRowCount(0)
        
        if not startup_items:
            return
        
        self.startup_table.setRowCount(len(startup_items))
        
        for row, item in enumerate(startup_items):
            name_item = QTableWidgetItem(item['name'])
            self.startup_table.setItem(row, 0, name_item)
            
            status_text = "Enabled" if item.get('enabled', True) else "Disabled"
            status_item = QTableWidgetItem(status_text)
            
            if not item.get('enabled', True):
                status_item.setForeground(QBrush(QColor(150, 150, 150)))
            else:
                status_item.setForeground(QBrush(QColor(0, 150, 0)))
                
            self.startup_table.setItem(row, 1, status_item)
            
            location_item = QTableWidgetItem(item.get('location', 'Unknown'))
            self.startup_table.setItem(row, 2, location_item)
            
            command_item = QTableWidgetItem(item.get('command', ''))
            self.startup_table.setItem(row, 3, command_item)
        
        self.startup_table.resizeColumnsToContents()
        self.startup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
    
    def _set_buttons_enabled(self, enabled):
        self.refresh_btn.setEnabled(enabled)
        self.high_cpu_btn.setEnabled(enabled)
        self.high_mem_btn.setEnabled(enabled)
        self.show_all_btn.setEnabled(enabled)
        
        if enabled and self.process_table.selectedItems():
            self.process_selection_changed()
        else:
            self.terminate_btn.setEnabled(False)
            self.force_terminate_btn.setEnabled(False)
            
        self.refresh_startup_btn.setEnabled(enabled)
        if enabled and self.startup_table.selectedItems():
            self.startup_selection_changed()
        else:
            self.disable_startup_btn.setEnabled(False)
    
    def _set_status(self, message):
        self.status_label.setText(message)