import oss2
import uuid
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.config import EnvConfig

logger = get_logger("OSSProvider")


class OSSProvider:
    """
    阿里云 OSS 存储提供者
    负责文件的上传及临时访问链接的生成
    """

    def __init__(self):
        self.access_key = EnvConfig.ALIYUN_ACCESS_KEY
        self.access_secret = EnvConfig.ALIYUN_ACCESS_SECRET
        self.endpoint = EnvConfig.ALIYUN_OSS_ENDPOINT
        self.bucket_name = EnvConfig.ALIYUN_OSS_BUCKET_NAME
        self.folder_name = EnvConfig.ALIYUN_OSS_FOLDER_NAME

        self.oss_client = None
        self._init_client()

    def _init_client(self):
        """初始化 OSS 客户端"""
        if not all([self.access_key, self.access_secret, self.endpoint, self.bucket_name]):
            logger.error("OSS 配置不完整，请检查 .env 文件")
            return

        try:
            auth = oss2.Auth(self.access_key, self.access_secret)
            # 确保 endpoint 不包含 https:// 协议头，oss2 会自动处理或需要纯域名
            endpoint_clean = self.endpoint.replace("https://", "").replace("http://", "")
            self.oss_client = oss2.Bucket(auth, endpoint_clean, self.bucket_name)
            logger.info(f"OSS 客户端初始化成功: {self.bucket_name}")
        except Exception as e:
            logger.error(f"初始化 OSS 客户端失败: {e}")

    def upload_file(self, file_path: str) -> str:
        """
        上传文件到 OSS 并返回预签名链接

        :param file_path: 本地文件路径
        :return: 预签名的临时访问链接
        """
        if not self.oss_client:
            raise ValueError("OSS client not initialized")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 1. 生成 OSS Key: {folder}/{uuid}.{ext}
        ext = path.suffix.lower()
        unique_id = str(uuid.uuid4())
        oss_key = f"{self.folder_name}/{unique_id}{ext}" if self.folder_name else f"{unique_id}{ext}"

        try:
            # 2. 上传文件
            logger.info(f"正在上传文件到 OSS: {path.name} -> {oss_key}")
            with open(file_path, 'rb') as fileobj:
                self.oss_client.put_object(oss_key, fileobj)

            # 3. 生成 60 分钟有效期的预签名 URL
            signed_url = self.oss_client.sign_url('GET', oss_key, expires=3600, slash_safe=True)

            logger.info(f"文件上传成功并生成临时链接: {signed_url}")
            return signed_url

        except Exception as e:
            logger.error(f"上传文件或生成链接失败: {e}")
            raise Exception(f"OSS 操作失败: {str(e)}")
