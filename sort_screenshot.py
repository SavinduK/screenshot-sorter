import os
import re
import time
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Path to your screenshots folder
USER = os.getlogin()
screenshot_folder = Path(f"C:/Users/K.G.S.Aman/Pictures/Screenshots")

# Path to the counter database
counter_file = screenshot_folder / "screenshot_counter.json"

# Regex to match already-correct filenames
pattern = re.compile(r"^Screenshot_(\d{8})_(\d+)(?:_\d+)?\.png$")

# Load or initialize counters
if counter_file.exists():
    with open(counter_file, "r") as f:
        date_counter = json.load(f)
else:
    date_counter = {}

def save_counters():
    """Save counters to JSON file."""
    with open(counter_file, "w") as f:
        json.dump(date_counter, f)

def process_file(file: Path):
    """Rename + move a screenshot file into correct folder."""
    if not file.is_file() or not file.name.lower().endswith(".png"):
        return

    # Skip if already in correct format and in monthly folder
    if pattern.match(file.name) and file.parent != screenshot_folder:
        print(f" Skipped (already sorted): {file}")
        return

    # Get creation date
    creation_time = datetime.fromtimestamp(file.stat().st_ctime)
    date_str = creation_time.strftime("%Y%m%d")
    month_str = creation_time.strftime("%Y-%m")  # Folder name: YYYY-MM

    # Get ID for this date from counter
    last_id = date_counter.get(date_str, 0) + 1
    date_counter[date_str] = last_id
    file_id = last_id

    # New filename
    new_name = f"Screenshot_{date_str}_{file_id}.png"

    # Target folder = Screenshots/YYYY-MM
    target_folder = screenshot_folder / month_str
    target_folder.mkdir(parents=True, exist_ok=True)
    new_path = target_folder / new_name

    # Avoid overwriting
    counter = 1
    while new_path.exists():
        new_name = f"Screenshot_{date_str}_{file_id}_{counter}.png"
        new_path = target_folder / new_name
        counter += 1

    # Move + rename
    os.rename(file, new_path)
    save_counters()
    print(f" Moved {file.name} -> {new_path.relative_to(screenshot_folder)}")


class ScreenshotHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".png"):
            process_file(Path(event.src_path))


if __name__ == "__main__":
    print(f"📂 Sorting existing screenshots in {screenshot_folder}...")

    # Process all existing screenshots in root folder
    for file in screenshot_folder.glob("*.png"):
        process_file(file)

    print(" Existing screenshots sorted!\n")
    print(f" Watching {screenshot_folder} for new screenshots...")

    # Start watcher for new files
    event_handler = ScreenshotHandler()
    observer = Observer()
    observer.schedule(event_handler, str(screenshot_folder), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
