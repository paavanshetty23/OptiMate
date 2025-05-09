import os
import time
import datetime
import threading
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QProgressBar, QFileDialog, QCheckBox, 
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox, QDoubleSpinBox, 
    QComboBox, QFrame, QSplitter, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor

class FileCleanupTab(QWidget):
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.main_layout = QVBoxLayout(self)
        
        self.active_task = None
        self.stop_event = None
        
        self._setup_ui()
        
        self._connect_signals()
        
        self.refresh_data()
    
    def _setup_ui(self):
        actions_group = QGroupBox("File Cleanup Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.scan_temp_btn = QPushButton("Scan Temporary Files")
        self.scan_trash_btn = QPushButton("Scan Recycle Bin/Trash")
        self.scan_large_btn = QPushButton("Find Large Unused Files")
        self.empty_trash_btn = QPushButton("Empty Recycle Bin/Trash")
        
        scan_options_layout = QHBoxLayout()
        
        self.min_size_label = QLabel("Min Size (MB):")
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(1, 10000)
        self.min_size_spin.setValue(100)
        
        self.days_unused_label = QLabel("Days Unused:")
        self.days_unused_spin = QSpinBox()
        self.days_unused_spin.setRange(1, 3650)
        self.days_unused_spin.setValue(30)
        
        self.simulate_checkbox = QCheckBox("Simulation Mode (No Actual Deletion)")
        self.simulate_checkbox.setChecked(True)
        
        dir_select_layout = QHBoxLayout()
        self.dir_path_label = QLabel("Scan Directory:")
        self.dir_path = QLabel("No directory selected")
        self.browse_btn = QPushButton("Browse...")
        
        dir_select_layout.addWidget(self.dir_path_label)
        dir_select_layout.addWidget(self.dir_path, 1)
        dir_select_layout.addWidget(self.browse_btn)
        
        scan_options_layout.addWidget(self.min_size_label)
        scan_options_layout.addWidget(self.min_size_spin)
        scan_options_layout.addWidget(self.days_unused_label)
        scan_options_layout.addWidget(self.days_unused_spin)
        
        actions_layout.addLayout(dir_select_layout)
        actions_layout.addWidget(self.scan_temp_btn)
        actions_layout.addWidget(self.scan_trash_btn)
        actions_layout.addWidget(self.scan_large_btn)
        actions_layout.addLayout(scan_options_layout)
        actions_layout.addWidget(self.simulate_checkbox)
        actions_layout.addWidget(self.empty_trash_btn)
        
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["File Path", "Size", "Last Accessed", "Select"])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        table_actions_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_none_btn = QPushButton("Select None")
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setEnabled(False)
        
        table_actions_layout.addWidget(self.select_all_btn)
        table_actions_layout.addWidget(self.select_none_btn)
        table_actions_layout.addStretch()
        table_actions_layout.addWidget(self.delete_selected_btn)
        
        results_layout.addWidget(self.results_table)
        results_layout.addLayout(table_actions_layout)
        
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel("Ready")
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_operation)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label, 1)
        progress_layout.addWidget(self.cancel_btn)
        
        self.main_layout.addWidget(actions_group)
        self.main_layout.addWidget(results_group)
        self.main_layout.addLayout(progress_layout)
    
    def _connect_signals(self):
        self.scan_temp_btn.clicked.connect(self.on_scan_temp)
        self.scan_trash_btn.clicked.connect(self.on_scan_trash)
        self.scan_large_btn.clicked.connect(self.on_scan_large)
        self.empty_trash_btn.clicked.connect(self.on_empty_trash)
        self.browse_btn.clicked.connect(self.on_browse)
        
        self.select_all_btn.clicked.connect(self.on_select_all)
        self.select_none_btn.clicked.connect(self.on_select_none)
        self.delete_selected_btn.clicked.connect(self.on_delete_selected)

    def _cancel_operation(self):
        if self.active_task and self.stop_event:
            self.stop_event.set()
            self._set_status("Cancelling operation...")
            
            QTimer.singleShot(500, self._finish_cancellation)
    
    def _finish_cancellation(self):
        if self.active_task:
            self.controller.stop_background_task(self.active_task)
            self.active_task = None
            self.stop_event = None
            self._end_operation("Operation cancelled.")
        
    def refresh_data(self):
        pass
    
    def on_browse(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Scan", os.path.expanduser("~")
        )
        
        if directory:
            self.dir_path.setText(directory)
    
    def on_scan_temp(self):
        self._start_operation("Scanning temporary files...")
        
        self.controller.run_task_in_background(
            task_id="temp_files_scan",
            func=lambda stop_event: self.controller.get_temp_files(),
            callback=self._on_temp_files_loaded
        )
    
    def _on_temp_files_loaded(self, temp_files):
        self._display_files(temp_files)
        self._end_operation(f"Found {len(temp_files)} temporary files.")
    
    def on_scan_trash(self):
        self._start_operation("Scanning recycle bin/trash...")
        
        self.controller.run_task_in_background(
            task_id="trash_scan",
            func=lambda stop_event: self.controller.get_trash_items(),
            callback=self._on_trash_loaded
        )
    
    def _on_trash_loaded(self, trash_items):
        self._display_files(trash_items)
        self._end_operation(f"Found {len(trash_items)} items in recycle bin/trash.")
    
    def on_scan_large(self):
        directory = self.dir_path.text()
        
        if directory == "No directory selected" or not os.path.exists(directory):
            QMessageBox.warning(self, "Warning", "Please select a valid directory to scan.")
            return
        
        min_size_mb = self.min_size_spin.value()
        days_unused = self.days_unused_spin.value()
        
        if self.active_task:
            self._cancel_operation()
            QTimer.singleShot(500, lambda: self._start_large_file_scan(directory, min_size_mb, days_unused))
            return
        
        self._start_large_file_scan(directory, min_size_mb, days_unused)
    
    def _start_large_file_scan(self, directory, min_size_mb, days_unused):
        self.active_task = "scan_large_files"
        
        self.stop_event = threading.Event()
        
        self._start_operation(f"Scanning for files larger than {min_size_mb}MB "
                             f"unused for {days_unused} days...")
        
        self.cancel_btn.setVisible(True)
        
        self.controller.run_task_in_background(
            task_id="scan_large_files",
            func=lambda stop_event: self.controller.find_large_unused_files(
                [directory], min_size_mb, days_unused, stop_event
            ),
            callback=self._on_scan_large_complete
        )
    
    def _on_scan_large_complete(self, results):
        self.cancel_btn.setVisible(False)
        
        if not results:
            if self.stop_event and self.stop_event.is_set():
                self._end_operation("File scan cancelled.")
            else:
                self._end_operation("No large unused files found matching criteria.")
            self.active_task = None
            self.stop_event = None
            return
            
        self._display_files(results)
        
        if self.stop_event and self.stop_event.is_set():
            self._end_operation(f"Scan cancelled. Found {len(results)} large unused files so far.")
        else:
            self._end_operation(f"Found {len(results)} large unused files.")
            
        self.active_task = None
        self.stop_event = None
    
    def on_empty_trash(self):
        reply = QMessageBox.question(
            self, "Confirm Empty Trash/Recycle Bin",
            "Are you sure you want to empty the trash/recycle bin?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            simulate = self.simulate_checkbox.isChecked()
            self._start_operation("Emptying trash/recycle bin...")
            
            try:
                success, error = self.controller.empty_trash(simulate)
                
                if success:
                    if simulate:
                        self._end_operation("Simulation: Trash/recycle bin would be emptied.")
                    else:
                        self._end_operation("Trash/recycle bin emptied successfully.")
                else:
                    self._end_operation(f"Failed to empty trash/recycle bin: {error}")
                    QMessageBox.critical(self, "Error", f"Failed to empty trash/recycle bin: {error}")
            except Exception as e:
                self._end_operation(f"Error: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to empty trash/recycle bin: {str(e)}")
    
    def on_select_all(self):
        for row in range(self.results_table.rowCount()):
            checkbox_item = self.results_table.cellWidget(row, 3)
            if isinstance(checkbox_item, QCheckBox):
                checkbox_item.setChecked(True)
        
        self._update_delete_button()
    
    def on_select_none(self):
        for row in range(self.results_table.rowCount()):
            checkbox_item = self.results_table.cellWidget(row, 3)
            if isinstance(checkbox_item, QCheckBox):
                checkbox_item.setChecked(False)
        
        self._update_delete_button()
    
    def on_delete_selected(self):
        selected_paths = []
        
        for row in range(self.results_table.rowCount()):
            checkbox_item = self.results_table.cellWidget(row, 3)
            if isinstance(checkbox_item, QCheckBox) and checkbox_item.isChecked():
                file_path = self.results_table.item(row, 0).text()
                selected_paths.append(file_path)
        
        if not selected_paths:
            QMessageBox.information(self, "Information", "No files selected for deletion.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_paths)} files?\n"
            f"This operation {'' if not self.simulate_checkbox.isChecked() else 'would'} "
            f"permanently delete these files.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            simulate = self.simulate_checkbox.isChecked()
            self._start_operation(f"{'Simulating deletion' if simulate else 'Deleting'} of {len(selected_paths)} files...")
            
            try:
                success_count, failure_count, errors = self.controller.delete_files(selected_paths, simulate)
                
                message = []
                if simulate:
                    message.append(f"Simulation: {success_count} files would be deleted.")
                else:
                    message.append(f"Successfully deleted {success_count} files.")
                
                if failure_count > 0:
                    message.append(f"Failed to delete {failure_count} files.")
                    
                self._end_operation(". ".join(message))
                
                if not simulate and success_count > 0:
                    self._remove_deleted_files(selected_paths)
            except Exception as e:
                self._end_operation(f"Error: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to delete files: {str(e)}")
    
    def _display_files(self, files):
        self.results_table.setRowCount(0)
        
        if not files:
            return
        
        self.results_table.setRowCount(len(files))
        
        for row, file_info in enumerate(files):
            self.results_table.setItem(row, 0, QTableWidgetItem(file_info['path']))
            
            size_str = file_info.get('size_formatted', str(file_info.get('size', 0)))
            self.results_table.setItem(row, 1, QTableWidgetItem(size_str))
            
            last_access = file_info.get('last_access_formatted')
            if not last_access and 'last_access' in file_info:
                last_access = datetime.datetime.fromtimestamp(file_info['last_access']).strftime('%Y-%m-%d %H:%M:%S')
            self.results_table.setItem(row, 2, QTableWidgetItem(last_access or "Unknown"))
            
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_delete_button)
            self.results_table.setCellWidget(row, 3, checkbox)
        
        self.results_table.resizeColumnsToContents()
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    
    def _remove_deleted_files(self, deleted_paths):
        deleted_set = set(deleted_paths)
        rows_to_remove = []
        
        for row in range(self.results_table.rowCount()):
            file_path = self.results_table.item(row, 0).text()
            if file_path in deleted_set:
                rows_to_remove.append(row)
        
        for row in sorted(rows_to_remove, reverse=True):
            self.results_table.removeRow(row)
    
    def _update_delete_button(self):
        any_selected = False
        
        for row in range(self.results_table.rowCount()):
            checkbox_item = self.results_table.cellWidget(row, 3)
            if isinstance(checkbox_item, QCheckBox) and checkbox_item.isChecked():
                any_selected = True
                break
        
        self.delete_selected_btn.setEnabled(any_selected)
    
    def _start_operation(self, message):
        self.progress_bar.setVisible(True)
        self.status_label.setText(message)
        
        self.scan_temp_btn.setEnabled(False)
        self.scan_trash_btn.setEnabled(False)
        self.scan_large_btn.setEnabled(False)
        self.empty_trash_btn.setEnabled(False)
        self.delete_selected_btn.setEnabled(False)
        
        QApplication.processEvents()
    
    def _end_operation(self, message):
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        
        self.cancel_btn.setVisible(False)
        
        self.scan_temp_btn.setEnabled(True)
        self.scan_trash_btn.setEnabled(True)
        self.scan_large_btn.setEnabled(True)
        self.empty_trash_btn.setEnabled(True)
        
        self._update_delete_button()
        
        QApplication.processEvents()
        
    def _set_status(self, message):
        self.status_label.setText(message)
        QApplication.processEvents()