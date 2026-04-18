export interface CityCoord {
  lat: number
  lng: number
  zhName: string
}

/** Keyed by the English `name` field of WORLD_CITIES (what EnvironmentCard writes into `data.city`). */
export const CITY_COORDS: Record<string, CityCoord> = {
  Shanghai: { lat: 31.2304, lng: 121.4737, zhName: '上海' },
  Beijing: { lat: 39.9042, lng: 116.4074, zhName: '北京' },
  'Hong Kong': { lat: 22.3193, lng: 114.1694, zhName: '香港' },
  Tokyo: { lat: 35.6762, lng: 139.6503, zhName: '东京' },
  Singapore: { lat: 1.3521, lng: 103.8198, zhName: '新加坡' },
  Seoul: { lat: 37.5665, lng: 126.978, zhName: '首尔' },
  Bangkok: { lat: 13.7563, lng: 100.5018, zhName: '曼谷' },
  Dubai: { lat: 25.2048, lng: 55.2708, zhName: '迪拜' },
  Paris: { lat: 48.8566, lng: 2.3522, zhName: '巴黎' },
  London: { lat: 51.5074, lng: -0.1278, zhName: '伦敦' },
  Milan: { lat: 45.4642, lng: 9.19, zhName: '米兰' },
  'New York': { lat: 40.7128, lng: -74.006, zhName: '纽约' },
  'Los Angeles': { lat: 34.0522, lng: -118.2437, zhName: '洛杉矶' },
  Sydney: { lat: -33.8688, lng: 151.2093, zhName: '悉尼' },
  Mumbai: { lat: 19.076, lng: 72.8777, zhName: '孟买' },
  Taipei: { lat: 25.033, lng: 121.5654, zhName: '台北' },
  Shenzhen: { lat: 22.5431, lng: 114.0579, zhName: '深圳' },
  Guangzhou: { lat: 23.1291, lng: 113.2644, zhName: '广州' },
  Chengdu: { lat: 30.5728, lng: 104.0668, zhName: '成都' },
  Hangzhou: { lat: 30.2741, lng: 120.1551, zhName: '杭州' },
}

export function lookupCity(city: string): CityCoord | undefined {
  return CITY_COORDS[city]
}
