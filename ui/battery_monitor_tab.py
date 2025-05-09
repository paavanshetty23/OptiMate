import os
import time
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSpinBox, QComboBox, 
    QGroupBox, QScrollArea, QSplitter, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush, QPalette

class BatteryMonitorTab(QWidget):
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.main_layout = QVBoxLayout(self)
        
        self._setup_ui()
        
        self._connect_signals()
        
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)
        
        self.refresh_data()
    
    def _setup_ui(self):
        status_group = QGroupBox("Current Battery Status")
        status_layout = QGridLayout(status_group)
        
        self.battery_level_label = QLabel("Battery Level:")
        self.battery_level_value = QLabel("N/A")
        self.battery_level_value.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.battery_level_bar = QProgressBar()
        self.battery_level_bar.setRange(0, 100)
        self.battery_level_bar.setValue(0)
        self.battery_level_bar.setFormat("%v%")
        self.battery_level_bar.setTextVisible(True)
        
        self.charging_status_label = QLabel("Charging Status:")
        self.charging_status_value = QLabel("N/A")
        
        self.time_remaining_label = QLabel("Time Remaining:")
        self.time_remaining_value = QLabel("N/A")
        
        self.health_status_label = QLabel("Battery Health:")
        self.health_status_value = QLabel("N/A")
        
        status_layout.addWidget(self.battery_level_label, 0, 0)
        status_layout.addWidget(self.battery_level_value, 0, 1)
        
        status_layout.addWidget(self.battery_level_bar, 1, 0, 1, 2)
        
        status_layout.addWidget(self.charging_status_label, 2, 0)
        status_layout.addWidget(self.charging_status_value, 2, 1)
        
        status_layout.addWidget(self.time_remaining_label, 3, 0)
        status_layout.addWidget(self.time_remaining_value, 3, 1)
        
        status_layout.addWidget(self.health_status_label, 4, 0)
        status_layout.addWidget(self.health_status_value, 4, 1)
        
        details_group = QGroupBox("Battery Details")
        details_layout = QGridLayout(details_group)
        
        self.design_capacity_label = QLabel("Design Capacity:")
        self.design_capacity_value = QLabel("N/A")
        
        self.current_capacity_label = QLabel("Current Capacity:")
        self.current_capacity_value = QLabel("N/A")
        
        self.cycle_count_label = QLabel("Cycle Count:")
        self.cycle_count_value = QLabel("N/A")
        
        self.technology_label = QLabel("Technology:")
        self.technology_value = QLabel("N/A")
        
        self.manufacturer_label = QLabel("Manufacturer:")
        self.manufacturer_value = QLabel("N/A")
        
        details_layout.addWidget(self.design_capacity_label, 0, 0)
        details_layout.addWidget(self.design_capacity_value, 0, 1)
        
        details_layout.addWidget(self.current_capacity_label, 1, 0)
        details_layout.addWidget(self.current_capacity_value, 1, 1)
        
        details_layout.addWidget(self.cycle_count_label, 2, 0)
        details_layout.addWidget(self.cycle_count_value, 2, 1)
        
        details_layout.addWidget(self.technology_label, 3, 0)
        details_layout.addWidget(self.technology_value, 3, 1)
        
        details_layout.addWidget(self.manufacturer_label, 4, 0)
        details_layout.addWidget(self.manufacturer_value, 4, 1)
        
        usage_group = QGroupBox("Battery Usage")
        usage_layout = QVBoxLayout(usage_group)
        
        discharge_rate_layout = QHBoxLayout()
        self.discharge_rate_label = QLabel("Current Discharge Rate:")
        self.discharge_rate_value = QLabel("N/A")
        discharge_rate_layout.addWidget(self.discharge_rate_label)
        discharge_rate_layout.addWidget(self.discharge_rate_value)
        discharge_rate_layout.addStretch()
        
        estimated_remaining_layout = QHBoxLayout()
        self.estimated_remaining_label = QLabel("Estimated Time Remaining:")
        self.estimated_remaining_value = QLabel("N/A")
        estimated_remaining_layout.addWidget(self.estimated_remaining_label)
        estimated_remaining_layout.addWidget(self.estimated_remaining_value)
        estimated_remaining_layout.addStretch()
        
        self.monitor_usage_btn = QPushButton("Monitor Battery Usage (30 seconds)")
        
        usage_layout.addLayout(discharge_rate_layout)
        usage_layout.addLayout(estimated_remaining_layout)
        usage_layout.addWidget(self.monitor_usage_btn)
        
        recommendations_group = QGroupBox("Battery Optimization Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(2)
        self.recommendations_table.setHorizontalHeaderLabels(["Recommendation", "Description"])
        self.recommendations_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.recommendations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.refresh_recommendations_btn = QPushButton("Refresh Recommendations")
        
        recommendations_layout.addWidget(self.recommendations_table)
        recommendations_layout.addWidget(self.refresh_recommendations_btn)
        
        status_layout_bar = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        
        self.refresh_btn = QPushButton("Refresh All")
        
        status_layout_bar.addWidget(self.progress_bar)
        status_layout_bar.addWidget(self.status_label, 1)
        status_layout_bar.addWidget(self.refresh_btn)
        
        top_panel = QHBoxLayout()
        top_panel.addWidget(status_group, 1)
        top_panel.addWidget(details_group, 1)
        
        self.main_layout.addLayout(top_panel)
        self.main_layout.addWidget(usage_group)
        self.main_layout.addWidget(recommendations_group)
        self.main_layout.addLayout(status_layout_bar)
    
    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.monitor_usage_btn.clicked.connect(self.monitor_battery_usage)
        self.refresh_recommendations_btn.clicked.connect(self.refresh_recommendations)
    
    def refresh_data(self):
        self._set_status("Refreshing battery information...")
        self.progress_bar.setVisible(True)
        
        self.controller.run_task_in_background(
            task_id="battery_status",
            func=lambda stop_event: self.controller.get_battery_status(),
            callback=self._on_battery_status_loaded
        )
    
    def _on_battery_status_loaded(self, battery_status):
        self._display_battery_status(battery_status)
        
        self.controller.run_task_in_background(
            task_id="battery_health",
            func=lambda stop_event: self.controller.get_battery_health(),
            callback=self._on_battery_health_loaded
        )
    
    def _on_battery_health_loaded(self, battery_health):
        self._display_battery_health(battery_health)
        
        self.refresh_recommendations()
        self._set_status("Battery information updated.")
        self.progress_bar.setVisible(False)
    
    def monitor_battery_usage(self):
        self._set_status("Monitoring battery usage...")
        self.progress_bar.setVisible(True)
        self.monitor_usage_btn.setEnabled(False)
        
        self.controller.run_task_in_background(
            task_id="power_usage",
            func=lambda stop_event: self.controller.get_power_usage_stats(30),
            callback=self._on_power_usage_loaded
        )
    
    def _on_power_usage_loaded(self, power_stats):
        self._display_power_usage(power_stats)
        
        if not power_stats.get('available', False):
            self._set_status("Battery monitoring unavailable. Your device might be plugged in or has no battery.")
            QMessageBox.information(self, "Information", 
                                  "Battery monitoring unavailable. Your device might be plugged in or has no battery.")
        else:
            self._set_status("Battery usage monitoring complete.")
            
        self.progress_bar.setVisible(False)
        self.monitor_usage_btn.setEnabled(True)
    
    def refresh_recommendations(self):
        self.controller.run_task_in_background(
            task_id="battery_recommendations",
            func=lambda stop_event: self.controller.get_battery_optimization_recommendations(),
            callback=self._display_recommendations
        )
    
    def _display_battery_status(self, status):
        if not status.get('available', False):
            self.battery_level_value.setText("No Battery")
            self.battery_level_bar.setValue(0)
            self.charging_status_value.setText("No Battery")
            self.time_remaining_value.setText("N/A")
            return
        
        battery_percent = status.get('percent', 0)
        self.battery_level_value.setText(f"{battery_percent}%")
        self.battery_level_bar.setValue(int(battery_percent))
        
        if battery_percent <= 10:
            self.battery_level_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif battery_percent <= 25:
            self.battery_level_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.battery_level_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
        
        if status.get('power_plugged', False):
            charging_text = "Plugged In"
            if status.get('charging', False):
                charging_text += ", Charging"
            self.charging_status_value.setText(charging_text)
        else:
            self.charging_status_value.setText("Discharging")
        
        time_left = status.get('time_left_formatted', "Unknown")
        if status.get('power_plugged', False):
            self.time_remaining_value.setText("Plugged In")
        else:
            self.time_remaining_value.setText(time_left)
        
        if 'status_detail' in status:
            self.health_status_value.setText(status['status_detail'])
        
    def _display_battery_health(self, health):
        if not health:
            self.design_capacity_value.setText("Unknown")
            self.current_capacity_value.setText("Unknown")
            self.cycle_count_value.setText("Unknown")
            self.health_status_value.setText("Unknown")
            return
        
        if 'design_capacity' in health:
            self.design_capacity_value.setText(str(health['design_capacity']))
        
        if 'current_capacity' in health:
            self.current_capacity_value.setText(str(health['current_capacity']))
        
        if 'cycle_count' in health:
            self.cycle_count_value.setText(str(health['cycle_count']))
        
        if 'health_percentage' in health:
            health_percent = health['health_percentage']
            health_text = f"{health_percent}%"
            
            if health_percent < 60:
                self.health_status_value.setStyleSheet("color: red;")
            elif health_percent < 80:
                self.health_status_value.setStyleSheet("color: orange;")
            else:
                self.health_status_value.setStyleSheet("color: green;")
                
            self.health_status_value.setText(health_text)
        
        if 'manufacturer' in health:
            self.manufacturer_value.setText(health['manufacturer'])
            
        if 'technology' in health:
            self.technology_value.setText(health['technology'])
    
    def _display_power_usage(self, power_stats):
        if not power_stats.get('available', False):
            self.discharge_rate_value.setText("N/A")
            self.estimated_remaining_value.setText("N/A")
            return
        
        if 'discharge_rate_percent_per_hour' in power_stats:
            discharge_rate = power_stats['discharge_rate_percent_per_hour']
            self.discharge_rate_value.setText(f"{discharge_rate}% per hour")
        
        if 'estimated_hours_remaining' in power_stats:
            hours = power_stats['estimated_hours_remaining']
            hours_int = int(hours)
            minutes = int((hours - hours_int) * 60)
            self.estimated_remaining_value.setText(f"{hours_int} hours, {minutes} minutes")
    
    def _display_recommendations(self, recommendations):
        self.recommendations_table.setRowCount(0)
        
        if not recommendations:
            return
        
        self.recommendations_table.setRowCount(len(recommendations))
        
        for row, recommendation in enumerate(recommendations):
            title_item = QTableWidgetItem(recommendation['title'])
            title_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.recommendations_table.setItem(row, 0, title_item)
            
            description_item = QTableWidgetItem(recommendation['description'])
            self.recommendations_table.setItem(row, 1, description_item)
        
        self.recommendations_table.resizeColumnsToContents()
        self.recommendations_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    
    def _set_status(self, message):
        self.status_label.setText(message)