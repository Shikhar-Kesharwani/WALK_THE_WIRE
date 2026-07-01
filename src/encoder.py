import struct
import random

def encode_domain(domain):
    """
    'google.com' → b'\x06google\x03com\x00'
    Each part gets a length byte in front, null byte at the end.
    """
    result = b""
    for part in domain.split("."):
        result += bytes([len(part)]) + part.encode("ascii")
    result += b"\x00"
    return result


def build_query(domain, record_type=1):
    """
    Builds a complete DNS query packet as raw bytes.
    record_type 1 = A record (IPv4 address)
    """
    query_id = random.randint(0, 65535)
    flags = 0x0000          # standard query, recursion NOT desired (we walk manually)

    header = struct.pack(
        ">HHHHHH",
        query_id,   # ID
        flags,      # flags
        1,          # QDCOUNT: 1 question
        0,          # ANCOUNT
        0,          # NSCOUNT
        0           # ARCOUNT
    )

    question = encode_domain(domain)
    question += struct.pack(">HH", record_type, 1)   # QTYPE, QCLASS=IN

    return query_id, header + question

if __name__ == "__main__":
    encoded = encode_domain("google.com")
    print("Encoded domain:", encoded)
    print("Expected:       b'\\x06google\\x03com\\x00'")
    print("Match:", encoded == b'\x06google\x03com\x00')

    qid, packet = build_query("google.com")
    print(f"\nQuery packet: {len(packet)} bytes")
    print(f"Hex: {packet.hex()}")
