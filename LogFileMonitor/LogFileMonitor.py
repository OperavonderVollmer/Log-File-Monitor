from OperaPowerRelay import opr
import os
import json
import time
import socket
import glob
import sys
import queue
import threading
from watchfiles import watch
import chardet

class Monitor:
    def __init__(self, name: str, log_file_path: str, offset: int = -2, encoding: str = "utf-8"):
        self._offset = offset
        self._name = name
        self._status = "OFFLINE"
        self._log_file_path = opr.clean_path(log_file_path)

        self._encoding = encoding

        self._observer_thread = None
        self._stop_event = threading.Event()

        opr.print_from("LogFileMonitor - Monitor Init", f"SUCCESS: Created {self._name} monitor")
        self._status = "STANDBY"
    

    def _observer_thread_func(self) -> None:
        opr.print_from("LogFileMonitor - Observer Thread", f"SUCCESS: Thread started for {self._name} monitor")

        for changes in watch(os.path.dirname(self._log_file_path)):
            if self._stop_event.is_set():
                return
            
            for change_type, file_path in changes:
                if file_path == self._log_file_path:
                    try:
                        with open(self._log_file_path, "rb") as f:
                            f.seek(0, 2)  # Move to the end of the file
                            f.seek(max(f.tell() - 4096, 0), 0)  # Move back 4KB (adjust if needed)
                            lines = f.readlines()
                            last_line = lines[self._offset].decode(self._encoding).strip() if lines else None

                            self.Communicate(last_line)

                    except Exception as e:
                        opr.print_from("LogFileMonitor - Observer Thread", f"ERROR: Failed to read log file: {e}")
                        continue

        opr.print_from("LogFileMonitor - Observer Thread", f"SUCCESS: Thread stopped for {self._name} monitor")

    

    def Communicate(self, output : str) -> None:
        communicate_out(output)

    def Start(self) -> None:
        
        if self._status == "RUNNING":
            return
        

        try:
            self._stop_event.clear()
            self._observer_thread = threading.Thread(target=self._observer_thread_func, daemon=True)
            self._observer_thread.start()

        except Exception as e:
            self._observer = None
            self._observer_thread = None
            opr.print_from("LogFileMonitor - Monitor Start", f"ERROR: Failed to start {self._name}: {e}")
            return

        
        opr.print_from("LogFileMonitor - Monitor Start", f"SUCCESS: Started monitor for {self._name} at {self._log_file_path}")
        self._status = "RUNNING"

    def Stop(self) -> None:
        
        if self._status == "STANDBY":
            return
        
        self._stop_event.set()
        self._observer_thread.join()
        self._observer_thread = None
        
        opr.print_from("LogFileMonitor - Monitor Stop", f"SUCCESS: Stopped monitor for {self._name} at {self._log_file_path}")
        self._status = "STANDBY"

    def __str__(self):
        return f"{self._name} - {self._status}"



def _load_json():
    opr.print_from("LogFileMonitor - Load JSON", "Loading config file")
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(root_dir, "config.json")
    if not os.path.exists(config_file_path):
        with open(config_file_path, "w") as f:
            opr.print_from("LogFileMonitor - Load JSON", "config.json not found, creating empty file")
            f.write("{}")
    
    with open(config_file_path, "r") as f:
        opr.print_from("LogFileMonitor - Load JSON", "SUCCESS: Loaded config.json")
        return json.load(f)

def _save_json():
    opr.print_from("LogFileMonitor - Save JSON", "Saving config file")
    root_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(root_dir, "config.json")
    with open(config_file_path, "w") as f:
        json.dump(PATHS, f)
        opr.print_from("LogFileMonitor - Save JSON", "SUCCESS: Saved config.json")

