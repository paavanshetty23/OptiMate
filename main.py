#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow
from core.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Laptop Optimizer")
    
    controller = AppController()
    
    main_window = MainWindow(controller)
    main_window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()