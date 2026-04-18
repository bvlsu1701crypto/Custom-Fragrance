import type {
  ZhActivityLevel,
  ZhConcentration,
  ZhOccasion,
  ZhScentFamily,
  ZhSeason,
  ZhSillage,
  ZhTimeOfDay,
} from './schemas'

export const OCCASION_MAP: Record<string, ZhOccasion> = {
  work: '职场',
  date: '约会',
  sport: '运动',
  daily: '日常',
  social: '社交聚会',
  formal: '正式场合',
}

export const SILLAGE_MAP: Record<string, ZhSillage> = {
  intimate: '贴身',
  close: '近距离',
  moderate: '中等扩散',
  strong: '强扩散',
}

export const CONCENTRATION_MAP: Record<string, ZhConcentration> = {
  edt: '淡香水(EDT)',
  edp: '香水(EDP)',
  parfum: '浓香水',
  extrait: '香精',
}

export const TIME_MAP: Record<string, ZhTimeOfDay> = {
  morning: '上午',
  afternoon: '下午',
  evening: '夜间',
  allday: '上午',
}

export const ACTIVITY_MAP: Record<string, ZhActivityLevel> = {
  resting: '静息',
  light: '轻度活动',
  moderate: '中度活动',
  intense: '剧烈运动',
}

export const SEASON_MAP: Record<string, ZhSeason> = {
  spring: '春',
  summer: '夏',
  autumn: '秋',
  winter: '冬',
}

export const CONDITION_MAP: Record<string, string> = {
  sunny: '晴天',
  cloudy: '阴天',
  rainy: '雨天',
}

export const SCENT_MAP: Record<string, ZhScentFamily> = {
  citrus: '柑橘',
  floral: '花香',
  woody: '木质',
  oriental: '东方/辛辣',
  spicy: '东方/辛辣',
  fresh: '海洋/清新',
  herbal: '青草/绿叶',
  sweet: '美食调',
  musky: '麝香',
  leather: '木质',
}

function makeTranslator<T extends string>(
  map: Record<string, T>,
  fallback: T,
  label: string,
): (id: string) => T {
  return (id) => {
    const value = map[id]
    if (!value) {
      console.warn(`[api] unknown ${label} id: "${id}", falling back to "${fallback}"`)
      return fallback
    }
    return value
  }
}

export const toZhOccasion = makeTranslator(OCCASION_MAP, '日常', 'occasion')
export const toZhSillage = makeTranslator(SILLAGE_MAP, '近距离', 'sillage')
export const toZhConcentration = makeTranslator(CONCENTRATION_MAP, '香水(EDP)', 'concentration')
export const toZhTimeOfDay = makeTranslator(TIME_MAP, '上午', 'time_of_day')
export const toZhActivity = makeTranslator(ACTIVITY_MAP, '静息', 'activity_level')
export const toZhSeason = makeTranslator(SEASON_MAP, '春', 'season')
export const toZhCondition = makeTranslator(CONDITION_MAP, '晴天', 'condition')
export const toZhScent = makeTranslator(SCENT_MAP, '花香', 'scent_family')
