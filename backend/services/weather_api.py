"""
天气 API 服务 (Weather API Service)

使用 Open-Meteo (https://open-meteo.com) 按经纬度查询当前天气；
无需 API key，免费，速率宽松。

缓存策略：以 (lat, lon) 四舍五入到小数点后2位作为缓存 key，
30 分钟内同一位置不重复请求。
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


def _wmo_to_condition(code: int) -> str:
    """
    Open-Meteo 的 WMO weather_code 映射到中文天气描述。
    https://open-meteo.com/en/docs#weathervariables
    """
    if code in (0, 1):
        return "晴天"
    if code in (2, 3, 45, 48):
        return "阴天"
    if 51 <= code <= 67:
        return "雨天"
    if 71 <= code <= 77:
        return "雪天"
    if 80 <= code <= 82:
        return "雨天"
    if 85 <= code <= 86:
        return "雪天"
    if 95 <= code <= 99:
        return "雨天"
    return "晴天"


class WeatherAPIService:
    """
    天气查询服务（Open-Meteo 实现）
    输入：经纬度 → 输出：WeatherInfo
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    CACHE_DURATION = timedelta(minutes=30)
    COORD_PRECISION = 2

    def __init__(self) -> None:
        self._cache: dict[tuple[float, float], tuple[WeatherInfo, datetime]] = {}

    def get_weather_by_coords(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[WeatherInfo]:
        """
        根据经纬度获取当前天气；失败返回 None（由调用方 fallback）
        """
        cache_key = (
            round(latitude, self.COORD_PRECISION),
            round(longitude, self.COORD_PRECISION),
        )

        if cache_key in self._cache:
            cached, fetched_at = self._cache[cache_key]
            if datetime.now() - fetched_at < self.CACHE_DURATION:
                logger.debug("[Weather] 缓存命中 %s", cache_key)
                return cached

        try:
            resp = requests.get(
                self.BASE_URL,
                params={
                    "latitude":  latitude,
                    "longitude": longitude,
                    "current":   "temperature_2m,relative_humidity_2m,weather_code",
                    "timezone":  "auto",
                },
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current") or {}

            temperature = round(float(current["temperature_2m"]), 1)
            humidity    = int(current["relative_humidity_2m"])
            code        = int(current.get("weather_code", 0))
            condition   = _wmo_to_condition(code)
            month       = datetime.now().month

            weather = WeatherInfo(
                temperature=temperature,
                humidity=humidity,
                condition=condition,
                city="",  # Open-Meteo 不返回 city，由调用方填充中文城市名
                season=_get_season(month),
                temp_level=_get_temp_level(temperature),
                humidity_level=_get_humidity_level(humidity),
            )

            self._cache[cache_key] = (weather, datetime.now())
            logger.info(
                "[Weather] 获取成功：%.4f,%.4f → %.1f°C %d%% %s",
                latitude, longitude, temperature, humidity, condition,
            )
            return weather

        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.warning(
                "[Weather] 查询失败（lat=%.4f, lon=%.4f）：%s",
                latitude, longitude, exc,
            )
            return None

    def get_fallback_weather(self) -> WeatherInfo:
        """
        查询失败时的兜底：按当前月份推断季节，温湿度取季节默认。
        """
        month = datetime.now().month
        season = _get_season(month)
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
            condition="晴天",
            city="",
            season=season,
            temp_level=_get_temp_level(temp),
            humidity_level=_get_humidity_level(hum),
        )
