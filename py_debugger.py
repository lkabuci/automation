import functools
import traceback
import inspect
import json
import os
from pathlib import Path
from datetime import datetime

def my_debug_function(func):
    log_path: Path = Path("/tmp/debug.json")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_signature = inspect.signature(func)
        func_file = inspect.getfile(func)
        func_line_no = inspect.getsourcelines(func)[1] + 1

        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S %d-%m-%Y"),
            "function": f"{func.__name__}",
            "path": f"{func_file}:{func_line_no}",
            "signature": str(func_signature),
            "args": args,
            "kwargs": kwargs,
            "call_stack": [],
            "result": None,
            "error": None,
        }

        full_stack = traceback.extract_stack()[:-1]  # Exclude the current wrapper call
        for frame in reversed(full_stack):
            log_entry["call_stack"].append({
                "function": frame.name,
                "path": f"{frame.filename}:{frame.lineno}",
            })

        try:
            result = func(*args, **kwargs)
            log_entry["result"] = result
        except Exception as e:
            log_entry["error"] = str(e)
            raise
        finally:
            log_file_path = log_path
            logs = []

            # Check if the file exists and is not empty, then load existing data
            if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
                with open(log_file_path, "r") as log_file:
                    logs = json.load(log_file)

            logs.append(log_entry)  # Append the new log entry

            # Write back the updated logs list
            with open(log_file_path, "w") as log_file:
                json.dump(logs, log_file, indent=4, default=str)

        return result
    return wrapper
