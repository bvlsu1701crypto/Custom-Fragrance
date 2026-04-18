"""
天气 API 服务 (Weather API Service)

职责：
  - 根据用户所在城市查询当前天气数据
  - 将天气数据转化为对香水推荐有意义的维度（温度区间、湿度级别、季节）
  - 缓存天气结果，避免重复请求同一城市
  - 处理 API 限流和异常

使用的外部 API：
  - OpenWeatherMap API（免费版）
  - 接口文档：https://openweathermap.org/current

返回的天气信息会被传入 Agent 1，用于辅助香调推荐
（例如：高温高湿天气建议推荐清爽柑橘调，寒冷天气建议推荐温暖木质调）
"""

import requests
from typing import Optional
from datetime import datetime, timedelta


class WeatherData:
    """天气数据结构"""

    def __init__(self, raw: dict):
        self.temperature: float = raw.get("main", {}).get("temp", 20) - 273.15  # K→℃
        self.humidity: int = raw.get("main", {}).get("humidity", 50)
        self.condition: str = raw.get("weather", [{}])[0].get("description", "晴天")
        self.city: str = raw.get("name", "未知城市")
        self.season: str = self._get_season()
        self.temp_level: str = self._get_temp_level()
        self.humidity_level: str = self._get_humidity_level()

    def _get_season(self) -> str:
        """根据当前月份判断季节"""
        month = datetime.now().month
        if month in (3, 4, 5):
            return "春"
        elif month in (6, 7, 8):
            return "夏"
        elif month in (9, 10, 11):
            return "秋"
        else:
            return "冬"

    def _get_temp_level(self) -> str:
        """温度区间分级"""
        if self.temperature < 10:
            return "寒冷"
        elif self.temperature < 20:
            return "凉爽"
        elif self.temperature < 30:
            return "温暖"
        else:
            return "炎热"

    def _get_humidity_level(self) -> str:
        """湿度级别分级"""
        if self.humidity < 40:
            return "干燥"
        elif self.humidity < 70:
            return "适中"
        else:
            return "潮湿"

    def to_dict(self) -> dict:
        """转换为字典，便于传入 Agent"""
        return {
            "temperature": round(self.temperature, 1),
            "humidity": self.humidity,
            "condition": self.condition,
            "city": self.city,
            "season": self.season,
            "temp_level": self.temp_level,
            "humidity_level": self.humidity_level,
        }


class WeatherAPIService:
    """
    天气 API 服务
    封装 OpenWeatherMap API 调用，提供天气数据给香水推荐流程
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    CACHE_DURATION = timedelta(minutes=30)  # 缓存30分钟

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._cache: dict[str, tuple[WeatherData, datetime]] = {}

    def get_current_weather(self, city: str) -> Optional[dict]:
        """
        获取指定城市的当前天气
        优先从缓存返回，超时则重新请求
        """
        # 检查缓存
        if city in self._cache:
            cached_data, cached_time = self._cache[city]
            if datetime.now() - cached_time < self.CACHE_DURATION:
                return cached_data.to_dict()

        # 请求天气 API
        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    "q": city,
                    "appid": self.api_key,
                    "lang": "zh_cn",
                },
                timeout=5,
            )
            response.raise_for_status()
            weather = WeatherData(response.json())

            # 写入缓存
            self._cache[city] = (weather, datetime.now())
            return weather.to_dict()

        except requests.RequestException as e:
            # 天气查询失败时返回 None，不中断主流程
            print(f"[WeatherAPI] 查询 {city} 天气失败: {e}")
            return None
