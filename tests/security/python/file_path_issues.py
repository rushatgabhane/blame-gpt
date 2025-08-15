"""
File path and directory traversal vulnerabilities.
"""

import os
import tempfile
import zipfile


# B108: Hardcoded /tmp usage
def create_temp_file():
    # Medium severity - hardcoded tmp path
    temp_path = "/tmp/sensitive_data.txt"
    with open(temp_path, "w") as f:
        f.write("secret information")
    return temp_path


# Directory traversal vulnerability
def read_file_by_name(filename):
    # High severity - directory traversal
    # User could pass "../../../etc/passwd"
    base_dir = "/var/www/uploads/"
    file_path = base_dir + filename

    with open(file_path) as f:
        return f.read()


# B202: Tarfile with unsafe extraction
def extract_archive_unsafely(archive_path, extract_to):
    # High severity - zip slip vulnerability
    with zipfile.ZipFile(archive_path, "r") as zip_file:
        for member in zip_file.namelist():
            # No path validation - allows directory traversal
            zip_file.extract(member, extract_to)


# B101: Hardcoded temporary file paths
def process_upload(user_file):
    # Medium severity - predictable temp file names
    temp_name = f"/tmp/upload_{user_file}"
    return temp_name


# File permission issues
def create_world_writable_file():
    # Medium severity - overly permissive file permissions
    filename = "/tmp/config.txt"

    # Create file
    with open(filename, "w") as f:
        f.write("sensitive config")

    # Make it world writable (777)
    os.chmod(filename, 0o777)

    return filename


# Symlink attack vulnerability
def follow_symlinks_unsafely(user_provided_path):
    # Medium severity - following symlinks without validation
    if os.path.exists(user_provided_path):
        # Could be a symlink to /etc/passwd
        with open(user_provided_path) as f:
            return f.read()


# Race condition in temp file creation
def insecure_temp_file():
    # Medium severity - race condition
    temp_name = tempfile.mktemp()  # Deprecated, insecure

    with open(temp_name, "w") as f:
        f.write("sensitive data")

    return temp_name
