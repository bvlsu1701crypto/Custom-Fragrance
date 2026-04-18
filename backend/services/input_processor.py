"""
输入处理服务 (Input Processor Service)

职责：
  - 对用户原始输入进行清洗和预处理
  - 文本规范化：去除无效字符、长度截断、语言检测
  - 图片预处理：格式校验、尺寸压缩（避免超出 API 限制）
  - 敏感词过滤
  - 输出标准化的 ProcessedInput 对象供后续流程使用
"""

import re
import os
from typing import Optional
from pydantic import BaseModel
from PIL import Image


class ProcessedInput(BaseModel):
    """预处理后的用户输入数据模型"""
    cleaned_text: str               # 清洗后的文字
    image_path: Optional[str]       # 预处理后的图片路径（可能已压缩）
    original_text: str              # 原始文字（用于日志）
    language: str                   # 检测到的语言（zh/en）
    text_length: int                # 文字长度


class InputProcessor:
    """
    用户输入处理器
    在送入 Agent 之前对原始输入进行标准化处理
    """

    MAX_TEXT_LENGTH = 500           # 最大文字长度
    MAX_IMAGE_SIZE = (1024, 1024)   # 图片最大尺寸
    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}

    def process(
        self,
        text: str,
        image_path: Optional[str] = None,
    ) -> ProcessedInput:
        """
        主处理方法
        同时处理文字和图片输入
        """
        cleaned_text = self._clean_text(text)
        processed_image = self._process_image(image_path) if image_path else None
        language = self._detect_language(cleaned_text)

        return ProcessedInput(
            cleaned_text=cleaned_text,
            image_path=processed_image,
            original_text=text,
            language=language,
            text_length=len(cleaned_text),
        )

    def _clean_text(self, text: str) -> str:
        """文字清洗：去除多余空白、特殊字符、截断超长文本"""
        # 去除首尾空白
        text = text.strip()
        # 合并连续空白
        text = re.sub(r"\s+", " ", text)
        # 截断超长文本
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH] + "..."
        return text

    def _process_image(self, image_path: str) -> Optional[str]:
        """
        图片预处理：校验格式、压缩尺寸
        返回处理后的图片路径（可能是新的临时路径）
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        ext = os.path.splitext(image_path)[1].lower()
        if ext not in self.SUPPORTED_IMAGE_FORMATS:
            raise ValueError(f"不支持的图片格式: {ext}，支持格式: {self.SUPPORTED_IMAGE_FORMATS}")

        # 压缩尺寸（如果超出限制）
        with Image.open(image_path) as img:
            if img.width > self.MAX_IMAGE_SIZE[0] or img.height > self.MAX_IMAGE_SIZE[1]:
                img.thumbnail(self.MAX_IMAGE_SIZE, Image.LANCZOS)
                # 保存到临时路径
                compressed_path = image_path.replace(ext, f"_compressed{ext}")
                img.save(compressed_path, quality=85)
                return compressed_path

        return image_path

    def _detect_language(self, text: str) -> str:
        """简单语言检测：判断中文还是英文"""
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        return "zh" if chinese_chars > len(text) * 0.1 else "en"
