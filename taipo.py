#!/usr/bin/env python3

import sys
import os
import json
from openai import OpenAI
import subprocess
import re
from yaspin import yaspin

DEBUG_MODE = os.getenv("TAIPO_DEBUG") == "1"

def style_command(text: str) -> str:
    return f"\033[1m\033[92m{text}\033[0m"  # bold + green

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get("mode", "manual")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "manual"  # Default to manual mode

def get_openai_response(command: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set your OPENAI_API_KEY in your environment.")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)

    prompt = (
        f"The command `{command}` was entered in a Unix shell but is not recognized. "
        "If it's a typo, respond only with the corrected command. "
        "If it cannot be confidently fixed, respond with a general suggestion. "
        "No explanations or extra text—just a corrected command or helpful suggestion."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    return content.strip() if content else ""

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

def process_suggested_command(command: str, mode: str) -> bool:
    """Process the suggested command based on mode"""
    if mode == "manual":
        print(f"✔ Suggestion: {style_command(command)}")
        confirm = input(f"\n⚡ Run {style_command(command)}? (y/N): ").strip().lower()
        if confirm == "y":
            return execute_command(command)
        else:
            print("👍 Skipped.")
            return False
    
    elif mode == "automatic":
        return execute_command(command)
    
    return False

def main():
    try:
        full_input = os.getenv("TAIPO_ORIGINAL_COMMAND")
        args = full_input.strip() if full_input else " ".join(sys.argv[1:])

        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] Failed command:\n{args}\033[0m")

        failed_command = args.split()[0]
        with yaspin(text=f"[taipo] Trying to make sense of: '{args}'...", color="cyan", side="right") as spinner:
            suggestion = get_openai_response(args)
            spinner.ok("✔")

        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] OpenAI response:\n{suggestion}\033[0m")

        maybe_command = extract_command(suggestion)
        
        # Load mode from config
        mode = load_config()
        
        if DEBUG_MODE:
            print(f"\033[94m🐛 [TAIPO_DEBUG] Mode: {mode}\033[0m")

        # Run command based on mode
        success = process_suggested_command(maybe_command, mode)
        
        if success:
            sys.exit(0)
        else:
            sys.exit(127)

    except KeyboardInterrupt:
        print("\nCanceled. Taipo will remember that.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()