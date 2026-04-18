"use client"

import { createContext, useContext, useState, ReactNode } from "react"

type Language = "zh" | "en"

interface Translations {
  // Header
  philosophy: string
  collection: string
  consultation: string
  signIn: string
  signUp: string
  begin: string
  
  // Hero
  heroSubtitle: string
  heroTitle: string
  heroTitleLine2: string
  
  // Philosophy section
  philosophyText1: string
  philosophyText2: string
  
  // Journey
  beginJourney: string
  tellUsAbout: string
  
  // Steps
  stepTwo: string
  bodyLanguage: string
  bodyLanguageDesc: string
  stepThree: string
  yourSurroundings: string
  surroundingsDesc: string
  yourProfile: string
  fragrancePortrait: string
  profileDesc: string
  
  // Navigation
  startOver: string
  back: string
  continue_: string
  analyzing: string
  revealProfile: string
  
  // Footer
  footerSubtitle: string
  
  // Sign up modal
  createAccount: string
  joinCommunity: string
  email: string
  password: string
  confirmPassword: string
  agreeTerms: string
  alreadyHaveAccount: string
  orContinueWith: string
  
  // Biometric
  bodyTemperature: string
  elevated: string
  normal: string
  activityLevel: string
  active: string
  resting: string
  
  // Environment
  city: string
  temperature: string
  hot: string
  cold: string
  comfortable: string
  humidity: string
  humid: string
  dry: string
  moderate: string
  weather: string
  season: string
  
  // Preferences
  occasion: string
  scentFamilies: string
  avoid: string
  longevity: string
  projection: string
  concentration: string
  budget: string
  timeOfDay: string
  additional: string
  additionalPlaceholder: string
  
  // Results
  analysis: string
  recommendedParams: string
  contextualFactors: string
  biometrics: string
  environment: string
  recommendedProfile: string
  notesToAvoid: string
  rawOutput: string
}

