"""
Agent 1: 分析器智能体 (Analyzer Agent)

职责：
  - 接收用户输入（文字描述、图片、场合、天气等）
  - 调用 Claude API 进行多模态理解
  - 提取关键语义信息：情绪倾向、场景类型、气味偏好关键词
  - 输出结构化的"香水需求分析报告"，供 Agent 2 使用

输入：
  - user_text: 用户的文字描述
  - image_path: 可选，用户上传的图片路径
  - weather_data: 当前天气信息（温度、湿度、季节）
  - occasion: 使用场合（约会、工作、休闲等）

输出：
  - AnalysisResult 对象，包含提取的香调偏好、强度建议、关键词列表
"""

import anthropic
from pydantic import BaseModel
from typing import Optional
import base64


class AnalysisResult(BaseModel):
    """分析结果数据模型"""
    mood: str                        # 情绪倾向（清新/温暖/神秘/活力等）
    season_fit: str                  # 季节适配（春/夏/秋/冬）
    intensity: str                   # 香气强度建议（淡/中/浓）
    scent_keywords: list[str]        # 气味关键词列表（如：["木质", "花香", "麝香"]）
    occasion_type: str               # 场合类型
    raw_analysis: str                # Claude 原始分析文本


class AnalyzerAgent:
    """
    分析器智能体
    负责理解用户意图，输出结构化香水需求
    """

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-6"

    def analyze(
        self,
        user_text: str,
        image_path: Optional[str] = None,
        weather_data: Optional[dict] = None,
        occasion: Optional[str] = None,
    ) -> AnalysisResult:
        """
        主分析方法
        将用户输入转化为结构化的香水需求分析报告
        """
        # 构建分析提示词
        prompt = self._build_prompt(user_text, weather_data, occasion)

        # 构建消息内容（支持多模态）
        content = self._build_content(prompt, image_path)

        # 调用 Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )

        raw_text = response.content[0].text

        # 解析返回结果
        return self._parse_response(raw_text, occasion or "日常")

    def _build_prompt(
        self,
        user_text: str,
        weather_data: Optional[dict],
        occasion: Optional[str],
    ) -> str:
        """构建发送给 Claude 的提示词"""
        weather_str = ""
        if weather_data:
            weather_str = f"\n当前天气：温度 {weather_data.get('temperature')}°C，湿度 {weather_data.get('humidity')}%，天气状况 {weather_data.get('condition')}"

        occasion_str = f"\n使用场合：{occasion}" if occasion else ""

        return f"""你是一位专业的香水顾问。请根据以下信息分析用户对香水的需求：

用户描述：{user_text}{weather_str}{occasion_str}

请以 JSON 格式返回分析结果，包含以下字段：
- mood: 情绪倾向（清新/温暖/神秘/活力/优雅 中选一）
- season_fit: 季节适配（春/夏/秋/冬）
- intensity: 香气强度（淡/中/浓）
- scent_keywords: 气味关键词数组（3-5个，如木质、花香、麝香、柑橘、海洋等）
- occasion_type: 场合类型
- raw_analysis: 100字以内的简短分析说明

只返回 JSON，不要其他内容。"""

    def _build_content(self, prompt: str, image_path: Optional[str]) -> list:
        """构建消息内容，支持图片输入"""
        content = [{"type": "text", "text": prompt}]

        if image_path:
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")
            content.insert(0, {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data,
                },
            })

        return content

    def _parse_response(self, raw_text: str, occasion: str) -> AnalysisResult:
        """解析 Claude 返回的 JSON 结果"""
        import json
        try:
            data = json.loads(raw_text)
            return AnalysisResult(
                mood=data.get("mood", "清新"),
                season_fit=data.get("season_fit", "春"),
                intensity=data.get("intensity", "中"),
                scent_keywords=data.get("scent_keywords", []),
                occasion_type=data.get("occasion_type", occasion),
                raw_analysis=data.get("raw_analysis", ""),
            )
        except json.JSONDecodeError:
            # 解析失败时返回默认值
            return AnalysisResult(
                mood="清新",
                season_fit="春",
                intensity="中",
                scent_keywords=["花香"],
                occasion_type=occasion,
                raw_analysis=raw_text,
            )
