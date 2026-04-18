"use client"

import { useState } from "react"
import Image from "next/image"
import { Header } from "@/components/header"
import { CompanionManifestoSection } from "@/components/companion-manifesto-section"
import { PhilosophySection } from "@/components/philosophy-section"
import { ProgressSteps } from "@/components/progress-steps"
import { PreferencesForm } from "@/components/preferences-form"
import { BiometricCard } from "@/components/biometric-card"
import { EnvironmentCard } from "@/components/environment-card"
import { RecommendationResult } from "@/components/recommendation-result"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useLanguage } from "@/lib/language-context"
import type {
  UserPreferences,
  BiometricData,
  EnvironmentData,
  RecommendationOutput,
} from "@/lib/types"
import {
  SCENT_FAMILIES,
  OCCASIONS,
  LONGEVITY_OPTIONS,
  SILLAGE_OPTIONS,
  CONCENTRATION_OPTIONS,
  BUDGET_OPTIONS,
  TIME_OPTIONS,
  ACTIVITY_LEVELS,
  WEATHER_CONDITIONS,
  SEASONS,
} from "@/lib/types"
import { ArrowLeft, ArrowRight } from "lucide-react"

const STEPS_ZH = ["偏好", "生理", "环境", "结果"]
const STEPS_EN = ["Preferences", "Biometrics", "Environment", "Results"]

const initialPreferences: UserPreferences = {
  occasion: "",
  scent_preference: [],
  longevity: "",
  sillage: "",
  concentration: "",
  budget_level: "",
  avoided_notes: [],
  time_of_day: "",
  free_description: "",
}

const initialBiometrics: BiometricData = {
  body_temperature: 36.5,
  heart_rate: 72,
  activity_level: "resting",
}

const initialEnvironment: EnvironmentData = {
  city: "Shanghai",
  temperature: 22,
  humidity: 55,
  condition: "sunny",
  season: "spring",
}