const translations: Record<Language, Translations> = {
  zh: {
    // Header
    philosophy: "理念",
    collection: "系列",
    consultation: "咨询",
    signIn: "登录",
    signUp: "注册",
    begin: "开始",
    
    // Hero
    heroSubtitle: "香气智能 · 生物识别香氛智能",
    heroTitle: "你的专属",
    heroTitleLine2: "香氛时刻",
    
    // Philosophy section
    philosophyText1: "香水的艺术是极其私人的——这是您的身体、环境与香氛本身之间的对话。",
    philosophyText2: "受东方哲学中身体与自然和谐统一的启发，ScentMind 考虑您独特的生理特征和周围环境，引导您找到感觉像是自我延伸的香氛。",
    
    // Journey
    beginJourney: "开始您的旅程",
    tellUsAbout: "告诉我们关于您自己",
    
    // Steps
    stepTwo: "第二步",
    bodyLanguage: "您身体的语言",
    bodyLanguageDesc: "您的生理特征说明了很多。体温、心率和活动水平都会影响香氛在您皮肤上的展现方式。分享您的 Apple Watch 读数，帮助我们了解您身体的当前状态。",
    stepThree: "第三步",
    yourSurroundings: "您的环境",
    surroundingsDesc: "同一款香氛在不同季节和气候下会有不同表现。湿度会放大香味，高温会加速挥发，寒冷则会抑制。了解您的环境帮助我们推荐在您的世界中表现出色的香氛。",
    yourProfile: "您的档案",
    fragrancePortrait: "香氛画像",
    profileDesc: "基于您独特的偏好、生理特征和环境组合，我们为您打造了个性化推荐。",
    
    // Navigation
    startOver: "重新开始",
    back: "返回",
    continue_: "继续",
    analyzing: "分析中",
    revealProfile: "查看我的档案",
    
    // Footer
    footerSubtitle: "香气智能 · 生物识别香氛发现",
    
    // Sign up modal
    createAccount: "创建账户",
    joinCommunity: "加入 ScentMind 社区，开启您的个性化香氛之旅",
    email: "邮箱地址",
    password: "密码",
    confirmPassword: "确认密码",
    agreeTerms: "我同意服务条款和隐私政策",
    alreadyHaveAccount: "已有账户？",
    orContinueWith: "或继续使用",
    
    // Biometric
    bodyTemperature: "体温 · Body Temperature",
    elevated: "偏高 Elevated",
    normal: "正常 Normal",
    activityLevel: "活动强度 · Activity Level",
    active: "活跃 Active",
    resting: "静息 Resting",
    
    // Environment
    city: "城市 · City",
    temperature: "气温 · Temperature",
    hot: "炎热 Hot",
    cold: "寒冷 Cold",
    comfortable: "舒适 Comfortable",
    humidity: "湿度 · Humidity",
    humid: "潮湿 Humid",
    dry: "干燥 Dry",
    moderate: "适中 Moderate",
    weather: "天气 · Weather",
    season: "季节 · Season",
    
    // Preferences
    occasion: "场合 · Occasion",
    scentFamilies: "香调 · Scent Families",
    avoid: "避免 · Avoid",
    longevity: "持久度 · Longevity",
    projection: "扩散度 · Projection",
    concentration: "浓度 · Concentration",
    budget: "预算 · Budget",
    timeOfDay: "时段 · Time of Day",
    additional: "补充 · Additional",
    additionalPlaceholder: "例如：我喜欢清新但不太浓烈的香味",
    
    // Results
    analysis: "分析 · Analysis",
    recommendedParams: "推荐参数 · Recommended Parameters",
    contextualFactors: "环境因素 · Contextual Factors",
    biometrics: "生理数据 · Biometrics",
    environment: "环境数据 · Environment",
    recommendedProfile: "香调建议 · Recommended Scent Profile",
    notesToAvoid: "避免香调 · Notes to Avoid",
    rawOutput: "原始输出",
  },
  en: {
    // Header
    philosophy: "Philosophy",
    collection: "Collection",
    consultation: "Consultation",
    signIn: "Sign in",
    signUp: "Sign up",
    begin: "Begin",
    
    // Hero
    heroSubtitle: "Biometric Fragrance Intelligence",
    heroTitle: "Your Exclusive",
    heroTitleLine2: "Fragrance Moment",
    
    // Philosophy section
    philosophyText1: "The art of fragrance is deeply personal—a dialogue between your body, your environment, and the essence itself.",
    philosophyText2: "Inspired by the Eastern philosophy of harmony between body and nature, ScentMind considers your unique physiology and surroundings to guide you toward fragrances that feel like an extension of yourself.",
    
    // Journey
    beginJourney: "Begin your journey",
    tellUsAbout: "Tell us about yourself",
    
    // Steps
    stepTwo: "Step Two",
    bodyLanguage: "Your Body's Language",
    bodyLanguageDesc: "Your physiology speaks volumes. Body temperature, heart rate, and activity level all influence how a fragrance unfolds on your skin. Share your Apple Watch readings to help us understand your body's current state.",
    stepThree: "Step Three",
    yourSurroundings: "Your Surroundings",
    surroundingsDesc: "The same fragrance transforms across seasons and climates. Humidity amplifies, heat accelerates, and cold subdues. Understanding your environment helps us recommend scents that perform beautifully in your world.",
    yourProfile: "Your Profile",
    fragrancePortrait: "A Fragrance Portrait",
    profileDesc: "Based on your unique combination of preferences, physiology, and environment, we've crafted a personalized recommendation.",
    
    // Navigation
    startOver: "Start over",
    back: "Back",
    continue_: "Continue",
    analyzing: "Analyzing",
    revealProfile: "Reveal my profile",
    
    // Footer
    footerSubtitle: "Biometric Fragrance Discovery",
    
    // Sign up modal
    createAccount: "Create Account",
    joinCommunity: "Join the ScentMind community and begin your personalized fragrance journey",
    email: "Email address",
    password: "Password",
    confirmPassword: "Confirm password",
    agreeTerms: "I agree to the Terms of Service and Privacy Policy",
    alreadyHaveAccount: "Already have an account?",
    orContinueWith: "Or continue with",
    
    // Biometric
    bodyTemperature: "Body Temperature",
    elevated: "Elevated",
    normal: "Normal",
    activityLevel: "Activity Level",
    active: "Active",
    resting: "Resting",
    
    // Environment
    city: "City",
    temperature: "Temperature",
    hot: "Hot",
    cold: "Cold",
    comfortable: "Comfortable",
    humidity: "Humidity",
    humid: "Humid",
    dry: "Dry",
    moderate: "Moderate",
    weather: "Weather",
    season: "Season",
    
    // Preferences
    occasion: "Occasion",
    scentFamilies: "Scent Families",
    avoid: "Avoid",
    longevity: "Longevity",
    projection: "Projection",
    concentration: "Concentration",
    budget: "Budget",
    timeOfDay: "Time of Day",
    additional: "Additional Notes",
    additionalPlaceholder: "e.g., I prefer fresh scents that aren't too strong",
    
    // Results
    analysis: "Analysis",
    recommendedParams: "Recommended Parameters",
    contextualFactors: "Contextual Factors",
    biometrics: "Biometrics",
    environment: "Environment",
    recommendedProfile: "Recommended Scent Profile",
    notesToAvoid: "Notes to Avoid",
    rawOutput: "Raw Output",
  },
}

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: Translations
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("zh")
  
  return (
    <LanguageContext.Provider value={{ language, setLanguage, t: translations[language] }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}
