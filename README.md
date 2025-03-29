# Log File Monitor

Log File Monitor is a Python package designed to detect changes in a specified log file and send those changes through a socket for processing by other scripts. It enables real-time monitoring and integration with external systems for analysis and synthesis.

## Features

- Monitors specified log files for real-time updates
- Streams new log entries through a socket for external processing
- Lightweight and efficient implementation
- Supports integration with various analysis and synthesis tools
- Configurable to monitor specific patterns or keywords

## Installation

### Prerequisites

- Python 3.x
- Required dependencies (install using pip):
  ```sh
  pip install watchdog git+https://github.com/OperavonderVollmer/OperaPowerRelay.git@v1.1.4
  ```

### Manual Installation

1. Clone or download the repository.
2. Navigate to the directory containing `setup.py`:
   ```sh
   cd /path/to/LogFileMonitor
   ```
3. Install the package in **editable mode**:
   ```sh
   pip install -e .
   ```

### Installing via pip:

```sh
pip install git+https://github.com/OperavonderVollmer/LogFileMonitor.git@main
```

Ensure that all necessary dependencies are installed in your environment.

## Dependencies

- `watchdog` for monitoring file changes
- `socket` (built-in) for communication with external scripts

## License

Log File Monitor is licensed under the MIT License.

