import json
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from .paths import get_root_path

# --- 增强的 .env 加载逻辑 ---
root_path = get_root_path()
env_path = root_path / ".env"

# 尝试加载 .env
print(f"正在尝试加载配置文件: {env_path}")
if env_path.exists():
    load_dotenv(env_path)
    print("配置文件加载成功")
else:
    print(f"警告: 配置文件不存在: {env_path}")
    # 尝试在当前工作目录查找 (应对某些特殊的启动方式)
    cwd_env = Path(os.getcwd()) / ".env"
    if cwd_env != env_path and cwd_env.exists():
        print(f"尝试加载当前目录配置文件: {cwd_env}")
        load_dotenv(cwd_env)

# 验证关键环境变量是否加载
if not os.getenv("ALIYUN_ACCESS_KEY"):
    print("严重警告: ALIYUN_ACCESS_KEY 未能从环境变量中加载！")

CONFIG_FILE = root_path / "config.json"
PROMPTS_FILE = root_path / "prompts.yaml"

DEFAULT_CONFIG = {
    "download_path": str(Path.home() / "Documents"),
<<<<<<< HEAD
    "rewrite_style": "深度润色",
    "custom_rewrite_prompt": "",
    "llm_provider": "DeepSeek"
=======
    "rewrite_style": "修正逐字稿",
    "custom_rewrite_prompt": "",
<<<<<<< HEAD
    "http_proxy": ""
>>>>>>> 555ca24 (修改润色设置)
=======
    "http_proxy": "",
    "cookie_file": ""
>>>>>>> 5f1a2c5 (fix bug)
}


def load_config():
    """加载配置文件，如果不存在则返回默认配置"""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # 确保所有默认键都存在
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception:
        return DEFAULT_CONFIG


def load_prompts():
    """加载提示词配置"""
    if not PROMPTS_FILE.exists():
        return {}

    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"加载 prompts.yaml 失败: {e}")
        return {}


def save_config(config):
    """保存配置到文件"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"保存配置失败: {e}")


def update_config(key, value):
    """更新单个配置项"""
    config = load_config()
    config[key] = value
    save_config(config)


def get_env(key, default=None):
    """获取环境变量"""
    return os.getenv(key, default)


def reload_env():
    """重新加载环境变量"""
    print(f"正在重新加载配置文件: {env_path}")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    # 尝试在当前工作目录查找
    cwd_env = Path(os.getcwd()) / ".env"
    if cwd_env != env_path and cwd_env.exists():
        load_dotenv(cwd_env, override=True)


class EnvConfig:
    """环境变量配置"""
    # 初始化类属性
    LLM_TEMPERATURE = None
    DEBUG = False
    ENABLE_THINKING = False
    LOG_LEVEL = None
    ALIYUN_ACCESS_KEY = None
    ALIYUN_ACCESS_SECRET = None
    ALIYUN_OSS_ENDPOINT = None
    ALIYUN_OSS_BUCKET_NAME = None
    ALIYUN_OSS_FOLDER_NAME = None

    # DeepSeek Config
    DEEPSEEK_API_KEY = None
    DEEPSEEK_BASE_URL = None
    DEEPSEEK_MODEL_NAME = None

    # Qwen Config
    QWEN_API_KEY = None
    QWEN_BASE_URL = None
    QWEN_MODEL_NAME = None

    @classmethod
    def reload(cls):
        """重新加载配置"""
        reload_env()

        # DeepSeek
        cls.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        cls.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        cls.DEEPSEEK_MODEL_NAME = os.getenv("DEEPSEEK_MODEL_NAME", "deepseek-chat")

        # Qwen
        cls.QWEN_API_KEY = os.getenv("QWEN_API_KEY")
        cls.QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        cls.QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "qwen-plus")

        # API Keys (ASR uses DashScope which shares key with Qwen)
        cls.DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", cls.QWEN_API_KEY)

        cls.ASR_MODEL_NAME = os.getenv("ASR_MODEL_NAME", "fun-asr-mtl")
        cls.ASR_BASE_URL = os.getenv("ASR_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        cls.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

        # Settings
        cls.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        cls.ENABLE_THINKING = os.getenv("ENABLE_THINKING", "False").lower() == "true"
        cls.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

        # Aliyun OSS
        cls.ALIYUN_ACCESS_KEY = os.getenv("ALIYUN_ACCESS_KEY")
        cls.ALIYUN_ACCESS_SECRET = os.getenv("ALIYUN_ACCESS_SECRET")
        cls.ALIYUN_OSS_ENDPOINT = os.getenv("ALIYUN_OSS_ENDPOINT")
        cls.ALIYUN_OSS_BUCKET_NAME = os.getenv("ALIYUN_OSS_BUCKET_NAME")
        cls.ALIYUN_OSS_FOLDER_NAME = os.getenv("ALIYUN_OSS_FOLDER_NAME", "voice_file")


# 初始化配置
EnvConfig.reload()
