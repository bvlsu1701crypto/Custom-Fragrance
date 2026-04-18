"""
编排服务 (Orchestrator Service)

核心调度器，协调两个 Agent 的完整工作流程：
  Agent1Input → Agent1Analyzer → Agent1Output → Agent2Executor → FinalOutput

错误处理策略：
  - Agent1 失败：整体失败，无法继续（无偏好画像就无法配方）
  - Agent2 描述生成失败：Agent2 内部已兜底，不会抛出
  - 天气查询失败：使用兜底天气，不中断流程
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from agents.agent1_analyzer import Agent1Analyzer
from agents.agent2_executor import Agent2Executor
from database.schemas import Agent1Input, Agent1Output, FinalOutput
from services.weather_api import WeatherAPIService
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """
    编排结果，包含最终输出和中间过程信息
    供 API 层使用，中间数据可用于调试和日志
    """
    success: bool
    final_output: FinalOutput | None = None
    agent1_output: Agent1Output | None = None
    error_message: str = ""
    duration_seconds: float = 0.0
    # 各阶段耗时（ms），便于性能分析
    stage_timings: dict[str, float] = field(default_factory=dict)


class PerfumeOrchestrator:
    """
    香水生成编排器

    单例使用方式（与 FastAPI lifespan 配合）：
        orchestrator = PerfumeOrchestrator()
        result = orchestrator.process_request(agent1_input)
    """

    def __init__(self) -> None:
        logger.info("[Orchestrator] 初始化中...")
        self.agent1   = Agent1Analyzer()
        self.agent2   = Agent2Executor()
        self.weather  = WeatherAPIService(api_key=getattr(settings, "WEATHER_API_KEY", ""))
        logger.info("[Orchestrator] 初始化完成")

    # ── 公开接口 ────────────────────────────────────────────────

    def process_request(self, agent_input: Agent1Input) -> OrchestrationResult:
        """
        完整处理一次香水生成请求

        流程：
          1. 天气查询（若 watch_data 含经纬度，用 WeatherAPIService 补全天气）
          2. Agent1：分析偏好画像 + 环境上下文
          3. Agent2：选油 → 配比 → 规格 → 描述文案

        Args:
            agent_input: 前端传入的 Agent1Input
                         （AppleWatchData + QuestionnaireAnswers + WeatherInfo）

        Returns:
            OrchestrationResult，success=True 时 final_output 有值
        """
        total_start = time.perf_counter()
        timings: dict[str, float] = {}

        # ── Step 0：确保天气字段完整 ───────────────────────────
        agent_input = self._ensure_weather(agent_input, timings)

        # ── Step 1：Agent1 分析 ────────────────────────────────
        t0 = time.perf_counter()
        try:
            agent1_output = self.agent1.analyze(agent_input)
        except Exception as exc:
            duration = time.perf_counter() - total_start
            logger.error("[Orchestrator] Agent1 失败：%s", exc, exc_info=True)
            return OrchestrationResult(
                success=False,
                error_message=f"需求分析失败：{exc}",
                duration_seconds=round(duration, 3),
                stage_timings=timings,
            )
        timings["agent1_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "[Orchestrator] Agent1 完成 (%.0fms) | 香调=%s 浓度=%s",
            timings["agent1_ms"],
            agent1_output.preference_profile.scent_families,
            agent1_output.preference_profile.concentration,
        )

        # ── Step 2：Agent2 执行 ────────────────────────────────
        t0 = time.perf_counter()
        try:
            final_output = self.agent2.execute(agent1_output)
        except Exception as exc:
            duration = time.perf_counter() - total_start
            logger.error("[Orchestrator] Agent2 失败：%s", exc, exc_info=True)
            return OrchestrationResult(
                success=False,
                agent1_output=agent1_output,
                error_message=f"配方生成失败：{exc}",
                duration_seconds=round(duration, 3),
                stage_timings=timings,
            )
        timings["agent2_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "[Orchestrator] Agent2 完成 (%.0fms) | 浓度=%.1f%% 留香=%.1fh",
            timings["agent2_ms"],
            final_output.concentration_percentage,
            final_output.estimated_longevity_hours,
        )

        total_duration = round(time.perf_counter() - total_start, 3)
        logger.info(
            "[Orchestrator] 请求完成，总耗时 %.2fs | Agent1=%.0fms Agent2=%.0fms",
            total_duration,
            timings.get("agent1_ms", 0),
            timings.get("agent2_ms", 0),
        )

        return OrchestrationResult(
            success=True,
            final_output=final_output,
            agent1_output=agent1_output,
            duration_seconds=total_duration,
            stage_timings=timings,
        )

    # ── 私有方法 ────────────────────────────────────────────────

    def _ensure_weather(
        self,
        agent_input: Agent1Input,
        timings: dict[str, float],
    ) -> Agent1Input:
        """
        若天气信息中 city 为 '未知'（前端未预先填充），
        则根据 watch_data 经纬度重新查询天气。
        查询失败时使用 WeatherAPIService.get_fallback_weather() 兜底。
        """
        if agent_input.weather.city != "未知":
            # 前端已传入完整天气，无需重查
            return agent_input

        t0 = time.perf_counter()
        lat = agent_input.watch_data.latitude
        lon = agent_input.watch_data.longitude

        weather = self.weather.get_weather_by_coords(lat, lon)
        if weather is None:
            logger.warning("[Orchestrator] 天气查询失败，使用兜底数据")
            weather = self.weather.get_fallback_weather()

        timings["weather_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(
            "[Orchestrator] 天气获取完成 (%.0fms)：%s %.1f°C",
            timings["weather_ms"], weather.city, weather.temperature,
        )

        # 用新天气替换原有字段，返回更新后的 Agent1Input
        return agent_input.model_copy(update={"weather": weather})
