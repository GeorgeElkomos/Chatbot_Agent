"""
File: remove_emoji.py (relative to Chatbot_Agent)
"""
# Aggressive fix for CrewAI Unicode issues on Windows
import os
import sys

def remove_emoji():
    os.environ["OTEL_SDK_DISABLED"] = "true"
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # Force UTF-8 encoding for Windows console before any CrewAI imports
    if sys.platform == "win32":
        try:
            # Reconfigure stdout and stderr to use UTF-8 with error handling
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            
            # Set Windows console to UTF-8 if possible
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            # If that fails, monkey patch print to strip emojis
            original_print = print
            def safe_print(*args, **kwargs):
                try:
                    original_print(*args, **kwargs)
                except UnicodeEncodeError:
                    # Strip non-ASCII characters and retry
                    safe_args = []
                    for arg in args:
                        if isinstance(arg, str):
                            safe_args.append(arg.encode('ascii', 'ignore').decode('ascii'))
                        else:
                            safe_args.append(arg)
                    original_print(*safe_args, **kwargs)
            
            import builtins
            builtins.print = safe_print



    # Patch Rich console after import to disable all output
    try:
        from rich.console import Console
        original_console_init = Console.__init__
        def patched_console_init(self, *args, **kwargs):
            # Force disable all Rich console features on Windows
            kwargs['file'] = open(os.devnull, 'w') if sys.platform == "win32" else kwargs.get('file')
            kwargs['force_terminal'] = False
            kwargs['no_color'] = True
            kwargs['quiet'] = True
            return original_console_init(self, *args, **kwargs)
        Console.__init__ = patched_console_init
    except Exception:
        pass

    # # Patch CrewAI event bus to prevent any logging
    # try:
    #     from crewai.utilities.events import crewai_event_bus
    #     import json
    #     import threading
    #     event_log_path = os.path.join(os.path.dirname(__file__), 'ai-output', 'event_bus_log.json')
    #     event_log_lock = threading.Lock()
    #     def make_serializable(obj):
    #         try:
    #             json.dumps(obj)
    #             return obj
    #         except Exception:
    #             return repr(obj)

    #     def logging_emit(*args, **kwargs):
    #         event = {
    #             "args": [make_serializable(a) for a in args],
    #             "kwargs": {k: make_serializable(v) for k, v in kwargs.items()}
    #         }
    #         # Append event to the log file as a JSON line
    #         with event_log_lock:
    #             with open(event_log_path, "a", encoding="utf-8") as f:
    #                 f.write(json.dumps(event, ensure_ascii=False) + "\n")
    #         # Optionally, call the original emit if you want to preserve CrewAI behavior
    #         # If not, just log and do nothing else
    #     crewai_event_bus.emit = logging_emit
    # except Exception:
    #     pass

    try:
        from crewai.utilities.events import crewai_event_bus
        def dummy_emit(*args, **kwargs):
            pass
        crewai_event_bus.emit = dummy_emit
    except Exception:
        pass

