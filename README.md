# VidScript

**VidScript** 是一款基于 Python 的桌面应用程序，旨在简化视频下载、音频提取以及利用 AI 大模型生成/润色讲稿的工作流程。

> ⚠️ **系统要求**：本项目深度依赖 Windows 平台的特定组件（如 `ffmpeg.exe` 和 `CustomTkinter` 的某些特性），目前 **仅支持 Windows 操作系统**。

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

## ⚙️ 配置与准备

### 1. 准备二进制文件
下载 `ffmpeg.exe` 并放置于 `bin/` 目录下。

### 2. 环境变量配置 (.env)
复制 `.env.example` 为 `.env`，并填写以下配置：

#### 🤖 AI 模型服务
| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `LLM_API_KEY` | **(必填)** 大模型 API 密钥 | - |
| `LLM_BASE_URL` | 大模型 API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_CHAT_NAME` | 模型名称 | `qwen-plus` |
| `ASR_MODEL_NAME` | 语音转文字模型 | `fun-asr-mtl` |
| `ASR_BASE_URL` | ASR API 地址 | `https://dashscope.aliyuncs.com/api/v1` |
| `LLM_TEMPERATURE`| 生成随机性 (0-1) | `0.7` |
| `ENABLE_THINKING`| 是否显示思考过程 | `False` |

#### ☁️ 阿里云 OSS (音频存储)
| 配置项 | 说明 | 示例 |
| :--- | :--- | :--- |
| `ALIYUN_ACCESS_KEY` | **(必填)** AccessKey ID | - |
| `ALIYUN_ACCESS_SECRET`| **(必填)** AccessKey Secret| - |
| `ALIYUN_OSS_ENDPOINT` | OSS 区域节点 | `https://oss-cn-beijing.aliyuncs.com/` |
| `ALIYUN_OSS_BUCKET_NAME`| 存储桶名称 | `vid-script` |
| `ALIYUN_OSS_FOLDER_NAME`| 存储目录 | `voice_file` |

#### 🛠️ 系统设置
| 配置项 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `DEBUG` | 调试模式 | `True` |
| `LOG_LEVEL` | 日志等级 | `DEBUG` |

### 3. 应用配置 (config.json)
程序运行时自动管理，包含：
- `download_path`: 视频下载路径
- `rewrite_style`: 默认润色风格
- `custom_rewrite_prompt`: 自定义提示词

## 📦 打包指南

推荐使用 **Nuitka** 进行打包：

```bash
uv run nuitka --standalone --show-progress --plugin-enable=tk-inter --include-data-dir=bin=bin --include-data-dir=assets=assets --windows-disable-console main.py
```

## 📄 许可证

MIT License
