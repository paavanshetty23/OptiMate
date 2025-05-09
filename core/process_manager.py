import os
import time
import signal
import subprocess
from typing import List, Dict, Optional, Tuple
import psutil
from platform.platform_detector import PlatformDetector

class ProcessManager:
    def __init__(self):
        self.platform = PlatformDetector.get_platform()
        self.system_processes = self._get_system_process_list()
    
    def get_running_processes(self) -> List[Dict[str, any]]:
        processes = []
        
        process_list = list(psutil.process_iter(['pid', 'name', 'username', 'status']))
        
        MAX_PROCESSES = 100
        if len(process_list) > MAX_PROCESSES:
            process_list = process_list[:MAX_PROCESSES]
        
        for proc in process_list:
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                username = proc.info['username'] if proc.info['username'] else "Unknown"
                status = proc.info['status'] if proc.info['status'] else "Unknown"
                
                try:
                    cpu_percent = proc.cpu_percent(interval=None)
                except:
                    cpu_percent = 0
                
                try:
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                except:
                    memory_mb = 0
                
                is_system = self._is_system_process(pid, name)
                exe = ""
                cmdline = ""
                
                if not is_system:
                    try:
                        exe = proc.exe() if hasattr(proc, 'exe') else ""
                    except:
                        exe = "Access Denied"
                    
                    try:
                        cmdline = " ".join(proc.cmdline()) if hasattr(proc, 'cmdline') else ""
                    except:
                        cmdline = "Access Denied"
                
                processes.append({
                    'pid': pid,
                    'name': name,
                    'username': username,
                    'status': status,
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'memory_formatted': f"{memory_mb:.2f} MB",
                    'cmdline': cmdline,
                    'exe': exe,
                    'is_system': is_system
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes
    
    def get_high_resource_processes(self, cpu_threshold: float = 5.0, memory_threshold_mb: float = 500) -> List[Dict[str, any]]:
        high_resource_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                try:
                    cpu_percent = proc.cpu_percent(interval=None)
                    
                    if cpu_percent >= cpu_threshold:
                        memory_mb = proc.memory_info().rss / (1024 * 1024)
                        
                        if cpu_percent >= cpu_threshold or memory_mb >= memory_threshold_mb:
                            is_system = self._is_system_process(pid, name)
                            
                            high_resource_processes.append({
                                'pid': pid,
                                'name': name,
                                'username': proc.info['username'] if proc.info['username'] else "Unknown",
                                'status': proc.info['status'] if proc.info['status'] else "Unknown",
                                'cpu_percent': cpu_percent,
                                'memory_mb': memory_mb,
                                'memory_formatted': f"{memory_mb:.2f} MB",
                                'is_system': is_system
                            })
                    else:
                        memory_mb = proc.memory_info().rss / (1024 * 1024)
                        if memory_mb >= memory_threshold_mb:
                            is_system = self._is_system_process(pid, name)
                            
                            high_resource_processes.append({
                                'pid': pid,
                                'name': name,
                                'username': proc.info['username'] if proc.info['username'] else "Unknown",
                                'status': proc.info['status'] if proc.info['status'] else "Unknown",
                                'cpu_percent': cpu_percent,
                                'memory_mb': memory_mb,
                                'memory_formatted': f"{memory_mb:.2f} MB",
                                'is_system': is_system
                            })
                except:
                    continue
            except:
                continue
        
        high_resource_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        MAX_HIGH_RESOURCE_PROCESSES = 50
        return high_resource_processes[:MAX_HIGH_RESOURCE_PROCESSES] if len(high_resource_processes) > MAX_HIGH_RESOURCE_PROCESSES else high_resource_processes

    def terminate_process(self, pid: int, force: bool = False) -> Tuple[bool, Optional[str]]: 
        try:
            if not psutil.pid_exists(pid):
                return False, f"Process with PID {pid} not found"
            
            process = psutil.Process(pid)
            
            if self._is_system_process(pid, process.name()):
                return False, f"Cannot terminate system process: {process.name()} (PID: {pid})"
            
            if force:
                process.kill()
            else:
                process.terminate()
                
            process.wait(timeout=5)
            
            return True, None
        except psutil.NoSuchProcess:
            return False, f"Process with PID {pid} not found"
        except psutil.AccessDenied:
            return False, f"Access denied when trying to terminate PID {pid}"
        except Exception as e:
            return False, str(e)
    
    def get_startup_items(self) -> List[Dict[str, any]]:
        startup_items = []
        
        if self.platform == PlatformDetector.WINDOWS:
            try:
                powershell_cmd = "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location"
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    for i in range(1, len(lines)):
                        if not lines[i].strip():
                            continue
                        parts = lines[i].split(None, 2)
                        if len(parts) >= 3:
                            name, command, location = parts
                            startup_items.append({
                                'name': name,
                                'command': command,
                                'enabled': True,
                                'location': location
                            })
            except Exception as e:
                print(f"Error getting Windows startup items: {e}")
        
        elif self.platform == PlatformDetector.LINUX:
            startup_paths = [
                "/etc/xdg/autostart",
                os.path.expanduser("~/.config/autostart")
            ]
            
            for startup_path in startup_paths:
                if os.path.exists(startup_path) and os.path.isdir(startup_path):
                    for file in os.listdir(startup_path):
                        if file.endswith(".desktop"):
                            file_path = os.path.join(startup_path, file)
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    
                                name = None
                                command = None
                                enabled = True
                                hidden = False
                                
                                for line in content.splitlines():
                                    if line.startswith("Name="):
                                        name = line[5:]
                                    elif line.startswith("Exec="):
                                        command = line[5:]
                                    elif line.startswith("Hidden="):
                                        hidden = line[7:].lower() == "true"
                                    elif line.startswith("X-GNOME-Autostart-enabled="):
                                        enabled = line[25:].lower() == "true"
                                
                                if hidden:
                                    continue
                                    
                                startup_items.append({
                                    'name': name or os.path.basename(file)[:-8],
                                    'command': command or "",
                                    'enabled': enabled,
                                    'location': startup_path
                                })
                            except Exception as e:
                                print(f"Error parsing {file_path}: {e}")
        
        return startup_items
    
    def disable_startup_item(self, item_name: str, item_location: str) -> Tuple[bool, Optional[str]]:
        try:
            if self.platform == PlatformDetector.WINDOWS:
                powershell_cmd = f"""
                $startupItem = Get-CimInstance Win32_StartupCommand | Where-Object {{ $_.Name -eq '{item_name}' }}
                if ($startupItem) {{
                    $registryPath = $startupItem.Location
                    $keyPath = ""
                    switch ($registryPath) {{
                        "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" {{ $keyPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" }}
                        "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" {{ $keyPath = "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" }}
                    }}
                    if ($keyPath) {{
                        Remove-ItemProperty -Path $keyPath -Name $startupItem.Name -ErrorAction SilentlyContinue
                        $true
                    }} else {{ $false }}
                }} else {{ $false }}
                """
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and "True" in result.stdout:
                    return True, None
                else:
                    return False, "Failed to disable startup item in Windows registry"
                
            elif self.platform == PlatformDetector.LINUX:
                if os.path.exists(item_location) and os.path.isdir(item_location):
                    for file in os.listdir(item_location):
                        if file.endswith(".desktop"):
                            file_path = os.path.join(item_location, file)
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                
                                if f"Name={item_name}" in content:
                                    new_content = []
                                    for line in content.splitlines():
                                        if line.startswith("X-GNOME-Autostart-enabled="):
                                            new_content.append("X-GNOME-Autostart-enabled=false")
                                        else:
                                            new_content.append(line)
                                    
                                    if "X-GNOME-Autostart-enabled=" not in content:
                                        new_content.append("X-GNOME-Autostart-enabled=false")
                                    
                                    with open(file_path, 'w') as f:
                                        f.write('\n'.join(new_content))
                                    
                                    return True, None
                            except Exception as e:
                                return False, str(e)
                
                return False, f"Startup item '{item_name}' not found in {item_location}"
        except Exception as e:
            return False, str(e)
    
    def _get_system_process_list(self) -> list:
        windows_system_processes = [
            "System", "smss.exe", "csrss.exe", "wininit.exe", "services.exe", 
            "lsass.exe", "winlogon.exe", "explorer.exe", "svchost.exe",
            "spoolsv.exe", "dwm.exe", "taskmgr.exe", "taskhost.exe"
        ]
        
        linux_system_processes = [
            "systemd", "init", "kthreadd", "kworker", "ksoftirqd", "watchdog",
            "migration", "rcu_", "kipmi", "sshd", "login", "bash", "sh",
            "Xorg", "x11", "gdm", "lightdm", "sddm"
        ]
        
        if self.platform == PlatformDetector.WINDOWS:
            return windows_system_processes
        elif self.platform == PlatformDetector.LINUX:
            return linux_system_processes
        return []
    
    def _is_system_process(self, pid: int, process_name: str) -> bool:
        if pid <= 4:
            return True
        
        if self.platform == PlatformDetector.WINDOWS:
            return any(process_name.lower() == sys_proc.lower() for sys_proc in self.system_processes)
        
        elif self.platform == PlatformDetector.LINUX:
            return any(process_name.lower().startswith(sys_proc.lower()) for sys_proc in self.system_processes)
            
        return False