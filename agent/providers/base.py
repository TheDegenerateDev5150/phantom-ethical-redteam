from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):

    @abstractmethod
    def convert_tools(self, tools: list) -> list:
        """Convert Anthropic-format tool specs to this provider's format."""

    @abstractmethod
    def call(self, messages: list, system_prompt: str, tools: list) -> tuple:
        """
        Make one API call.
        Args:
            messages: conversation in standard (Anthropic-compatible) format
            system_prompt: system string
            tools: tools already converted by convert_tools()
        Returns:
            (text_blocks: list[str], tool_calls: list[dict])
            tool_calls items: {"id": str, "name": str, "input": dict}
        """