const SCENT_NOTE_LIBRARY = {
  citrus: {
    top: ["佛手柑", "柠檬叶", "葡萄柚"],
    middle: ["橙花", "苦橙叶", "白茶"],
    base: ["白麝香", "香根草", "雪松"],
    openingZh: "以明亮的柑橘气息开启，带出干净、利落的第一印象",
    openingEn: "opens with a bright citrus lift, creating a clean and polished first impression",
    heartZh: "中段透出轻盈的花叶与茶感，让空气感更清澈",
    heartEn: "its heart carries airy petals and soft tea facets that keep the profile crystalline",
    baseZh: "尾韵则以柔和木质与白麝香收束，留下干净的轮廓",
    baseEn: "before settling into soft woods and white musk for a neat, refined dry-down",
  },
  floral: {
    top: ["梨子", "粉红胡椒", "橙花"],
    middle: ["茉莉", "玫瑰", "鸢尾"],
    base: ["麝香", "檀香", "琥珀"],
    openingZh: "开场带有细腻而有光泽的花瓣气息，温柔却不失存在感",
    openingEn: "begins with luminous petals that feel graceful, polished, and quietly expressive",
    heartZh: "花心层次在肌肤上慢慢舒展，显得柔和而立体",
    heartEn: "the floral heart unfurls slowly on skin, adding softness with dimensional depth",
    baseZh: "后调落在丝绒般的麝香与木质上，显得贴肤又优雅",
    baseEn: "it then rests on velvety musk and woods, staying elegant and close to the skin",
  },
  woody: {
    top: ["柏树", "豆蔻", "葡萄柚皮"],
    middle: ["雪松", "鸢尾根", "干草"],
    base: ["檀香", "岩兰草", "琥珀木"],
    openingZh: "前调带有克制的木质辛香，显得沉稳而有结构",
    openingEn: "starts with restrained woody spice, immediately giving the scent structure and composure",
    heartZh: "中调转向干净的雪松与根茎气息，带来冷静的深度",
    heartEn: "the heart moves into cedar and root-like facets, lending calm depth and clarity",
    baseZh: "基底则以温润木香拉长余韵，留下安静的力量感",
    baseEn: "its base stretches the trail with smooth woods, leaving behind a quiet sense of strength",
  },
  oriental: {
    top: ["藏红花", "粉红胡椒", "肉桂"],
    middle: ["琥珀", "玫瑰", "焚香"],
    base: ["安息香", "广藿香", "香草荚"],
    openingZh: "起笔微带辛香与树脂感，氛围感浓郁而富有层次",
    openingEn: "enters with spice and resin, instantly creating a denser and more atmospheric aura",
    heartZh: "中段的琥珀与香脂气息逐渐升温，呈现出包裹感",
    heartEn: "ambered resins build through the heart, making the composition warmer and more enveloping",
    baseZh: "尾声沉入香草与广藿香的深处，显得绵密、持久且迷人",
    baseEn: "the finish sinks into vanilla and patchouli, giving it a long, textured, and magnetic finish",
  },
  fresh: {
    top: ["海盐", "青柠", "黄瓜"],
    middle: ["水生花瓣", "鼠尾草", "绿叶"],
    base: ["漂流木", "白麝香", "矿石气息"],
    openingZh: "最初像一阵带湿度的空气拂面，通透、轻快而醒神",
    openingEn: "arrives like cool air against the skin, transparent, brisk, and instantly awakening",
    heartZh: "中调保留了水感与绿意，让整体显得松弛而有呼吸感",
    heartEn: "aquatic and green facets keep the heart relaxed and breathable",
    baseZh: "收尾留下一点矿物与漂流木的洁净感，克制却很耐闻",
    baseEn: "a mineral, driftwood-like finish keeps the dry-down restrained and highly wearable",
  },
  herbal: {
    top: ["迷迭香", "罗勒", "青柠皮"],
    middle: ["薰衣草", "快乐鼠尾草", "紫苏"],
    base: ["苔藓", "雪松", "白麝香"],
    openingZh: "开头带有草叶被揉碎后的清苦香气，显得清醒而克制",
    openingEn: "opens with crushed herbs and leafy bitterness, giving it an alert and restrained character",
    heartZh: "中段的芳香植物感让轮廓更清晰，也更有呼吸感",
    heartEn: "aromatic herbs shape the heart with sharper contours and more air",
    baseZh: "尾调落在苔藓和木质上，干净中带一点自然的粗粝",
    baseEn: "moss and woods in the base leave behind a natural dryness with subtle texture",
  },
  spicy: {
    top: ["黑胡椒", "姜", "小豆蔻"],
    middle: ["肉桂叶", "康乃馨", "焚香"],
    base: ["琥珀", "愈创木", "零陵香豆"],
    openingZh: "前调有鲜明的辛香节奏，利落地拉起存在感",
    openingEn: "its opening has a vivid spicy pulse that sharpens the scent's presence immediately",
    heartZh: "中调热度渐深，带出更成熟也更立体的层次",
    heartEn: "the warmth deepens through the heart, giving the composition maturity and contrast",
    baseZh: "收尾则靠琥珀与木香托住热度，显得有张力却不过分张扬",
    baseEn: "amber and woods in the base support that warmth without making it overwhelming",
  },
  sweet: {
    top: ["焦糖奶油", "梨", "可可"],
    middle: ["香草兰", "杏仁花", "零陵香豆"],
    base: ["琥珀", "檀香", "麝香"],
    openingZh: "开场有柔软的甜感，像光线照在奶油与果肉表面",
    openingEn: "opens with a plush sweetness, like light touching cream and ripe fruit",
    heartZh: "中调的香草与杏仁感让它显得温柔、圆润，也更亲近人",
    heartEn: "vanilla and almond tones round out the heart, making it tender and approachable",
    baseZh: "尾调保留了柔滑的余温，甜而不腻，带着细腻的包覆感",
    baseEn: "the dry-down keeps a smooth residual warmth that feels indulgent without becoming heavy",
  },
  musky: {
    top: ["白棉花", "醛香", "梨花"],
    middle: ["鸢尾", "白玫瑰", "皮肤气息"],
    base: ["白麝香", "开司米木", "龙涎香调"],
    openingZh: "一开始像刚换上的干净织物，温柔、轻盈，又很贴近皮肤",
    openingEn: "begins like clean fabric against skin, soft, airy, and intimately close",
    heartZh: "中调逐渐显出粉感与肤感，营造出安静的亲密距离",
    heartEn: "powdery and skin-like nuances appear in the heart, creating a quiet intimacy",
    baseZh: "后调则像体温留在织物上的余韵，细腻而持久",
    baseEn: "the base lingers like body warmth on fabric, delicate yet persistent",
  },
  leather: {
    top: ["藏红花", "佛手柑", "黑胡椒"],
    middle: ["皮革", "紫罗兰叶", "柏木"],
    base: ["烟熏木", "琥珀", "广藿香"],
    openingZh: "前调带一点冷感辛香，像皮革表面被光线擦过的瞬间",
    openingEn: "opens with cool spice, like light passing over the surface of polished leather",
    heartZh: "中段皮革质感逐渐展开，利落、干燥且带一点锋利感",
    heartEn: "the leather texture expands through the heart, dry, precise, and slightly sharp-edged",
    baseZh: "底部的烟熏木质让它留下更深的轮廓，显得成熟而有态度",
    baseEn: "smoky woods in the base deepen the silhouette, giving it maturity and attitude",
  },
} as const

