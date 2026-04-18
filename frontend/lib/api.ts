/**
 * Backend API client
 * Maps frontend form values (English IDs) to backend Chinese enums,
 * calls POST /api/generate-perfume, then maps the response back to
 * the RecommendationOutput shape the UI expects.
 */

import type { UserPreferences, BiometricData, EnvironmentData, RecommendationOutput } from "@/lib/types"
import {
  OCCASIONS,
  SCENT_FAMILIES,
  LONGEVITY_OPTIONS,
  SILLAGE_OPTIONS,
  CONCENTRATION_OPTIONS,
  BUDGET_OPTIONS,
  TIME_OPTIONS,
  ACTIVITY_LEVELS,
  WEATHER_CONDITIONS,
  SEASONS,
} from "@/lib/types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ── Value maps: frontend ID → backend Chinese literal ──────────

const OCCASION_MAP: Record<string, string> = {
  work: "职场",
  date: "约会",
  sport: "运动",
  daily: "日常",
  social: "社交聚会",
  formal: "正式场合",
  home: "居家",
}

const SCENT_MAP: Record<string, string> = {
  citrus: "柑橘",
  floral: "花香",
  woody: "木质",
  oriental: "东方/辛辣",
  fresh: "海洋/清新",
  herbal: "青草/绿叶",
  spicy: "东方/辛辣",  // merged with oriental in backend
  sweet: "美食调",
  musky: "麝香",
  leather: "木质",    // closest backend equivalent
}

const LONGEVITY_MAP: Record<string, string> = {
  short: "2小时以内",
  medium: "2-4小时",
  long: "4-6小时",
  extended: "6小时以上",
}

const SILLAGE_MAP: Record<string, string> = {
  intimate: "贴身",
  close: "近距离",
  moderate: "中等扩散",
  strong: "强扩散",
}

const CONCENTRATION_MAP: Record<string, string> = {
  edt: "淡香水(EDT)",
  edp: "香水(EDP)",
  parfum: "浓香水",
  extrait: "香精",
}

const BUDGET_MAP: Record<string, string> = {
  budget: "经济",
  midrange: "中档",
  premium: "高档",
  luxury: "奢华",
}

const TIME_MAP: Record<string, string> = {
  morning: "清晨",
  afternoon: "下午",
  evening: "傍晚",
  allday: "上午",
}

const ACTIVITY_MAP: Record<string, string> = {
  resting: "静息",
  light: "轻度活动",
  moderate: "中度活动",
  intense: "剧烈运动",
}

const CONDITION_MAP: Record<string, string> = {
  sunny: "晴天",
  cloudy: "阴天",
  rainy: "小雨",
}

const SEASON_MAP: Record<string, string> = {
  spring: "春",
  summer: "夏",
  autumn: "秋",
  winter: "冬",
}

// ── City name → [latitude, longitude] ─────────────────────────

const CITY_COORDS: Record<string, [number, number]> = {
  "Shanghai": [31.2304, 121.4737],
  "Beijing": [39.9042, 116.4074],
  "Hong Kong": [22.3193, 114.1694],
  "Tokyo": [35.6762, 139.6503],
  "Singapore": [1.3521, 103.8198],
  "Seoul": [37.5665, 126.9780],
  "Bangkok": [13.7563, 100.5018],
  "Dubai": [25.2048, 55.2708],
  "Paris": [48.8566, 2.3522],
  "London": [51.5074, -0.1278],
  "Milan": [45.4642, 9.1900],
  "New York": [40.7128, -74.0060],
  "Los Angeles": [34.0522, -118.2437],
  "Sydney": [-33.8688, 151.2093],
  "Mumbai": [19.0760, 72.8777],
  "Taipei": [25.0330, 121.5654],
  "Shenzhen": [22.5431, 114.0579],
  "Guangzhou": [23.1291, 113.2644],
  "Chengdu": [30.5728, 104.0668],
  "Hangzhou": [30.2741, 120.1551],
}

// ── Computed field helpers ─────────────────────────────────────

function getTempLevel(temp: number): string {
  if (temp < 10) return "寒冷(<10°C)"
  if (temp < 20) return "凉爽(10-20°C)"
  if (temp < 30) return "温暖(20-30°C)"
  return "炎热(>30°C)"
}

function getHumidityLevel(humidity: number): string {
  if (humidity < 40) return "干燥(<40%)"
  if (humidity <= 70) return "适中(40-70%)"
  return "潮湿(>70%)"
}

