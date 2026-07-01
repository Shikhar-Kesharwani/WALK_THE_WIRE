import time

class DNSCache:
    def __init__(self):
        self._store = {}    # key → (value, expires_at)

    def get(self, domain, record_type=1):
        key = f"{domain}:{record_type}"
        if key in self._store:
            value, expires_at = self._store[key]
            if time.time() < expires_at:
                return value
            else:
                del self._store[key]   # expired
        return None

    def set(self, domain, record_type, value, ttl=300):
        key = f"{domain}:{record_type}"
        self._store[key] = (value, time.time() + ttl)

    def stats(self):
        now = time.time()
        live = sum(1 for _, (_, exp) in self._store.items() if exp > now)
        return {"total": len(self._store), "live": live}