function pickVariant<T>(items: T[], seed: string) {
  const index = Array.from(seed).reduce((sum, char) => sum + char.charCodeAt(0), 0) % items.length
  return items[index]
}

function getPrimaryScentIds(scentIds: string[]) {
  return Array.from(new Set(scentIds)).slice(0, 3)
}

function ensureZhSentence(text: string) {
  return /[。！？]$/.test(text) ? text : `${text}。`
}

function ensureEnSentence(text: string) {
  return /[.!?]$/.test(text) ? text : `${text}.`
}

function buildFragranceNotes(scentIds: string[]) {
  const primaryIds = getPrimaryScentIds(scentIds)
  const topNotes = primaryIds.flatMap((id) => SCENT_NOTE_LIBRARY[id as keyof typeof SCENT_NOTE_LIBRARY]?.top || [])
  const middleNotes = primaryIds.flatMap((id) => SCENT_NOTE_LIBRARY[id as keyof typeof SCENT_NOTE_LIBRARY]?.middle || [])
  const baseNotes = primaryIds.flatMap((id) => SCENT_NOTE_LIBRARY[id as keyof typeof SCENT_NOTE_LIBRARY]?.base || [])

  return {
    topNotes: Array.from(new Set(topNotes)).slice(0, 3),
    middleNotes: Array.from(new Set(middleNotes)).slice(0, 3),
    baseNotes: Array.from(new Set(baseNotes)).slice(0, 3),
  }
}

