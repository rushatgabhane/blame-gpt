"""
Cryptographic security issues for testing.
"""

import hashlib
import ssl

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def generate_weak_key():
    import random

    return random.randint(1000, 9999)


def weak_hashing_examples():
    data = b"sensitive data"

    md5_hash = hashlib.md5(data).hexdigest()

    sha1_hash = hashlib.sha1(data).hexdigest()

    return md5_hash, sha1_hash


def insecure_ssl_context():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def weak_encryption():
    key = b"12345678"
    cipher = Cipher(
        algorithms.TripleDES(key),
        modes.ECB(),
        backend=default_backend(),
    )
    return cipher


def insecure_cipher_mode():
    key = b"sixteen byte key"
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    return cipher


def parse_xml_unsafely(xml_data):
    import xml.etree.ElementTree as ET
    return ET.fromstring(xml_data)
