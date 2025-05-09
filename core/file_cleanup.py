import os
import time
import shutil
import datetime
import threading
from typing import List, Dict, Tuple, Optional, Callable
from platform.platform_detector import PlatformDetector

class FileCleanup:
    
    def __init__(self):
        self.platform = PlatformDetector.get_platform()
        self.temp_dir = PlatformDetector.get_temp_directory()
        self.trash_dir = PlatformDetector.get_trash_directory()
        
    def get_temp_files(self) -> List[Dict[str, any]]:
        temp_files = []
        
        try:
            if os.path.exists(self.temp_dir):
                for root, _, files in os.walk(self.temp_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            if os.path.isfile(file_path):
                                file_size = os.path.getsize(file_path)
                                last_access = os.path.getatime(file_path)
                                
                                temp_files.append({
                                    'path': file_path,
                                    'size': file_size,
                                    'size_formatted': self._format_size(file_size),
                                    'last_access': last_access,
                                    'last_access_formatted': datetime.datetime.fromtimestamp(last_access).strftime('%Y-%m-%d %H:%M:%S')
                                })
                        except (PermissionError, FileNotFoundError, OSError) as e:
                            continue
        except Exception as e:
            print(f"Error accessing temporary directory: {e}")
            
        return temp_files
    
    def get_trash_items(self) -> List[Dict[str, any]]:
        trash_items = []
        
        try:
            if self.platform == PlatformDetector.WINDOWS:
                if os.path.exists(self.trash_dir):
                    for root, _, files in os.walk(self.trash_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if os.path.isfile(file_path):
                                    file_size = os.path.getsize(file_path)
                                    last_access = os.path.getatime(file_path)
                                    
                                    trash_items.append({
                                        'path': file_path,
                                        'size': file_size,
                                        'size_formatted': self._format_size(file_size),
                                        'last_access': last_access,
                                        'last_access_formatted': datetime.datetime.fromtimestamp(last_access).strftime('%Y-%m-%d %H:%M:%S')
                                    })
                            except (PermissionError, FileNotFoundError, OSError):
                                continue
            elif self.platform == PlatformDetector.LINUX:
                trash_files = os.path.join(self.trash_dir, "files")
                trash_info = os.path.join(self.trash_dir, "info")
                
                if os.path.exists(trash_files):
                    for root, _, files in os.walk(trash_files):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                if os.path.isfile(file_path):
                                    file_size = os.path.getsize(file_path)
                                    last_access = os.path.getatime(file_path)
                                    
                                    trash_items.append({
                                        'path': file_path,
                                        'size': file_size,
                                        'size_formatted': self._format_size(file_size),
                                        'last_access': last_access,
                                        'last_access_formatted': datetime.datetime.fromtimestamp(last_access).strftime('%Y-%m-%d %H:%M:%S')
                                    })
                            except (PermissionError, FileNotFoundError, OSError):
                                continue
        except Exception as e:
            print(f"Error accessing trash directory: {e}")
            
        return trash_items

    def find_large_unused_files(self, search_paths: List[str], min_size_mb: float = 100,
                              days_unused: int = 30, stop_event=None) -> List[Dict[str, any]]:
        large_unused_files = []
        min_size_bytes = min_size_mb * 1024 * 1024
        cutoff_time = time.time() - (days_unused * 24 * 60 * 60)
        
        batch_size = 1000
        processed_files = 0
        total_files_found = 0
        
        skip_dirs = self._get_skip_directories()
        
        for search_path in search_paths:
            if not os.path.exists(search_path) or not os.path.isdir(search_path):
                continue
                
            try:
                for root, dirs, files in os.walk(search_path, topdown=True):
                    if stop_event and stop_event.is_set():
                        return large_unused_files
                    
                    dirs[:] = [d for d in dirs if os.path.join(root, d) not in skip_dirs and 
                              not self._should_skip_directory(d)]
                    
                    for file in files:
                        processed_files += 1
                        
                        if stop_event and stop_event.is_set():
                            return large_unused_files
                            
                        if processed_files % 100 == 0:
                            time.sleep(0.001)
                            
                        try:
                            file_path = os.path.join(root, file)
                            
                            if not os.path.isfile(file_path):
                                continue
                                
                            try:
                                file_stats = os.stat(file_path)
                                file_size = file_stats.st_size
                                
                                if file_size >= min_size_bytes:
                                    last_access = file_stats.st_atime
                                    
                                    if last_access <= cutoff_time:
                                        large_unused_files.append({
                                            'path': file_path,
                                            'size': file_size,
                                            'size_formatted': self._format_size(file_size),
                                            'last_access': last_access,
                                            'last_access_formatted': datetime.datetime.fromtimestamp(last_access).strftime('%Y-%m-%d %H:%M:%S'),
                                            'days_unused': int((time.time() - last_access) / (24 * 60 * 60))
                                        })
                                        total_files_found += 1
                                        
                                        if len(large_unused_files) >= batch_size:
                                            large_unused_files.sort(key=lambda x: x['size'], reverse=True)
                                            if len(large_unused_files) > 1000:
                                                large_unused_files = large_unused_files[:1000]
                            except (PermissionError, FileNotFoundError, OSError):
                                continue
                                
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
                            
            except (PermissionError, OSError):
                continue
        
        large_unused_files.sort(key=lambda x: x['size'], reverse=True)
        return large_unused_files

    def _get_skip_directories(self) -> List[str]:
        skip_dirs = []
        
        if self.platform == PlatformDetector.WINDOWS:
            skip_dirs = [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows')),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SysWOW64'),
                self.temp_dir,
                self.trash_dir
            ]
            appdata = os.environ.get('APPDATA')
            if appdata:
                skip_dirs.append(appdata)
                
        elif self.platform in [PlatformDetector.LINUX, PlatformDetector.MAC]:
            skip_dirs = [
                '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/local/bin',
                '/lib', '/usr/lib', '/etc', '/var/lib', '/proc', '/dev',
                self.temp_dir, self.trash_dir
            ]
            if self.platform == PlatformDetector.MAC:
                skip_dirs.extend(['/System', '/Library/Caches'])
                
            home = os.path.expanduser("~")
            skip_dirs.append(os.path.join(home, '.cache'))
            
        return skip_dirs
        
    def _should_skip_directory(self, dirname: str) -> bool:
        skip_patterns = [
            '.', '__pycache__', 'node_modules', '.git', '.svn', 
            'cache', 'tmp', 'temp', 'logs'
        ]
        
        dirname_lower = dirname.lower()
        return (dirname.startswith('.') or 
                any(pattern in dirname_lower for pattern in skip_patterns))
                
    def delete_files(self, file_paths: List[str], simulate: bool = False) -> Tuple[int, int, List[str]]:
        success_count = 0
        failure_count = 0
        errors = []
        
        for file_path in file_paths:
            try:
                if self._is_system_file(file_path):
                    errors.append(f"Skipped system file: {file_path}")
                    failure_count += 1
                    continue
                
                if not simulate:
                    os.remove(file_path)
                
                success_count += 1
            except (PermissionError, FileNotFoundError, OSError) as e:
                errors.append(f"Failed to delete {file_path}: {str(e)}")
                failure_count += 1
                
        return success_count, failure_count, errors
    
    def empty_trash(self, simulate: bool = False) -> Tuple[bool, Optional[str]]:
        try:
            if simulate:
                return True, None
            
            if self.platform == PlatformDetector.WINDOWS:
                import winshell
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            elif self.platform in [PlatformDetector.LINUX, PlatformDetector.MAC]:
                if os.path.exists(self.trash_dir):
                    for item in os.listdir(self.trash_dir):
                        item_path = os.path.join(self.trash_dir, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def _is_system_file(self, file_path: str) -> bool:
        system_dirs = []
        
        if self.platform == PlatformDetector.WINDOWS:
            system_dirs = [
                os.environ.get('WINDIR', 'C:\\Windows'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SysWOW64'),
                os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'))
            ]
        elif self.platform in [PlatformDetector.LINUX, PlatformDetector.MAC]:
            system_dirs = [
                '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/usr/local/bin',
                '/lib', '/usr/lib', '/etc', '/var/lib', '/opt'
            ]
            if self.platform == PlatformDetector.MAC:
                system_dirs.extend(['/System', '/Library'])
        
        for system_dir in system_dirs:
            if system_dir and os.path.commonpath([system_dir]) == os.path.commonpath([system_dir, file_path]):
                return True
        
        return False