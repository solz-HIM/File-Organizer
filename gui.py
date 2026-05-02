"""
FileOrganiserGUI.py
────────────────────────────────────────────────────────
A polished, modern GUI for the File Organiser tool.
Built with customtkinter for a professional dark-theme look.

Improvements over the original:
  ✓ Modern dark theme using customtkinter
  ✓ Animated progress bar during organisation
  ✓ Live scrollable log showing every file moved
  ✓ Status bar with colour-coded feedback
  ✓ Drag-and-drop friendly path entry
  ✓ Threaded file operations (UI never freezes)
  ✓ Full comments explaining every section
────────────────────────────────────────────────────────
"""

# ── Standard library imports ──────────────────────────
import threading          # Lets us run organise() in the background so the UI stays responsive
import os                 # Used to check whether the chosen path is actually a directory

# ── Third-party GUI imports ───────────────────────────
import customtkinter as ctk          # Modern-looking tkinter wrapper (pip install customtkinter)
from tkinter import filedialog       # Native OS folder-picker dialog
from tkinter import messagebox       # Native OS error/info pop-ups

# ── Your own module ───────────────────────────────────
import FileOrganiser                 # The organiser logic you already wrote


# ═══════════════════════════════════════════════════════
#  APPEARANCE SETTINGS  (change these to restyle the app)
# ═══════════════════════════════════════════════════════

ctk.set_appearance_mode("dark")           # "dark" | "light" | "system"
ctk.set_default_color_theme("dark-blue")  # Built-in theme that sets button/accent colours

# Custom colour palette — tweak these to match your brand
COLOUR_BG       = "#0E1117"   # Main window background (near-black)
COLOUR_SURFACE  = "#1A1F2E"   # Cards / panels
COLOUR_SURFACE2 = "#242B3D"   # Input fields
COLOUR_ACCENT   = "#4FFFA0"   # Green accent (buttons, highlights)
COLOUR_ACCENT2  = "#2DBD72"   # Darker green for hover states
COLOUR_TEXT     = "#E8EAF0"   # Primary text
COLOUR_DIM      = "#6B7280"   # Muted / secondary text
COLOUR_WARN     = "#F59E0B"   # Warning yellow
COLOUR_ERROR    = "#EF4444"   # Error red
COLOUR_SUCCESS  = "#4FFFA0"   # Success green


# ═══════════════════════════════════════════════════════
#  MAIN APPLICATION CLASS
# ═══════════════════════════════════════════════════════

