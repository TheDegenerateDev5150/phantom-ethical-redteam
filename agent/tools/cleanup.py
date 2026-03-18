import glob
import shutil
import os
import tempfile


def run() -> str:
    """
    Remove only Phantom's own temporary files.
    Preserves: logs/<session>/ directories (mission reports, scan results).
    Removes:   logs/temp/  and  /tmp/phantom_*
    """
    deleted = []
    errors = []

    # Explicit temp dir inside logs/ (never touches session subdirs)
    logs_temp = os.path.join("logs", "temp")
    if os.path.exists(logs_temp):
        try:
            shutil.rmtree(logs_temp)
            deleted.append(logs_temp)
        except Exception as e:
            errors.append(f"{logs_temp}: {e}")

    # OS temp directory — only phantom-prefixed entries
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
        return f"⚠️ Cleanup partial — deleted: {deleted}, errors: {errors}"
    if deleted:
        return f"✅ Temp files deleted: {deleted}\n   (Mission reports in logs/<session>/ are preserved)"
    return "✅ Nothing to clean (mission reports in logs/<session>/ preserved)"


TOOL_SPEC = {
    "name": "cleanup_temp",
    "description": (
        "Remove Phantom's own temporary files (logs/temp/, /tmp/phantom_*). "
        "Mission reports and scan results in logs/<session>/ are always preserved."
    ),
    "input_schema": {"type": "object", "properties": {}},
}
