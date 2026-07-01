import socket
from src.encoder import build_query
from src.parser import parse_response

def test_google_dns():
    """
    Integration test to query 8.8.8.8 for google.com and parse the response.
    This validates that our parser works on real-world DNS responses.
    """
    qid, packet = build_query("google.com")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    
    try:
        sock.sendto(packet, ("8.8.8.8", 53))
        data, _ = sock.recvfrom(1024)
    except socket.timeout:
        pytest.skip("Could not reach 8.8.8.8")
    finally:
        sock.close()

    result = parse_response(data)
    assert result["header"]["answers"] > 0
    assert len(result["answers"]) > 0
    
    # At least one answer should be an A record (type 1)
    a_records = [ans for ans in result["answers"] if ans["type"] == 1]
    assert len(a_records) > 0
    assert a_records[0]["name"] == "google.com"

if __name__ == "__main__":
    test_google_dns()
    print("test_google_dns passed (manually executed).")