def _add_monitor() -> str:
    
    while True:
        mode = opr.input_from("LogFileMonitor - Wizard | Add", "[1] Quick [2] Quick Start [3] Custom [4] Custom Start")
        if mode in ["1", "2", "3", "4"]:
            break
        opr.print_from("LogFileMonitor - Wizard | Add", "Invalid input")

    name = opr.input_from("LogFileMonitor - Wizard | Add","Monitor Name")

    s_name = opr.sanitize_text(name)[0]

    if s_name in [monitor._name for monitor in MONITORS]:
        return f"Monitor with name {s_name} already exists"


    if not PATHS:
        return "There are no saved paths in the config file"
    


    opr.print_from("LogFileMonitor - Wizard | Add", "Select a path", 1)
    for i, path in enumerate(PATHS.keys(), 1):
        opr.print_from("LogFileMonitor - Wizard | Add", f"[{i}]: {path}")
    
    while True:        
        choice = opr.input_from("LogFileMonitor - Wizard | Add", f"Select a path (1-{len(PATHS)})")
        if choice.isdigit() and int(choice) in range(1, len(PATHS) + 1):
            break
        opr.print_from("LogFileMonitor - Wizard | Add","Invalid selection. Please enter a valid number.")    
        

    path = list(PATHS.keys())[int(choice) - 1]
    
    chosen_path, prefix = PATHS[path]

    s_path = get_latest_log(chosen_path, prefix)

    if s_path in [monitor._log_file_path for monitor in MONITORS]:
        return f"FAILED: Monitor with path {s_path} already exists"

    encoding = "utf-8"
    offset = -2

    if mode == "2":
        while True:
            en_choice = opr.input_from("LogFileMonitor - Wizard | Add", f"Please select an encoding: [1] UTF-8 [2] UTF-16 [3] UTF-32")
            if en_choice in ["1", "2", "3"]:
                break
            opr.print_from("LogFileMonitor - Wizard | Add", "Invalid input")

        encoding = ["utf-8", "utf-16", "utf-32"][int(en_choice) - 1]
        
        while True:
            offset = int(opr.input_from("LogFileMonitor - Wizard | Add", "Please enter a number for the offset: "))
            if offset.isdigit():                
                break
            opr.print_from("LogFileMonitor - Wizard | Add", "Invalid input")
        if offset > 0:
            offset = offset * -1
        

    monitor = Monitor(s_name, s_path, offset, encoding)
    MONITORS.append(monitor)
    if mode == "2" or mode == "4":
        monitor.Start()
    return f"SUCCESS: Monitor added: {monitor}"

def _list_monitors() -> str:
    if not MONITORS:
        return "No monitors found"
    
    message = ""
    for monitor in MONITORS:
        opr.print_from("LogFileMonitor - Wizard | List", f"{monitor}")
        message += f"{str(monitor)}\n"

    return message

def _remove_monitor() -> str:
    name = opr.input_from("LogFileMonitor - Wizard | Remove", "Monitor Name")
    s_name = opr.sanitize_text(name)[0]

    for monitor in MONITORS:
        if monitor._name == s_name:
            MONITORS.remove(monitor)
            return f"Monitor removed: {monitor}"
        
    return f"Monitor with name {s_name} not found"

def _start_monitor() -> str:
    opr.print_from("LogFileMonitor - Wizard | Start", "Select a path", 1)
    for i, monitor in enumerate(MONITORS, 1):
        opr.print_from("LogFileMonitor - Wizard | Start", f"[{i}]: {monitor}")
    
    while True:        
        choice = opr.input_from("LogFileMonitor - Wizard | Start", f"Select a Monitor (1-{len(MONITORS)})")
        if choice.isdigit() and int(choice) in range(1, len(MONITORS) + 1):
            break
        opr.print_from("LogFileMonitor - Wizard | Start","Invalid selection. Please enter a valid number.")    
        

    monitor = MONITORS[int(choice) - 1]

    monitor.Start()
    return f"Monitor started: {monitor}"


def _stop_monitor() -> str:
    opr.print_from("LogFileMonitor - Wizard | Stop", "Select a path", 1)
    for i, monitor in enumerate(MONITORS, 1):
        opr.print_from("LogFileMonitor - Wizard | Stop", f"[{i}]: {monitor}")
    
    while True:        
        choice = opr.input_from("LogFileMonitor - Wizard | Stop", f"Select a Monitor (1-{len(MONITORS)})")
        if choice.isdigit() and int(choice) in range(1, len(MONITORS) + 1):
            break
        opr.print_from("LogFileMonitor - Wizard | Stop", "Invalid selection. Please enter a valid number.")    
        

    monitor = MONITORS[int(choice) - 1]

    monitor.Stop()
    return f"Monitor stopped: {monitor}"

def _config_path() -> str:

# is meant to overwrite if path already exists
    name = opr.input_from("LogFileMonitor - Wizard | Path", "Path Name")
    s_name = opr.sanitize_text(name)[0]

    path = opr.input_from("LogFileMonitor - Wizard | Path", "Folder Containing the log file")
    s_path = opr.clean_path(opr.sanitize_text(path)[0])

    prefix = opr.input_from("LogFileMonitor - Wizard | Path", "Prefix of the log file")
    s_prefix = opr.sanitize_text(prefix)[0]

    PATHS[s_name] = s_path, s_prefix

    _save_json()

    return f"Path added: {s_name} - {s_path} - {s_prefix}"

