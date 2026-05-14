# Publishing

This project is packaged for PyPI as `claude-for-claude`.
The console script exposed by the package is `clfc`.

## Preflight

Run from the repository root:

```powershell
git status --short --branch
python -m unittest discover -v
```

Confirm the version is updated in both files:

- `pyproject.toml`
- `clfc/__init__.py`

## Build

Clean old local artifacts:

```powershell
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue
```

Build source and wheel distributions:

```powershell
python -m build
```

Validate package metadata:

```powershell
python -m twine check dist/*
```

## Local Wheel Smoke Test

Create a clean virtual environment and install the wheel:

```powershell
$venv = Join-Path $env:TEMP "clfc-wheel-test"
Remove-Item -Recurse -Force $venv -ErrorAction SilentlyContinue
python -m venv $venv
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install (Get-ChildItem dist\*.whl | Select-Object -First 1).FullName
& "$venv\Scripts\clfc.exe" --help
& "$venv\Scripts\clfc.exe" doctor
```

`doctor` may warn if Claude Code or Ollama is missing on the test machine. The command should still start and report useful diagnostics.

## Upload To TestPyPI

Use a TestPyPI API token. Do not commit tokens or `.pypirc` files.

```powershell
python -m twine upload --repository testpypi dist/*
```

Then install from TestPyPI:

```powershell
py -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ claude-for-claude
clfc --help
```

## Upload To PyPI

Use a PyPI API token:

```powershell
python -m twine upload dist/*
```

After upload:

```powershell
py -m pip install --upgrade claude-for-claude
clfc --help
clfc doctor
```

## Release Checklist

1. Update version in `pyproject.toml` and `clfc/__init__.py`.
2. Run tests.
3. Build with `python -m build`.
4. Run `python -m twine check dist/*`.
5. Smoke test the wheel in a clean virtual environment.
6. Upload to TestPyPI if desired.
7. Upload to PyPI.
8. Create and push a matching Git tag.
