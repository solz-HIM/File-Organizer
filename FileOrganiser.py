"""
FileOrganiser.py
────────────────────────────────────────────────────────
Core file organisation engine.
Imported and used by FileOrganiserGUI.py

Improvements over the original:
  ✓ Many more file categories and extensions covered
  ✓ Returns detailed results (moved, skipped, errors) not just a count
  ✓ Full undo support — every move is recorded and reversible
  ✓ Callback hook so the GUI can display live per-file log messages
  ✓ Skips hidden files (files starting with a dot e.g. .DS_Store)
  ✓ Never overwrites files — always renames safely
  ✓ Detailed comments explaining every decision
────────────────────────────────────────────────────────
"""

# ── Standard library imports ──────────────────────────
import os       # File path operations, checking existence, making directories
import shutil   # High-level file operations (move, copy)
import json     # Saving/loading the undo history log to a file
import logging  # Writing messages to a log file for debugging
import datetime # Timestamping undo sessions

# ── Set up a file logger ──────────────────────────────
# This writes debug info to organiser.log alongside your script.
# It won't clutter the GUI — it's only for developers reading the log file.
logging.basicConfig(
    filename="organiser.log",
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ═══════════════════════════════════════════════════════
#  CATEGORY MAP
#  Keys   = the folder name that will be created
#  Values = list of file extensions that belong there
#  Add or remove extensions here to customise behaviour.
# ═══════════════════════════════════════════════════════

CATEGORIES: dict[str, list[str]] = {
    "Images":        ["jpg", "jpeg", "png", "gif", "bmp", "webp",
                      "tiff", "tif", "svg", "ico", "heic", "raw", "cr2", "nef"],

    "Videos":        ["mp4", "mkv", "avi", "mov", "wmv", "flv",
                      "webm", "m4v", "mpeg", "mpg", "3gp"],

    "Music":         ["mp3", "wav", "aac", "flac", "ogg", "wma",
                      "m4a", "opus", "aiff"],

    "Documents":     ["pdf", "doc", "docx", "odt", "rtf", "txt",
                      "md", "tex", "wpd", "pages"],

    "Spreadsheets":  ["xls", "xlsx", "ods", "csv", "tsv", "numbers"],

    "Presentations": ["ppt", "pptx", "odp", "key"],

    "Archives":      ["zip", "rar", "7z", "tar", "gz", "bz2",
                      "xz", "iso", "dmg", "cab"],

    "Programs":      ["exe", "msi", "deb", "rpm", "pkg", "app",
                      "bat", "cmd", "sh", "apk"],

    "Code":          ["py", "js", "ts", "html", "css", "java",
                      "c", "cpp", "h", "cs", "go", "rs", "rb",
                      "php", "swift", "kt", "sql", "json", "xml",
                      "yaml", "yml", "toml", "ini", "cfg", "env"],

    "Fonts":         ["ttf", "otf", "woff", "woff2", "eot"],

    "eBooks":        ["epub", "mobi", "azw", "azw3", "fb2", "djvu"],

    "3D & Design":   ["obj", "stl", "fbx", "blend", "psd", "ai",
                      "xd", "fig", "sketch", "dwg", "dxf"],

    # Catch-all — files with unrecognised extensions go here
    "Others":        [],
}

# Path to the JSON file that stores undo history
# It is created in the same folder as this script
UNDO_LOG_PATH = os.path.join(os.path.dirname(__file__), ".organiser_undo.json")


# ═══════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def _get_category(extension: str) -> str:
    """
    Given a file extension (without the dot, e.g. 'mp3'),
    return the matching category name, or 'Others' if none match.

    We iterate through CATEGORIES and check if the extension appears
    in that category's list.  The 'Others' key always acts as fallback.
    """
    ext = extension.lower().strip()   # Normalise: lowercase, no stray spaces

    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category

    return "Others"   # Nothing matched — put it in the catch-all folder


def _safe_destination(folder: str, filename: str) -> str:
    """
    Build a destination path that is guaranteed not to already exist.

    If 'report.pdf' already exists in the destination folder we try:
      report_1.pdf, report_2.pdf, report_3.pdf … until we find a free name.

    This prevents any file from ever being silently overwritten.
    """
    destination = os.path.join(folder, filename)

    # If the path is already free, return it immediately
    if not os.path.exists(destination):
        return destination

    # Split the filename into stem and extension so we can insert a counter
    # e.g.  "report.pdf"  →  base="report"  ext=".pdf"
    base, ext = os.path.splitext(filename)
    counter = 1

    while os.path.exists(destination):
        destination = os.path.join(folder, f"{base}_{counter}{ext}")
        counter += 1

    return destination


def _load_undo_log() -> list:
    """
    Load the undo history from the JSON file on disk.
    Returns an empty list if the file doesn't exist yet or is corrupted.
    The undo log is a list of sessions; each session is a list of move records.
    """
    try:
        with open(UNDO_LOG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # File doesn't exist yet (first run) or got corrupted — start fresh
        return []


def _save_undo_log(log: list) -> None:
    """
    Write the undo history list back to the JSON file.
    We keep only the last 10 sessions to stop the file growing forever.
    """
    # Trim to the most recent 10 sessions
    trimmed = log[-10:]

    with open(UNDO_LOG_PATH, "w") as f:
        json.dump(trimmed, f, indent=2)


# ═══════════════════════════════════════════════════════
#  MAIN PUBLIC FUNCTION
# ═══════════════════════════════════════════════════════

def organize_files(
        folder_path: str,
        log_callback=None,
) -> dict:
    """
    Organise all files in folder_path into category sub-folders.

    Parameters
    ──────────
    folder_path  : str
        Absolute path to the folder the user wants to organise.

    log_callback : callable | None
        Optional function the GUI passes in to receive live status messages.
        Called as log_callback("some message") for each file processed.
        If None, messages are only written to organiser.log.

    Returns
    ───────
    dict with keys:
        "moved"   : int   — number of files successfully moved
        "skipped" : int   — number of files skipped (dirs, hidden files)
        "errors"  : int   — number of files that failed to move
        "summary" : str   — human-readable one-liner result
        "session" : list  — full list of move records (used for undo)

    Why return a dict instead of just a string?
    The GUI can now show individual counts (moved/skipped/errors)
    rather than one combined message.  The original only returned a string,
    which made it hard to colour-code the result or handle errors separately.
    """

    # ── Internal helper: send a message to the GUI log AND the log file ──
    def _emit(message: str) -> None:
        logging.info(message)
        if log_callback:
            log_callback(message)

    # ── Validate the folder path ──────────────────────
    if not folder_path:
        return {"moved": 0, "skipped": 0, "errors": 0,
                "summary": "No folder path provided.", "session": []}

    if not os.path.exists(folder_path):
        return {"moved": 0, "skipped": 0, "errors": 0,
                "summary": "Folder does not exist.", "session": []}

    if not os.path.isdir(folder_path):
        return {"moved": 0, "skipped": 0, "errors": 0,
                "summary": "Path is not a folder.", "session": []}

    # ── Counters ──────────────────────────────────────
    moved   = 0   # Files successfully moved
    skipped = 0   # Files deliberately skipped
    errors  = 0   # Files that raised an exception

    # session_moves records every file move so the user can undo later
    # Each entry is {"source": "...", "destination": "..."} 
    session_moves: list[dict] = []

    _emit(f"Scanning: {folder_path}")

    # ── Iterate over every item in the folder ─────────
    for filename in os.listdir(folder_path):

        file_path = os.path.join(folder_path, filename)

        # Skip sub-directories — we only organise files, not folders
        if os.path.isdir(file_path):
            _emit(f"  ↷ Skipping folder: {filename}")
            skipped += 1
            continue

        # Skip hidden files (start with a dot on macOS/Linux, e.g. .DS_Store)
        if filename.startswith("."):
            _emit(f"  ↷ Skipping hidden file: {filename}")
            skipped += 1
            continue

        # Skip files with no extension — we can't categorise them reliably
        if "." not in filename:
            _emit(f"  ↷ Skipping (no extension): {filename}")
            skipped += 1
            continue

        # ── Determine which category folder this file belongs in ──
        extension     = filename.rsplit(".", 1)[-1]   # Take the LAST part after a dot
        #   rsplit vs split: "archive.tar.gz" → rsplit gives "gz", split also gives "gz"
        #   but rsplit is slightly safer with unusual filenames
        category_name = _get_category(extension)

        # ── Create the category folder if it doesn't exist ────────
        category_folder_path = os.path.join(folder_path, category_name)

        if not os.path.exists(category_folder_path):
            os.makedirs(category_folder_path, exist_ok=True)
            # exist_ok=True prevents a crash if two threads create the folder simultaneously
            _emit(f"  📁 Created folder: {category_name}/")

        # ── Work out the destination path (safe, no overwrite) ────
        destination = _safe_destination(category_folder_path, filename)

        # ── Move the file ─────────────────────────────
        try:
            shutil.move(file_path, destination)

            # Record this move so we can undo it later
            session_moves.append({
                "source":      file_path,
                "destination": destination,
            })

            moved += 1
            _emit(f"  ✓ {filename}  →  {category_name}/{os.path.basename(destination)}")
            logging.info(f"Moved: {file_path}  →  {destination}")

        except PermissionError:
            # File is locked by another program (e.g. a PDF open in Adobe)
            errors += 1
            _emit(f"  ✗ Permission denied: {filename}")
            logging.error(f"PermissionError: {file_path}")

        except Exception as error:
            # Catch-all for any other unexpected error — log it but keep going
            errors += 1
            _emit(f"  ✗ Failed ({filename}): {error}")
            logging.error(f"Error moving {file_path}: {error}")

    # ── Save this session to the undo log ─────────────
    if session_moves:
        undo_log = _load_undo_log()

        # Each session has a timestamp and the list of moves
        undo_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "folder":    folder_path,
            "moves":     session_moves,
        })

        _save_undo_log(undo_log)

    # ── Build the human-readable summary string ────────
    parts = [f"{moved} file{'s' if moved != 1 else ''} organised"]
    if skipped:
        parts.append(f"{skipped} skipped")
    if errors:
        parts.append(f"{errors} error{'s' if errors != 1 else ''}")
    summary = "  •  ".join(parts)

    _emit(f"\n{summary}")

    return {
        "moved":   moved,
        "skipped": skipped,
        "errors":  errors,
        "summary": summary,
        "session": session_moves,
    }


