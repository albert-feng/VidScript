import PyInstaller.__main__
import shutil
import os
from pathlib import Path


def build():
    # 1. 运行 PyInstaller
    print("开始打包...")

    # 基础参数
    args = [
        "main.py",
        "--name=VidScript",
        "--onedir",  # 目录模式，方便放外部配置文件
        "--noconsole",  # 无控制台窗口
        "--clean",  # 清理缓存
        "--noconfirm",  # 覆盖输出目录不询问
    ]

    # 隐藏导入 (解决常见库的动态加载问题)
    hidden_imports = [
        "yt_dlp",
        "customtkinter",
        "openai",
        "oss2",
        "dashscope",
        "yaml",  # pyyaml
        "dotenv",  # python-dotenv
    ]
    for imp in hidden_imports:
        args.append(f"--hidden-import={imp}")

    # 收集数据文件 (特别是 customtkinter 的主题文件)
    args.append("--collect-all=customtkinter")
    args.append("--collect-all=dashscope")  # dashscope 可能有依赖

    PyInstaller.__main__.run(args)

    # 2. 复制配置文件到 dist/VidScript/
    print("正在复制配置文件...")
    dist_dir = Path("dist/VidScript")

    # 确保输出目录存在
    if not dist_dir.exists():
        print(f"错误: 打包目录 {dist_dir} 不存在")
        return

    files_to_copy = [".env.example", ".env", "prompts.yaml"]

    for filename in files_to_copy:
        src = Path(filename)
        dst = dist_dir / filename
        if src.exists():
            print(f"复制 {src} -> {dst}")
            shutil.copy2(src, dst)
        else:
            print(f"警告: 源文件 {src} 不存在，跳过复制")

    # 复制目录
    dirs_to_copy = ["bin", "assets"]

    for dirname in dirs_to_copy:
        src = Path(dirname)
        dst = dist_dir / dirname
        if src.exists():
            print(f"复制目录 {src} -> {dst}")
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            print(f"警告: 源目录 {src} 不存在，跳过复制")

    print("打包完成！输出目录: dist/VidScript")
    print("请进入 dist/VidScript 目录运行 VidScript.exe")


if __name__ == "__main__":
    build()
