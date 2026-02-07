import subprocess
import os
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.paths import get_bin_path

logger = get_logger("AudioExtractor")


class AudioExtractor:
    """
    使用 ffmpeg 从视频文件中提取音频
    """

    def __init__(self):
        self.ffmpeg_path = get_bin_path("ffmpeg.exe")
        if not self.ffmpeg_path.exists():
            logger.error(f"未找到 ffmpeg.exe: {self.ffmpeg_path}")

    def extract_mp3(self, video_path: str) -> str:
        """
        将视频转换为 mp3 音频
        :param video_path: 视频文件路径
        :return: 生成的音频文件路径
        """
        v_path = Path(video_path)
        if not v_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 构造音频文件名：{title}_音频.mp3
        # 注意：输入的 video_path 已经是 {title}_视频.ext
        # 用户要求：文件名参考视频文件命名方式：{title}_音频.{ext}
        # 如果视频是 0_ASh-12_视频.mp4，音频应该是 0_ASh-12_音频.mp3

        base_name = v_path.stem
        if base_name.endswith("_视频"):
            title = base_name.rsplit("_视频", 1)[0]
        else:
            title = base_name

        audio_filename = f"{title}_音频.mp3"
        audio_path = v_path.parent / audio_filename

        logger.info(f"开始提取音频: {v_path.name} -> {audio_filename}")

        # ffmpeg 转换命令
        # -i 输入文件
        # -q:a 2 质量设置 (约 190 kbps)
        # -y 覆盖已存在文件
        cmd = [
            str(self.ffmpeg_path),
            "-i", str(v_path),
            "-q:a", "2",
            "-y",
            str(audio_path)
        ]

        try:
            # 执行命令，隐藏窗口 (Windows)
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                startupinfo=startupinfo
            )
            logger.info(f"音频提取完成: {audio_path}")
            return str(audio_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg 执行失败: {e.stderr}")
            raise Exception(f"音频提取失败: {e.stderr}")
        except Exception as e:
            logger.error(f"提取音频过程中发生错误: {str(e)}")
            raise e
