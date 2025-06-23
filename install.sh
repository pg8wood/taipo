#!/bin/bash

set -e

echo "📦 Setting up taipo..."

# Create virtual environment and install dependencies
python3 -m venv ./.venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r ./requirements.txt

# Ensure taipo.py is executable
chmod +x ./taipo.py

# Prompt for mode selection
echo ""
echo "🤖 Choose your taipo mode:"
echo "1) Manual - Ask before running any command (default)"
echo "2) Automatic - Run commands automatically without asking"
echo ""
read -p "Select mode (1-2) [1]: " mode_choice

case $mode_choice in
  2)
    mode="automatic"
    ;;
  *)
    mode="manual"
    ;;
esac

echo "✅ Selected mode: $mode"

# Create config.json
cat > config.json << EOF
{
  "mode": "$mode",
  "version": "1.0"
}
EOF

echo "📝 Created config.json with $mode mode"

# Add sourcing of local handler.zsh to .zshrc if not already present
if ! grep -q 'source.*taipo.*command_not_found_handler.zsh' ~/.zshrc; then
  echo '' >> ~/.zshrc
  echo '# taipo command-not-found hook' >> ~/.zshrc
  echo "source $(pwd)/command_not_found_handler.zsh" >> ~/.zshrc
  echo "✅ Hook added to .zshrc"
else
  echo "🔁 Hook already present in .zshrc"
fi

source ~/.zshrc

echo "🎉 taipo is installed!"
echo "👉 Don't forget to add your OPENAI_API_KEY to your shell config (e.g. .zshrc) and source it or restart your shell!"