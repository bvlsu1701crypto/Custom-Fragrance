"use client"

import Image from "next/image"
import type { RecommendationOutput } from "@/lib/types"
import { useLanguage } from "@/lib/language-context"
import { ShareCard } from "@/components/share-card"

interface RecommendationResultProps {
  result: RecommendationOutput
}

export function RecommendationResult({ result }: RecommendationResultProps) {
  const { language, t } = useLanguage()

  return (
    <div className="space-y-16">
      {/* Hero Analysis */}
      <section className="relative">
        <div className="grid gap-8 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <div className="relative aspect-[3/4] overflow-hidden">
              <Image
                src="/images/ingredients.jpg"
                alt="Fragrance ingredients"
                fill
                className="object-cover"
              />
            </div>
          </div>
          <div className="flex flex-col justify-center lg:col-span-3 lg:pl-8">
            <p className="mb-4 text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {t.analysis}
            </p>
            <p className="font-serif text-2xl leading-relaxed tracking-tight lg:text-3xl">
              {result.analysis_summary}
            </p>
            <div className="mt-8 h-px w-24 bg-foreground/30" />
          </div>
        </div>
      </section>

      {/* Fragrance Notes - NEW */}
      <section className="border border-border bg-card p-8 md:p-12">
        <h3 className="mb-10 text-center text-xs uppercase tracking-[0.3em] text-muted-foreground">
          {language === "zh" ? "香调结构 · Fragrance Notes" : "Fragrance Notes Structure"}
        </h3>
        <div className="grid gap-8 md:grid-cols-3">
          {/* Top Notes */}
          <div className="text-center">
            <div className="mb-4">
              <span className="inline-block rounded-full border border-accent/30 px-4 py-1 text-xs uppercase tracking-[0.2em] text-accent">
                {language === "zh" ? "前调 · Top Notes" : "Top Notes"}
              </span>
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
              {language === "zh" ? "初次接触时感受到的香气" : "First impression, lasts 15-30 mins"}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {result.fragrance_notes.topNotes.map((note) => (
                <span 
                  key={note} 
                  className="border border-foreground/20 bg-secondary/30 px-4 py-2 font-serif text-sm"
                >
                  {note}
                </span>
              ))}
            </div>
          </div>
          
          {/* Middle Notes */}
          <div className="text-center">
            <div className="mb-4">
              <span className="inline-block rounded-full border border-chart-2/30 px-4 py-1 text-xs uppercase tracking-[0.2em] text-chart-2">
                {language === "zh" ? "中调 · Heart Notes" : "Heart Notes"}
              </span>
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
              {language === "zh" ? "香水的核心与灵魂" : "Core of the fragrance, lasts 2-4 hours"}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {result.fragrance_notes.middleNotes.map((note) => (
                <span 
                  key={note} 
                  className="border border-foreground/20 bg-secondary/30 px-4 py-2 font-serif text-sm"
                >
                  {note}
                </span>
              ))}
            </div>
          </div>
          
          {/* Base Notes */}
          <div className="text-center">
            <div className="mb-4">
              <span className="inline-block rounded-full border border-chart-4/30 px-4 py-1 text-xs uppercase tracking-[0.2em] text-chart-4">
                {language === "zh" ? "后调 · Base Notes" : "Base Notes"}
              </span>
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
              {language === "zh" ? "持久留香的基底" : "Foundation, lasts 4-8+ hours"}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {result.fragrance_notes.baseNotes.map((note) => (
                <span 
                  key={note} 
                  className="border border-foreground/20 bg-secondary/30 px-4 py-2 font-serif text-sm"
                >
                  {note}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Fragrance Description - NEW */}
      <section className="mx-auto max-w-3xl text-center">
        <div className="mb-6 flex items-center justify-center gap-4">
          <div className="h-px w-12 bg-border" />
          <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {language === "zh" ? "气味描述 · Scent Description" : "Scent Description"}
          </span>
          <div className="h-px w-12 bg-border" />
        </div>
        <p className="font-serif text-lg leading-relaxed text-foreground/90 md:text-xl">
          {language === "zh" ? result.fragrance_description.zh : result.fragrance_description.en}
        </p>
      </section>

      {/* Recommendation Details */}
      <div className="grid gap-px bg-border md:grid-cols-2">
        {/* Fragrance Parameters */}
        <section className="bg-card p-8 md:p-10">
          <h3 className="mb-8 text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {t.recommendedParams}
          </h3>
          <div className="space-y-6">
            <div className="flex items-baseline justify-between border-b border-border pb-4">
              <span className="text-sm text-muted-foreground">{language === "zh" ? "场合 Occasion" : "Occasion"}</span>
              <span className="font-serif text-lg">{result.occasion}</span>
            </div>
            <div className="flex items-baseline justify-between border-b border-border pb-4">
              <span className="text-sm text-muted-foreground">{language === "zh" ? "持久度 Longevity" : "Longevity"}</span>
              <span className="font-serif text-lg">{result.longevity}</span>
            </div>
            <div className="flex items-baseline justify-between border-b border-border pb-4">
              <span className="text-sm text-muted-foreground">{language === "zh" ? "扩散度 Projection" : "Projection"}</span>
              <span className="font-serif text-lg">{result.sillage}</span>
            </div>
            <div className="flex items-baseline justify-between border-b border-border pb-4">
              <span className="text-sm text-muted-foreground">{language === "zh" ? "浓度 Concentration" : "Concentration"}</span>
              <span className="font-serif text-lg">{result.concentration}</span>
            </div>
            <div className="flex items-baseline justify-between border-b border-border pb-4">
              <span className="text-sm text-muted-foreground">{language === "zh" ? "预算 Budget" : "Budget"}</span>
              <span className="font-serif text-lg">{result.budget_level}</span>
            </div>
            <div className="flex items-baseline justify-between pb-4">
              <span className="text-sm text-muted-foreground">{language === "zh" ? "时段 Time" : "Time of Day"}</span>
              <span className="font-serif text-lg">{result.time_of_day}</span>
            </div>
          </div>
        </section>

        {/* Context Data */}
        <section className="bg-card p-8 md:p-10">
          <h3 className="mb-8 text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {t.contextualFactors}
          </h3>
          <div className="space-y-8">
            <div>
              <p className="mb-4 text-xs uppercase tracking-[0.2em] text-muted-foreground/70">
                {t.biometrics}
              </p>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "体温 Temperature" : "Temperature"}</span>
                  <span className="font-mono text-sm">{result.body_temperature}°C</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "心率 Heart Rate" : "Heart Rate"}</span>
                  <span className="font-mono text-sm">{result.heart_rate} bpm</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "活动 Activity" : "Activity"}</span>
                  <span className="text-sm">{result.activity_level}</span>
                </div>
              </div>
            </div>

            <div className="border-t border-border pt-6">
              <p className="mb-4 text-xs uppercase tracking-[0.2em] text-muted-foreground/70">
                {t.environment}
              </p>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "地点 Location" : "Location"}</span>
                  <span className="text-sm">{result.city}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "气温 Temp" : "Temp"}</span>
                  <span className="font-mono text-sm">{result.temperature}°C</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "湿度 Humidity" : "Humidity"}</span>
                  <span className="font-mono text-sm">{result.humidity}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "天气 Weather" : "Weather"}</span>
                  <span className="text-sm">{result.condition}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">{language === "zh" ? "季节 Season" : "Season"}</span>
                  <span className="text-sm">{result.season}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Scent Profile */}
      <section className="border border-border p-8 md:p-10">
        <h3 className="mb-8 text-center text-xs uppercase tracking-[0.3em] text-muted-foreground">
          {t.recommendedProfile}
        </h3>
        <div className="flex flex-wrap justify-center gap-3">
          {result.scent_preference.map((scent) => (
            <span 
              key={scent} 
              className="border border-foreground px-6 py-3 font-serif text-lg tracking-wide"
            >
              {scent}
            </span>
          ))}
        </div>
        {result.avoided_notes.length > 0 && (
          <div className="mt-10 border-t border-border pt-8">
            <p className="mb-4 text-center text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {t.notesToAvoid}
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {result.avoided_notes.map((note) => (
                <span 
                  key={note} 
                  className="border border-destructive/30 px-4 py-2 text-sm tracking-wide text-destructive/80"
                >
                  {note}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Share Card */}
      <ShareCard result={result} />
    </div>
  )
}
