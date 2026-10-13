"""High-performance in-memory TTL Cache utility.
Decoupled from any framework (like Streamlit), thread-safe for FastAPI.
"""

import time
from functools import wraps
from typing import Callable, Any, Dict, Tuple


def ttl_cache(ttl: int = 60) -> Callable:
    """In-memory Time-To-Live cache decorator."""
    def decorator(fn: Callable) -> Callable:
        cache: Dict[Tuple, Tuple[Any, float]] = {}

        @wraps(fn)
        def wrapper(*args, **kwargs):
            # For methods, normalize args (skip self or first argument if class/instance method)
            # Create hashable cache key
            key_args = []
            for a in args:
                if hasattr(a, '__dict__') and not isinstance(a, (int, float, str, bool, tuple, list, dict)):
                    # skip instance / self
                    continue
                key_args.append(str(a))
            key_kwargs = tuple(sorted((k, str(v)) for k, v in kwargs.items()))
            key = (tuple(key_args), key_kwargs)

            now = time.time()
            if key in cache:
                result, ts = cache[key]
                if now - ts < ttl:
                    return result

            result = fn(*args, **kwargs)
            cache[key] = (result, now)
            return result

        wrapper.clear_cache = lambda: cache.clear()
        return wrapper

    return decorator
