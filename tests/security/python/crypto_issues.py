"""
Cryptographic security issues for testing.
"""

import hashlib
import ssl

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


# B303: Weak cryptographic key
def generate_weak_key():
    # Medium severity - weak random number generation
    import random

    return random.randint(1000, 9999)


# B324: Multiple weak hash functions
def weak_hashing_examples():
    data = b"sensitive data"

    # Medium severity - MD5
    md5_hash = hashlib.md5(data).hexdigest()

    # Medium severity - SHA1
    sha1_hash = hashlib.sha1(data).hexdigest()

    return md5_hash, sha1_hash


# B502: SSL/TLS certificate verification disabled
def insecure_ssl_context():
    # High severity - SSL verification disabled
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


# B304: Insecure cipher usage
def weak_encryption():
    # Medium severity - DES is weak encryption
    key = b"12345678"  # 8 bytes for DES
    cipher = Cipher(
        algorithms.TripleDES(key),
        modes.ECB(),  # ECB mode is also insecure
        backend=default_backend(),
    )
    return cipher


# B305: Insecure cipher mode
def insecure_cipher_mode():
    # Medium severity - ECB mode
    key = b"sixteen byte key"
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    return cipher


# B313: XML parsing vulnerabilities
def parse_xml_unsafely(xml_data):
    import xml.etree.ElementTree as ET

    # Medium severity - XML external entity processing enabled
    return ET.fromstring(xml_data)
