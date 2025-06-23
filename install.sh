#!/bin/bash

set -e

echo "📦 Setting up taipo..."

# Create virtual environment and install dependencies
python3 -m venv ./.venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r ./requirements.txt

# Ensure taipo.py is executable
chmod +x ./taipo.py

# Add sourcing of local handler.zsh to .zshrc if not already present
if ! grep -q 'source.*taipo.*command_not_found_handler.zsh' ~/.zshrc; then
  echo '' >> ~/.zshrc
  echo '# taipo command-not-found hook' >> ~/.zshrc
  echo "source $(pwd)/command_not_found_handler.zsh" >> ~/.zshrc
  echo "✅ Hook added to .zshrc"
else
  echo "🔁 Hook already present in .zshrc"
fi

echo "🎉 taipo is installed!"
echo "👉 Don't forget to add your OPENAI_API_KEY to your shell config (e.g. .zshrc) and source it or restart your shell!"