export type ZhActivityLevel = '静息' | '轻度活动' | '中度活动' | '剧烈运动'
export type ZhOccasion = '日常' | '职场' | '约会' | '社交聚会' | '运动' | '居家' | '正式场合'
export type ZhScentFamily =
  | '花香'
  | '木质'
  | '柑橘'
  | '东方/辛辣'
  | '海洋/清新'
  | '美食调'
  | '麝香'
  | '青草/绿叶'
export type ZhLongevity = '2小时以内' | '2-4小时' | '4-6小时' | '6小时以上'
export type ZhSillage = '贴身' | '近距离' | '中等扩散' | '强扩散'
export type ZhConcentration = '淡香水(EDT)' | '香水(EDP)' | '浓香水' | '香精'
export type ZhBudget = '经济' | '中档' | '高档' | '奢华'
export type ZhTimeOfDay = '清晨' | '上午' | '下午' | '傍晚' | '夜间'
export type ZhSeason = '春' | '夏' | '秋' | '冬'
export type ZhTempLevel = '寒冷(<10°C)' | '凉爽(10-20°C)' | '温暖(20-30°C)' | '炎热(>30°C)'
export type ZhHumidityLevel = '干燥(<40%)' | '适中(40-70%)' | '潮湿(>70%)'
export type ZhDiffusionDistance = '贴身' | '近距离' | '中等' | '强扩散'

export interface AppleWatchData {
  body_temperature: number
  latitude: number
  longitude: number
  heart_rate?: number | null
  activity_level: ZhActivityLevel
}

export interface WeatherInfo {
  temperature: number
  humidity: number
  condition: string
  city: string
  season: ZhSeason
  temp_level: ZhTempLevel
  humidity_level: ZhHumidityLevel
}

export interface QuestionnaireAnswers {
  occasion: ZhOccasion
  scent_preference: ZhScentFamily[]
  longevity: ZhLongevity
  sillage: ZhSillage
  concentration: ZhConcentration
  budget_level: ZhBudget
  avoided_notes: string[]
  time_of_day: ZhTimeOfDay
}

export interface Agent1Input {
  user_text?: string
  watch_data: AppleWatchData
  questionnaire: QuestionnaireAnswers
  weather?: WeatherInfo
}

export interface FormulaNote {
  name: string
  percentage: number
  diffusion_distance: ZhDiffusionDistance
  ingredient_id?: number | null
}

export interface PerfumeFormula {
  top_notes: FormulaNote[]
  middle_notes: FormulaNote[]
  base_notes: FormulaNote[]
}

export interface FinalOutput {
  formula: PerfumeFormula
  scent_description: string
  selection_rationale: string
  volume_ml: number
  estimated_longevity_hours: number
  concentration_percentage: number
  weather_snapshot?: WeatherInfo | null
}

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}
