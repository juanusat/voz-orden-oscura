import os
import sys

# Allow running this file when cwd is ./backend by ensuring project root is on sys.path
here = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(here, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend import create_app
except Exception:
    # fallback if run as a module from backend folder
    from __init__ import create_app

app = create_app()

if __name__ == "__main__":
    app.run(port=5702, host="0.0.0.0", debug=True)