# ═══════════════════════════════════════════════════════
#  UNDO FUNCTION
# ═══════════════════════════════════════════════════════

def undo_last_session(log_callback=None) -> dict:
    """
    Reverses the most recent organise session by moving every file
    back to its original location.

    Parameters
    ──────────
    log_callback : callable | None
        Same as in organize_files() — passes messages to the GUI live log.

    Returns
    ───────
    dict with keys:
        "restored" : int  — files successfully moved back
        "errors"   : int  — files that could not be restored
        "summary"  : str  — human-readable result
    """

    def _emit(message: str) -> None:
        logging.info(message)
        if log_callback:
            log_callback(message)

    # Load the saved undo history
    undo_log = _load_undo_log()

    if not undo_log:
        return {"restored": 0, "errors": 0, "summary": "Nothing to undo."}

    # Pop the most recent session off the end of the list
    last_session = undo_log.pop()
    moves        = last_session.get("moves", [])
    timestamp    = last_session.get("timestamp", "unknown time")

    _emit(f"Undoing session from {timestamp}  ({len(moves)} moves)")

    restored = 0
    errors   = 0

    # Reverse the list so we undo moves in reverse order
    # (matters if filenames were renamed to avoid conflicts)
    for move in reversed(moves):
        source      = move["source"]       # Where the file originally was
        destination = move["destination"]  # Where we moved it to

        # Only attempt to restore if the file is still where we put it
        if not os.path.exists(destination):
            _emit(f"  ✗ Already gone: {os.path.basename(destination)}")
            errors += 1
            continue

        try:
            # Make sure the original directory still exists (it usually does)
            original_dir = os.path.dirname(source)
            os.makedirs(original_dir, exist_ok=True)

            # Move the file back to its original location
            shutil.move(destination, source)
            restored += 1
            _emit(f"  ✓ Restored: {os.path.basename(source)}")

        except Exception as error:
            errors += 1
            _emit(f"  ✗ Could not restore {os.path.basename(source)}: {error}")
            logging.error(f"Undo error: {destination} → {source}: {error}")

    # Save the updated log (with this session removed)
    _save_undo_log(undo_log)

    summary = f"{restored} file{'s' if restored != 1 else ''} restored"
    if errors:
        summary += f"  •  {errors} error{'s' if errors != 1 else ''}"

    _emit(summary)

    return {"restored": restored, "errors": errors, "summary": summary}


