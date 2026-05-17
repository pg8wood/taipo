#!/usr/bin/env python3

import sys
import os
import json
import subprocess
import re
import urllib.request
import urllib.error
import difflib
from yaspin import yaspin

DEBUG_MODE = os.getenv("TAIPO_DEBUG") == "1"

def style_command(text: str) -> str:
    return f"\033[1m\033[92m{text}\033[0m"  # bold + green

def load_config() -> dict:
    """Load configuration from config.json"""
    config_path = os.path.expanduser("~/.config/taipo/config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError):
        return {"mode": "manual", "version": "1.0"}

class LLMProvider:
    """Base class for shell auto-correction agents."""
    def get_suggestion(self, command: str, close_matches: list[str], smart_mode: bool = False) -> tuple[str, float]:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    """OpenAI API Provider."""
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    def get_suggestion(self, command: str, close_matches: list[str], smart_mode: bool = False) -> tuple[str, float]:
        try:
            from openai import OpenAI
        except ImportError:
            print("❌ Please install the `openai` python package to use the OpenAI provider.")
            print("👉 Run: pip install openai")
            sys.exit(1)

        if not self.api_key:
            print("❌ Please set your OPENAI_API_KEY in your environment.")
            sys.exit(1)

        if smart_mode:
            prompt = (
                f"The command `{command}` was entered in a Unix shell but is not recognized. "
                "Respond with ONLY a JSON object containing:\n"
                "1. 'command': the corrected command.\n"
                "2. 'confidence': a number between 0.0 and 1.0 indicating your confidence in this correction\n"
                "Example: {\"command\": \"git status\", \"confidence\": 0.95}\n"
                "If you cannot confidently fix it, use a low confidence score (0.0-0.3).\n"
                f"The most similar known commands to '{command}' are: {close_matches}"
            )
        else:
            prompt = (
                f"The command `{command}` was entered in a Unix shell but is not recognized. "
                "If it's a typo, respond only with the corrected command. "
                "If it cannot be confidently fixed, respond with a general suggestion. "
                "No explanations or extra text—just a corrected command.\n"
                f"The most similar known commands to '{command}' are: {close_matches}"
            )

        if DEBUG_MODE:
            print("\033[94m🐛 [TAIPO_DEBUG] OpenAI prompt:\n" + prompt + "\033[0m")

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        content = response.choices[0].message.content
        if not content:
            return "", 0.0

        if smart_mode:
            try:
                data = json.loads(content.strip())
                return data.get("command", ""), data.get("confidence", 0.0)
            except json.JSONDecodeError:
                # Fallback if model fails to output valid JSON
                return content.strip(), 0.5
        else:
            return content.strip(), 1.0

class OllamaProvider(LLMProvider):
    """Local Ollama Provider."""
    def __init__(self, url: str, model: str):
        self.url = url
        self.model = model

    def get_suggestion(self, command: str, close_matches: list[str], smart_mode: bool = False) -> tuple[str, float]:
        if smart_mode:
            prompt = (
                f"The command `{command}` was entered in a Unix shell but is not recognized. "
                "Respond with ONLY a JSON object containing:\n"
                "1. 'command': the corrected command.\n"
                "2. 'confidence': a number between 0.0 and 1.0 indicating your confidence in this correction\n"
                "Example: {\"command\": \"git status\", \"confidence\": 0.95}\n"
                "If you cannot confidently fix it, use a low confidence score (0.0-0.3).\n"
                f"The most similar known commands to '{command}' are: {close_matches}"
            )
        else:
            prompt = (
                f"The command `{command}` was entered in a Unix shell but is not recognized. "
                "If it's a typo, respond only with the corrected command. "
                "If it cannot be confidently fixed, respond with a general suggestion. "
                "No explanations or extra text—just a corrected command.\n"
                f"The most similar known commands to '{command}' are: {close_matches}"
            )

        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] Ollama prompt:\n{prompt}\033[0m")

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are a helpful shell assistant. You correct terminal command typos."},
                {"role": "user", "content": prompt}
            ],
            "options": {
                "temperature": 0.2
            }
        }

        if smart_mode:
            payload["format"] = "json"

        try:
            req = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["message"]["content"]
        except Exception as e:
            raise RuntimeError(
                f"Ollama request to {self.url} failed.\n"
                f"Please ensure Ollama is running and that you have pulled the '{self.model}' model (e.g., `ollama pull {self.model}`).\n"
                f"Error details: {e}"
            )

        if not content:
            return "", 0.0

        if smart_mode:
            try:
                # Clean up any potential markdown block markers if present
                clean_content = content.strip()
                if clean_content.startswith("```"):
                    start = clean_content.find("{")
                    end = clean_content.rfind("}")
                    if start != -1 and end != -1:
                        clean_content = clean_content[start:end+1]
                data = json.loads(clean_content)
                return data.get("command", ""), data.get("confidence", 0.0)
            except json.JSONDecodeError:
                return content.strip(), 0.5
        else:
            clean_content = content.strip()
            # If the model wrapped the result in backticks, extract it
            if clean_content.startswith("`") and clean_content.endswith("`"):
                clean_content = clean_content[1:-1].strip()
            return clean_content, 1.0

