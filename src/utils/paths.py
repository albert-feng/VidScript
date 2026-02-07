import sys
from pathlib import Path


def get_root_path() -> Path:
    """
    获取项目根目录。
    兼容开发环境和打包环境 (PyInstaller / Nuitka)。
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的环境
        # PyInstaller 使用 sys._MEIPASS
        # Nuitka 打包后 sys.argv[0] 或 sys.executable 指向程序路径
        return Path(sys.executable).parent
    else:
        # 开发环境，假设当前文件在 src/utils/ 下
        return Path(__file__).resolve().parent.parent.parent


def get_bin_path(filename: str = "") -> Path:
    """获取 bin 目录下的文件路径"""
    path = get_root_path() / "bin"
    if filename:
        path = path / filename
    return path


def get_assets_path(filename: str = "") -> Path:
    """获取 assets 目录下的文件路径"""
    path = get_root_path() / "assets"
    if filename:
        path = path / filename
    return path


def get_temp_path(filename: str = "") -> Path:
    """获取 temp 目录下的文件路径"""
    path = get_root_path() / "temp"
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    if filename:
        path = path / filename
    return path


def get_config_path(filename: str = "") -> Path:
    """获取 config 目录下的文件路径"""
    path = get_root_path() / "config"
    if filename:
        path = path / filename
    return path
