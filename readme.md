# Setting up the Python virtual environment for the project

1. Create the venv (from your project folder)
```bash
python -m venv .venv

```
2. Activate the venv
```powershell
# PowerShell
.\.venv\Scripts\Activate
```
3. Use pip inside the venv
```bash
pip install <package>
pip install -r requirements.txt
pip freeze > requirements.txt
```
4. Deactivate
```bash
deactivate
```

# Creating a build version

1. First install all packages in the venv
```bash
pip install -r requirements.txt
```
2. Create the build via.:
```bash
pyinstaller --onefile --name ResolutionSwitcher --noconsole main.py
```