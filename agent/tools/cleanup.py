"""Remove Phantom's temporary files (preserves mission reports)."""

import glob
import shutil
import os
import logging
import tempfile

logger = logging.getLogger(__name__)


def _secure_delete(path: str):
    """Overwrite file with zeros before deleting (prevents forensic recovery)."""
    try:
        size = os.path.getsize(path)
        with open(path, "wb") as f:
            f.write(b"\x00" * size)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass  # Best effort — still delete even if overwrite fails
    os.remove(path)


def run() -> str:
    deleted = []
    errors = []

    logs_temp = os.path.join("logs", "temp")
    if os.path.exists(logs_temp):
        try:
            shutil.rmtree(logs_temp)
            deleted.append(logs_temp)
        except Exception as e:
            errors.append(f"{logs_temp}: {e}")

    # Securely delete auth.json files (contain credentials)
    for auth_file in glob.glob(os.path.join("logs", "*", "auth.json")):
        try:
            _secure_delete(auth_file)
            deleted.append(auth_file)
        except Exception as e:
            errors.append(f"{auth_file}: {e}")

    tmp_dir = tempfile.gettempdir()
    for path in glob.glob(os.path.join(tmp_dir, "phantom_*")):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            deleted.append(path)
        except Exception as e:
            errors.append(f"{path}: {e}")

    if errors:
        logger.warning("Cleanup partial: deleted=%s, errors=%s", deleted, errors)
        return f"Cleanup partial \u2014 deleted: {deleted}, errors: {errors}"
    if deleted:
        logger.info("Cleanup: deleted %s", deleted)
        return f"Temp files deleted: {deleted}\n   (Mission reports in logs/<session>/ preserved)"
    return "Nothing to clean (mission reports in logs/<session>/ preserved)"


TOOL_SPEC = {
    "name": "cleanup_temp",
    "description": (
        "Remove Phantom's temporary files (logs/temp/, /tmp/phantom_*). "
        "Mission reports and scan results in logs/<session>/ are always preserved."
    ),
    "input_schema": {"type": "object", "properties": {}},
}
