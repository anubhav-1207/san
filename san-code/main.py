import sys
from pathlib import Path
from tui import SANEditor

if __name__ == "__main__":
    # doc: Creates a argument for:
    # python main.py <open_file_path>
    txt = ""
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.exists():
            txt = p.read_text()
    SANEditor(initial_text=txt).run()
