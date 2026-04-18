export interface UserPreferences {
  occasion: string
  scent_preference: string[]
  longevity: string
  sillage: string
  concentration: string
  budget_level: string
  avoided_notes: string[]
  time_of_day: string
  free_description: string
}

export interface BiometricData {
  body_temperature: number
  heart_rate: number
  activity_level: string
}

export interface EnvironmentData {
  city: string
  temperature: number
  humidity: number
  condition: string
  season: string
}

export interface RecommendationOutput {
  occasion: string
  scent_preference: string[]
  longevity: string
  sillage: string
  concentration: string
  budget_level: string
  avoided_notes: string[]
  time_of_day: string
  body_temperature: number
  heart_rate: number
  activity_level: string
  temperature: number
  humidity: number
  condition: string
  season: string
  city: string
  analysis_summary: string
  fragrance_notes: FragranceNotes
  fragrance_description: FragranceDescription
}

export const SCENT_FAMILIES = [
  { id: 'citrus', name: 'Citrus', nameZh: '柑橘调' },
  { id: 'floral', name: 'Floral', nameZh: '花香调' },
  { id: 'woody', name: 'Woody', nameZh: '木质调' },
  { id: 'oriental', name: 'Oriental', nameZh: '东方调' },
  { id: 'fresh', name: 'Fresh/Aquatic', nameZh: '水生调' },
  { id: 'herbal', name: 'Herbal', nameZh: '草本调' },
  { id: 'spicy', name: 'Spicy', nameZh: '辛辣调' },
  { id: 'sweet', name: 'Sweet/Gourmand', nameZh: '美食调' },
  { id: 'musky', name: 'Musky', nameZh: '麝香调' },
  { id: 'leather', name: 'Leather', nameZh: '皮革调' },
]

export const OCCASIONS = [
  { id: 'work', name: 'Work/Office', nameZh: '职场' },
  { id: 'date', name: 'Date Night', nameZh: '约会' },
  { id: 'sport', name: 'Sports/Active', nameZh: '运动' },
  { id: 'daily', name: 'Daily Casual', nameZh: '日常' },
  { id: 'social', name: 'Social Events', nameZh: '社交' },
  { id: 'formal', name: 'Formal/Special', nameZh: '正式' },
]

export const LONGEVITY_OPTIONS = [
  { id: 'short', name: 'Under 2 hours', nameZh: '2小时以内' },
  { id: 'medium', name: '2-4 hours', nameZh: '2-4小时' },
  { id: 'long', name: '4-6 hours', nameZh: '4-6小时' },
  { id: 'extended', name: '6+ hours', nameZh: '6小时以上' },
]

export const SILLAGE_OPTIONS = [
  { id: 'intimate', name: 'Intimate', nameZh: '贴身' },
  { id: 'close', name: 'Close Range', nameZh: '近距离' },
  { id: 'moderate', name: 'Moderate', nameZh: '中等扩散' },
  { id: 'strong', name: 'Strong Projection', nameZh: '强扩散' },
]

export const CONCENTRATION_OPTIONS = [
  { id: 'edt', name: 'Eau de Toilette', nameZh: '淡香水' },
  { id: 'edp', name: 'Eau de Parfum', nameZh: '香水' },
  { id: 'parfum', name: 'Parfum', nameZh: '浓香水' },
  { id: 'extrait', name: 'Extrait', nameZh: '香精' },
]

export const BUDGET_OPTIONS = [
  { id: 'budget', name: 'Budget', nameZh: '经济', range: '$30-60' },
  { id: 'midrange', name: 'Mid-Range', nameZh: '中档', range: '$60-120' },
  { id: 'premium', name: 'Premium', nameZh: '高档', range: '$120-250' },
  { id: 'luxury', name: 'Luxury', nameZh: '奢华', range: '$250+' },
]

export const TIME_OPTIONS = [
  { id: 'morning', name: 'Morning', nameZh: '早晨' },
  { id: 'afternoon', name: 'Afternoon', nameZh: '下午' },
  { id: 'evening', name: 'Evening', nameZh: '晚间' },
  { id: 'allday', name: 'All Day', nameZh: '全天' },
]

export const ACTIVITY_LEVELS = [
  { id: 'resting', name: 'Resting', nameZh: '静息' },
  { id: 'light', name: 'Light Activity', nameZh: '轻度活动' },
  { id: 'moderate', name: 'Moderate Activity', nameZh: '中度活动' },
  { id: 'intense', name: 'Intense Exercise', nameZh: '剧烈运动' },
]

export const WEATHER_CONDITIONS = [
  { id: 'sunny', name: 'Sunny', nameZh: '晴天' },
  { id: 'cloudy', name: 'Cloudy', nameZh: '阴天' },
  { id: 'rainy', name: 'Rainy', nameZh: '雨天' },
]

export const SEASONS = [
  { id: 'spring', name: 'Spring', nameZh: '春' },
  { id: 'summer', name: 'Summer', nameZh: '夏' },
  { id: 'autumn', name: 'Autumn', nameZh: '秋' },
  { id: 'winter', name: 'Winter', nameZh: '冬' },
]

export const WORLD_CITIES = [
  { id: 'shanghai', name: 'Shanghai', nameZh: '上海', country: 'China' },
  { id: 'beijing', name: 'Beijing', nameZh: '北京', country: 'China' },
  { id: 'hongkong', name: 'Hong Kong', nameZh: '香港', country: 'China' },
  { id: 'tokyo', name: 'Tokyo', nameZh: '东京', country: 'Japan' },
  { id: 'singapore', name: 'Singapore', nameZh: '新加坡', country: 'Singapore' },
  { id: 'seoul', name: 'Seoul', nameZh: '首尔', country: 'South Korea' },
  { id: 'bangkok', name: 'Bangkok', nameZh: '曼谷', country: 'Thailand' },
  { id: 'dubai', name: 'Dubai', nameZh: '迪拜', country: 'UAE' },
  { id: 'paris', name: 'Paris', nameZh: '巴黎', country: 'France' },
  { id: 'london', name: 'London', nameZh: '伦敦', country: 'UK' },
  { id: 'milan', name: 'Milan', nameZh: '米兰', country: 'Italy' },
  { id: 'newyork', name: 'New York', nameZh: '纽约', country: 'USA' },
  { id: 'losangeles', name: 'Los Angeles', nameZh: '洛杉矶', country: 'USA' },
  { id: 'sydney', name: 'Sydney', nameZh: '悉尼', country: 'Australia' },
  { id: 'mumbai', name: 'Mumbai', nameZh: '孟买', country: 'India' },
  { id: 'taipei', name: 'Taipei', nameZh: '台北', country: 'Taiwan' },
  { id: 'shenzhen', name: 'Shenzhen', nameZh: '深圳', country: 'China' },
  { id: 'guangzhou', name: 'Guangzhou', nameZh: '广州', country: 'China' },
  { id: 'chengdu', name: 'Chengdu', nameZh: '成都', country: 'China' },
  { id: 'hangzhou', name: 'Hangzhou', nameZh: '杭州', country: 'China' },
]

export interface FragranceNotes {
  topNotes: string[]
  middleNotes: string[]
  baseNotes: string[]
}

export interface FragranceDescription {
  zh: string
  en: string
}
