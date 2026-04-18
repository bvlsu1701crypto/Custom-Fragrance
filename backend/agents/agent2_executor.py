"""
Agent 2: 执行器智能体 (Executor Agent)

职责：
  - 接收 Agent 1 输出的结构化香水需求分析报告
  - 查询数据库，匹配合适的香水原料/配方
  - 生成香水调配方案（包括原料比例、调配说明）
  - 生成面向用户的自然语言推荐结果

输入：
  - analysis_result: AnalysisResult 对象（来自 Agent 1）
  - available_ingredients: 可用原料列表（来自数据库）

输出：
  - PerfumeRecommendation 对象，包含配方和推荐说明
"""

import anthropic
from pydantic import BaseModel
from typing import Optional
from agents.agent1_analyzer import AnalysisResult


class Ingredient(BaseModel):
    """香水原料数据模型"""
    name: str               # 原料名称
    name_cn: str            # 中文名称
    category: str           # 分类（前调/中调/后调）
    scent_type: str         # 气味类型
    intensity_level: int    # 强度等级 (1-5)
    ratio: float            # 建议比例 (0.0-1.0)


class PerfumeFormula(BaseModel):
    """香水配方数据模型"""
    name: str                       # 配方名称
    description: str                # 配方描述
    top_notes: list[Ingredient]     # 前调原料
    middle_notes: list[Ingredient]  # 中调原料
    base_notes: list[Ingredient]    # 后调原料
    total_volume_ml: float          # 建议总量(ml)


class PerfumeRecommendation(BaseModel):
    """最终推荐结果数据模型"""
    formula: PerfumeFormula         # 具体配方
    story: str                      # 香水故事/推荐语
    usage_tips: str                 # 使用建议
    matching_score: float           # 匹配度评分 (0-100)


class ExecutorAgent:
    """
    执行器智能体
    负责根据分析结果生成具体的香水配方和推荐方案
    """

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-6"

    def execute(
        self,
        analysis_result: AnalysisResult,
        available_ingredients: list[dict],
    ) -> PerfumeRecommendation:
        """
        主执行方法
        根据分析结果从可用原料中选配香水方案
        """
        # 构建执行提示词
        prompt = self._build_prompt(analysis_result, available_ingredients)

        # 调用 Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text

        # 解析并构建推荐结果
        return self._parse_response(raw_text, available_ingredients)

    def _build_prompt(
        self,
        analysis: AnalysisResult,
        ingredients: list[dict],
    ) -> str:
        """构建发送给 Claude 的执行提示词"""
        ingredients_str = "\n".join([
            f"- {item['name_cn']}({item['name']}): {item['category']}，气味类型:{item['scent_type']}，强度:{item['intensity_level']}/5"
            for item in ingredients[:30]  # 最多传入30种原料避免超出 token
        ])

        return f"""你是一位专业的香水调香师。请根据以下分析报告和可用原料，设计一款香水配方。

【用户需求分析】
- 情绪倾向：{analysis.mood}
- 季节适配：{analysis.season_fit}
- 香气强度：{analysis.intensity}
- 气味关键词：{', '.join(analysis.scent_keywords)}
- 使用场合：{analysis.occasion_type}
- 分析说明：{analysis.raw_analysis}

【可用原料库】
{ingredients_str}

请以 JSON 格式返回配方方案，结构如下：
{{
  "formula": {{
    "name": "配方名称",
    "description": "配方描述",
    "top_notes": [{{"name": "原料英文名", "name_cn": "中文名", "category": "前调", "scent_type": "气味类型", "intensity_level": 3, "ratio": 0.3}}],
    "middle_notes": [...],
    "base_notes": [...],
    "total_volume_ml": 10
  }},
  "story": "这款香水的故事和推荐语（100字以内）",
  "usage_tips": "使用建议（50字以内）",
  "matching_score": 85
}}

只从可用原料库中选取，只返回 JSON。"""

    def _parse_response(
        self,
        raw_text: str,
        available_ingredients: list[dict],
    ) -> PerfumeRecommendation:
        """解析 Claude 返回的配方 JSON"""
        import json

        try:
            data = json.loads(raw_text)
            formula_data = data.get("formula", {})

            def parse_ingredients(items: list) -> list[Ingredient]:
                return [Ingredient(**item) for item in items]

            formula = PerfumeFormula(
                name=formula_data.get("name", "定制香水"),
                description=formula_data.get("description", ""),
                top_notes=parse_ingredients(formula_data.get("top_notes", [])),
                middle_notes=parse_ingredients(formula_data.get("middle_notes", [])),
                base_notes=parse_ingredients(formula_data.get("base_notes", [])),
                total_volume_ml=formula_data.get("total_volume_ml", 10.0),
            )

            return PerfumeRecommendation(
                formula=formula,
                story=data.get("story", ""),
                usage_tips=data.get("usage_tips", ""),
                matching_score=float(data.get("matching_score", 80)),
            )

        except (json.JSONDecodeError, Exception) as e:
            # 解析失败时返回默认配方
            return PerfumeRecommendation(
                formula=PerfumeFormula(
                    name="清新定制香",
                    description="根据您的偏好调配的个性香水",
                    top_notes=[],
                    middle_notes=[],
                    base_notes=[],
                    total_volume_ml=10.0,
                ),
                story="专为您定制的独特香气",
                usage_tips="喷于手腕和颈部",
                matching_score=75.0,
            )
