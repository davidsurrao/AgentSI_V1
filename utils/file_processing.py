import os

def read_file(file_path):
    """Reads a file and returns its content."""
    if not os.path.exists(file_path):
        return "File not found"
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def write_file(file_path, content):
    """Writes content to a file."""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    return "File written successfully"