# ═══════════════════════════════════════════════════════
#  PREVIEW FUNCTION
# ═══════════════════════════════════════════════════════

def preview_organisation(folder_path: str) -> list[dict]:
    """
    Scans the folder and returns what WOULD happen without moving anything.

    Useful for a future 'Preview' tab in the GUI where users can review
    the plan before committing.

    Returns
    ───────
    List of dicts, each with:
        "filename"  : str  — original filename
        "extension" : str  — file extension
        "category"  : str  — which folder it would go into
        "size_kb"   : float — file size in kilobytes
    """
    results = []

    if not os.path.isdir(folder_path):
        return results

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Same skip rules as organize_files()
        if os.path.isdir(file_path):
            continue
        if filename.startswith("."):
            continue
        if "." not in filename:
            continue

        extension = filename.rsplit(".", 1)[-1]
        category  = _get_category(extension)
        size_kb   = os.path.getsize(file_path) / 1024   # Convert bytes → kilobytes

        results.append({
            "filename":  filename,
            "extension": extension.upper(),
            "category":  category,
            "size_kb":   round(size_kb, 1),
        })

    # Sort alphabetically by category, then by filename within each category
    results.sort(key=lambda r: (r["category"], r["filename"].lower()))

    return results


# ═══════════════════════════════════════════════════════
#  QUICK SELF-TEST  (runs only when you execute this file directly)
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    # Quick smoke-test: print what organize_files would do on the Desktop
    import tempfile, pathlib

    # Create a temporary folder with dummy files to test against
    with tempfile.TemporaryDirectory() as tmp:
        # Make some dummy files
        for name in ["photo.jpg", "song.mp3", "report.pdf", "script.py", "mystery"]:
            pathlib.Path(tmp, name).write_text("test content")

        print("── Preview ─────────────────────────────")
        for row in preview_organisation(tmp):
            print(f"  {row['filename']:20}  →  {row['category']}")

        print("\n── Organise ────────────────────────────")
        result = organize_files(tmp, log_callback=print)
        print(f"\nResult: {result['summary']}")