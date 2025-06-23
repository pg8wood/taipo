#!/usr/bin/env python3

import sys
import os
from openai import OpenAI
import subprocess
import re

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
    if len(sys.argv) < 2:
        print("Usage: taipo.py <command>")
        sys.exit(1)

    original_args = sys.argv[1:]
    original_command = " ".join(original_args)
    print(f"taipo 🤖: Hmm… `{original_command}`? Let me see...")

    try:
        suggestion = get_openai_response(original_args[0])
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        sys.exit(1)

    print(f"\n💡 Suggestion:\n{suggestion}")

    fixed_command = extract_command(suggestion)
    rest_of_args = original_args[1:]
    full_command = " ".join([fixed_command] + rest_of_args)

    confirm = input(f"\n⚡ Run `{full_command}`? (y/N): ").strip().lower()
    if confirm == "y":
        try:
            subprocess.run(full_command, shell=True, check=True)
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"❌ That didn't work: {e}")
            sys.exit(e.returncode)
    else:
        print("👍 Skipped. Hope the suggestion helped!")
        sys.exit(127)

if __name__ == "__main__":
    main()