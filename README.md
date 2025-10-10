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
- Set your `OPENAI_API_KEY` as an environment variable. Keep it somewhere safe.

## 💻 Usage 
**taipo** will automatically be invoked any time your shell doesn't recognize a command ✨ no command line muscle memory changes needed!

### Smarter suggestions

To improve ergonomics, taipo now considers:

- Commands discoverable on your `PATH` (via zsh `$commands`)
- Recent entries from your `~/.zsh_history` to surface locally-invoked scripts or tools (including `./scripts/foo` becoming `foo`)

This helps corrections prefer things you actually use, even if they are project scripts or binaries not globally installed.

## 💡 Modes

- 🟢 **manual**: You'll be prompted before any suggested command is run.
- 🟣 **smart**: Asks the AI how confident it is about the typo correction. If 90% confient or greater, the command is run auto-magically. Otherwise, you'll be asked to confirm.
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
- The raw prompt sent to OpenAI
- The raw response

Helpful for devs or the curious 😎


## 💻 Requirements

- Python 3.7+
- `zsh`
- An OpenAI API key (set `OPENAI_API_KEY` in your environment)