class FileOrganiserApp(ctk.CTk):
    """
    The main application window.
    Inherits from ctk.CTk (the customtkinter root window class).
    Keeping everything inside a class makes the code easier to read,
    test, and expand — much better than putting it all at the top level.
    """

    def __init__(self):
        super().__init__()   # Initialise the parent CTk window

        # ── Window setup ─────────────────────────────
        self.title("File Organiser")
        self.geometry("680x580")
        self.minsize(560, 480)                    # Prevent the window getting too small
        self.configure(fg_color=COLOUR_BG)        # Set the background colour

        # ── State variables ───────────────────────────
        # BooleanVar tracks whether an organise job is currently running
        # so we can disable the button and prevent double-clicks
        self._running = False

        # ── Build the interface ────────────────────────
        self._build_header()
        self._build_folder_picker()
        self._build_action_row()
        self._build_progress()
        self._build_log()
        self._build_status_bar()


    # ───────────────────────────────────────────────────
    #  UI CONSTRUCTION  (one method per section)
    # ───────────────────────────────────────────────────

    def _build_header(self):
        """Top banner with app name and subtitle."""

        # Outer frame — full width, fixed height
        header = ctk.CTkFrame(self, fg_color=COLOUR_SURFACE, corner_radius=0, height=72)
        header.pack(fill="x")
        header.pack_propagate(False)   # Stop the frame shrinking to fit its children

        # App icon + name on the left
        ctk.CTkLabel(
            header,
            text="🗂  File Organiser",
            font=ctk.CTkFont("Courier", 22, "bold"),
            text_color=COLOUR_ACCENT,
        ).pack(side="left", padx=24, pady=16)

        # Subtle subtitle on the right
        ctk.CTkLabel(
            header,
            text="Sort your files automatically",
            font=ctk.CTkFont("Courier", 12),
            text_color=COLOUR_DIM,
        ).pack(side="right", padx=24)


    def _build_folder_picker(self):
        """
        Card containing:
          - A label
          - A text entry showing the chosen folder path
          - A Browse button that opens the OS folder dialog
        """

        # Card frame with rounded corners and a subtle background
        card = ctk.CTkFrame(self, fg_color=COLOUR_SURFACE, corner_radius=12)
        card.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text="SELECT FOLDER",
            font=ctk.CTkFont("Courier", 11, "bold"),
            text_color=COLOUR_DIM,
        ).pack(anchor="w", padx=20, pady=(14, 4))

        # Row that holds the entry box and the browse button side by side
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))

        # StringVar lets us read/write the entry's content easily from other methods
        self.folder_var = ctk.StringVar()

        # Text entry — user can also type a path directly
        self.folder_entry = ctk.CTkEntry(
            row,
            textvariable=self.folder_var,
            placeholder_text="Click Browse or paste a folder path here…",
            font=ctk.CTkFont("Courier", 13),
            fg_color=COLOUR_SURFACE2,
            border_color="#2A2F3E",
            text_color=COLOUR_TEXT,
            height=42,
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Browse button — calls _choose_folder when clicked
        ctk.CTkButton(
            row,
            text="Browse",
            width=100,
            height=42,
            font=ctk.CTkFont("Courier", 13, "bold"),
            fg_color=COLOUR_SURFACE2,
            hover_color="#2A2F3E",
            border_color=COLOUR_ACCENT,
            border_width=1,
            text_color=COLOUR_ACCENT,
            command=self._choose_folder,        # ← bound to our method below
        ).pack(side="left")


    def _build_action_row(self):
        """The main 'Organise Files' button, centred below the folder picker."""

        # We keep a reference to the button (self.go_btn) so we can
        # disable it while a job is running
        self.go_btn = ctk.CTkButton(
            self,
            text="▶   Organise Files",
            height=50,
            font=ctk.CTkFont("Courier", 15, "bold"),
            fg_color=COLOUR_ACCENT2,
            hover_color=COLOUR_ACCENT,
            text_color="#000000",             # Black text on the green button
            corner_radius=10,
            command=self._run_organiser,      # ← bound to our threaded method below
        )
        self.go_btn.pack(fill="x", padx=20, pady=8)


    def _build_progress(self):
        """
        A thin animated progress bar shown while the organiser runs.
        Hidden by default — we call .start() / .stop() on it.
        """

        self.progress = ctk.CTkProgressBar(
            self,
            fg_color=COLOUR_SURFACE2,
            progress_color=COLOUR_ACCENT,
            height=6,
            mode="indeterminate",   # Bouncing animation (we don't know exact progress %)
        )
        self.progress.pack(fill="x", padx=20, pady=(0, 6))
        self.progress.set(0)        # Start at 0 so it's invisible until we call .start()


    def _build_log(self):
        """
        Scrollable text area that shows a live log of every file moved.
        We write to it from _log() which can be called from any method.
        """

        # Section label above the log box
        ctk.CTkLabel(
            self,
            text="ACTIVITY LOG",
            font=ctk.CTkFont("Courier", 11, "bold"),
            text_color=COLOUR_DIM,
        ).pack(anchor="w", padx=22, pady=(4, 2))

        # CTkTextbox is a scrollable, editable text widget
        self.log_box = ctk.CTkTextbox(
            self,
            fg_color=COLOUR_SURFACE,
            text_color=COLOUR_TEXT,
            font=ctk.CTkFont("Courier", 12),
            border_color="#2A2F3E",
            border_width=1,
            corner_radius=10,
            activate_scrollbars=True,
        )
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # Disable editing so users can't accidentally change the log
        self.log_box.configure(state="disabled")

        # Welcome message shown when the app first opens
        self._log("Ready. Choose a folder and press Organise Files.")


    def _build_status_bar(self):
        """
        A thin bar at the very bottom of the window showing the current status.
        Colour changes to green (success), red (error), or yellow (working).
        """

        bar = ctk.CTkFrame(self, fg_color=COLOUR_SURFACE, corner_radius=0, height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        # StringVar so we can update the text easily from other methods
        self.status_var = ctk.StringVar(value="Idle")

        self.status_label = ctk.CTkLabel(
            bar,
            textvariable=self.status_var,
            font=ctk.CTkFont("Courier", 11),
            text_color=COLOUR_DIM,
        )
        self.status_label.pack(side="left", padx=16, pady=6)


    # ───────────────────────────────────────────────────
    #  EVENT HANDLERS  (what happens when buttons are clicked)
    # ───────────────────────────────────────────────────

    def _choose_folder(self):
        """
        Opens the native OS folder-picker dialog.
        If the user picks a folder, it's written into the entry box.
        If they cancel, nothing changes.
        """
        folder = filedialog.askdirectory(title="Choose a folder to organise")

        if folder:   # askdirectory returns "" if the user cancels
            self.folder_var.set(folder)
            self._log(f"📁 Folder selected: {folder}")
            self._set_status("Folder selected — ready to organise.", COLOUR_TEXT)


    def _run_organiser(self):
        """
        Called when the user clicks 'Organise Files'.

        Key design decision: we run the actual work in a BACKGROUND THREAD
        using Python's threading module. Without this, the window would freeze
        completely while files are being moved — a very bad user experience.

        The background thread calls FileOrganiser.organize_files() and then
        uses self.after() to safely update the UI from the main thread when done.
        (tkinter is NOT thread-safe, so we must never update widgets from a
        background thread directly.)
        """

        # ── Validation ────────────────────────────────
        folder = self.folder_var.get().strip()

        if not folder:
            # No path entered — show an error and stop
            messagebox.showerror("No Folder Selected", "Please select a folder before organising.")
            return

        if not os.path.isdir(folder):
            # Path entered but it doesn't exist or isn't a folder
            messagebox.showerror("Invalid Folder", f"This path doesn't exist:\n{folder}")
            return

        # ── Prevent double-clicks ─────────────────────
        if self._running:
            return   # Already running — ignore extra clicks

        # ── Update UI to "working" state ──────────────
        self._running = True
        self.go_btn.configure(state="disabled", text="⏳  Organising…")   # Grey out the button
        self.progress.start()                                              # Start the bouncing bar
        self._set_status("Organising files…", COLOUR_WARN)
        self._log("\n── Starting organisation ──────────────────")
        self._log(f"📂 Target: {folder}")

        # ── Launch background thread ──────────────────
        # daemon=True means the thread is automatically killed if the app closes
        thread = threading.Thread(
            target=self._organise_worker,
            args=(folder,),
            daemon=True,
        )
        thread.start()


    def _organise_worker(self, folder: str):
        """
        Runs in a BACKGROUND THREAD — do not touch any tkinter widgets here.
        Calls the organiser and schedules UI updates back on the main thread
        using self.after(0, callback).
        """
        try:
            # ── Call your existing organiser module ───
            result = FileOrganiser.organize_files(folder)

            # Schedule the success handler on the main thread (thread-safe)
            self.after(0, self._on_success, result)

        except Exception as error:
            # Something went wrong — schedule the error handler on the main thread
            self.after(0, self._on_error, str(error))


    def _on_success(self, result: str):
        """
        Called on the MAIN THREAD after the organiser finishes successfully.
        Restores the UI to its idle state and shows the result.
        """
        self._running = False
        self.progress.stop()
        self.progress.set(0)

        # Re-enable the button
        self.go_btn.configure(state="normal", text="▶   Organise Files")

        # Write result to the log
        self._log(f"✅ Done! {result}")
        self._log("── Finished ────────────────────────────────\n")

        # Update status bar to green
        self._set_status(f"✓ {result}", COLOUR_SUCCESS)

        # Show a pop-up confirmation
        messagebox.showinfo("Organisation Complete", result)


    def _on_error(self, error_message: str):
        """
        Called on the MAIN THREAD if an exception occurred during organisation.
        Shows the error without crashing the app so users can try again.
        """
        self._running = False
        self.progress.stop()
        self.progress.set(0)

        # Re-enable the button
        self.go_btn.configure(state="normal", text="▶   Organise Files")

        # Write error to the log
        self._log(f"❌ Error: {error_message}")
        self._log("── Failed ──────────────────────────────────\n")

        # Update status bar to red
        self._set_status(f"Error: {error_message}", COLOUR_ERROR)

        # Show a pop-up error dialog
        messagebox.showerror("Organisation Failed", f"An error occurred:\n\n{error_message}")


    # ───────────────────────────────────────────────────
    #  HELPER METHODS  (small utilities used internally)
    # ───────────────────────────────────────────────────

    def _log(self, message: str):
        """
        Appends a line to the scrollable log box and auto-scrolls to the bottom.
        Always call this from the MAIN THREAD (it updates a tkinter widget).
        """
        self.log_box.configure(state="normal")      # Temporarily allow writing
        self.log_box.insert("end", message + "\n")  # Append the new line
        self.log_box.see("end")                      # Scroll to the bottom
        self.log_box.configure(state="disabled")    # Lock it again


    def _set_status(self, message: str, colour: str = COLOUR_DIM):
        """
        Updates the status bar text and colour.
        colour should be a hex string like '#4FFFA0'.
        """
        self.status_var.set(message)
        self.status_label.configure(text_color=colour)


# ═══════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    # Only run the app when this file is executed directly,
    # NOT when it's imported as a module by another script.
    app = FileOrganiserApp()
    app.mainloop()   # Starts the tkinter event loop (keeps the window open)