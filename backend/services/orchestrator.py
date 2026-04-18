"""
编排服务 (Orchestrator Service)

职责：
  - 作为整个业务流程的总调度中心
  - 协调 Agent 1（分析器）和 Agent 2（执行器）的执行顺序
  - 调用数据库、天气 API 等外部服务
  - 处理异常和错误，保证流程健壮性
  - 返回最终结果给 API 层

完整业务流程：
  用户输入 → InputProcessor → WeatherAPI → Agent1 → DB查询 → Agent2 → 返回结果
"""

from typing import Optional
from services.input_processor import InputProcessor, ProcessedInput
from services.weather_api import WeatherAPIService
from agents.agent1_analyzer import AnalyzerAgent, AnalysisResult
from agents.agent2_executor import ExecutorAgent, PerfumeRecommendation
from database.db_manager import DatabaseManager
from config.settings import Settings


class PerfumeGenerationRequest:
    """香水生成请求数据类"""

    def __init__(
        self,
        user_text: str,
        image_path: Optional[str] = None,
        occasion: Optional[str] = None,
        city: Optional[str] = None,          # 城市名，用于查询天气
        custom_ingredients: Optional[list] = None,  # 用户指定的原料偏好
    ):
        self.user_text = user_text
        self.image_path = image_path
        self.occasion = occasion
        self.city = city
        self.custom_ingredients = custom_ingredients


class PerfumeGenerationResult:
    """香水生成结果数据类"""

    def __init__(
        self,
        recommendation: PerfumeRecommendation,
        analysis: AnalysisResult,
        weather_used: Optional[dict] = None,
    ):
        self.recommendation = recommendation
        self.analysis = analysis
        self.weather_used = weather_used
        self.success = True
        self.error_message = None


class Orchestrator:
    """
    业务编排器
    统一调度所有智能体和服务，驱动香水生成完整流程
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.input_processor = InputProcessor()
        self.weather_service = WeatherAPIService(api_key=settings.WEATHER_API_KEY)
        self.analyzer = AnalyzerAgent(api_key=settings.ANTHROPIC_API_KEY)
        self.executor = ExecutorAgent(api_key=settings.ANTHROPIC_API_KEY)
        self.db_manager = DatabaseManager(db_path=settings.DATABASE_PATH)

    async def generate_perfume(
        self,
        request: PerfumeGenerationRequest,
    ) -> PerfumeGenerationResult:
        """
        香水生成主流程
        按顺序执行：输入处理 → 天气查询 → Agent1分析 → DB查询 → Agent2执行
        """
        try:
            # Step 1: 预处理用户输入
            processed_input: ProcessedInput = self.input_processor.process(
                text=request.user_text,
                image_path=request.image_path,
            )

            # Step 2: 获取天气数据（可选）
            weather_data = None
            if request.city:
                weather_data = self.weather_service.get_current_weather(request.city)

            # Step 3: Agent 1 分析用户需求
            analysis: AnalysisResult = self.analyzer.analyze(
                user_text=processed_input.cleaned_text,
                image_path=processed_input.image_path,
                weather_data=weather_data,
                occasion=request.occasion,
            )

            # Step 4: 从数据库查询匹配的香基（按家族精确匹配）
            candidate_bases = self.db_manager.query_bases(
                family=analysis.recommended_family,
                limit=8,
            )

            # Step 5: Agent 2 从候选香基中选出推荐
            recommendation: PerfumeRecommendation = self.executor.execute(
                analysis_result=analysis,
                candidate_bases=candidate_bases,
            )

            return PerfumeGenerationResult(
                recommendation=recommendation,
                analysis=analysis,
                weather_used=weather_data,
            )

        except Exception as e:
            # 统一异常处理
            result = PerfumeGenerationResult(
                recommendation=None,
                analysis=None,
            )
            result.success = False
            result.error_message = str(e)
            return result
