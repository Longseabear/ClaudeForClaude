# Installation

ClaudeForClaude is published as the Python package `claude-for-claude`.
The installed command is `clfc`.

## Requirements

- Python 3.10 or newer
- Claude Code installed and available as `claude`
- Windows PowerShell is the primary supported shell
- Ollama is optional, but recommended when Claude Code is configured to use an Ollama Anthropic-compatible endpoint

Check Python:

```powershell
py --version
```

Check Claude Code:

```powershell
claude --version
```

## Install From PyPI

After the first release is uploaded to PyPI:

```powershell
py -m pip install --upgrade claude-for-claude
```

Then verify the CLI:

```powershell
clfc --help
clfc doctor
```

If PowerShell cannot find `clfc`, your Python Scripts directory is probably not on `PATH`.
You can still run the package directly:

```powershell
py -m clfc.cli.main --help
```

## Install With pipx

`pipx` is a good fit because CLFC is a command-line tool:

```powershell
py -m pip install --user pipx
py -m pipx ensurepath
pipx install claude-for-claude
```

Upgrade later:

```powershell
pipx upgrade claude-for-claude
```

## Install From GitHub

Use this before a PyPI release exists, or when testing `main`:

```powershell
py -m pip install --upgrade "git+https://github.com/Longseabear/ClaudeForClaude.git"
```

## Editable Local Install

For development inside a clone:

```powershell
git clone https://github.com/Longseabear/ClaudeForClaude.git
cd ClaudeForClaude
py -m pip install -e .
clfc --help
```

The repository also includes `.\clfc.cmd` for local Windows development, but PyPI installs should use the generated `clfc` command.

## First Run

From the workspace you want CLFC to manage:

```powershell
clfc doctor
clfc init
clfc index
clfc list
clfc open
```

To start a new Claude Code session with CLFC launcher defaults:

```powershell
clfc interactive
```

To resume an indexed session:

```powershell
clfc resume <session-id-or-prefix>
```

## Uninstall

For pip:

```powershell
py -m pip uninstall claude-for-claude
```

For pipx:

```powershell
pipx uninstall claude-for-claude
```

Uninstalling the package does not delete Claude Code transcripts or CLFC runtime metadata under `.clfc`, `%LOCALAPPDATA%\clfc`, or `%USERPROFILE%\.clfc`.
