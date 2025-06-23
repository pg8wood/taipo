#!/usr/bin/env python3

import sys
import os
from openai import OpenAI
import subprocess
import re

DEBUG_MODE = os.getenv("TAIPO_DEBUG") == "1"

def get_openai_response(command: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Please set your OPENAI_API_KEY in your environment.")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)

    prompt = (
        f"The command `{command}` was entered in a Unix shell but is not recognized. "
        "If it's a typo, respond only with the corrected command in backticks. "
        "If it cannot be confidently fixed, respond with a general suggestion. "
        "No explanations or extra text—just a corrected command or helpful suggestion."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()

def extract_command(text: str) -> str:
    match = re.search(r"`([^`]+)`", text) or re.search(r'"([^"]+)"', text)
    return match.group(1).strip() if match else text.strip()

def main():
    full_input = os.getenv("TAIPO_ORIGINAL_COMMAND")
    if full_input:
        args = full_input.strip()
    else:
        args = " ".join(sys.argv[1:])

    if DEBUG_MODE:
        print(f"\033[94m🐛 [TAIPO_DEBUG] Failed command:\n{args}\033[0m")

    failed_command = args.split()[0]
    print(f"taipo 🤖: Hmm… `{failed_command}`? Let me see...")

    try:
        suggestion = get_openai_response(args)
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        sys.exit(1)

    if DEBUG_MODE:
        print(f"\033[94m🐛 [TAIPO_DEBUG] OpenAI response:\n{suggestion}\033[0m")

    print(f"\n💡 Suggestion:\n{suggestion}")

    maybe_command = extract_command(suggestion)
    confirm = input(f"\n⚡ Run `{maybe_command}`? (y/N): ").strip().lower()
    if confirm == "y":
        print(f"\n🚀 Running: {maybe_command}")
        try:
            subprocess.run(maybe_command, shell=True, check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"❌ That didn't work: {e}")
            sys.exit(e.returncode)
    else:
        print("👍 Skipped. Hope the suggestion helped!")
        sys.exit(127)

if __name__ == "__main__":
    main()