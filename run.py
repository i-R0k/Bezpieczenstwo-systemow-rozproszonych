from pathlib import Path
import os
import subprocess
import sys
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer


ROOT = Path(__file__).parent.resolve()

API_DIR = ROOT / "VetClinic" / "API"
API_PACKAGE_DIR = API_DIR / "vetclinic_api"
GUI_DIR = ROOT / "VetClinic" / "GUI"

procs: list[subprocess.Popen] = []


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_entries = [str(API_DIR), str(GUI_DIR), str(ROOT)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    return env


def start_processes() -> None:
    global procs
    stop_processes()
    print("Uruchamiam API i GUI...")

    env = _child_env()
    procs = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "vetclinic_api.main:app"],
            cwd=str(API_DIR),
            env=env,
        ),
        subprocess.Popen(
            [sys.executable, "-m", "vetclinic_gui.main"],
            cwd=str(GUI_DIR),
            env=env,
        ),
    ]


def stop_processes() -> None:
    global procs
    for proc in procs:
        try:
            proc.terminate()
        except Exception:
            pass
    time.sleep(0.5)
    procs = []


def on_change(event) -> None:
    print(f"Detected change in {event.src_path!r}, restarting...")
    start_processes()


if __name__ == "__main__":
    start_processes()

    handler = PatternMatchingEventHandler(
        patterns=["*.py"],
        ignore_directories=True,
    )
    handler.on_modified = on_change
    handler.on_created = on_change
    handler.on_deleted = on_change

    observer = Observer()
    observer.schedule(handler, str(API_PACKAGE_DIR), recursive=True)
    observer.schedule(handler, str(GUI_DIR), recursive=True)
    observer.start()

    print("Watching for changes. Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        observer.stop()

    observer.join()
    stop_processes()
