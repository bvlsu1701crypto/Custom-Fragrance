"""
天气 API 服务 (Weather API Service)

根据 Apple Watch 提供的经纬度联网查询当前天气，
结果转换为 WeatherInfo 模型返回给 Agent1。

缓存策略：以 (lat, lon) 四舍五入到小数点后2位作为缓存 key，
30 分钟内同一位置不重复请求。

使用的外部 API：OpenWeatherMap（免费版）
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import requests

from database.schemas import WeatherInfo

logger = logging.getLogger(__name__)


def _get_season(month: int) -> str:
    if month in (3, 4, 5):
        return "春"
    elif month in (6, 7, 8):
        return "夏"
    elif month in (9, 10, 11):
        return "秋"
    else:
        return "冬"


def _get_temp_level(temp: float) -> str:
    if temp < 10:
        return "寒冷(<10°C)"
    elif temp < 20:
        return "凉爽(10-20°C)"
    elif temp < 30:
        return "温暖(20-30°C)"
    else:
        return "炎热(>30°C)"


def _get_humidity_level(humidity: int) -> str:
    if humidity < 40:
        return "干燥(<40%)"
    elif humidity < 70:
        return "适中(40-70%)"
    else:
        return "潮湿(>70%)"


class WeatherAPIService:
    """
    天气查询服务
    输入：Apple Watch GPS 经纬度
    输出：WeatherInfo（传入 Agent1Input）
    """

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    CACHE_DURATION = timedelta(minutes=30)
    # 经纬度精度：保留2位小数（约1km精度，足够天气查询）
    COORD_PRECISION = 2

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        # key: (lat_rounded, lon_rounded)  value: (WeatherInfo, fetch_time)
        self._cache: dict[tuple[float, float], tuple[WeatherInfo, datetime]] = {}

    def get_weather_by_coords(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[WeatherInfo]:
        """
        根据经纬度获取当前天气

        Args:
            latitude:  纬度（来自 AppleWatchData.latitude）
            longitude: 经度（来自 AppleWatchData.longitude）

        Returns:
            WeatherInfo 实例；查询失败时返回 None，不中断主流程
        """
        cache_key = (
            round(latitude, self.COORD_PRECISION),
            round(longitude, self.COORD_PRECISION),
        )

        # 命中缓存
        if cache_key in self._cache:
            cached, fetched_at = self._cache[cache_key]
            if datetime.now() - fetched_at < self.CACHE_DURATION:
                logger.debug("[Weather] 缓存命中 %s", cache_key)
                return cached

        # 调用 OpenWeatherMap API
        try:
            resp = requests.get(
                self.BASE_URL,
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "appid": self.api_key,
                    "lang": "zh_cn",
                },
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()

            temperature = round(data["main"]["temp"] - 273.15, 1)   # K → ℃
            humidity    = int(data["main"]["humidity"])
            condition   = data["weather"][0]["description"]
            city        = data.get("name", "未知")
            month       = datetime.now().month

            weather = WeatherInfo(
                temperature=temperature,
                humidity=humidity,
                condition=condition,
                city=city,
                season=_get_season(month),
                temp_level=_get_temp_level(temperature),
                humidity_level=_get_humidity_level(humidity),
            )

            self._cache[cache_key] = (weather, datetime.now())
            logger.info(
                "[Weather] 获取成功：%s %.1f°C %d%% %s",
                city, temperature, humidity, condition,
            )
            return weather

        except requests.RequestException as exc:
            logger.warning(
                "[Weather] 查询失败（lat=%.4f, lon=%.4f）：%s",
                latitude, longitude, exc,
            )
            return None

    def get_fallback_weather(self) -> WeatherInfo:
        """
        查询失败时的兜底天气数据
        基于当前月份推断季节，其余使用常见默认值
        """
        month = datetime.now().month
        season = _get_season(month)
        # 按季节给出合理的默认温湿度
        defaults = {
            "春": (18.0, 55),
            "夏": (32.0, 75),
            "秋": (16.0, 50),
            "冬": (5.0,  40),
        }
        temp, hum = defaults[season]

        logger.info("[Weather] 使用兜底天气数据，季节=%s", season)
        return WeatherInfo(
            temperature=temp,
            humidity=hum,
            condition="未知",
            city="未知",
            season=season,
            temp_level=_get_temp_level(temp),
            humidity_level=_get_humidity_level(hum),
        )
