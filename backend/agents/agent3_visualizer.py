"""
Agent3 视觉化生成器 (Agent3 Visualizer)

使用 wan2.7-image-pro（阿里云百炼 DashScope）文生图模型，根据 Agent2 生成的香调信息
和气味描述，生成一张香氛主题背景图，以 base64 字符串返回。

如果未配置 DASHSCOPE_API_KEY，则静默跳过，返回 None，不影响主流程。
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

import requests

from config.settings import settings
from database.schemas import FinalOutput

logger = logging.getLogger(__name__)

# wan2.7-image-pro 同步端点
DASHSCOPE_SYNC_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
)


class Agent3Visualizer:
    """调用百炼 wan2.7-image-pro 同步文生图接口，返回 base64 编码的背景图"""

    def __init__(self) -> None:
        self.api_key = settings.DASHSCOPE_API_KEY or ""

    # ── 公开方法 ───────────────────────────────────────────────

    def generate(self, final_output: FinalOutput) -> Optional[str]:
        if not self.api_key:
            logger.info("[Agent3] 未配置 DASHSCOPE_API_KEY，跳过图片生成")
            return None

        try:
            prompt = self._build_prompt(final_output)
            logger.info("[Agent3] 开始生成图片 | prompt=%s", prompt[:80])

            image_url = self._call_sync(prompt)
            if not image_url:
                return None

            return self._url_to_base64(image_url)

        except Exception as exc:
            logger.warning("[Agent3] 图片生成失败: %s", exc)
            return None

    # ── 私有方法 ───────────────────────────────────────────────

    def _build_prompt(self, final_output: FinalOutput) -> str:
        top = ", ".join(n.name for n in final_output.formula.top_notes)
        mid = ", ".join(n.name for n in final_output.formula.middle_notes)
        base = ", ".join(n.name for n in final_output.formula.base_notes)
        mood = final_output.scent_description[:100]

        return (
            f"Luxury perfume bottle photography, artistic and cinematic. "
            f"Top notes: {top}. Heart notes: {mid}. Base notes: {base}. "
            f"Mood: {mood}. "
            f"Style: soft bokeh background, golden hour lighting, "
            f"premium fragrance advertisement, high fashion editorial, "
            f"shallow depth of field, elegant botanical elements, dreamy atmosphere."
        )

    def _call_sync(self, prompt: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.DASHSCOPE_IMAGE_MODEL,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "size": "2K",
                "n": 1,
                "watermark": False,
                "thinking_mode": False,
            },
        }

        # 文生图同步可能耗时较长（含 thinking 关闭也常需 30-60s），给足超时
        resp = requests.post(DASHSCOPE_SYNC_URL, json=body, headers=headers, timeout=180)
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("output", {}).get("choices", [])
        if not choices:
            logger.warning("[Agent3] 响应无 choices: %s", data)
            return None

        for content in choices[0].get("message", {}).get("content", []):
            if content.get("type") == "image":
                logger.info("[Agent3] 图片生成成功")
                return content.get("image")

        logger.warning("[Agent3] choices 中未找到 image 类型: %s", data)
        return None

    @staticmethod
    def _url_to_base64(url: str) -> Optional[str]:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return base64.b64encode(resp.content).decode("utf-8")
        except Exception as exc:
            logger.warning("[Agent3] 下载图片失败: %s", exc)
            return None
