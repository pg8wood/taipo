# taipo
An AI-powered oopsie catcher. Bevause typing ish ard and ths hsell is mean. 

![taipo demo](demo.gif)

---

## 🧠 What is taipo?

**taipo** watches for commands that fail in your shell (`command not found`) and asks AI to figure out what you meant to type.

If you typo something like:

```bash
❯ got status
```

taipo steps in with:

```sh
[taipo] Trying to make sense of: 'got status'... ✔
⚡ Run git status? (y/N):
```

And if you're in **autonomous mode**, it runs the fixed command for you:

```sh
[taipo] Trying to make sense of: 'got status'... ✔
🚀 Executing git status
```

## 🔧 Installation

- Clone the repo and run the install script:
```bash
git clone https://github.com/pg8wood/taipo.git
cd taipo
./install.sh
```
The installer will prompt you to select your preferred LLM provider, mode, and model settings.

## 🧠 LLM Providers

**taipo** supports multiple LLM backends to fit your workflow. You can run completely locally and privately for free, or connect to cloud services:

### 1. Ollama (Default - Local & Free)
Ollama runs high-performance models locally on your own machine. No API fees, no rate limits, and absolute privacy.
* **Recommended Models:**
  * `qwen2.5-coder:14b` (Default) - Incredibly fast, highly optimized for CLI and coding.
  * `qwen2.5-coder:32b` - A great step up for powerful Apple Silicon Macs (like M4 Max with 64GB/128GB RAM).
  * `llama3.3` (70B) - Extreme reasoning, perfect if you have plenty of RAM to spare!

Make sure you pull the model first before running:
```bash
ollama pull qwen2.5-coder:14b
```

### 2. OpenAI (Cloud - Paid)
Use cloud-hosted GPT models. Requires a paid API key.
* **Recommended Models:** `gpt-4o-mini`, `gpt-4`.

---

## ⚙️ Configuration

You can customize **taipo** by editing `~/.config/taipo/config.json`. Here is a complete example configuration:

```json
{
  "mode": "manual",
  "version": "1.0",
  "provider": "ollama",
  "ollama": {
    "url": "http://localhost:11434/api/chat",
    "model": "qwen2.5-coder:14b"
  },
  "openai": {
    "model": "gpt-4o-mini"
  }
}
```

### 🔌 Environment Variables

For maximum flexibility, you can override any configuration option using environment variables in your shell config (e.g. `~/.zshrc`):

| Variable | Description | Default |
| --- | --- | --- |
| `TAIPO_PROVIDER` | LLM backend to use (`ollama` or `openai`) | Loaded from `config.json` |
| `OLLAMA_MODEL` | Local Ollama model name | `qwen2.5-coder:14b` |
| `OLLAMA_URL` | Local Ollama API endpoint | `http://localhost:11434/api/chat` |
| `OPENAI_API_KEY` | OpenAI authentication key | None |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| `TAIPO_DEBUG` | Set to `1` to output internal prompts and raw LLM answers | `0` |

---

## 💡 Modes

- 🟢 **manual**: You'll be prompted before any suggested command is run.
- 🟣 **smart**: Asks the AI how confident it is about the typo correction. If 90% confident or greater, the command is run auto-magically. Otherwise, you'll be asked to confirm.
- 🔴 **autonomous**: Suggestions are executed immediately.

> [!CAUTION]
> Smart and autonomous modes will **immediately** execute generated code. Use at your own risk.

You can change the mode later by editing `~/.config/taipo/config.json` or re-running the install script.

## 🐛 Debug Mode

Enable debugging by setting an environment variable:

```bash
export TAIPO_DEBUG=1
```

This will print:
- The failed command
- The raw prompt sent to the LLM provider
- The raw response

Helpful for devs or the curious 😎

## 💻 Requirements

- Python 3.7+
- `zsh`
- Local **Ollama** running OR an **OpenAI API Key** (set `OPENAI_API_KEY` in environment)