import os
import shutil

categories = {
    "Images": ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    "Music": ['mp3', 'wav', 'aac'],
    "Videos": ['mp4', 'mkv', 'avi'],
    "Documents": ['pdf', 'docx', 'txt', 'xlsx', 'pptx'],
    "Archives": ['zip', 'rar', '7z'],
    "Programs": ['exe', 'msi'],
}

def organize_files(folder_path):
    moved = 0

    if not os.path.exists(folder_path):
        return "Folder does not exist."

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isdir(file_path):
            continue

        if '.' not in filename:
            continue

        extension = filename.split('.')[-1].lower()

        category_folder = "Others"

        for category, exts in categories.items():
            if extension in exts:
                category_folder = category
                break

        new_folder = os.path.join(folder_path, category_folder)

        if not os.path.exists(new_folder):
            os.mkdir(new_folder)

        destination = os.path.join(new_folder, filename)

        base, ext = os.path.splitext(filename)
        count = 1

        while os.path.exists(destination):
            destination = os.path.join(
                new_folder, f"{base}_{count}{ext}"
            )
            count += 1

        shutil.move(file_path, destination)
        moved += 1

    return f"{moved} files organized successfully."