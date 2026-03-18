import logging
from tools import ALL_TOOLS
from tools import nuclei, sqlmap, ffuf, recon, set_phish, cleanup, bettercap, zphisher, cyberstrike, read_log, payloads, human_input, report
from providers import get_provider


class AgentClient:

    def __init__(self, config: dict):
        self.provider = get_provider(config)
        self.raw_tools = ALL_TOOLS
        self.tools = self.provider.convert_tools(ALL_TOOLS)
        self.mapping = {
            "run_nuclei": nuclei.run,
            "run_sqlmap": sqlmap.run,
            "run_ffuf": ffuf.run,
            "run_recon": recon.run,
            "generate_phish_template": set_phish.run,
            "cleanup_temp": cleanup.run,
            "run_bettercap": bettercap.run,
            "generate_zphisher_template": zphisher.run,
            "run_cyberstrike": cyberstrike.run,
            "read_log": read_log.run,
            "run_payloads": payloads.run,
            "request_human_input": human_input.run,
            "generate_report": report.run,
        }

    def _compact_old_tool_results(self, messages: list, keep_last_n: int = 3) -> list:
        """Truncate content of old tool_result blocks to avoid context overflow."""
        # Identify indices of turns that contain tool results
        tool_result_indices = [
            i for i, m in enumerate(messages)
            if m.get("role") == "user"
            and isinstance(m.get("content"), list)
            and any(b.get("type") == "tool_result" for b in m["content"])
        ]
        # Only compact turns older than the last keep_last_n tool result turns
        to_compact = set(tool_result_indices[:-keep_last_n]) if len(tool_result_indices) > keep_last_n else set()
        if not to_compact:
            return messages

        result = []
        for i, msg in enumerate(messages):
            if i in to_compact:
                compacted = []
                for block in msg["content"]:
                    if block.get("type") == "tool_result":
                        content = str(block.get("content", ""))
                        if len(content) > 400:
                            block = {**block, "content": content[:400] + " [...compacted]"}
                    compacted.append(block)
                result.append({**msg, "content": compacted})
            else:
                result.append(msg)
        return result

    def think(self, messages: list, system_prompt: str) -> list:
        messages = self._compact_old_tool_results(messages)
        text_blocks, tool_calls = self.provider.call(messages, system_prompt, self.tools)

        new_messages = messages.copy()

        # Build assistant message (single block per turn)
        assistant_blocks = []
        for text in text_blocks:
            print("🤖 Phantom :", text)
            logging.info(f"Reasoning: {text[:300]}...")
            assistant_blocks.append({"type": "text", "text": text})

        for tc in tool_calls:
            assistant_blocks.append({
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": tc["input"],
            })

        if assistant_blocks:
            new_messages.append({"role": "assistant", "content": assistant_blocks})

        # Execute tools — collect all results in a single user message
        if tool_calls:
            tool_results = []
            for tc in tool_calls:
                logging.info(f"🔧 Execution : {tc['name']}")
                tool_func = self.mapping.get(tc["name"])

                if tool_func:
                    try:
                        result = tool_func(**tc["input"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tc["id"],
                            "content": str(result),
                        })
                    except Exception as e:
                        error_msg = f"Erreur {tc['name']}: {str(e)}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tc["id"],
                            "content": error_msg,
                        })
                        logging.error(error_msg)
                else:
                    logging.warning(f"Tool inconnu : {tc['name']}")

            if tool_results:
                new_messages.append({"role": "user", "content": tool_results})

        return new_messages
