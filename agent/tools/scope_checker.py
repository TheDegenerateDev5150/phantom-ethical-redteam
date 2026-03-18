import re
from urllib.parse import urlparse


def load_scope_targets(scope_file: str = "scopes/current_scope.md") -> list:
    """Extract all URLs, domains and IPs from the scope file."""
    try:
        with open(scope_file, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return []

    targets = []

    # Extract URLs → keep netloc (host[:port])
    for url in re.findall(r'https?://[^\s\'"<>\]]+', content):
        netloc = urlparse(url).netloc
        if netloc:
            targets.append(netloc.lower().split(":")[0])

    # Extract bare IPs / CIDRs
    for ip in re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d+)?\b', content):
        targets.append(ip)

    return list(set(targets))


def is_in_scope(target: str, scope_file: str = "scopes/current_scope.md") -> bool:
    """
    Return True if target is within the authorized scope.
    Permissive (returns True) if scope cannot be parsed.
    """
    scope_targets = load_scope_targets(scope_file)
    if not scope_targets:
        return True  # No parseable scope — handled by main.py

    # Normalize target: extract domain/IP
    t = target.lower().strip()
    if t.startswith("http"):
        t = urlparse(t).netloc or t
    t = t.split(":")[0].split("/")[0]  # strip port and path

    for s in scope_targets:
        s = s.split(":")[0]
        if t == s:
            return True
        if t.endswith("." + s):   # subdomain of scope
            return True
        if s.endswith("." + t):   # scope is subdomain of target (rare but valid)
            return True

    return False


def scope_guard(target: str, scope_file: str = "scopes/current_scope.md") -> str | None:
    """
    Return an error string if target is out of scope, None if OK.
    Use at the top of every tool that accepts a target.
    """
    if not is_in_scope(target, scope_file):
        authorized = load_scope_targets(scope_file)
        return (
            f"❌ SCOPE VIOLATION: '{target}' is not in the authorized scope.\n"
            f"   Authorized targets: {authorized}\n"
            f"   Check scopes/current_scope.md."
        )
    return None
