import os
import sys
from sys import platform as sys_platform

class PlatformDetector:
    WINDOWS = "windows"
    LINUX = "linux"
    MAC = "darwin"
    UNKNOWN = "unknown"
    
    @staticmethod
    def get_platform():
        system = sys_platform.lower()
        
        if system.startswith("win"):
            return PlatformDetector.WINDOWS
        elif system.startswith("linux"):
            return PlatformDetector.LINUX
        elif system.startswith("darwin"):
            return PlatformDetector.MAC
        else:
            return PlatformDetector.UNKNOWN
    
    @staticmethod
    def get_temp_directory():
        if PlatformDetector.get_platform() == PlatformDetector.WINDOWS:
            return os.environ.get('TEMP')
        else:
            return "/tmp"
    
    @staticmethod
    def get_trash_directory():
        if PlatformDetector.get_platform() == PlatformDetector.WINDOWS:
            return os.path.expanduser("~\\$Recycle.Bin")
        elif PlatformDetector.get_platform() == PlatformDetector.LINUX:
            return os.path.expanduser("~/.local/share/Trash")
        elif PlatformDetector.get_platform() == PlatformDetector.MAC:
            return os.path.expanduser("~/.Trash")
        else:
            return None
    
    @staticmethod
    def is_admin():
        try:
            if PlatformDetector.get_platform() == PlatformDetector.WINDOWS:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False