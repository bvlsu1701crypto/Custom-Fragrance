"""
Agent 2: 执行器智能体 (Executor Agent) — 香基推荐模式

职责：
  - 接收 Agent 1 输出的分析报告 + 候选香基列表（含配方明细）
  - 从候选香基中选出最匹配的 1-2 个推荐给用户
  - 生成自然语言的推荐故事、使用建议、个性化微调建议

输入：
  - analysis_result: AnalysisResult 对象（来自 Agent 1）
  - candidate_bases: 候选香基列表（来自 db_manager.query_bases）

输出：
  - PerfumeRecommendation 对象，含首推香基 + 可选备选 + 个性化建议
"""

import json
import re
import anthropic
from pydantic import BaseModel
from typing import Optional
from agents.agent1_analyzer import AnalysisResult


class BaseIngredient(BaseModel):
    """香基中的单个原料条目（用于展示）"""
    ingredient: str
    ingredient_id: int
    parts: int
    role: str


class BaseRecommendation(BaseModel):
    """单个香基推荐"""
    base_id: str                    # B01-B30
    base_name: str
    family: str
    style: str
    ingredients: list[BaseIngredient]   # 配方明细
    high_impact_notes: Optional[str] = None
    test_suggestion: Optional[str] = None
    story: str                      # 推荐理由 / 故事
    usage_tips: str                 # 使用建议
    matching_score: float           # 0-100


class PerfumeRecommendation(BaseModel):
    """最终推荐结果"""
    primary: BaseRecommendation
    alternative: Optional[BaseRecommendation] = None
    personalization_tips: str       # 个性化微调建议


class ExecutorAgent:
    """执行器：从候选香基中选出最匹配的推荐"""

    def __init__(self, api_key: str, model: str = "claude-opus-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def execute(
        self,
        analysis_result: AnalysisResult,
        candidate_bases: list[dict],
    ) -> PerfumeRecommendation:
        """从候选香基中挑选并生成推荐"""

        if not candidate_bases:
            return self._fallback_recommendation(analysis_result, candidate_bases)

        prompt = self._build_prompt(analysis_result, candidate_bases)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text
        return self._parse_response(raw_text, analysis_result, candidate_bases)

    def _build_prompt(
        self,
        analysis: AnalysisResult,
        bases: list[dict],
    ) -> str:
        """构建推荐 prompt"""

        # 最多传 8 个候选香基给 Claude，避免 prompt 太长
        sample = bases[:8]
        bases_str_parts = []
        for b in sample:
            detail_lines = [
                f"    - {d['ingredient']} × {d['parts']} 份 ({d['role']})"
                for d in b.get("details", [])
            ]
            bases_str_parts.append(
                f"【{b['id']} {b['name']}】家族: {b['family']}，风格: {b['style']}\n"
                + "  配方明细:\n"
                + "\n".join(detail_lines)
            )
        bases_str = "\n\n".join(bases_str_parts)

        return f"""你是一位专业调香师。请根据用户需求，从下列候选香基中选出最匹配的 1 个作为首推，再选 1 个作为备选（可选）。

【用户需求分析】
- 情绪倾向：{analysis.mood}
- 季节适配：{analysis.season_fit}
- 香气强度：{analysis.intensity}
- 气味关键词：{', '.join(analysis.scent_keywords)}
- 使用场合：{analysis.occasion_type}
- 推荐家族：{analysis.recommended_family}
- 分析说明：{analysis.raw_analysis}

【候选香基库】
{bases_str}

请以 JSON 格式返回推荐结果，结构如下：
{{
  "primary_base_id": "B01",
  "primary_story": "100字以内的推荐故事，把用户需求与这款香基的调性连接起来",
  "primary_usage_tips": "50字以内的使用建议",
  "primary_matching_score": 88,
  "alternative_base_id": "B02 或 null",
  "alternative_story": "100字以内（如有备选）",
  "alternative_usage_tips": "50字以内（如有备选）",
  "alternative_matching_score": 80,
  "personalization_tips": "150字以内的个性化微调建议，例如建议在此香基基础上加入某种原料"
}}

必须从候选列表中选择，只返回 JSON，不要加 markdown 代码围栏。"""

    def _parse_response(
        self,
        raw_text: str,
        analysis: AnalysisResult,
        candidate_bases: list[dict],
    ) -> PerfumeRecommendation:
        """解析 Claude 返回的推荐 JSON，填充完整的香基数据"""

        cleaned = raw_text.strip()
        fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
        if fence:
            cleaned = fence.group(1)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return self._fallback_recommendation(analysis, candidate_bases)

        by_id = {b["id"]: b for b in candidate_bases}

        primary_id = data.get("primary_base_id")
        primary_base = by_id.get(primary_id) or candidate_bases[0]
        primary = self._build_base_recommendation(
            primary_base,
            story=data.get("primary_story", ""),
            usage_tips=data.get("primary_usage_tips", ""),
            score=float(data.get("primary_matching_score", 80)),
        )

        alternative = None
        alt_id = data.get("alternative_base_id")
        if alt_id and alt_id in by_id and alt_id != primary.base_id:
            alternative = self._build_base_recommendation(
                by_id[alt_id],
                story=data.get("alternative_story", ""),
                usage_tips=data.get("alternative_usage_tips", ""),
                score=float(data.get("alternative_matching_score", 70)),
            )

        return PerfumeRecommendation(
            primary=primary,
            alternative=alternative,
            personalization_tips=data.get("personalization_tips", ""),
        )

    def _build_base_recommendation(
        self,
        base: dict,
        story: str,
        usage_tips: str,
        score: float,
    ) -> BaseRecommendation:
        """根据 DB 中的香基 dict 构造 BaseRecommendation"""
        ingredients = [
            BaseIngredient(
                ingredient=d["ingredient"],
                ingredient_id=int(d["ingredient_id"]),
                parts=int(d["parts"]),
                role=str(d["role"]),
            )
            for d in base.get("details", [])
        ]
        return BaseRecommendation(
            base_id=base["id"],
            base_name=base["name"],
            family=base["family"],
            style=base["style"],
            ingredients=ingredients,
            high_impact_notes=_none_if_na(base.get("high_impact_notes")),
            test_suggestion=_none_if_na(base.get("test_suggestion")),
            story=story,
            usage_tips=usage_tips,
            matching_score=score,
        )

    def _fallback_recommendation(
        self,
        analysis: AnalysisResult,
        candidate_bases: list[dict],
    ) -> PerfumeRecommendation:
        """解析失败时的兜底：直接选第一个候选"""
        if not candidate_bases:
            # 极端情况：DB 为空，返回空推荐
            empty = BaseRecommendation(
                base_id="",
                base_name="暂无匹配香基",
                family=analysis.recommended_family,
                style="",
                ingredients=[],
                story="数据库中暂无匹配的香基，请稍后重试",
                usage_tips="",
                matching_score=0.0,
            )
            return PerfumeRecommendation(
                primary=empty,
                alternative=None,
                personalization_tips="",
            )

        primary = self._build_base_recommendation(
            candidate_bases[0],
            story=f"这款 {candidate_bases[0]['name']} 符合您的 {analysis.recommended_family} 偏好",
            usage_tips="喷于手腕和颈部内侧",
            score=80.0,
        )
        return PerfumeRecommendation(
            primary=primary,
            alternative=None,
            personalization_tips="可根据个人喜好微调原料比例",
        )


def _none_if_na(value) -> Optional[str]:
    """处理 pandas NaN/None 转字符串的问题"""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    return s
