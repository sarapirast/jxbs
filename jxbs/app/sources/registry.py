"""
Registry of active job sources
"""
from .adzuna import AdzunaSource
from .jsearch import JSearchSource

# Instantiated lazily in get_active_sources() so a missing API key for one
# source doesn't crash the whole app at import time.
_SOURCE_CLASSES = {
    "adzuna": AdzunaSource,
    "jsearch": JSearchSource,
}


def get_active_sources() -> list:
    """
    Returns instances of every source with valid credentials configured.
    Sources missing env vars are skipped with a warning
    """
    active = []
    for name, cls in _SOURCE_CLASSES.items():
        try:
            active.append(cls())
        except RuntimeError as e:
            print(f"[sources] skipping {name}: {e}")
    return active
