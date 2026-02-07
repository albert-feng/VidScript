from openai import OpenAI
from ..utils.logger import get_logger
from ..utils.config import EnvConfig, load_prompts

logger = get_logger("LLMProvider")


class LLMProvider:
    def __init__(self):
        # 重新加载环境变量配置
        EnvConfig.reload()

        self.api_key = EnvConfig.LLM_API_KEY
        self.base_url = EnvConfig.LLM_BASE_URL
        self.model_name = EnvConfig.LLM_CHAT_NAME

        if not self.api_key:
            logger.warning("LLM_API_KEY 未配置，LLM 功能将不可用")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 加载提示词配置
        self.prompts_config = load_prompts()

    def _get_system_prompt(self, style: str, custom_prompt: str = "", context: str = "") -> str:
        """根据风格生成 System Prompt"""
        # 从配置文件获取基础提示词，如果不存在则使用默认值
        default_base = "你是一个专业的视频脚本润色助手。请根据用户的要求对提供的原始文稿进行润色。"
        base_prompt = self.prompts_config.get("base_prompt", default_base)

        # 获取预定义的风格提示词
        styles_config = self.prompts_config.get("styles", {})

        # 构建提示词字典
        default_deep = (
            "请对文稿进行深度润色，优化逻辑结构，丰富词汇，使其更具深度和感染力。\n"
            "保持原意的基础上，提升表达的专业性和流畅度。"
        )
        default_oral = (
            "请将文稿转换为口语化的风格，适合视频旁白或演讲。\n"
            "使用短句，避免生僻词，增加互动感，使其听起来自然亲切。"
        )
        default_academic = (
            "请将文稿改写为学术风格，使用严谨的术语和客观的语气。\n"
            "强调逻辑性和条理性，适合用于学术报告或专业讲座。"
        )

        prompts = {
            "深度润色": styles_config.get("深度润色", default_deep),
            "口语化转换": styles_config.get("口语化转换", default_oral),
            "学术风提炼": styles_config.get("学术风提炼", default_academic),
            "自定义": custom_prompt
        }

        specific_prompt = prompts.get(style, prompts["深度润色"])

        final_prompt = f"{base_prompt}\n\n具体要求：\n{specific_prompt}"

        # 添加背景信息
        if context:
            final_prompt += f"\n\n背景信息：\n{context}"

        return final_prompt

    def polish_text(self, text: str, style: str, custom_prompt: str = "", context: str = "") -> str:
        """
        调用 LLM 对文本进行润色

        Args:
            text: 原始文本
            style: 润色风格
            custom_prompt: 自定义提示词（仅当 style="自定义" 时生效）
            context: 背景信息（可选，添加到提示词中）

        Returns:
            润色后的文本
        """
        if not text:
            return ""

        system_prompt = self._get_system_prompt(style, custom_prompt, context)
        logger.info(f"正在调用 LLM 进行润色，风格: {style}")

        try:
            kwargs = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": EnvConfig.LLM_TEMPERATURE,
                "stream": False
            }

            if EnvConfig.ENABLE_THINKING:
                kwargs["extra_body"] = {"enable_thinking": True}

            response = self.client.chat.completions.create(**kwargs)

            result = response.choices[0].message.content
            logger.info("LLM 润色完成")
            return result

        except Exception as e:
            error_msg = f"LLM 调用失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
