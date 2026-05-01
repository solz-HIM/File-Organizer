from tkinter import *
from tkinter import filedialog, messagebox
import FileOrganiser

def choose_folder():
    folder = filedialog.askdirectory()
    entry.delete(0, END)
    entry.insert(0, folder)

def run_FileOrganiser():
    folder = entry.get()

    if folder == "":
        messagebox.showerror("Error", "Please select a folder.")
        return

    result = FileOrganiser.organize_files(folder)
    messagebox.showinfo("Success", result)


root = Tk()
root.title("File Organiser")
root.geometry("500x250")

Label(root, text="Select Folder:", font=("Arial", 18)).pack(pady=10)

entry = Entry(root, width=50)
entry.pack(pady=10)

Button(root, text="Browse", command=choose_folder).pack(pady=5)
Button(root, text="Organize Files", command=run_FileOrganiser).pack(pady=10)

root.mainloop()