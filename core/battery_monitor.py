import os
import re
import time
import subprocess
from typing import Dict, Optional, Tuple, List
import psutil
from platform.platform_detector import PlatformDetector

class BatteryMonitor:
    
    def __init__(self):
        self.platform = PlatformDetector.get_platform()
        
    def get_battery_status(self) -> Dict[str, any]:
        battery_info = {'available': False}
        
        battery = psutil.sensors_battery()
        if battery:
            battery_info.update({
                'available': True,
                'percent': battery.percent,
                'power_plugged': battery.power_plugged,
                'charging': battery.power_plugged,
                'seconds_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            })
            
            if battery_info['seconds_left'] and battery_info['seconds_left'] > 0:
                minutes, seconds = divmod(battery_info['seconds_left'], 60)
                hours, minutes = divmod(minutes, 60)
                battery_info['time_left_formatted'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                battery_info['time_left_formatted'] = "Unknown"
            
            if self.platform == PlatformDetector.WINDOWS:
                windows_info = self._get_windows_battery_info()
                battery_info.update(windows_info)
            elif self.platform == PlatformDetector.LINUX:
                linux_info = self._get_linux_battery_info()
                battery_info.update(linux_info)
        
        return battery_info
    
    def get_battery_health(self) -> Dict[str, any]:
        health_info = {}
        
        if self.platform == PlatformDetector.WINDOWS:
            try:
                powershell_cmd = """
                $battery = Get-WmiObject -Class "BatteryStaticData" -Namespace "ROOT\\WMI"
                $batteryStatus = Get-WmiObject -Class "BatteryStatus" -Namespace "ROOT\\WMI"
                $batteryFullCharged = Get-WmiObject -Class "BatteryFullChargedCapacity" -Namespace "ROOT\\WMI"
                $designCapacity = $battery.DesignedCapacity
                $fullChargeCapacity = $batteryFullCharged.FullChargedCapacity
                $cycleCount = $battery.CycleCount
                
                $healthPercentage = [Math]::Round(($fullChargeCapacity / $designCapacity) * 100, 2)
                
                $result = @{
                    DesignCapacity = $designCapacity
                    FullChargeCapacity = $fullChargeCapacity
                    CycleCount = if($cycleCount -ne $null) { $cycleCount } else { -1 }
                    HealthPercentage = $healthPercentage
                }
                $result | ConvertTo-Json
                """
                
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    
                    design_capacity_match = re.search(r'"DesignCapacity"\s*:\s*(\d+)', output)
                    full_charge_match = re.search(r'"FullChargeCapacity"\s*:\s*(\d+)', output)
                    cycle_count_match = re.search(r'"CycleCount"\s*:\s*(-?\d+)', output)
                    health_percentage_match = re.search(r'"HealthPercentage"\s*:\s*([\d.]+)', output)
                    
                    if design_capacity_match and full_charge_match:
                        design_capacity = int(design_capacity_match.group(1))
                        full_charge_capacity = int(full_charge_match.group(1))
                        
                        health_info['design_capacity'] = design_capacity
                        health_info['current_capacity'] = full_charge_capacity
                        
                        if design_capacity > 0:
                            health_info['health_percentage'] = round((full_charge_capacity / design_capacity) * 100, 2)
                        
                        if cycle_count_match:
                            cycle_count = int(cycle_count_match.group(1))
                            if cycle_count >= 0:
                                health_info['cycle_count'] = cycle_count
            except Exception as e:
                print(f"Error getting Windows battery health: {e}")
        
        elif self.platform == PlatformDetector.LINUX:
            try:
                for battery_dir in self._find_linux_battery_dirs():
                    design_capacity = self._read_linux_battery_file(os.path.join(battery_dir, "energy_full_design"))
                    if design_capacity is None:
                        design_capacity = self._read_linux_battery_file(os.path.join(battery_dir, "charge_full_design"))
                    
                    current_capacity = self._read_linux_battery_file(os.path.join(battery_dir, "energy_full"))
                    if current_capacity is None:
                        current_capacity = self._read_linux_battery_file(os.path.join(battery_dir, "charge_full"))
                    
                    cycle_count = self._read_linux_battery_file(os.path.join(battery_dir, "cycle_count"))
                    
                    if design_capacity and current_capacity:
                        health_info['design_capacity'] = design_capacity
                        health_info['current_capacity'] = current_capacity
                        
                        health_info['health_percentage'] = round((current_capacity / design_capacity) * 100, 2)
                        
                        if cycle_count is not None:
                            health_info['cycle_count'] = cycle_count
                        
                        break
            except Exception as e:
                print(f"Error getting Linux battery health: {e}")
        
        return health_info
    
    def get_power_usage_stats(self, duration_seconds: int = 60) -> Dict[str, float]:
        power_stats = {'available': False}
        
        try:
            battery = psutil.sensors_battery()
            if not battery or battery.power_plugged:
                return power_stats
            
            if battery.secsleft > 0 and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours_remaining = battery.secsleft / 3600
                discharge_rate = battery.percent / hours_remaining if hours_remaining > 0 else 0
                
                power_stats = {
                    'available': True,
                    'discharge_rate_percent_per_hour': round(discharge_rate, 2),
                    'estimated_hours_remaining': round(hours_remaining, 2),
                    'current_percent': battery.percent
                }
            else:
                power_stats = {
                    'available': True,
                    'discharge_rate_percent_per_hour': 10.0,
                    'estimated_hours_remaining': battery.percent / 10.0,
                    'current_percent': battery.percent
                }
        except Exception as e:
            print(f"Error monitoring power usage: {e}")
        
        return power_stats
    
    def get_optimization_recommendations(self) -> List[Dict[str, str]]:
        recommendations = []
        battery_status = self.get_battery_status()
        
        if not battery_status.get('available') or battery_status.get('power_plugged', True):
            recommendations.append({
                'title': "Check Battery Status",
                'description': "Battery information is unavailable or your device is currently charging."
            })
            return recommendations
        
        battery_percent = battery_status.get('percent', 0)
        
        if battery_percent < 20:
            recommendations.append({
                'title': "Critical Battery Level",
                'description': "Battery is below 20%. Connect to power source soon or enable battery saver mode."
            })
        
        recommendations.extend([
            {
                'title': "Reduce Screen Brightness",
                'description': "Lowering screen brightness can significantly extend battery life."
            },
            {
                'title': "Enable Battery Saver Mode",
                'description': "Use your operating system's battery saver mode to extend battery life."
            },
            {
                'title': "Close High Power Applications",
                'description': "Applications that use 3D graphics or perform intensive calculations consume more power."
            },
            {
                'title': "Disable Unused Connections",
                'description': "Turn off Wi-Fi, Bluetooth and other connections when not in use."
            },
            {
                'title': "Optimize Power Settings",
                'description': "Adjust sleep times and power plans in your system settings."
            }
        ])
        
        if self.platform == PlatformDetector.WINDOWS:
            recommendations.append({
                'title': "Run Windows Power Troubleshooter",
                'description': "Use the built-in Windows power troubleshooter to identify issues."
            })
        elif self.platform == PlatformDetector.LINUX:
            recommendations.append({
                'title': "Install TLP or PowerTop",
                'description': "These utilities can help optimize Linux power consumption."
            })
        
        return recommendations
    
    def _get_windows_battery_info(self) -> Dict[str, any]:
        windows_info = {}
        
        try:
            powershell_cmd = """
            (Get-WmiObject -Class Win32_Battery).BatteryStatus
            """
            
            result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                battery_status = int(result.stdout.strip())
                status_map = {
                    1: "Discharging",
                    2: "AC connected, charging",
                    3: "AC connected, fully charged",
                    4: "Low",
                    5: "Critical",
                    6: "Charging",
                    7: "Charging, high rate",
                    8: "Charging, low rate",
                    9: "Charging, critical",
                    10: "Undefined",
                    11: "Partially charged"
                }
                windows_info['status_detail'] = status_map.get(battery_status, "Unknown")
                
                powershell_cmd = """
                (Get-WmiObject -Class Win32_Battery).Description
                """
                
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip():
                    windows_info['name'] = result.stdout.strip()
        except Exception as e:
            print(f"Error getting Windows battery details: {e}")
        
        return windows_info
    
    def _get_linux_battery_info(self) -> Dict[str, any]:
        linux_info = {}
        
        try:
            for battery_dir in self._find_linux_battery_dirs():
                manufacturer = self._read_linux_battery_file(os.path.join(battery_dir, "manufacturer"))
                if manufacturer:
                    linux_info['manufacturer'] = manufacturer
                
                model_name = self._read_linux_battery_file(os.path.join(battery_dir, "model_name"))
                if model_name:
                    linux_info['model'] = model_name
                
                technology = self._read_linux_battery_file(os.path.join(battery_dir, "technology"))
                if technology:
                    linux_info['technology'] = technology
                
                status = self._read_linux_battery_file(os.path.join(battery_dir, "status"))
                if status:
                    linux_info['status_detail'] = status
                
                if linux_info:
                    break
        except Exception as e:
            print(f"Error getting Linux battery details: {e}")
        
        return linux_info
    
    def _find_linux_battery_dirs(self) -> List[str]:
        battery_dirs = []
        
        base_path = "/sys/class/power_supply"
        
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                type_path = os.path.join(item_path, "type")
                
                if os.path.exists(type_path):
                    with open(type_path, 'r') as f:
                        if f.read().strip() == "Battery":
                            battery_dirs.append(item_path)
        
        return battery_dirs
    
    def _read_linux_battery_file(self, path: str) -> Optional[int]:
        if not os.path.exists(path):
            return None
            
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
                
            try:
                return int(content)
            except ValueError:
                return content
        except:
            return None