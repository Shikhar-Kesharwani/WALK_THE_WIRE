import socket
from src.encoder import build_query
from src.parser import parse_response
from src.cache import DNSCache

ROOT_SERVERS = [
    "198.41.0.4",     # a.root-servers.net
    "199.9.14.201",   # b.root-servers.net
    "192.33.4.12",    # c.root-servers.net
    "199.7.91.13",    # d.root-servers.net
    "192.203.230.10", # e.root-servers.net
]

_cache = DNSCache()

def send_query(ip, domain, record_type=1):
    """Send one DNS query to one nameserver. Returns parsed response."""
    qid, packet = build_query(domain, record_type)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(packet, (ip, 53))
        data, _ = sock.recvfrom(1024)
    finally:
        sock.close()
    return parse_response(data)


def resolve(domain, record_type=1, depth=0, trace=None):
    """
    Iterative DNS resolution.
    Starts at a root server, follows referrals manually.
    """
    def log(msg):
        print(msg)
        if trace is not None:
            trace.append(msg)

    # Check cache first
    cached = _cache.get(domain, record_type)
    if cached:
        log(f"[CACHE HIT] {domain} → {cached}")
        return cached
        
    indent = "  " * depth
    nameserver_ip = ROOT_SERVERS[0]

    log(f"\n{indent}Resolving: {domain}")

    for step in range(20):      # max 20 hops before giving up
        log(f"{indent}[Step {step+1}] → {nameserver_ip}")

        try:
            response = send_query(nameserver_ip, domain, record_type)
        except socket.timeout:
            log(f"{indent}  Timeout. Trying next root server.")
            nameserver_ip = ROOT_SERVERS[1]
            continue
        except Exception as e:
            log(f"{indent}  Error: {e}")
            return None

        # Check response code — 3 = NXDOMAIN (domain doesn't exist)
        if response["header"]["rcode"] == 3:
            log(f"{indent}  NXDOMAIN — {domain} does not exist")
            return None

        # CASE 1: Got a direct answer
        for ans in response["answers"]:
            if ans["type"] == record_type:
                log(f"{indent}  ✓ Answer: {domain} → {ans['data']}")
                _cache.set(domain, record_type, ans["data"], ttl=ans["ttl"])
                return ans["data"]
            elif ans["type"] == 5:      # CNAME — follow the alias
                cname = ans["data"]
                log(f"{indent}  → CNAME alias: {domain} → {cname}")
                resolved = resolve(cname, record_type, depth + 1, trace)
                if resolved:
                    _cache.set(domain, record_type, resolved, ttl=ans["ttl"])
                return resolved

        # CASE 2: Referral with glue records (nameserver IP is given directly)
        glue = {
            r["name"]: r["data"]
            for r in response["additional"]
            if r["type"] == 1
        }
        ns_records = [r for r in response["authority"] if r["type"] == 2]

        for ns_record in ns_records:
            ns_name = ns_record["data"]
            if ns_name in glue:
                ns_ip = glue[ns_name]
                log(f"{indent}  → Referred to {ns_name} ({ns_ip}) [glue]")
                nameserver_ip = ns_ip
                break
        else:
            # CASE 3: Referral but no glue — must resolve the NS name first
            if ns_records:
                ns_name = ns_records[0]["data"]
                log(f"{indent}  → Referred to {ns_name} (no glue — resolving it first)")
                ns_ip = resolve(ns_name, record_type=1, depth=depth+1, trace=trace)
                if ns_ip:
                    nameserver_ip = ns_ip
                    continue
            log(f"{indent}  Dead end — no referral found.")
            return None

    log(f"{indent}  Max steps reached.")
    return None

if __name__ == "__main__":
    result = resolve("github.com")
    print(f"\nFINAL: github.com → {result}")
