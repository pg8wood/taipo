#!/bin/bash

set -e

echo "📦 Setting up taipo..."

# Create virtual environment and install dependencies
echo "Creating virtual environment..."
rm -rf ./.venv

# Try default python3 first, then fallback to macOS system python3 if needed
python3 -m venv ./.venv 2>/dev/null || {
  echo "⚠️  Default 'python3' failed (likely a pre-release Homebrew/ensurepip issue)."
  echo "🔄 Falling back to macOS system '/usr/bin/python3'..."
  rm -rf ./.venv
  /usr/bin/python3 -m venv ./.venv
} || {
  echo "❌ Failed to create virtual environment with system Python as well."
  exit 1
}
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r ./requirements.txt

# Ensure taipo.py is executable
chmod +x ./taipo.py

# Prompt for mode selection
echo ""
echo "🤖 Choose your taipo mode:"
echo "1) Manual - Ask before running any command (default)"
echo "2) Smart - Run automatically if AI is confident, ask if unsure"
echo "3) Autonomous - Run commands automatically without asking ⚠️"
echo ""
echo "⚠️  Warning: Autonomous mode will execute any command the AI suggests without confirmation!"
echo ""
read -p "Select mode (1-3) [1]: " mode_choice

case $mode_choice in
  2)
    mode="smart"
    ;;
  3)
    mode="autonomous"
    ;;
  *)
    mode="manual"
    ;;
esac

echo "✅ Selected mode: $mode"

# Prompt for LLM provider
echo ""
echo "🧠 Choose your LLM Provider:"
echo "1) Ollama - Run models locally, 100% free and open-source (default)"
echo "2) OpenAI - Use ChatGPT cloud API (requires paid API key)"
echo ""
read -p "Select provider (1-2) [1]: " provider_choice

case $provider_choice in
  2)
    provider="openai"
    echo ""
    read -p "OpenAI Model [gpt-4o-mini]: " openai_model
    openai_model="${openai_model:-gpt-4o-mini}"
    ;;
  *)
    provider="ollama"
    echo ""
    read -p "Ollama URL [http://localhost:11434/api/chat]: " ollama_url
    ollama_url="${ollama_url:-http://localhost:11434/api/chat}"
    
    echo ""
    echo "💡 Choose a local Ollama model. Recommended models for your machine:"
    echo "  - qwen2.5-coder:14b  (Recommended default - extremely fast & accurate)"
    echo "  - qwen2.5-coder:32b  (Smarter, runs beautifully on M4 Max with 128GB RAM)"
    echo "  - llama3.3           (Large 70B model - highly capable, requires significant RAM)"
    echo ""
    read -p "Ollama Model [qwen2.5-coder:14b]: " ollama_model
    ollama_model="${ollama_model:-qwen2.5-coder:14b}"
    ;;
esac

# Create config.json
CONFIG_DIR="$HOME/.config/taipo"
mkdir -p "$CONFIG_DIR"

# Write config.json to new location
cat > "$CONFIG_DIR/config.json" << EOF
{
  "mode": "$mode",
  "version": "1.0",
  "provider": "$provider",
  "ollama": {
    "url": "${ollama_url:-http://localhost:11434/api/chat}",
    "model": "${ollama_model:-qwen2.5-coder:14b}"
  },
  "openai": {
    "model": "${openai_model:-gpt-4o-mini}"
  }
}
EOF

echo "📝 Created $CONFIG_DIR/config.json"

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
if [ "$provider" = "ollama" ]; then
  echo "👉 Make sure Ollama is running and you have downloaded your model:"
  echo "   ollama run $ollama_model"
else
  echo "👉 Don't forget to add your OPENAI_API_KEY to your shell config (e.g. .zshrc) and source it or restart your shell!"
fi