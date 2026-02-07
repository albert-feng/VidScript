import sys
import os
from pathlib import Path

# 将项目根目录添加到 python path，以便能找到 src
root_path = Path(__file__).resolve().parent
sys.path.append(str(root_path))

from src.ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
