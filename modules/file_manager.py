import os
import shutil

CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx"],
    "Audio": [".mp3", ".wav", ".flac", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar"],
    "Code": [".py", ".js", ".html", ".css", ".cpp", ".c", ".java"]
}

def organize_folder(folder_path):
    if not os.path.exists(folder_path):
        return "Folder not found."
    moved = 0
    for f in os.listdir(folder_path):
        fp = os.path.join(folder_path, f)
        if os.path.isfile(fp):
            ext = os.path.splitext(f)[1].lower()
            for cat, exts in CATEGORIES.items():
                if ext in exts:
                    dest = os.path.join(folder_path, cat)
                    os.makedirs(dest, exist_ok=True)
                    try:
                        shutil.move(fp, os.path.join(dest, f))
                        moved += 1
                    except Exception:
                        pass
                    break
    return f"Organized {moved} files."

def find_large_files(folder_path, size_mb=100):
    found = []
    try:
        for root, _, files in os.walk(folder_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    size = os.path.getsize(fp) / (1024 * 1024)
                    if size >= size_mb:
                        found.append(f"{f} ({size:.1f}MB)")
                except Exception: pass
        return f"Found {len(found)} files: " + ", ".join(found[:5]) if found else "No large files."
    except Exception as e:
        return f"Error: {str(e)}"