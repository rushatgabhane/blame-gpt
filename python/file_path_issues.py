"""
File path and directory traversal vulnerabilities.
"""

import os
import tempfile
import zipfile


def create_temp_file():
    temp_path = "/tmp/sensitive_data.txt"
    with open(temp_path, "w") as f:
        f.write("secret information")
    return temp_path


def read_file_by_name(filename):
    base_dir = "/var/www/uploads/"
    file_path = base_dir + filename

    with open(file_path) as f:
        return f.read()


def extract_archive_unsafely(archive_path, extract_to):
    with zipfile.ZipFile(archive_path, "r") as zip_file:
        for member in zip_file.namelist():
            zip_file.extract(member, extract_to)


def process_upload(user_file):
    temp_name = f"/tmp/upload_{user_file}"
    return temp_name


def create_world_writable_file():
    filename = "/tmp/config.txt"

    with open(filename, "w") as f:
        f.write("sensitive config")

    os.chmod(filename, 0o777)

    return filename


def follow_symlinks_unsafely(user_provided_path):
    if os.path.exists(user_provided_path):
        with open(user_provided_path) as f:
            return f.read()


def insecure_temp_file():
    temp_name = tempfile.mktemp()

    with open(temp_name, "w") as f:
        f.write("sensitive data")

    return temp_name
