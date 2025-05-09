# OptiMate

A cross-platform laptop optimization application designed to help users improve system performance, manage battery life, and clean unnecessary files.

## Tech Stack

- **Python**: Core programming language
- **PyQt5**: GUI framework for creating the desktop application
- **psutil**: Cross-platform library for retrieving system information
- **subprocess**: Module for spawning new processes and communicating with them
- **os/shutil**: Modules for file system operations and management
- **re**: Regular expression module for pattern matching
- **threading**: Module for concurrent operations to improve responsiveness

## Techniques

- **MVC Architecture**: Separation of the application into Model (core), View (UI), and Controller components
- **Multithreading**: Background task processing to keep UI responsive during resource-intensive operations
- **Event-Driven Programming**: Responding to user interactions and system events
- **Cross-Platform Development**: Code organization to handle platform-specific functionality
- **Lazy Loading**: Loading and processing information only when needed
- **Real-time Monitoring**: Continuous tracking of system metrics
- **Defensive Programming**: Robust error handling and exception management
- **Safe Operations**: Simulation options before performing destructive actions

## Features

### File Cleanup
- Identify and remove temporary files
- Empty trash/recycle bin
- Find large unused files taking up disk space
- Safely delete unnecessary files with simulation option

### Process Management
- Monitor running processes and their resource usage
- Identify high-resource-consuming applications
- Terminate unwanted processes
- Manage startup applications

### Battery Health Monitor
- View detailed battery status and health metrics
- Get power usage statistics
- Receive optimization recommendations for better battery life
- Monitor battery usage patterns

## System Requirements
- Windows, macOS, or Linux operating system
- Python 3.6 or higher
- PyQt5 for the graphical user interface

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/OptiMate.git

# Navigate to the project directory
cd OptiMate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### Getting Started
1. Launch the application by running `main.py`
2. The main interface consists of three tabs:
   - **File Cleanup**: Manage disk space and remove unnecessary files
   - **Process Manager**: Monitor and control running processes
   - **Battery Health**: Track and optimize battery performance

### File Cleanup
- Click "Scan" to identify temporary files or large unused files
- Select files to delete or click "Empty Trash" to clear the recycle bin
- Use the "Simulate" option for a safe preview before actual deletion

### Process Manager
- View real-time list of running processes with CPU and memory usage
- Sort by resource consumption to identify performance bottlenecks
- Terminate unnecessary processes to free up resources
- Disable startup items to improve boot time

### Battery Health
- Monitor current battery status including charge level and power state
- View detailed health metrics and estimated remaining time
- Get personalized recommendations to extend battery life
- Track power usage trends over time

## Project Structure
```
laptop_optimizer/
├── main.py                # Application entry point
├── core/                  # Core functionality modules
│   ├── app_controller.py  # Main application controller
│   ├── battery_monitor.py # Battery monitoring utilities
│   ├── file_cleanup.py    # File management and cleanup
│   └── process_manager.py # Process monitoring and control
├── platform/              # Platform-specific functionality
│   └── platform_detector.py # OS detection and platform-specific features
└── ui/                    # User interface components
    ├── battery_monitor_tab.py # Battery interface
    ├── file_cleanup_tab.py    # File cleanup interface
    ├── main_window.py         # Main application window
    └── process_manager_tab.py # Process manager interface
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
[MIT License](LICENSE)

## Acknowledgements
- PyQt5 for the GUI framework
- All contributors who have helped to improve OptiMate

## Contact
For questions or suggestions, please open an issue in the GitHub repository.