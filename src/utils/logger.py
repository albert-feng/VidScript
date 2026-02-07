import logging
import sys
import os
from datetime import datetime


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        self.logger = logging.getLogger("VidScript")

        # 从环境变量获取日志级别，默认为 INFO
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)

        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器 (保存在 temp 目录下)
        from .paths import get_temp_path
        log_dir = get_temp_path()
        log_file = log_dir / f"vidscript_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger


# 全局单例
logger = Logger().get_logger()


def get_logger(name: str):
    """获取带名称的子日志记录器"""
    return logging.getLogger(f"VidScript.{name}")
