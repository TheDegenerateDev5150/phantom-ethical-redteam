import os
import subprocess
from .scope_checker import scope_guard
from .logs_helper import log_path


def run(url: str, level: int = 3, risk: int = 3, timeout: int = 300) -> str:
    guard = scope_guard(url)
    if guard:
        return guard

    output_dir = log_path("sqlmap")
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "sqlmap", "-u", url, "--batch",
        "--level", str(level), "--risk", str(risk),
        "--output-dir", output_dir,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return f"✅ sqlmap done\n{result.stdout[-500:]}"
    except subprocess.TimeoutExpired:
        return f"⚠️ sqlmap timed out after {timeout}s — increase timeout parameter if needed"
    except Exception as e:
        return f"❌ Error sqlmap : {str(e)}"


TOOL_SPEC = {
    "name": "run_sqlmap",
    "description": "Automated SQL injection detection and exploitation (level, risk and timeout configurable)",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "level": {"type": "integer", "default": 3},
            "risk": {"type": "integer", "default": 3},
            "timeout": {
                "type": "integer",
                "default": 300,
                "description": "Max execution time in seconds (default 300, increase for complex injections)",
            },
        },
        "required": ["url"],
    },
}
