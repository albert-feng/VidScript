import os
import yt_dlp
from pathlib import Path
from typing import Callable, Optional
from ..utils.logger import get_logger
from ..utils.paths import get_root_path

# 获取针对下载器的专用日志记录器
logger = get_logger("Downloader")


class YtDlpLogger:
    """
    自定义 Logger 类，用于将 yt-dlp 的内部日志重定向到 Python 标准 logging 模块
    """

    def debug(self, msg):
        # 过滤掉 yt-dlp 冗长的进度条调试信息
        if not msg.startswith('[debug] '):
            logger.debug(msg)

    def info(self, msg):
        logger.info(msg)

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


class YtDlpDownloader:
    """
    基于 yt-dlp 的高性能视频下载类
    支持进度反馈、Cookie 注入、自动重试及异常处理
    """

    def __init__(self, on_progress_update: Optional[Callable[[dict], None]] = None):
        """
        :param on_progress_update: 进度回调函数，接收包含进度数据的字典
        """
        self.on_progress_update = on_progress_update
        self.cache_dir = get_root_path() / "cache"

        # 确保缓存目录存在
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _progress_hook(self, d: dict):
        """
        yt-dlp 进度钩子
        解析百分比、速度、ETA 并通过回调通知外部
        """
        try:
            if d['status'] == 'downloading':
                # 提取百分比
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                percentage = (downloaded / total * 100) if total else 0

                # 封装进度数据
                progress_data = {
                    "status": "downloading",
                    "percentage": round(percentage, 2),
                    "speed": d.get('_speed_str', 'N/A'),
                    "eta": d.get('_eta_str', 'N/A'),
                    "filename": os.path.basename(d.get('filename', ''))
                }

                if self.on_progress_update:
                    self.on_progress_update(progress_data)

            elif d['status'] == 'finished':
                logger.info(f"文件下载完成: {d['filename']}")
                if self.on_progress_update:
                    self.on_progress_update({"status": "finished", "percentage": 100.0})
        except Exception as e:
            # 捕获钩子内部的异常，防止中断下载进程
            logger.debug(f"进度钩子解析异常 (非致命): {str(e)}")

    def get_info(self, url: str, proxy: Optional[str] = None) -> dict:
        """
        获取视频元数据信息（不下载视频）
        :param url: 视频地址
        :param proxy: HTTP代理设置，若为 None 则不使用代理
        :return: 包含标题、时长、缩略图等信息的字典
        """
        ydl_opts = {
            'logger': YtDlpLogger(),
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
        }
        if proxy:
            ydl_opts['proxy'] = proxy
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown Title"),
                    "duration": info.get("duration", 0),
                    "thumbnail": info.get("thumbnail", ""),
                    "ext": info.get("ext", "mp4")
                }
        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            raise Exception(f"无法获取视频信息: {str(e)}")

    def download(  # noqa: C901
        self, url: str, browser: Optional[str] = None, save_dir: Optional[str] = None, proxy: Optional[str] = None
    ) -> dict:
        """
        执行下载任务
        :param url: 视频地址
        :param browser: 自动提取 Cookie 的浏览器名称 (chrome, edge, firefox 等)，若为 None 则不提取
        :param save_dir: 自定义保存目录，若为 None 则使用默认 cache 目录
        :param proxy: HTTP代理设置，若为 None 则不使用代理
        :return: 包含下载成功的本地文件绝对路径和标题的字典
        """
        download_path = Path(save_dir) if save_dir else self.cache_dir
        if not download_path.exists():
            download_path.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            # 格式选择：优先 mp4
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            # 路径管理：使用完整标题 (限制长度为 20 字符，防止路径过长)
            'outtmpl': str(download_path / '%(title).20s.%(ext)s'),
            # 日志重定向
            'logger': YtDlpLogger(),
            # 进度钩子
            'progress_hooks': [self._progress_hook],
            # 安全与兼容性
            'nocheckcertificate': True,
            # 限制重试次数
            'retries': 5,
            # 允许文件名包含非 ASCII 字符（如中文）
            'restrictfilenames': False,
            # 指定 FFmpeg 路径，避免在新电脑上依赖系统 PATH
            'ffmpeg_location': str(get_root_path() / "bin"),
        }

        # 代理设置
        if proxy:
            ydl_opts['proxy'] = proxy

        # 仅在指定了浏览器时才注入 Cookie 配置
        if browser:
            logger.info(f"尝试从浏览器 {browser} 提取 Cookie")
            ydl_opts['cookiesfrombrowser'] = (browser,)

        try:
            cookie_msg = f"使用 {browser} cookies" if browser else "不使用 cookies"
            logger.info(f"启动下载任务: {url} ({cookie_msg})")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "Unknown Title")

                # 获取最终生成的文件路径
                file_path = ydl.prepare_filename(info)

                # 处理合并流后缀可能变化的情况 (如 .mp4 变为 .mkv)
                if not os.path.exists(file_path):
                    base_path = os.path.splitext(file_path)[0]
                    for ext in ['.mp4', '.mkv', '.webm']:
                        if os.path.exists(base_path + ext):
                            file_path = base_path + ext
                            break

                abs_path = os.path.abspath(file_path)
                logger.info(f"下载成功，文件路径: {abs_path}")
                return {
                    "path": abs_path,
                    "title": title
                }

        except yt_dlp.utils.DownloadError as e:
            original_msg = str(e)
            logger.error(f"下载失败 (网络/地址无效): {original_msg}")
            raise Exception(f"下载失败: {original_msg}")
        except yt_dlp.utils.ExtractorError as e:
            original_msg = str(e)
            logger.error(f"提取失败 (网站规则变动): {original_msg}")
            raise Exception(f"提取失败: {original_msg}")
        except Exception as e:
            logger.error(f"下载过程中发生未知错误: {str(e)}")
            raise e


# --- 多线程调用示例 ---
if __name__ == "__main__":
    import threading
    import time

    def my_progress_callback(data):
        if data['status'] == 'downloading':
            print(f"\r进度: {data['percentage']}% | 速度: {data['speed']} | ETA: {data['eta']}", end="")
        elif data['status'] == 'finished':
            print("\n下载任务已圆满完成！")

    def run_async_download(url):
        downloader = YtDlpDownloader(on_progress_update=my_progress_callback)
        try:
            # 模拟在子线程中运行
            path = downloader.download(url)
            print(f"最终保存路径: {path}")
        except Exception as e:
            print(f"运行出错: {e}")

    # 目标视频 URL (示例)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # 创建并启动线程，避免阻塞主线程（GUI 线程）
    download_thread = threading.Thread(target=run_async_download, args=(test_url,))
    download_thread.start()

    print("主线程正在运行，界面不会卡死...")
    # 模拟主线程继续做其他事情
    while download_thread.is_alive():
        time.sleep(1)
