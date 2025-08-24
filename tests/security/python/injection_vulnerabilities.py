"""
Injection vulnerability examples for security testing.
"""

import os
import sqlite3
import subprocess


# B602: Subprocess with shell=True
def execute_system_command(filename):
    # High severity - command injection via shell
    cmd = f"cat /etc/passwd; rm {filename}"
    return subprocess.call(cmd, shell=True)


# B605: Shell command from string
def dangerous_system_call(user_path):
    # Medium severity - os.system with user input
    os.system(f"ls -la {user_path}")


# B608: SQL injection through string formatting
def sql_injection_examples():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create test table
    cursor.execute("CREATE TABLE users (id INTEGER, name TEXT, email TEXT)")

    def vulnerable_query1(user_id):
        # Medium severity - % formatting
        query = "SELECT * FROM users WHERE id = %s" % user_id
        return cursor.execute(query)

    def vulnerable_query2(username):
        # Medium severity - .format()
        query = f"SELECT * FROM users WHERE name = '{username}'"
        return cursor.execute(query)

    def vulnerable_query3(email):
        # Medium severity - f-string
        query = f"SELECT * FROM users WHERE email = '{email}'"
        return cursor.execute(query)

    # Test with malicious inputs
    vulnerable_query1("1 OR 1=1")
    vulnerable_query2("admin' OR '1'='1")
    vulnerable_query3("test@test.com' OR 1=1 --")


# B606: Process execution without full path
def partial_path_execution():
    # Medium severity - using partial executable path
    subprocess.call(["rm", "-rf", "/tmp/test"])


# B607: Starting process with partial path
def start_with_partial_path(file_to_delete):
    # Medium severity - partial path vulnerability
    subprocess.Popen(["rm", file_to_delete])


# LDAP injection example
def ldap_injection(username):
    # Medium severity - LDAP injection
    ldap_filter = f"(&(objectClass=user)(uid={username}))"
    return ldap_filter


# XPath injection
def xpath_injection(user_input):
    # Medium severity - XPath injection
    xpath_query = f"//user[name/text()='{user_input}' and password/text()='secret']"
    return xpath_query