function buildFragranceDescription({
  scentIds,
  preferences,
  biometrics,
  environment,
  adjustedConcentration,
  adjustedSillage,
}: {
  scentIds: string[]
  preferences: UserPreferences
  biometrics: BiometricData
  environment: EnvironmentData
  adjustedConcentration: string
  adjustedSillage: string
}) {
  const primaryIds = getPrimaryScentIds(scentIds)
  const primaryProfiles = primaryIds
    .map((id) => SCENT_NOTE_LIBRARY[id as keyof typeof SCENT_NOTE_LIBRARY])
    .filter(Boolean)

  const openingZh = primaryProfiles.map((profile) => profile.openingZh)
  const heartZh = primaryProfiles.map((profile) => profile.heartZh)
  const baseZh = primaryProfiles.map((profile) => profile.baseZh)
  const openingEn = primaryProfiles.map((profile) => profile.openingEn)
  const heartEn = primaryProfiles.map((profile) => profile.heartEn)
  const baseEn = primaryProfiles.map((profile) => profile.baseEn)

  const occasionToneZh = {
    work: "整体克制而有分寸，适合在近距离中留下专业、稳定的印象",
    date: "它会在靠近时显得更有温度，让氛围自然变得亲密",
    sport: "整体轻快不黏腻，更强调清爽与行动中的舒适度",
    daily: "穿起来没有负担，像你日常状态里最自然的一面",
    social: "在社交场景里，它会比平时更有记忆点，但不过度抢戏",
    formal: "轮廓更完整也更讲究，适合正式场合里需要被认真感知的时刻",
  } as const
  const occasionToneEn = {
    work: "The overall tone stays measured and composed, ideal for leaving a professional impression at close range.",
    date: "It feels warmer as someone gets closer, letting intimacy build naturally.",
    sport: "The composition stays brisk and non-cloying, prioritizing freshness and comfort in motion.",
    daily: "It wears easily, like the most natural extension of your everyday state.",
    social: "In social settings it has more memorability than a basic daily scent, without becoming performative.",
    formal: "Its silhouette feels more complete and intentional, fitting moments that call for polish and presence.",
  } as const

  const climateToneZh = environment.temperature > 28 && environment.humidity > 70
    ? "考虑到当下偏热且潮湿的环境，这支香会更强调通透感与扩散时的清洁边界。"
    : environment.temperature < 15 && environment.humidity < 40
      ? "在偏冷偏干的空气里，它的木质与暖感会被托得更完整，尾韵也更有包裹性。"
      : "在当前的温湿度条件下，它会以相对平衡的节奏展开，前中后调衔接自然。"
  const climateToneEn = environment.temperature > 28 && environment.humidity > 70
    ? "Because the air is currently hot and humid, the scent leans into transparency and a cleaner boundary in projection."
    : environment.temperature < 15 && environment.humidity < 40
      ? "In cooler, drier air, its woods and warmth gain more shape, and the dry-down feels more enveloping."
      : "In the current temperature and humidity, it unfolds at a balanced pace with a natural transition from top to base."

  const bodyToneZh = biometrics.activity_level === "intense" || biometrics.activity_level === "moderate"
    ? "结合你当前偏活跃的身体状态，推荐会更偏轻盈，避免在体温上升时显得厚重。"
    : biometrics.body_temperature > 37
      ? "考虑到体温略高，整体会更偏向清透和提气，减少闷感。"
      : "在你当前的身体状态下，它会以较从容的方式贴合肌肤，层次释放更平滑。"
  const bodyToneEn = biometrics.activity_level === "intense" || biometrics.activity_level === "moderate"
    ? "Given your more active body state, the recommendation stays lighter so it won't feel dense as body heat rises."
    : biometrics.body_temperature > 37
      ? "With slightly elevated body temperature, the profile shifts toward clarity and lift to avoid feeling stuffy."
      : "With your current body state, it sits on skin in a more composed way and reveals its layers smoothly."

  const concentrationToneZh = {
    edt: "浓度偏轻，存在感更像一层流动的空气。",
    edp: "浓度适中，既能保留轮廓，也不会压过你的日常状态。",
    parfum: "更高的浓度让细节更凝练，香气的存在感也更稳定。",
    extrait: "高浓度会让香气显得更饱满，层次贴得更紧，也更有戏剧性。",
  } as const
  const concentrationToneEn = {
    edt: "Its lighter concentration makes the presence feel almost like moving air around you.",
    edp: "The concentration stays balanced, preserving definition without overpowering your day-to-day rhythm.",
    parfum: "A richer concentration tightens the details and makes the scent feel more constant in presence.",
    extrait: "At this higher concentration, the fragrance becomes fuller, denser, and more dramatic in its layering.",
  } as const

  const sillageToneZh = {
    intimate: "扩散范围贴身，更适合让人靠近之后才慢慢察觉。",
    close: "扩散控制在舒适范围内，能被感受到，但不会先于你进入房间。",
    moderate: "中等扩散让它在移动时留下适度痕迹，兼顾存在感与分寸。",
    strong: "更明显的扩散会把气场向外推开，适合希望香气承担更多表达的时刻。",
  } as const
  const sillageToneEn = {
    intimate: "Its projection stays close, revealing itself gradually only when someone enters your space.",
    close: "The sillage stays comfortable and noticeable without entering a room before you do.",
    moderate: "Moderate projection leaves a measured trace in motion, balancing presence with restraint.",
    strong: "A stronger sillage pushes the aura outward, better for moments when you want the scent to speak more clearly.",
  } as const

  const timeToneZh = {
    morning: "它尤其适合早晨的节奏，干净、提气，又不会打断思路。",
    afternoon: "放在下午使用，会显得清晰而稳定，适合延续一整天的状态。",
    evening: "到了傍晚以后，香气里的层次会显得更柔和，也更有氛围。",
    allday: "作为全天使用的气味，它在存在感与耐闻度之间拿捏得比较均衡。",
  } as const
  const timeToneEn = {
    morning: "It feels especially right for mornings: clear, uplifting, and never mentally disruptive.",
    afternoon: "Worn in the afternoon, it reads as steady and focused, extending the shape of the day.",
    evening: "By evening, its layers feel softer and more atmospheric.",
    allday: "As an all-day profile, it balances wearability with a clear point of view.",
  } as const

  const seed = [preferences.occasion, preferences.time_of_day, environment.season, primaryIds.join("-")].join("|")
  const zhLead = pickVariant([
    "这支推荐不是单纯把几种常见香调叠在一起，",
    "这次生成的气味轮廓，更像是从你的选择里慢慢长出来的，",
    "如果把这次结果想象成一段气味叙事，它的开头并不仓促，",
  ], seed)
  const enLead = pickVariant([
    "This recommendation doesn't read like a generic blend of familiar accords; rather, it ",
    "What emerged here feels less like a preset perfume profile and more like something shaped by your choices: it ",
    "If this result were read as a scent narrative, it would begin without rushing; it ",
  ], seed)

  const zhSentences = [
    ensureZhSentence(`${zhLead}${openingZh[0] || "从清晰的前调开始"}`),
    ensureZhSentence(heartZh[0] || "中调逐渐展开层次"),
    heartZh[1] ? ensureZhSentence(heartZh[1]) : "",
    ensureZhSentence(baseZh[0] || "最后落在更稳定的基底上"),
    ensureZhSentence(occasionToneZh[(preferences.occasion || "daily") as keyof typeof occasionToneZh] || occasionToneZh.daily),
    ensureZhSentence(timeToneZh[(preferences.time_of_day || "allday") as keyof typeof timeToneZh] || timeToneZh.allday),
    climateToneZh,
    bodyToneZh,
    ensureZhSentence(concentrationToneZh[(adjustedConcentration || "edp") as keyof typeof concentrationToneZh] || concentrationToneZh.edp),
    ensureZhSentence(sillageToneZh[(adjustedSillage || "close") as keyof typeof sillageToneZh] || sillageToneZh.close),
  ].filter(Boolean)

  const enSentences = [
    ensureEnSentence(`${enLead}${openingEn[0] || "begins with a clear and balanced opening"}`),
    ensureEnSentence(heartEn[0] || "Its heart develops with measured layering"),
    heartEn[1] ? ensureEnSentence(heartEn[1]) : "",
    ensureEnSentence(baseEn[0] || "It settles into a more grounded base over time"),
    ensureEnSentence(occasionToneEn[(preferences.occasion || "daily") as keyof typeof occasionToneEn] || occasionToneEn.daily),
    ensureEnSentence(timeToneEn[(preferences.time_of_day || "allday") as keyof typeof timeToneEn] || timeToneEn.allday),
    climateToneEn,
    bodyToneEn,
    ensureEnSentence(concentrationToneEn[(adjustedConcentration || "edp") as keyof typeof concentrationToneEn] || concentrationToneEn.edp),
    ensureEnSentence(sillageToneEn[(adjustedSillage || "close") as keyof typeof sillageToneEn] || sillageToneEn.close),
  ].filter(Boolean)

  const zh = zhSentences.join("")
  const en = enSentences.join(" ")

  return { zh, en }
}

