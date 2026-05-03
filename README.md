# 📂 File Organizer (Python)

A modern and efficient file organization tool built with Python that automatically sorts files into categorized folders, detects duplicates, and provides a user-friendly GUI for seamless interaction.

---

## 🚀 Features

* 📁 **Automatic File Sorting**
  Organizes files into folders based on file type (e.g., Images, Documents, Videos, etc.)

* 🖥️ **Graphical User Interface (GUI)**
  Simple and modern interface for selecting directories and running the organizer

* 🔍 **Duplicate File Detection**
  Detects duplicate files and allows users to choose whether to keep or remove them

* 📍 **Custom Directory Support**
  Works on any folder selected by the user (not limited to Downloads)

* ⚡ **Fast & Lightweight**
  Optimized for speed using built-in Python libraries

---

## 🛠️ Tech Stack

* Python 3.x
* os
* shutil
* tkinter (for GUI)

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/solz-HIM/File-Organizer.git
cd File-Organizer
```

### 2. Install dependencies

No external packages required (uses built-in Python libraries)

---

## ▶️ Usage

### Run the application

```bash
python main.py
```

### Steps:

1. Launch the app
2. Select the folder you want to organize
3. Click **Organize Files**
4. Review duplicates (if any)
5. Confirm actions

---

## 📁 Example Folder Structure

Before:

```
Downloads/
  image1.jpg
  doc1.pdf
  video1.mp4
```

After:

```
Downloads/
  Images/
    image1.jpg
  Documents/
    doc1.pdf
  Videos/
    video1.mp4
```

---

## 🧠 How It Works

* Scans all files in the selected directory
* Identifies file types using extensions
* Creates folders dynamically if they don’t exist
* Moves files into their respective categories
* Detects duplicate files using file name/hash comparison



## 📌 Future Improvements

* Drag-and-drop support
* Cloud storage integration
* File preview before organizing
* AI-based smart categorization

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a new branch (`feature-new`)
3. Commit your changes
4. Push and open a Pull Request

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👤 Author

**Solz**
Aspiring Software Developer | Python Enthusiast

---

## ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub!
