"""
Rate limiter setup using slowapi.
Import `limiter` and use @limiter.limit("N/minute") on route handlers.
Apply the SlowAPIMiddleware in main.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate-limit by client IP address.
# Swap to a user-identity key function once HttpOnly cookie auth is adopted.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
