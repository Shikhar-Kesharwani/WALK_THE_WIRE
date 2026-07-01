import pytest
from src.encoder import encode_domain, build_query

def test_encode_domain():
    assert encode_domain("google.com") == b'\x06google\x03com\x00'
    assert encode_domain("www.example.org") == b'\x03www\x07example\x03org\x00'

def test_build_query():
    qid, packet = build_query("google.com")
    assert len(packet) == 28
    # The flags should be 0x0000
    assert packet[2:4] == b'\x00\x00'
    # QDCOUNT is 1
    assert packet[4:6] == b'\x00\x01'
    # Check the question part
    assert packet[12:24] == b'\x06google\x03com\x00'
