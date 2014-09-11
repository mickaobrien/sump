import shutil
import os
from hashlib import md5

def move_file(original_path, new_path):
    shutil.move(original_path, new_path)

def get_all_files(src):
    all_files = []
    for root, dirs, files in os.walk(src):
        for f in files:
            all_files.append(os.path.join(root, f))
    return all_files

def move_all_files(src, dest):
    files = get_all_files(src)
    for f in files:
        new_file_path = f.replace(src, dest)
        make_dir(os.path.dirname(new_file_path))
        os.rename(f, new_file_path)

def hashify(s):
    return md5(s).hexdigest()

def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_dirs(paths):
    for path in paths:
        make_dir(path)