function generateRecommendation(
  preferences: UserPreferences,
  biometrics: BiometricData,
  environment: EnvironmentData
): RecommendationOutput {
  let adjustedConcentration = preferences.concentration
  let adjustedSillage = preferences.sillage
  let adjustedScents = [...preferences.scent_preference]
  const summaryParts: string[] = []

  if (biometrics.body_temperature > 37) {
    adjustedConcentration = "edt"
    if (!adjustedScents.includes("citrus")) adjustedScents.push("citrus")
    if (!adjustedScents.includes("fresh")) adjustedScents.push("fresh")
    summaryParts.push("Elevated body temperature detected - recommending lighter, fresher options")
  }

  if (biometrics.activity_level === "intense" || biometrics.activity_level === "moderate") {
    adjustedConcentration = "edt"
    adjustedSillage = adjustedSillage === "strong" || adjustedSillage === "moderate" ? "close" : adjustedSillage
    summaryParts.push("Active state detected - reducing projection for comfort")
  }

  if (environment.temperature > 28 && environment.humidity > 70) {
    if (!adjustedScents.includes("citrus")) adjustedScents.push("citrus")
    if (!adjustedScents.includes("fresh")) adjustedScents.push("fresh")
    if (!adjustedScents.includes("herbal")) adjustedScents.push("herbal")
    summaryParts.push("Hot and humid environment - emphasizing fresh, aquatic notes")
  } else if (environment.temperature < 15 && environment.humidity < 40) {
    if (!adjustedScents.includes("woody")) adjustedScents.push("woody")
    if (!adjustedScents.includes("oriental")) adjustedScents.push("oriental")
    if (!adjustedScents.includes("spicy")) adjustedScents.push("spicy")
    summaryParts.push("Cool and dry conditions - favoring warm, enveloping scents")
  }

  if (preferences.occasion === "work" || preferences.occasion === "formal") {
    if (adjustedSillage === "strong" || adjustedSillage === "moderate") {
      adjustedSillage = "close"
    }
    adjustedScents = adjustedScents.filter((s) => s !== "sweet")
    summaryParts.push("Professional setting - keeping projection subtle and sophisticated")
  } else if (preferences.occasion === "sport") {
    adjustedSillage = "intimate"
    adjustedConcentration = "edt"
    summaryParts.push("Athletic activity - light and close projection recommended")
  }

  // Enhanced: User's additional notes have higher priority influence
  if (preferences.free_description) {
    const desc = preferences.free_description.toLowerCase()
    const userNoteParts: string[] = []
    
    // Fresh/Light preferences - prioritize citrus and fresh notes
    if (desc.includes("fresh") || desc.includes("light") || desc.includes("清新") || desc.includes("清爽") || desc.includes("淡")) {
      adjustedScents = adjustedScents.filter(s => s !== "oriental" && s !== "sweet")
      if (!adjustedScents.includes("citrus")) adjustedScents.unshift("citrus")
      if (!adjustedScents.includes("fresh")) adjustedScents.unshift("fresh")
      adjustedConcentration = "edt"
      userNoteParts.push("fresh and light profile prioritized")
    }
    
    // Long-lasting preferences
    if (desc.includes("long") || desc.includes("lasting") || desc.includes("持久") || desc.includes("持香")) {
      adjustedConcentration = "parfum"
      userNoteParts.push("extended longevity emphasized")
    }
    
    // Subtle/Not too strong preferences
    if (desc.includes("subtle") || desc.includes("不要太浓") || desc.includes("不要太强") || desc.includes("低调")) {
      adjustedSillage = "intimate"
      adjustedConcentration = "edt"
      userNoteParts.push("subtle projection selected")
    }
    
    // Sweet/Gourmand preferences
    if (desc.includes("sweet") || desc.includes("甜") || desc.includes("美食")) {
      if (!adjustedScents.includes("sweet")) adjustedScents.unshift("sweet")
      userNoteParts.push("gourmand notes added")
    }
    
    // Woody/Warm preferences
    if (desc.includes("woody") || desc.includes("warm") || desc.includes("木质") || desc.includes("温暖")) {
      if (!adjustedScents.includes("woody")) adjustedScents.unshift("woody")
      if (!adjustedScents.includes("oriental")) adjustedScents.unshift("oriental")
      userNoteParts.push("warm woody character emphasized")
    }
    
    // Floral preferences
    if (desc.includes("floral") || desc.includes("flower") || desc.includes("花香") || desc.includes("花")) {
      if (!adjustedScents.includes("floral")) adjustedScents.unshift("floral")
      userNoteParts.push("floral notes highlighted")
    }
    
    // Strong/Powerful preferences
    if (desc.includes("strong") || desc.includes("powerful") || desc.includes("浓") || desc.includes("强烈")) {
      adjustedSillage = "strong"
      adjustedConcentration = "parfum"
      userNoteParts.push("bold projection selected")
    }
    
    // Unisex/Gender-neutral preferences
    if (desc.includes("unisex") || desc.includes("neutral") || desc.includes("中性")) {
      adjustedScents = adjustedScents.filter(s => s !== "sweet")
      if (!adjustedScents.includes("woody")) adjustedScents.push("woody")
      if (!adjustedScents.includes("citrus")) adjustedScents.push("citrus")
      userNoteParts.push("unisex character maintained")
    }
    
    // Masculine preferences
    if (desc.includes("masculine") || desc.includes("男性") || desc.includes("阳刚")) {
      if (!adjustedScents.includes("woody")) adjustedScents.unshift("woody")
      if (!adjustedScents.includes("leather")) adjustedScents.unshift("leather")
      adjustedScents = adjustedScents.filter(s => s !== "floral" && s !== "sweet")
      userNoteParts.push("masculine profile shaped")
    }
    
    // Feminine preferences
    if (desc.includes("feminine") || desc.includes("女性") || desc.includes("柔美")) {
      if (!adjustedScents.includes("floral")) adjustedScents.unshift("floral")
      if (!adjustedScents.includes("musky")) adjustedScents.unshift("musky")
      userNoteParts.push("feminine elegance crafted")
    }
    
    // Special occasion mentions
    if (desc.includes("special") || desc.includes("特别") || desc.includes("重要") || desc.includes("important")) {
      adjustedConcentration = "parfum"
      userNoteParts.push("special occasion intensity applied")
    }
    
    if (userNoteParts.length > 0) {
      summaryParts.push("Based on your personal notes: " + userNoteParts.join(", "))
    }
  }

  if (adjustedScents.length === 0) {
    adjustedScents = ["woody", "citrus"]
  }

  const summary = summaryParts.length > 0 
    ? summaryParts.join(". ") + "."
    : "Based on your preferences and current conditions, we recommend a balanced fragrance profile suited to your lifestyle."

  const getOccasionName = (id: string) => OCCASIONS.find(o => o.id === id)?.nameZh || id
  const getLongevityName = (id: string) => LONGEVITY_OPTIONS.find(o => o.id === id)?.nameZh || id
  const getSillageName = (id: string) => SILLAGE_OPTIONS.find(o => o.id === id)?.nameZh || id
  const getConcentrationName = (id: string) => CONCENTRATION_OPTIONS.find(o => o.id === id)?.nameZh || id
  const getBudgetName = (id: string) => BUDGET_OPTIONS.find(o => o.id === id)?.nameZh || id
  const getTimeName = (id: string) => TIME_OPTIONS.find(o => o.id === id)?.nameZh || id
  const getActivityName = (id: string) => ACTIVITY_LEVELS.find(o => o.id === id)?.nameZh || id
  const getConditionName = (id: string) => WEATHER_CONDITIONS.find(o => o.id === id)?.nameZh || id
  const getSeasonName = (id: string) => SEASONS.find(o => o.id === id)?.nameZh || id
  const getScentName = (id: string) => SCENT_FAMILIES.find(o => o.id === id)?.nameZh || id
  const fragranceNotes = buildFragranceNotes(adjustedScents)
  const fragranceDescription = buildFragranceDescription({
    scentIds: adjustedScents,
    preferences,
    biometrics,
    environment,
    adjustedConcentration: adjustedConcentration || "edp",
    adjustedSillage: adjustedSillage || "close",
  })

  return {
    occasion: getOccasionName(preferences.occasion || "daily"),
    scent_preference: adjustedScents.map(getScentName),
    longevity: getLongevityName(preferences.longevity || "medium"),
    sillage: getSillageName(adjustedSillage || "close"),
    concentration: getConcentrationName(adjustedConcentration || "edp"),
    budget_level: getBudgetName(preferences.budget_level || "midrange"),
    avoided_notes: preferences.avoided_notes.map(getScentName),
    time_of_day: getTimeName(preferences.time_of_day || "allday"),
    body_temperature: biometrics.body_temperature,
    heart_rate: biometrics.heart_rate,
    activity_level: getActivityName(biometrics.activity_level),
    temperature: environment.temperature,
    humidity: environment.humidity,
    condition: getConditionName(environment.condition),
    season: getSeasonName(environment.season),
    city: environment.city,
    analysis_summary: summary,
    fragrance_notes: fragranceNotes,
    fragrance_description: fragranceDescription,
  }
}

