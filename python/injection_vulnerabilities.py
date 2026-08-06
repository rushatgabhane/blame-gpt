"""
Injection vulnerability examples for security testing.
"""

import os
import sqlite3
import subprocess


def execute_system_command(filename):
    cmd = f"cat /etc/passwd; rm {filename}"
    return subprocess.call(cmd, shell=True)


def dangerous_system_call(user_path):
    os.system(f"ls -la {user_path}")


def sql_injection_examples():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, email TEXT)")

    def vulnerable_query1(user_id):
        query = "SELECT * FROM users WHERE id = %s" % user_id
        return cursor.execute(query)

    def vulnerable_query2(username):
        query = f"SELECT * FROM users WHERE name = '{username}'"
        return cursor.execute(query)

    def vulnerable_query3(email):
        query = f"SELECT * FROM users WHERE email = '{email}'"
        return cursor.execute(query)

    vulnerable_query1("1 OR 1=1")
    vulnerable_query2("admin' OR '1'='1")
    vulnerable_query3("test@test.com' OR 1=1 --")


def partial_path_execution():
    subprocess.call(["rm", "-rf", "/tmp/test"])


def start_with_partial_path(file_to_delete):
    subprocess.Popen(["rm", file_to_delete])


def ldap_injection(username):
    ldap_filter = f"(&(objectClass=user)(uid={username}))"
    return ldap_filter


def xpath_injection(user_input):
    xpath_query = f"//user[name/text()='{user_input}' and password/text()='secret']"
    return xpath_query
