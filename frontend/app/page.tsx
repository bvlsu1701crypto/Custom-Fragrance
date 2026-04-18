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
import type {
  UserPreferences,
  BiometricData,
  EnvironmentData,
} from "@/lib/types"
import { generatePerfume } from "@/lib/api/service"
import { ApiError } from "@/lib/api/schemas"
import { useRecommendation } from "@/lib/recommendation-context"
import { toast } from "sonner"
import { ArrowLeft, ArrowRight } from "lucide-react"

const STEPS_ZH = ["偏好", "生理", "环境", "结果"]
const STEPS_EN = ["Preferences", "Biometrics", "Environment", "Results"]

const initialPreferences: UserPreferences = {
  occasion: "",
  scent_preference: [],
  sillage: "",
  concentration: "",
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
}

export default function Home() {
  const { language, t } = useLanguage()
  const { result, setRecommendation, clear } = useRecommendation()
  const [currentStep, setCurrentStep] = useState(result ? 3 : 0)
  const [preferences, setPreferences] = useState<UserPreferences>(initialPreferences)
  const [biometrics, setBiometrics] = useState<BiometricData>(initialBiometrics)
  const [environment, setEnvironment] = useState<EnvironmentData>(initialEnvironment)
  const [isGenerating, setIsGenerating] = useState(false)

  const STEPS = language === "zh" ? STEPS_ZH : STEPS_EN

  const handleNext = async () => {
    if (currentStep === 2) {
      setIsGenerating(true)
      try {
        const { recommendation, raw } = await generatePerfume(preferences, biometrics, environment)
        setRecommendation(recommendation, raw)
        setCurrentStep(3)
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.detail
            : err instanceof Error
              ? err.message
              : "生成失败，请稍后重试"
        toast.error(message)
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
    clear()
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