def get_provider(config: dict) -> LLMProvider:
    """Resolve and return the appropriate LLM provider based on environment and config."""
    provider_type = os.getenv("TAIPO_PROVIDER")
    if not provider_type:
        provider_type = config.get("provider")

    # Fallback/backward compatibility check
    if not provider_type:
        if os.getenv("OPENAI_API_KEY"):
            provider_type = "openai"
        else:
            provider_type = "ollama"

    provider_type = provider_type.lower()

    if provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        openai_config = config.get("openai", {})
        model = os.getenv("OPENAI_MODEL") or openai_config.get("model") or "gpt-4"
        return OpenAIProvider(api_key=api_key, model=model)
    elif provider_type == "ollama":
        ollama_config = config.get("ollama", {})
        url = os.getenv("OLLAMA_URL") or ollama_config.get("url") or "http://localhost:11434/api/chat"
        model = os.getenv("OLLAMA_MODEL") or ollama_config.get("model") or "qwen2.5-coder:14b"
        return OllamaProvider(url=url, model=model)
    else:
        print(f"❌ Unknown LLM provider '{provider_type}' specified.")
        print("👉 Supported providers: 'openai', 'ollama'")
        sys.exit(1)

def extract_command(text: str) -> str:
    match = re.search(r"`([^`]+)`", text) or re.search(r'"([^"]+)"', text)
    return match.group(1).strip() if match else text.strip()

def execute_command(command: str) -> bool:
    """Execute the given command and return success status"""
    print(f"\nExecuting {style_command(command)}")
    print()  # Visual separator before command output
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def process_suggested_command(command: str, mode: str, confidence: float = 1.0) -> bool:
    """Process the suggested command based on mode"""
    if mode == "manual":
        print(f"✔ Suggestion: {style_command(command)}")
        confirm = input(f"\n⚡ Run {style_command(command)}? (y/N): ").strip().lower()
        if confirm == "y":
            return execute_command(command)
        else:
            print("👍 Skipped.")
            return False
    
    elif mode == "autonomous":
        return execute_command(command)
    
    elif mode == "smart":
        confidence_threshold = 0.9  # Run automatically if confidence >= 90%
        
        if confidence >= confidence_threshold:
            print(f"✔ Suggestion: {style_command(command)} (confidence: {confidence:.1%})")
            return execute_command(command)
        else:
            print(f"✔ Suggestion: {style_command(command)} (confidence: {confidence:.1%})")
            print(f"🤔 Low confidence ({confidence:.1%}) - asking for confirmation")
            confirm = input(f"\n⚡ Run {style_command(command)}? (y/N): ").strip().lower()
            if confirm == "y":
                return execute_command(command)
            else:
                print("👍 Skipped.")
                return False
    
    return False

def main():
    try:
        full_input = os.getenv("TAIPO_ORIGINAL_COMMAND")
        args = full_input.strip() if full_input else " ".join(sys.argv[1:])

        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] Failed command:\n{args}\033[0m")

        available_commands_string = subprocess.getoutput("zsh -c 'print -rlo -- $commands:t'")

        config = load_config()
        mode = config.get("mode", "manual")

        with yaspin(text=f"[taipo] Trying to make sense of: '{args}'...", color="cyan", side="right") as spinner:
            provider = get_provider(config)
            command_list = available_commands_string.splitlines()
            base_command = args.split()[0] if args else ""
            close_matches = difflib.get_close_matches(base_command, command_list, n=5, cutoff=0.75)
            
            suggestion, confidence = provider.get_suggestion(
                args, 
                close_matches=close_matches, 
                smart_mode=(mode == "smart")
            )
            spinner.ok("✔")

        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] LLM response:\n{suggestion}\033[0m")

        maybe_command = extract_command(suggestion)
        
        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] Mode: {mode}\033[0m")

        # Run command based on mode
        success = process_suggested_command(maybe_command, mode, confidence)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(127)

    except KeyboardInterrupt:
        print("\nCanceled. Taipo will remember that.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Taipo error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()