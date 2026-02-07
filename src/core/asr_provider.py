import json
from http import HTTPStatus
from urllib import request
import dashscope
from dashscope.audio.asr import Transcription
from ..utils.logger import get_logger
from ..utils.config import EnvConfig

logger = get_logger("ASRProvider")


class ASRProvider:
    """
    阿里云 DashScope 语音转文字服务提供者
    """

    def __init__(self):
        self.api_key = EnvConfig.DASHSCOPE_API_KEY
        self.base_url = EnvConfig.ASR_BASE_URL
        self.model = EnvConfig.ASR_MODEL_NAME

        if not self.api_key:
            logger.error("未配置 API Key (DASHSCOPE_API_KEY 或 LLM_API_KEY)")
            raise ValueError("未配置 API Key，请检查 .env 文件中的 LLM_API_KEY")

        # 配置全局 API Key 和 Base URL
        dashscope.api_key = self.api_key
        dashscope.base_http_api_url = self.base_url

    def transcribe(self, file_url: str) -> str:
        """
        调用 ASR 模型将录音文件转化为文本
        :param file_url: 录音文件的临时访问链接
        :return: 识别出的文本
        """
        logger.info(f"开始调用 ASR 服务，模型: {self.model}, URL: {file_url}")

        try:
            # 提交转写任务
            task_response = Transcription.async_call(
                model=self.model,
                file_urls=[file_url],
                language_hints=['zh', 'en']  # 指定待识别音频的语言代码
            )

            logger.info(f"ASR 任务已提交，Task ID: {task_response.output.task_id}")

            # 等待任务完成
            transcription_response = Transcription.wait(task=task_response.output.task_id)

            if transcription_response.status_code == HTTPStatus.OK:
                for transcription in transcription_response.output['results']:
                    if transcription['subtask_status'] == 'SUCCEEDED':
                        result_url = transcription['transcription_url']
                        # 获取转写结果详情
                        result_data = request.urlopen(result_url).read().decode('utf8')
                        result_json = json.loads(result_data)

                        # 从 transcripts 中提取所有文本并拼接
                        full_text = ""
                        if 'transcripts' in result_json:
                            for transcript in result_json['transcripts']:
                                if 'text' in transcript:
                                    full_text += transcript['text'] + "\n"

                        logger.info("ASR 任务处理成功，文本内容已提取")
                        return full_text.strip()
                    else:
                        logger.error(f"ASR 子任务失败: {transcription}")
                        raise Exception(f"ASR 子任务失败: {transcription}")
            else:
                logger.error(f"ASR 任务失败: {transcription_response.output.message}")
                raise Exception(f"ASR 任务失败: {transcription_response.output.message}")

        except Exception as e:
            logger.error(f"ASR 识别过程中发生错误: {str(e)}")
            raise e
