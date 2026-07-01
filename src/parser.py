import struct
import socket

def decode_domain(data, offset):
    """
    Reads a domain name from raw bytes at position `offset`.
    Handles compression pointers (0xC0...).
    Returns (domain_string, new_offset_after_name).
    """
    labels = []
    jumped = False
    original_offset = offset
    max_jumps = 10       # safety: prevent infinite pointer loops
    jumps = 0

    while True:
        if offset >= len(data):
            raise ValueError(f"offset {offset} out of bounds")

        length = data[offset]

        if length & 0xC0 == 0xC0:
            # Compression pointer
            if offset + 1 >= len(data):
                raise ValueError("Pointer out of bounds")
            pointer = struct.unpack(">H", data[offset:offset+2])[0]
            pointer = pointer & 0x3FFF      # strip top 2 bits
            if not jumped:
                original_offset = offset + 2
            offset = pointer
            jumped = True
            jumps += 1
            if jumps > max_jumps:
                raise ValueError("Too many pointer jumps — possible loop")
            continue

        offset += 1

        if length == 0:
            break   # end of name

        labels.append(data[offset:offset+length].decode("ascii"))
        offset += length

    domain = ".".join(labels)
    return domain, (original_offset if jumped else offset)


def parse_header(data):
    """Parse the fixed 12-byte DNS header."""
    id_, flags, qdcount, ancount, nscount, arcount = struct.unpack(
        ">HHHHHH", data[:12]
    )
    return {
        "id": id_,
        "flags": flags,
        "questions": qdcount,
        "answers": ancount,
        "authority": nscount,
        "additional": arcount,
        "rcode": flags & 0x000F    # bottom 4 bits = response code
    }


def parse_record(data, offset):
    """
    Parse one resource record (answer / authority / additional).
    Returns (record_dict, new_offset).
    """
    name, offset = decode_domain(data, offset)
    rtype, rclass, ttl, rdlength = struct.unpack(">HHIH", data[offset:offset+10])
    offset += 10
    rdata_raw = data[offset:offset+rdlength]

    if rtype == 1:      # A record — IPv4
        rdata = socket.inet_ntoa(rdata_raw)
    elif rtype == 2:    # NS record — nameserver name
        rdata, _ = decode_domain(data, offset)
    elif rtype == 5:    # CNAME
        rdata, _ = decode_domain(data, offset)
    elif rtype == 28:   # AAAA — IPv6
        rdata = socket.inet_ntop(socket.AF_INET6, rdata_raw)
    else:
        rdata = rdata_raw.hex()

    offset += rdlength
    return {"name": name, "type": rtype, "ttl": ttl, "data": rdata}, offset


def parse_response(data):
    """Parse a full DNS response into a readable dict."""
    header = parse_header(data)
    offset = 12

    # Skip past the question section (we already know what we asked)
    for _ in range(header["questions"]):
        _, offset = decode_domain(data, offset)
        offset += 4     # skip qtype + qclass

    answers, authority, additional = [], [], []

    for _ in range(header["answers"]):
        rec, offset = parse_record(data, offset)
        answers.append(rec)

    for _ in range(header["authority"]):
        rec, offset = parse_record(data, offset)
        authority.append(rec)

    for _ in range(header["additional"]):
        rec, offset = parse_record(data, offset)
        additional.append(rec)

    return {
        "header": header,
        "answers": answers,
        "authority": authority,
        "additional": additional
    }
