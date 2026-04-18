"use client"

import { useState } from "react"
import Image from "next/image"
import { Header } from "@/components/header"
import { PhilosophySection } from "@/components/philosophy-section"
import { ProgressSteps } from "@/components/progress-steps"
import { PreferencesForm } from "@/components/preferences-form"
import { BiometricCard } from "@/components/biometric-card"
import { EnvironmentCard } from "@/components/environment-card"
import { RecommendationResult } from "@/components/recommendation-result"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useLanguage } from "@/lib/language-context"
import { generatePerfumeViaAPI } from "@/lib/api"
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
    fragrance_notes: {
      topNotes: ["柠檬", "香柠檬", "香草"],
      middleNotes: ["鸢尾", "茉莉", "桦木"],
      baseNotes: ["香草", "焦糖", "雪松"],
    },
    fragrance_description: {
      zh: "这款香氛以清新的柠檬和香柠檬开场，带来一丝活力与清爽。随着时间推移，优雅的鸢尾与茉莉在中调绽放，散发出细腻的花香气息，同时桦木带来一抹清冷的木质感。基调由温暖的香草与焦糖构成，甜美却不腻人，雪松则为整体增添了沉稳与持久的余韵。这是一款适合日常穿戴的香氛，既清新又温暖，充满层次感。",
      en: "This fragrance opens with a burst of fresh lemon and bergamot, delivering an invigorating and refreshing top note. As time unfolds, elegant iris and jasmine bloom in the heart, exuding a delicate floral essence, while birch adds a cool, woody undertone. The base is composed of warm vanilla and caramel—sweet yet not cloying—while cedar provides depth and a lasting, grounded finish. This is a versatile scent perfect for everyday wear, balancing freshness with warmth and layered sophistication."
    },
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

  const handleNext = async () => {
    if (currentStep === 2) {
      setIsGenerating(true)
      try {
        const recommendation = await generatePerfumeViaAPI(preferences, biometrics, environment)
        setResult(recommendation)
        setCurrentStep(3)
      } catch (error) {
        console.error("[API] 后端调用失败，降级为本地生成:", error)
        const recommendation = generateRecommendation(preferences, biometrics, environment)
        setResult(recommendation)
        setCurrentStep(3)
      } finally {
        setIsGenerating(false)
      }
    } else {
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length - 1))
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
                className="object-cover"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-transparent to-background" />
              
              {/* Floating text overlay */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="mb-4 text-xs uppercase tracking-[0.4em] text-foreground/80">
                    {t.heroSubtitle}
                  </p>
                  <h1 className="font-serif text-5xl tracking-tight text-foreground sm:text-6xl lg:text-7xl">
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
