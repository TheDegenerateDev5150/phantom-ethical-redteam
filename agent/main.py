# agent/main.py
import os
import yaml
from anthropic import Anthropic
from tools import nuclei, sqlmap, ffuf, recon, cleanup
import logging

logging.basicConfig(filename='logs/agent.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

with open('config.yaml') as f:
    config = yaml.safe_load(f)

client = Anthropic(api_key=config['anthropic_api_key'])

TOOLS = {
    "run_nuclei": nuclei.run,
    "run_sqlmap": sqlmap.run,
    "run_ffuf": ffuf.run,
    "recon_domain": recon.domain,
    "cleanup_temp": cleanup.run,
    # add others
}

def main():
    print("🚀 Phantom - Claude Ethical RedTeam Started")
    scope = open("scopes/current_scope.md").read()
    print(f"Scope actif :\n{scope}")

    messages = [
        {"role": "user", "content": f"Scope actuel :\n{scope}\n\nStart the mission mission. Think step by step."}
    ]

    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # or opus
            max_tokens=4096,
            system=open("prompts/system_prompt.txt").read(),
            messages=messages,
            tools=[{"name": name, "input_schema": tool.__schema__} for name, tool in TOOLS.items()]  # to define in each tool
        )

        # Gestion tool calling Claude (standard Anthropic)
        for content in response.content:
            if content.type == "tool_use":
                tool_name = content.name
                args = content.input
                logging.info(f"Executing {tool_name} with {args}")
                result = TOOLS[tool_name](**args)
                messages.append({"role": "user", "content": f"Tool result: {result}"})
            else:
                print(content.text)
                messages.append({"role": "assistant", "content": content.text})

if __name__ == "__main__":
    main()
