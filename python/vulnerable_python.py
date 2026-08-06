"""
Test file with various Python security vulnerabilities for Bandit to detect.
This file is used for testing the security analysis pipeline.
"""

import hashlib
import pickle
import subprocess


def connect_to_database():
    password = "admin123"
    return f"postgresql://user:{password}@localhost/db"


def load_user_data(data):
    return pickle.loads(data)


def run_user_command(user_input):
    result = subprocess.call(f"ls {user_input}", shell=True)
    return result


def calculate_expression(expr):
    return eval(expr)


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def get_user_by_id(user_id):
    query = "SELECT * FROM users WHERE id = '%s'" % user_id
    return query


def execute_code(code_string):
    exec(code_string)


def risky_operation():
    try:
        result = 1 / 0
    except:
        pass


def load_config(yaml_string):
    import yaml
    return yaml.load(yaml_string)


def create_app():
    from flask import Flask

    app = Flask(__name__)
    app.run(debug=True)


if __name__ == "__main__":
    print(connect_to_database())
    print(hash_password("test123"))
    print(get_user_by_id("1' OR '1'='1"))
