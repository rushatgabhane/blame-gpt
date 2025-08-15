"""
Test file with various Python security vulnerabilities for Bandit to detect.
This file is used for testing the security analysis pipeline.
"""

import hashlib
import pickle
import subprocess


# B101: Hardcoded password
def connect_to_database():
    password = "admin123"  # High severity - hardcoded password
    return f"postgresql://user:{password}@localhost/db"


# B301: Pickle usage vulnerability
def load_user_data(data):
    return pickle.loads(data)  # High severity - arbitrary code execution


# B404/B603: Subprocess with shell injection risk
def run_user_command(user_input):
    # Medium severity - subprocess with user input
    result = subprocess.call(f"ls {user_input}", shell=True)
    return result


# B307: Use of eval
def calculate_expression(expr):
    # Medium severity - eval with user input
    return eval(expr)


# B324: Weak cryptographic hash
def hash_password(password):
    # Medium severity - MD5 is cryptographically weak
    return hashlib.md5(password.encode()).hexdigest()


# B608: SQL injection via string formatting
def get_user_by_id(user_id):
    # Medium severity - SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = '%s'" % user_id
    return query


# B102: Test for exec usage
def execute_code(code_string):
    # High severity - exec with user input
    exec(code_string)


# B110: Try/except pass (information disclosure)
def risky_operation():
    try:
        # Some operation that might fail
        result = 1 / 0
    except:
        pass  # Medium severity - bare except clause


# B506: Test for yaml.load
def load_config(yaml_string):
    import yaml

    # Medium severity - unsafe YAML loading
    return yaml.load(yaml_string)


# B201: Flask debug mode
def create_app():
    from flask import Flask

    app = Flask(__name__)
    app.run(debug=True)  # Medium severity - debug mode in production


if __name__ == "__main__":
    # Trigger some vulnerabilities for testing
    print(connect_to_database())
    print(hash_password("test123"))
    print(get_user_by_id("1' OR '1'='1"))
