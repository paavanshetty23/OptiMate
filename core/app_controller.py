import os
import sys
import time
import threading
from typing import List, Dict, Any, Callable, Optional

from PyQt5.QtCore import QObject, pyqtSignal, QThread

from platform.platform_detector import PlatformDetector
from core.file_cleanup import FileCleanup
from core.process_manager import ProcessManager
from core.battery_monitor import BatteryMonitor

class TaskWorker(QObject):
    taskCompleted = pyqtSignal(object)
    taskFailed = pyqtSignal(str)
    
    def __init__(self, func, **kwargs):
        super().__init__()
        self.func = func
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(**self.kwargs)
            self.taskCompleted.emit(result)
        except Exception as e:
            self.taskFailed.emit(str(e))

class AppController:
    
    def __init__(self):
        self.platform_detector = PlatformDetector()
        self.file_cleanup = FileCleanup()
        self.process_manager = ProcessManager()
        self.battery_monitor = BatteryMonitor()
        
        self.platform = self.platform_detector.get_platform()
        self.is_admin = self.platform_detector.is_admin()
        
        self.tasks = {}
        self.task_results = {}
        self._stop_events = {}
        self.threads = {}
        
    def get_temp_files(self):
        return self.file_cleanup.get_temp_files()
    
    def get_trash_items(self):
        return self.file_cleanup.get_trash_items()
    
    def find_large_unused_files(self, search_paths: List[str], min_size_mb: float = 100, days_unused: int = 30):
        return self.file_cleanup.find_large_unused_files(search_paths, min_size_mb, days_unused)
    
    def delete_files(self, file_paths: List[str], simulate: bool = False):
        return self.file_cleanup.delete_files(file_paths, simulate)
    
    def empty_trash(self, simulate: bool = False):
        return self.file_cleanup.empty_trash(simulate)
    
    def get_running_processes(self):
        return self.process_manager.get_running_processes()
    
    def get_high_resource_processes(self, cpu_threshold: float = 5.0, memory_threshold_mb: float = 500):
        return self.process_manager.get_high_resource_processes(cpu_threshold, memory_threshold_mb)
    
    def terminate_process(self, pid: int, force: bool = False):
        return self.process_manager.terminate_process(pid, force)
    
    def get_startup_items(self):
        return self.process_manager.get_startup_items()
    
    def disable_startup_item(self, item_name: str, item_location: str):
        return self.process_manager.disable_startup_item(item_name, item_location)
    
    def get_battery_status(self):
        return self.battery_monitor.get_battery_status()
    
    def get_battery_health(self):
        return self.battery_monitor.get_battery_health()
    
    def get_power_usage_stats(self, duration_seconds: int = 60):
        return self.battery_monitor.get_power_usage_stats(duration_seconds)
    
    def get_battery_optimization_recommendations(self):
        return self.battery_monitor.get_optimization_recommendations()
    
    def run_task_in_background(self, task_id: str, func: Callable, callback: Optional[Callable] = None, **kwargs):
        self.stop_background_task(task_id)
        
        thread = QThread()
        self.threads[task_id] = thread
        
        if 'stop_event' in func.__code__.co_varnames:
            stop_event = threading.Event()
            self._stop_events[task_id] = stop_event
            kwargs['stop_event'] = stop_event
        
        worker = TaskWorker(func, **kwargs)
        worker.moveToThread(thread)
        
        thread.started.connect(worker.run)
        worker.taskCompleted.connect(lambda result: self._on_task_completed(task_id, result, callback))
        worker.taskFailed.connect(lambda error: self._on_task_failed(task_id, error, callback))
        worker.taskCompleted.connect(thread.quit)
        worker.taskFailed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._cleanup_thread(task_id))
        
        self.tasks[task_id] = worker
        
        thread.start()
        
        return True
    
    def _on_task_completed(self, task_id: str, result, callback: Optional[Callable]):
        self.task_results[task_id] = {'success': True, 'result': result}
        if callback:
            callback(result)
    
    def _on_task_failed(self, task_id: str, error: str, callback: Optional[Callable]):
        self.task_results[task_id] = {'success': False, 'error': error}
        if callback:
            callback(None)
    
    def _cleanup_thread(self, task_id: str):
        if task_id in self.threads:
            del self.threads[task_id]
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def stop_background_task(self, task_id: str):
        if task_id in self._stop_events:
            self._stop_events[task_id].set()
        
        if task_id in self.threads:
            thread = self.threads[task_id]
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
                if thread.isRunning():
                    thread.terminate()
            return True
        return False
    
    def get_task_result(self, task_id: str):
        return self.task_results.get(task_id)
    
    def is_task_running(self, task_id: str):
        return task_id in self.threads and self.threads[task_id].isRunning()
    
    def scan_for_large_files_in_background(self, search_paths: List[str], min_size_mb: float = 100, 
                                         days_unused: int = 30, callback: Optional[Callable] = None):
        def task(stop_event):
            results = []
            for path in search_paths:
                if stop_event.is_set():
                    break
                try:
                    for root, _, files in os.walk(path):
                        if stop_event.is_set():
                            break
                        for file in files:
                            if stop_event.is_set():
                                break
                            try:
                                file_path = os.path.join(root, file)
                                if os.path.isfile(file_path):
                                    file_stats = os.stat(file_path)
                                    file_size = file_stats.st_size
                                    last_access = file_stats.st_atime
                                    
                                    cutoff_time = time.time() - (days_unused * 24 * 60 * 60)
                                    if (file_size >= min_size_mb * 1024 * 1024 and 
                                        last_access <= cutoff_time):
                                        
                                        results.append({
                                            'path': file_path,
                                            'size': file_size,
                                            'size_formatted': self.file_cleanup._format_size(file_size),
                                            'last_access': last_access,
                                            'days_unused': int((time.time() - last_access) / (24 * 60 * 60))
                                        })
                            except (PermissionError, FileNotFoundError, OSError):
                                continue
                except Exception as e:
                    print(f"Error scanning {path}: {e}")
            
            results.sort(key=lambda x: x['size'], reverse=True)
            return results
        
        return self.run_task_in_background(
            task_id="scan_large_files",
            func=task,
            callback=callback
        )