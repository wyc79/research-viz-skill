# Python environment management

The skill's policy is **always ask before installing**. Detect what's missing, present a small menu, and let the user pick. Concrete commands and the pieces you'd put in the shell wrappers below.

## Detection

```bash
which python3 && python3 --version
python3 -c "import sys; print(sys.executable, sys.prefix)"
echo "VIRTUAL_ENV=${VIRTUAL_ENV:-(none)}"
ls -d ./.venv 2>/dev/null || true
ls -d ./visualizations/.venv 2>/dev/null || true
```

Importability check:

```bash
python3 -c "
import importlib, sys
mods = ['pandas','numpy','matplotlib','seaborn','streamlit','altair','openpyxl']
missing = [m for m in mods if importlib.util.find_spec(m) is None]
print('missing:', missing)
"
```

Only install the modules required by the subskill the user is invoking. Minimum sets:

- **parser**: `pandas`, `numpy`, `openpyxl`
- **plot_gen**: `pandas`, `numpy`, `matplotlib`, `seaborn`
- **interactive**: `pandas`, `streamlit` (+ `altair` only if altair charts will be used)

## The four options to offer the user

### 1. Install into the current env

```bash
python3 -m pip install pandas numpy matplotlib seaborn openpyxl
```

Append `streamlit altair` for the interactive subskill. Use `--user` if you don't have permission to write to the system site-packages and there's no venv active.

### 2. Create a venv at `visualizations/.venv` and install there (recommended for reproducibility)

```bash
python3 -m venv visualizations/.venv
source visualizations/.venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install pandas numpy matplotlib seaborn openpyxl streamlit altair
```

The bundled `parse_input.sh` / `generate_plot.sh` / `interactive_page.sh` already contain a snippet that activates `visualizations/.venv` automatically if it exists:

```bash
if [ -f "${VIZ_DIR}/.venv/bin/activate" ]; then
    source "${VIZ_DIR}/.venv/bin/activate"
fi
```

So once the venv is created and populated, the `.sh` wrappers Just Work.

### 3. Create a fresh conda env

```bash
conda create -n research-viz python=3.11 -y
conda activate research-viz
python -m pip install pandas numpy matplotlib seaborn openpyxl streamlit altair
```

If the user goes this route, the shell wrappers won't auto-activate the conda env (we'd need to know the env name). Update the wrappers to do:

```bash
# Insert near the top of each .sh wrapper
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate <env-name>
```

Or document in `info/how_to_use.md` that the user must `conda activate <env-name>` themselves before running the wrappers.

### 4. Skip — user installs themselves

Pause and wait for the user to confirm before retrying. Do not silently fall back to a different option.

## After installing

After installing, **rerun the importability check** to confirm everything is actually importable in the env you'll execute against. Then write a one-line entry under "Python env" in `info/context.md` so future agents know which env to activate.

## Pinning

For reproducibility, after a successful install, generate a freeze:

```bash
python -m pip freeze > visualizations/requirements.txt
```

Useful when sharing the workspace.
