import sys


def run(question: str) -> str:
    """Pause execution and ask the operator a question."""
    print(f"\n{'=' * 55}")
    print(f"  ❓ Phantom requests human input:")
    print(f"  {question}")
    print(f"{'=' * 55}")

    try:
        if not sys.stdin.isatty():
            return "⚠️ Human input requested but stdin is not a terminal (non-interactive mode)."
        answer = input("  Your answer: ").strip()
        print()
        return f"Human response: {answer}" if answer else "Human provided no response."
    except (EOFError, KeyboardInterrupt):
        return "Human input unavailable."


TOOL_SPEC = {
    "name": "request_human_input",
    "description": (
        "Pause and ask the operator a question requiring human judgment "
        "(scope clarification, attack confirmation, credential input, ambiguous target, etc.). "
        "Only use when genuinely blocked without human context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The specific question to ask the operator",
            }
        },
        "required": ["question"],
    },
}
