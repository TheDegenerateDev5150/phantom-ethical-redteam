import google.generativeai as genai
from .base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):

    DEFAULT_MODEL = "gemini-1.5-pro"

    def __init__(self, api_key: str, model: str = None):
        genai.configure(api_key=api_key)
        self.model_name = model or self.DEFAULT_MODEL

    def convert_tools(self, tools: list) -> list:
        declarations = []
        for t in tools:
            # Strip 'default' keys — Gemini schema doesn't support them
            props = {
                k: {kk: vv for kk, vv in v.items() if kk != "default"}
                for k, v in t["input_schema"].get("properties", {}).items()
            }
            declarations.append(
                genai.protos.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            k: genai.protos.Schema(type=genai.protos.Type.STRING)
                            for k in props
                        },
                        required=t["input_schema"].get("required", []),
                    ),
                )
            )
        return [genai.protos.Tool(function_declarations=declarations)]

    def _to_provider_contents(self, messages: list) -> list:
        # Build a lookup: tool_use_id -> function_name (needed for function_response)
        id_to_name: dict = {}
        for msg in messages:
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if block.get("type") == "tool_use":
                        id_to_name[block["id"]] = block["name"]

        contents = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                if isinstance(content, str):
                    contents.append({"role": "user", "parts": [{"text": content}]})
                elif isinstance(content, list):
                    parts = []
                    for block in content:
                        if block.get("type") == "tool_result":
                            fn_name = id_to_name.get(block["tool_use_id"], "tool")
                            parts.append({
                                "function_response": {
                                    "name": fn_name,
                                    "response": {"result": block["content"]},
                                }
                            })
                    if parts:
                        contents.append({"role": "user", "parts": parts})

            elif role == "assistant":
                parts = []
                if isinstance(content, str):
                    parts.append({"text": content})
                elif isinstance(content, list):
                    for block in content:
                        if block.get("type") == "text":
                            parts.append({"text": block["text"]})
                        elif block.get("type") == "tool_use":
                            parts.append({
                                "function_call": {
                                    "name": block["name"],
                                    "args": block["input"],
                                }
                            })
                if parts:
                    contents.append({"role": "model", "parts": parts})

        return contents

    def call(self, messages: list, system_prompt: str, tools: list) -> tuple:
        model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=tools,
            system_instruction=system_prompt,
        )

        contents = self._to_provider_contents(messages)
        response = model.generate_content(contents)

        text_blocks = []
        tool_calls = []

        for part in response.parts:
            if hasattr(part, "text") and part.text:
                text_blocks.append(part.text)
            if hasattr(part, "function_call") and part.function_call.name:
                fc = part.function_call
                tool_calls.append({
                    "id": f"gemini-{fc.name}-{len(tool_calls)}",
                    "name": fc.name,
                    "input": dict(fc.args),
                })

        return text_blocks, tool_calls
