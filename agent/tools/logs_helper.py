import os
import glob
from datetime import datetime


def init_session() -> str:
    """Create a timestamped session directory under logs/ and store it in env."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join("logs", ts)
    os.makedirs(session_dir, exist_ok=True)
    os.environ["PHANTOM_SESSION_DIR"] = session_dir
    return session_dir


def log_path(filename: str) -> str:
    """Return a session-scoped path under logs/<session>/<filename>, creating dirs as needed."""
    session_dir = os.environ.get("PHANTOM_SESSION_DIR", "logs")
    path = os.path.join(session_dir, filename)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def find_latest(filename: str) -> str | None:
    """Search for filename in the current session dir, then in all session dirs (newest first)."""
    # Current session first
    current = log_path(filename)
    if os.path.exists(current):
        return current

    # Walk all logs/<session>/ subdirs, newest first
    pattern = os.path.join("logs", "*", filename)
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if matches:
        return matches[0]

    # Root logs/ fallback
    root = os.path.join("logs", filename)
    return root if os.path.exists(root) else None