export default function Home() {
  const { language, t } = useLanguage()
  const [currentStep, setCurrentStep] = useState(0)
  const [preferences, setPreferences] = useState<UserPreferences>(initialPreferences)
  const [biometrics, setBiometrics] = useState<BiometricData>(initialBiometrics)
  const [environment, setEnvironment] = useState<EnvironmentData>(initialEnvironment)
  const [result, setResult] = useState<RecommendationOutput | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const STEPS = language === "zh" ? STEPS_ZH : STEPS_EN

  const scrollToTop = () => {
    requestAnimationFrame(() => {
      window.scrollTo({ top: 0, behavior: "smooth" })
    })
  }

  const handleNext = async () => {
    if (currentStep === 2) {
      setIsGenerating(true)
      await new Promise((resolve) => setTimeout(resolve, 1500))
      const recommendation = generateRecommendation(preferences, biometrics, environment)
      setResult(recommendation)
      setIsGenerating(false)
      setCurrentStep(3)
      scrollToTop()
    } else {
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1))
      scrollToTop()
    }
  }

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0))
  }

  const handleReset = () => {
    setCurrentStep(0)
    setPreferences(initialPreferences)
    setBiometrics(initialBiometrics)
    setEnvironment(initialEnvironment)
    setResult(null)
  }

  const isNextDisabled = () => {
    if (currentStep === 0) {
      return !preferences.occasion || preferences.scent_preference.length === 0
    }
    return false
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="mx-auto max-w-6xl px-6 pb-24 pt-28">
        {/* Hero Section with Oriental Aesthetics */}
        {currentStep === 0 && (
          <div className="mb-20">
            {/* Full-width hero image */}
            <div className="relative mb-16 h-[50vh] min-h-[400px] w-full overflow-hidden">
              <Image
                src="/images/hero-botanical.jpg"
                alt="Botanical perfume composition"
                fill
                className="object-cover object-center"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/42 via-transparent to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-l from-background/28 via-transparent to-transparent" />
              
              {/* Floating text overlay */}
              <div className="absolute inset-0 flex items-end justify-end p-6 sm:p-8 lg:p-10">
                <div className="max-w-[min(20rem,58%)] text-right sm:max-w-[22rem] lg:max-w-[26rem]">
                  <p className="mb-3 text-[10px] uppercase tracking-[0.34em] text-foreground/78 sm:text-xs">
                    {t.heroSubtitle}
                  </p>
                  <h1 className="font-serif text-3xl leading-[0.96] tracking-tight text-foreground drop-shadow-[0_8px_24px_rgba(48,34,18,0.18)] sm:text-4xl lg:text-5xl">
                    {t.heroTitle}
                    <br />
                    <span className="italic">{t.heroTitleLine2}</span>
                  </h1>
                </div>
              </div>
            </div>

            {/* Philosophy section */}
            <div className="grid gap-16 lg:grid-cols-2 lg:gap-24">
              <div className="flex flex-col justify-center">
                <div className="mb-6 h-px w-16 bg-foreground/30" />
                <p className="mb-6 font-serif text-2xl leading-relaxed tracking-tight">
                  {t.philosophyText1}
                </p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {t.philosophyText2}
                </p>
              </div>
              <div className="relative aspect-[4/5] overflow-hidden">
                <Image
                  src="/images/ingredients.jpg"
                  alt="Natural perfume ingredients"
                  fill
                  className="object-cover"
                />
              </div>
            </div>

            {/* Decorative divider */}
            <div className="my-20 flex items-center justify-center gap-4">
              <div className="h-px w-24 bg-border" />
              <svg className="h-6 w-6 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2 C12 2, 8 8, 12 12 C16 16, 12 22, 12 22" />
              </svg>
              <div className="h-px w-24 bg-border" />
            </div>

            {/* Philosophy Section - Brand Story */}
            <PhilosophySection />

            {/* Design Philosophy - Emotional Companion View */}
            <div className="my-20">
              <CompanionManifestoSection />
            </div>

            {/* Decorative divider before journey */}
            <div className="my-20 flex items-center justify-center gap-4">
              <div className="h-px w-24 bg-border" />
              <svg className="h-6 w-6 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2 C12 2, 8 8, 12 12 C16 16, 12 22, 12 22" />
              </svg>
              <div className="h-px w-24 bg-border" />
            </div>

            {/* Begin journey prompt */}
            <div className="text-center">
              <p className="mb-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                {t.beginJourney}
              </p>
              <h2 className="font-serif text-3xl tracking-tight">
                {t.tellUsAbout}
              </h2>
            </div>
          </div>
        )}

        {/* Progress Steps */}
        <ProgressSteps currentStep={currentStep} steps={STEPS} />

        {/* Step Content */}
        <div className="mt-12">
          {currentStep === 0 && (
            <PreferencesForm data={preferences} onChange={setPreferences} />
          )}

          {currentStep === 1 && (
            <div className="mx-auto max-w-3xl">
              <div className="mb-12 grid gap-8 lg:grid-cols-2">
                <div className="relative aspect-square overflow-hidden">
                  <Image
                    src="/images/biometric-zen.jpg"
                    alt="Harmony of nature and technology"
                    fill
                    className="object-cover"
                  />
                </div>
                <div className="flex flex-col justify-center">
                  <p className="mb-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                    {t.stepTwo}
                  </p>
                  <h2 className="mb-4 font-serif text-3xl tracking-tight">
                    {t.bodyLanguage}
                  </h2>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {t.bodyLanguageDesc}
                  </p>
                </div>
              </div>
              <BiometricCard data={biometrics} onChange={setBiometrics} />
            </div>
          )}

          {currentStep === 2 && (
            <div className="mx-auto max-w-3xl">
              <div className="mb-12 grid gap-8 lg:grid-cols-2">
                <div className="flex flex-col justify-center lg:order-2">
                  <p className="mb-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                    {t.stepThree}
                  </p>
                  <h2 className="mb-4 font-serif text-3xl tracking-tight">
                    {t.yourSurroundings}
                  </h2>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {t.surroundingsDesc}
                  </p>
                </div>
                <div className="relative aspect-square overflow-hidden lg:order-1">
                  <Image
                    src="/images/nature-texture.jpg"
                    alt="Natural water texture"
                    fill
                    className="object-cover"
                  />
                </div>
              </div>
              <EnvironmentCard data={environment} onChange={setEnvironment} />
            </div>
          )}

          {currentStep === 3 && result && (
            <div>
              <div className="mb-12 text-center">
                <p className="mb-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                  {t.yourProfile}
                </p>
                <h2 className="font-serif text-3xl tracking-tight">
                  {t.fragrancePortrait}
                </h2>
                <p className="mx-auto mt-4 max-w-lg text-sm text-muted-foreground">
                  {t.profileDesc}
                </p>
              </div>
              <RecommendationResult result={result} />
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-16 flex items-center justify-between border-t border-border pt-8">
          <Button
            variant="ghost"
            onClick={currentStep === 3 ? handleReset : handleBack}
            disabled={currentStep === 0 && !result}
            className="gap-2 text-xs uppercase tracking-[0.15em]"
          >
            {currentStep === 3 ? (
              t.startOver
            ) : (
              <>
                <ArrowLeft className="h-4 w-4" />
                {t.back}
              </>
            )}
          </Button>

          {currentStep < 3 && (
            <Button
              onClick={handleNext}
              disabled={isNextDisabled() || isGenerating}
              className="gap-2 border border-foreground bg-foreground text-background text-xs uppercase tracking-[0.15em] hover:bg-foreground/90"
            >
              {isGenerating ? (
                <>
                  <Spinner className="h-4 w-4" />
                  {t.analyzing}
                </>
              ) : currentStep === 2 ? (
                t.revealProfile
              ) : (
                <>
                  {t.continue_}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          )}
        </div>
      </main>

      {/* Footer with oriental touch */}
      <footer className="border-t border-border bg-secondary/30 py-16">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="font-serif text-lg tracking-tight">ScentMind</p>
          <p className="mt-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {t.footerSubtitle}
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <div className="h-px w-12 bg-border" />
            <svg className="h-4 w-4 text-muted-foreground/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
              <circle cx="12" cy="12" r="10" />
            </svg>
            <div className="h-px w-12 bg-border" />
          </div>
        </div>
      </footer>
    </div>
  )
}
