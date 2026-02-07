# VidScript

**VidScript** 是一款基于 Python 的桌面应用程序，旨在简化视频下载、音频提取以及利用 AI 大模型生成/润色讲稿的工作流程。

## 🚀 功能特性

- **视频下载**：集成 `yt-dlp`，支持多平台视频下载。
- **音频处理**：自动提取视频音频（需 FFmpeg 支持）。
- **AI 赋能**：调用 ASR (语音转文字) 和 LLM (大语言模型) API 自动生成讲稿。
- **现代化 UI**：使用 `CustomTkinter` 构建的高性能、深色模式响应式界面。
- **独立运行**：支持单文件打包，内置二进制依赖管理。

## 🛠️ 技术栈

- **语言**: Python 3.11+
- **包管理**: [uv](https://github.com/astral-sh/uv) (推荐)
- **界面**: CustomTkinter
- **核心**: yt-dlp, requests, httpx
- **配置**: python-dotenv
- **打包**: Nuitka (推荐) / PyInstaller

## 📂 项目结构

```text
VidScript/
├── assets/          # 静态资源（图标、Logo）
├── bin/             # 外部二进制文件（ffmpeg.exe, koushare-dl.exe）
├── config/          # 配置文件
├── src/             # 源代码
│   ├── core/        # 业务逻辑（下载器、AI 服务）
│   ├── ui/          # 界面布局与交互
│   └── utils/       # 工具类（路径管理、日志、装饰器）
├── temp/            # 运行时缓存与临时文件
├── main.py          # 程序入口点
├── pyproject.toml   # uv/PEP 621 项目配置
└── requirements.txt # 传统项目依赖
```

## 🏗️ 开发环境配置

### 使用 uv (推荐)

1. **安装 uv** (如果尚未安装)
   ```powershell
   powershell -ExecutionPolicy ByPass -c "ir https://astral-sh.uv.run/install.ps1"
   ```

2. **同步项目环境**
   ```bash
   uv sync
   ```

3. **运行程序**
   ```bash
   uv run python main.py
   ```

### 传统方式 (pip + venv)

1. **安装依赖**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **运行程序**
   ```bash
   python main.py
   ```

## ⚙️ 准备工作

1. **准备二进制文件**
   - 下载 `ffmpeg.exe` 并放置于 `bin/` 目录下。

2. **配置环境变量**
   - 复制 `.env.example` 为 `.env` 并填写你的 API Key。

## 📦 打包指南

推荐使用 **Nuitka** 进行打包：

```bash
uv run nuitka --standalone --show-progress --plugin-enable=tk-inter --include-data-dir=bin=bin --include-data-dir=assets=assets --windows-disable-console main.py
```

## 📄 许可证

MIT License