def get_latest_log(log_directory: str, log_prefix: str) -> str | None:
    
    log_pattern = os.path.join(log_directory, f"{log_prefix}*.txt")
    
    log_files = glob.glob(log_pattern)
    
    if not log_files:
        return None 
    
    latest_log = max(log_files, key=os.path.getmtime)
    opr.print_from("LogFileMonitor - Get Latest Log", f"SUCCESS: Found latest log file: {os.path.basename(latest_log)}")
    return latest_log

def log_monitor_wizard(command: str) -> str:
    
    match command.lower().strip():
        case "list":
            _list_monitors()
            return "Monitors Listed"
        
        case "add":
            return _add_monitor()
    
        case "remove":            
            return _remove_monitor()
        
        case "start":
            return _start_monitor()

        case "stop":
            return _stop_monitor()

        case "path":
            return _config_path()

        case _:
            return "Invalid command"

def socket_thread():
    opr.print_from("LogFileMonitor - Socket", "Starting socket thread")
    SOCKET.bind(("127.0.0.1", PORT))
    SOCKET.listen(1)

    while True:
        try:
            connection, address = SOCKET.accept()
            opr.print_from("LogFileMonitor - Socket", f"SUCCESS: Connected to client at {address}")
            
            while True:
                data = OUTPUT_QUEUE.get(timeout=1)
                opr.print_from("LogFileMonitor - Socket", f"Sending data: {data}")
                connection.sendall(data.encode('utf-8'))
        
        except (BrokenPipeError, ConnectionResetError):
            opr.print_from("LogFileMonitor - Socket", "ERROR: Client disconnected. Waiting for a new connection...")

        except socket.timeout:
            continue    
        
        except Exception as e:
            opr.print_from("LogFileMonitor - Socket", f"ERROR: {e}")
            break
        break

def _dummy_socket():
    opr.print_from("LogFileMonitor - Dummy Socket", "Starting dummy socket thread")
    while True:
        try:
            _ = OUTPUT_QUEUE.get(timeout=1)
            opr.print_from("LogFileMonitor - Dummy Socket", _)
        except queue.Empty:
            time.sleep(1)
            continue

def communicate_out(output: str) -> None:
    OUTPUT_QUEUE.put(output)

PORT = 50006
MONITORS: list[Monitor] = []
PATHS: dict[str, tuple[str, str]] = {}
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
OUTPUT_QUEUE = queue.Queue()
SOCKET_THREAD = threading.Thread(target=socket_thread, daemon=True)
DUMMY_SOCKET = threading.Thread(target=_dummy_socket, daemon=True)

if __name__ == '__main__':
    opr.print_from("LogFileMonitor", "Starting LogFileMonitor")

    PATHS = _load_json()

    while True:
        decision = opr.input_from("LogFileMonitor - Main", "Select Production (1) or Testing (2)")
        if decision == "1":
            SOCKET_THREAD.start()
            break

        elif decision == "2":
            DUMMY_SOCKET.start()
            break

        else:
            opr.print_from("LogFileMonitor - Main", "Invalid selection. Please enter 1 or 2.")


    retry_count = 0
    while True:
        
        try:
            decision = opr.input_from("LogFileMonitor - Main", "LogFileMonitor Command (list, add, remove, start, stop, path)")
            opr.print_from("LogFileMonitor - Main", log_monitor_wizard(decision))

            time.sleep(1)

        except KeyboardInterrupt:
            opr.print_from("LogFileMonitor", "KeyboardInterrupt detected", 1)
            break

        except Exception as e:
            opr.print_from("LogFileMonitor", f"ERROR: {e}")
            retry_count += 1
            if retry_count > 5:
                opr.print_from("LogFileMonitor", "Too many retries, exiting...")
                break
            opr.print_from("LogFileMonitor", "Retrying...")
    
    _save_json()

    opr.print_from("LogFileMonitor", "Exiting LogFileMonitor")
    SOCKET.close()
    
    if SOCKET_THREAD.is_alive():
        SOCKET_THREAD.join()
    
    if DUMMY_SOCKET.is_alive():
        DUMMY_SOCKET.join()

    sys.exit(0)

