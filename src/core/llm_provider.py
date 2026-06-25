from openai import OpenAI
from ..utils.logger import get_logger
from ..utils.config import EnvConfig, load_prompts

logger = get_logger("LLMProvider")


class LLMProvider:
    def __init__(self, provider: str = "deepseek"):
        # 重新加载环境变量配置
        EnvConfig.reload()

        self.provider = provider.lower()
        if self.provider == "deepseek":
            self.api_key = EnvConfig.DEEPSEEK_API_KEY
            self.base_url = EnvConfig.DEEPSEEK_BASE_URL
            self.model_name = EnvConfig.DEEPSEEK_MODEL_NAME
        elif self.provider == "qwen":
            self.api_key = EnvConfig.QWEN_API_KEY
            self.base_url = EnvConfig.QWEN_BASE_URL
            self.model_name = EnvConfig.QWEN_MODEL_NAME
        else:
            logger.warning(f"未知模型提供商: {self.provider}，默认使用 DeepSeek")
            self.provider = "deepseek"
            self.api_key = EnvConfig.DEEPSEEK_API_KEY
            self.base_url = EnvConfig.DEEPSEEK_BASE_URL
            self.model_name = EnvConfig.DEEPSEEK_MODEL_NAME

        if not self.api_key:
            logger.warning(f"API Key ({self.provider}) 未配置，LLM 功能将不可用")

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
            "修正逐字稿": styles_config.get("修正逐字稿", default_deep),
            "口语化转换": styles_config.get("口语化转换", default_oral),
            "学术风提炼": styles_config.get("学术风提炼", default_academic),
            "自定义": custom_prompt
        }

        specific_prompt = prompts.get(style, prompts["修正逐字稿"])

        final_prompt = f"{base_prompt}\n\n具体要求：\n{specific_prompt}"

        # 添加背景信息
        if context:
            final_prompt += f"\n\n背景信息：\n{context}"

        return final_prompt

    def _split_text(self, text: str, max_length: int = 2000) -> list[str]:
        """
        智能切分长文本
        优先按换行符切分，其次按句号/问号/感叹号切分，再次按逗号切分，最后强制切分
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break

            # 截取当前最大长度的文本片段
            target_text = text[:max_length]
            split_pos = -1

            # 优先级 1: 换行符
            pos = target_text.rfind('\n')
            if pos > max_length * 0.5:
                split_pos = pos + 1

            # 优先级 2: 句子结束符
            if split_pos == -1:
                for p in ['。', '！', '？', '；', '.', '!', '?', ';']:
                    pos = target_text.rfind(p)
                    if pos > max_length * 0.5:  # 只有在后半部分找到才算有效，避免切分太碎
                        if pos > split_pos:
                            split_pos = pos + 1

            # 优先级 3: 逗号等次级标点
            if split_pos == -1:
                for p in ['，', ',', '：', ':']:
                    pos = target_text.rfind(p)
                    if pos > max_length * 0.5:
                        if pos > split_pos:
                            split_pos = pos + 1

            # 优先级 4: 强制切分
            if split_pos == -1:
                split_pos = max_length

            chunks.append(text[:split_pos])
            text = text[split_pos:]

        return chunks

    def _call_llm_api(self, text: str, style: str, custom_prompt: str, context: str) -> str:
        """单次调用 LLM API"""
        system_prompt = self._get_system_prompt(style, custom_prompt, context)

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
            return response.choices[0].message.content

        except Exception as e:
            error_msg = f"LLM 调用失败: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def polish_text(self, text: str, style: str, custom_prompt: str = "", context: str = "") -> str:
        """
        调用 LLM 对文本进行润色，支持长文本自动分段

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

        logger.info(f"开始润色任务，风格: {style}，文本长度: {len(text)}")

        # 1. 文本切分
        chunks = self._split_text(text, max_length=2000)
        total_chunks = len(chunks)

        if total_chunks > 1:
            logger.info(f"文本过长，已自动切分为 {total_chunks} 个片段进行处理")

        results = []
        for i, chunk in enumerate(chunks, 1):
            if total_chunks > 1:
                logger.info(f"正在处理片段 {i}/{total_chunks} ({len(chunk)} 字符)...")

            # 2. 调用 API
            # 为避免每个片段都重复大量背景信息导致 token 浪费，可以考虑简化后续片段的 context
            # 但为了效果稳定性，暂时对每个片段都使用完整 prompt
            try:
                chunk_result = self._call_llm_api(chunk, style, custom_prompt, context)
                results.append(chunk_result)
            except Exception as e:
                logger.error(f"片段 {i} 处理失败: {e}")
                # 策略：如果失败，保留原文并标记，或者直接抛出异常？
                # 这里选择抛出异常，让上层处理重试
                raise e

        logger.info("所有片段处理完成，正在合并结果")

        # 3. 结果合并
        # 简单的换行符拼接
        return "\n".join(results)
