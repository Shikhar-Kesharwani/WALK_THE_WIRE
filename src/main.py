import time
import sys
import os

# Add the project root to the path so that src.* imports work correctly when running main.py directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.resolver import resolve

BANNER = """
╔══════════════════════════════════════════════╗
║        DNS Resolver — Built From Scratch     ║
║        No libraries. Pure Python + UDP.      ║
╚══════════════════════════════════════════════╝
"""

def resolve_with_trace(domain):
    print(f"\n{'─'*55}")
    print(f"  Query: {domain}")
    print(f"{'─'*55}")
    start = time.time()
    result = resolve(domain)
    elapsed = time.time() - start
    print(f"{'─'*55}")
    if result:
        print(f"  ✅  {domain} → {result}")
    else:
        print(f"  ❌  Could not resolve {domain}")
    print(f"  ⏱   {elapsed:.3f}s")
    print(f"{'─'*55}\n")
    return result


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    print(BANNER)

    domains = sys.argv[1:] if len(sys.argv) > 1 else [
        "google.com",
        "github.com",
        "twitter.com",
        "icrisat.org",
        "nonexistent-domain-xyz.com",    # test NXDOMAIN
    ]

    for domain in domains:
        resolve_with_trace(domain)
        time.sleep(0.5)
