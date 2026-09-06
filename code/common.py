"""Shared paths and credential loading. Keys are read from disk and never printed."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, INTERIM, FINAL, OUT = ROOT/"data"/"raw", ROOT/"data"/"interim", ROOT/"data"/"final", ROOT/"out"
for d in (RAW, INTERIM, FINAL, OUT): d.mkdir(parents=True, exist_ok=True)

HOME = pathlib.Path.home()
# Searched in order. Whichever exists first wins, so the key can live wherever
# is most convenient. The project 'keys' dir is listed for discoverability.
SEARCH_DIRS = [
    ROOT/"keys",
    HOME/".config"/"research",
    HOME/"Desktop",
    HOME,
]
(ROOT/"keys").mkdir(exist_ok=True)

def _candidates(name):
    for d in SEARCH_DIRS:
        for fn in (f"{name}.key", f"{name}.txt", f"{name}.key.txt", name):
            yield d/fn

def load_key(name):
    """Return the credential named `name`, or None. Never logs the value."""
    for p in _candidates(name):
        if p.is_file():
            v = p.read_text().strip().strip('"').strip("'")
            if v:
                return v
    return None

def key_location(name):
    """Where the key was found, for logging. Returns the path, not the value."""
    for p in _candidates(name):
        if p.is_file() and p.read_text().strip():
            return p
    return None

def require_key(name):
    k = load_key(name)
    if not k:
        raise SystemExit(
            f"MISSING CREDENTIAL '{name}'. Put the key in a plain text file at any of:\n"
            + "\n".join(f"  {d}/{name}.key" for d in SEARCH_DIRS)
        )
    return k

SEED = 20260823  # fixed for the whole project; recorded in the pre-registration