// Deduplicate after mapping (e.g. spicy+oriental both → 东方/辛辣)
function mapScentIds(ids: string[]): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const id of ids) {
    const mapped = SCENT_MAP[id]
    if (mapped && !seen.has(mapped)) {
      seen.add(mapped)
      result.push(mapped)
    }
  }
  return result.length > 0 ? result : ["柑橘"]
}

// ── Backend response shape ─────────────────────────────────────

interface FormulaNote {
  name: string
  percentage: number
  diffusion_distance: string
  ingredient_id: number | null
}

interface FinalOutput {
  formula: {
    top_notes: FormulaNote[]
    middle_notes: FormulaNote[]
    base_notes: FormulaNote[]
  }
  scent_description: string
  selection_rationale: string
  volume_ml: number
  estimated_longevity_hours: number
  concentration_percentage: number
}

// ── Main API function ──────────────────────────────────────────

export async function generatePerfumeViaAPI(
  preferences: UserPreferences,
  biometrics: BiometricData,
  environment: EnvironmentData
): Promise<RecommendationOutput> {
  const [lat, lng] = CITY_COORDS[environment.city] ?? [31.2304, 121.4737]

  const body = {
    user_text: preferences.free_description || "",
    watch_data: {
      body_temperature: biometrics.body_temperature,
      latitude: lat,
      longitude: lng,
      heart_rate: biometrics.heart_rate,
      activity_level: ACTIVITY_MAP[biometrics.activity_level] ?? "静息",
    },
    questionnaire: {
      occasion: OCCASION_MAP[preferences.occasion] ?? "日常",
      scent_preference: mapScentIds(preferences.scent_preference),
      longevity: LONGEVITY_MAP[preferences.longevity] ?? "2-4小时",
      sillage: SILLAGE_MAP[preferences.sillage] ?? "近距离",
      concentration: CONCENTRATION_MAP[preferences.concentration] ?? "香水(EDP)",
      budget_level: BUDGET_MAP[preferences.budget_level] ?? "中档",
      avoided_notes: preferences.avoided_notes
        .map((id) => SCENT_MAP[id] ?? id)
        .filter(Boolean),
      time_of_day: TIME_MAP[preferences.time_of_day] ?? "下午",
    },
    weather: {
      temperature: environment.temperature,
      humidity: environment.humidity,
      condition: CONDITION_MAP[environment.condition] ?? "晴天",
      city: environment.city,
      season: SEASON_MAP[environment.season] ?? "春",
      temp_level: getTempLevel(environment.temperature),
      humidity_level: getHumidityLevel(environment.humidity),
    },
  }

  const res = await fetch(`${API_BASE}/api/generate-perfume`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(`Backend ${res.status}: ${msg}`)
  }

  const data: FinalOutput = await res.json()

  // ── Label helpers (use the same lookup tables as before) ──────
  const label = <T extends { id: string; nameZh: string }>(list: T[], id: string) =>
    list.find((o) => o.id === id)?.nameZh ?? id

  return {
    occasion: label(OCCASIONS, preferences.occasion || "daily"),
    scent_preference: preferences.scent_preference.map((id) =>
      label(SCENT_FAMILIES, id)
    ),
    longevity: label(LONGEVITY_OPTIONS, preferences.longevity || "medium"),
    sillage: label(SILLAGE_OPTIONS, preferences.sillage || "close"),
    concentration: label(CONCENTRATION_OPTIONS, preferences.concentration || "edp"),
    budget_level: label(BUDGET_OPTIONS, preferences.budget_level || "midrange"),
    avoided_notes: preferences.avoided_notes.map((id) =>
      label(SCENT_FAMILIES, id)
    ),
    time_of_day: label(TIME_OPTIONS, preferences.time_of_day || "afternoon"),
    body_temperature: biometrics.body_temperature,
    heart_rate: biometrics.heart_rate,
    activity_level: label(ACTIVITY_LEVELS, biometrics.activity_level),
    temperature: environment.temperature,
    humidity: environment.humidity,
    condition: label(WEATHER_CONDITIONS, environment.condition),
    season: label(SEASONS, environment.season),
    city: environment.city,
    analysis_summary: data.selection_rationale,
    fragrance_notes: {
      topNotes: data.formula.top_notes.map((n) => n.name),
      middleNotes: data.formula.middle_notes.map((n) => n.name),
      baseNotes: data.formula.base_notes.map((n) => n.name),
    },
    fragrance_description: {
      zh: data.scent_description,
      en: data.scent_description,
    },
  }
}
