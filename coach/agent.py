import os
import yaml
import uuid
import datetime
import json
from pathlib import Path

from prompts import SYSTEM_PROMPT, START_PROMPT, DISPATCHER_PROMPT
from memory_manager import MemoryManager
from mode_classifier import classify, effort_tier
from tool_registry import execute as execute_tool, registered_tools

BASE = Path(__file__).parent
CONFIG_PATH = BASE / "config.yaml"


class CoachAgent:
    def __init__(self):
        self.config = self._load_config()
        self.memory = MemoryManager()
        self.model_type = self.config.get("model_type", "local")
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.api_url = self.config.get("api_url", "http://localhost:11434/v1/chat/completions")
        self.model_name = self.config.get("model_name", "llama3")
        self.temp = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 2048)
        self._phase = None

    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def call_model(self, system, user):
        import requests
        headers = {"Content-Type": "application/json"}
        if self.model_type != "local" and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": self.temp,
            "max_tokens": self.max_tokens
        }
        resp = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def dispatch_tool(self, user_input):
        prompt = DISPATCHER_PROMPT.format(query=user_input)
        try:
            raw_response = self.call_model("You are a strict text classification router.", prompt)
            tool_name = None
            args = []
            reason = ""

            for line in raw_response.splitlines():
                line = line.strip()
                if line.startswith("TOOL:"):
                    val = line.split(":", 1)[1].strip()
                    if val.lower() not in ("none", "null", ""):
                        tool_name = val
                elif line.startswith("ARG:"):
                    val = line.split(":", 1)[1].strip()
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    elif val.startswith("'") and val.endswith("'"):
                        val = val[1:-1]
                    args.append(val)
                elif line.startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            return tool_name, args, reason
        except Exception as e:
            print(f"DEBUG: LLM dispatch failed ({e}).")
            return None, [], f"Dispatch failed: {e}"

    def _build_context(self, user_input, tool_name="", tool_output=""):
        context = self.memory.get_context_for_query(user_input)
        parts = [context] if context else []
        if tool_output:
            parts.append(f"EXECUTED TOOL ({tool_name}):\n{tool_output}")
        return "\n\n".join(parts)

    def handle_minimal(self, user_input):
        response = self.call_model(SYSTEM_PROMPT, user_input)
        return response

    def handle_native(self, user_input):
        tool_name, args, reason = self.dispatch_tool(user_input)
        tool_output = ""
        if tool_name:
            print(f"DEBUG: Tool: {tool_name} args={args} reason={reason}")
            tool_output = execute_tool(tool_name, args)
            print(f"DEBUG: Output:\n{tool_output[:300]}\n")

        context = self._build_context(user_input, tool_name, tool_output)
        full_system = f"{SYSTEM_PROMPT}\n\n{context}" if context else SYSTEM_PROMPT
        return self.call_model(full_system, user_input)

    def handle_algorithm(self, user_input, classification):
        effort = classification.get("effort", "E1")
        mode_block = (
            f"TASK MODE: ALGORITHM\n"
            f"INTENT: {classification['intent']}\n"
            f"EFFORT TIER: {effort}\n"
            f"Execute the 7-phase protocol: OBSERVE -> THINK -> PLAN -> BUILD -> EXECUTE -> VERIFY -> LEARN\n"
            f"Phase transitions are one-way. Never skip phases."
        )
        tool_name, args, reason = self.dispatch_tool(user_input)
        tool_output = ""
        if tool_name:
            print(f"DEBUG: Tool: {tool_name} args={args} reason={reason}")
            tool_output = execute_tool(tool_name, args)
            print(f"DEBUG: Output:\n{tool_output[:300]}\n")

        context = self._build_context(user_input, tool_name, tool_output)
        full_system = f"{SYSTEM_PROMPT}\n\n{mode_block}\n\n{context}"
        return self.call_model(full_system, user_input)

    def process_input(self, user_input):
        classification = classify(user_input)
        classification["effort"] = effort_tier(user_input)
        mode = classification["mode"]
        intent = classification["intent"]
        effort = classification["effort"]

        print(f"MODE: {mode} | intent={intent} | effort={effort}")

        if mode == "MINIMAL":
            return self.handle_minimal(user_input)
        if mode == "ALGORITHM":
            return self.handle_algorithm(user_input, classification)

        return self.handle_native(user_input)


def main_loop():
    agent = CoachAgent()
    print("\n=== Coach 2.0 (Deep Memory Active) ===")

    initial_context = agent.memory.get_context_for_query("morning")
    greeting = agent.call_model(SYSTEM_PROMPT, START_PROMPT.format(memory=initial_context))
    print(f"\n{greeting}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("exit", "quit", "bye"):
            break

        if not user_input:
            continue

        response = agent.process_input(user_input)
        print(f"\n=== Coach ===\n{response}\n=============\n")


if __name__ == '__main__':
    main_loop()
