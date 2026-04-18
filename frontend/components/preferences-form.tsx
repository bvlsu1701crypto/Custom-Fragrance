"use client"

import { Textarea } from "@/components/ui/textarea"
import {
  type UserPreferences,
  SCENT_FAMILIES,
  OCCASIONS,
  LONGEVITY_OPTIONS,
  SILLAGE_OPTIONS,
  CONCENTRATION_OPTIONS,
  BUDGET_OPTIONS,
  TIME_OPTIONS,
} from "@/lib/types"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/lib/language-context"

interface PreferencesFormProps {
  data: UserPreferences
  onChange: (data: UserPreferences) => void
}

export function PreferencesForm({ data, onChange }: PreferencesFormProps) {
  const { language, t } = useLanguage()
  
  const toggleScentPreference = (scentId: string) => {
    const newPreferences = data.scent_preference.includes(scentId)
      ? data.scent_preference.filter((s) => s !== scentId)
      : [...data.scent_preference, scentId]
    onChange({ ...data, scent_preference: newPreferences })
  }

  const toggleAvoidedNote = (scentId: string) => {
    const newAvoided = data.avoided_notes.includes(scentId)
      ? data.avoided_notes.filter((s) => s !== scentId)
      : [...data.avoided_notes, scentId]
    onChange({ ...data, avoided_notes: newAvoided })
  }

  const getName = (item: { name: string; nameZh: string }) => 
    language === "zh" ? item.nameZh : item.name

  return (
    <div className="space-y-16">
      {/* Occasion */}
      <section className="border border-border bg-card p-8 md:p-10">
        <div className="mb-8">
          <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.occasion}</span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight">
            {language === "zh" ? "你打算在什么场合使用？" : "When will you wear it?"}
          </h3>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {OCCASIONS.map((occasion) => (
            <button
              key={occasion.id}
              onClick={() => onChange({ ...data, occasion: occasion.id })}
              className={cn(
                "border px-5 py-4 text-left transition-all duration-300",
                data.occasion === occasion.id
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
              )}
            >
              <span className="block text-xs uppercase tracking-[0.15em]">{occasion.nameZh}</span>
              <span className="mt-1 block text-sm">{occasion.name}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Scent Preferences */}
      <section className="border border-border bg-card p-8 md:p-10">
        <div className="mb-8">
          <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.scentFamilies}</span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight">
            {language === "zh" ? "什么香调吸引你？" : "What draws you in?"}
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {language === "zh" ? "选择所有与你共鸣的香调" : "Select all that resonate with you"}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {SCENT_FAMILIES.map((scent) => (
            <button
              key={scent.id}
              onClick={() => toggleScentPreference(scent.id)}
              className={cn(
                "border px-5 py-3 transition-all duration-300",
                data.scent_preference.includes(scent.id)
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
              )}
            >
              <span className="block font-serif text-lg">{scent.nameZh}</span>
              <span className="block text-xs uppercase tracking-wider">{scent.name}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Avoided Notes */}
      <section className="border border-border bg-card p-8 md:p-10">
        <div className="mb-8">
          <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.avoid}</span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight">
            {language === "zh" ? "需要避开的香调" : "What to stay away from"}
          </h3>
        </div>
        <div className="flex flex-wrap gap-3">
          {SCENT_FAMILIES.map((scent) => (
            <button
              key={scent.id}
              onClick={() => toggleAvoidedNote(scent.id)}
              disabled={data.scent_preference.includes(scent.id)}
              className={cn(
                "border px-4 py-2 transition-all duration-300",
                data.avoided_notes.includes(scent.id)
                  ? "border-destructive bg-destructive/10 text-destructive"
                  : data.scent_preference.includes(scent.id)
                    ? "cursor-not-allowed border-border/50 text-muted-foreground/40"
                    : "border-border text-muted-foreground hover:border-destructive/50"
              )}
            >
              <span className="text-sm">{scent.nameZh} {scent.name}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Longevity & Sillage */}
      <div className="grid gap-6 md:grid-cols-2">
        <section className="border border-border bg-card p-8">
          <div className="mb-6">
            <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.longevity}</span>
            <h3 className="mt-2 font-serif text-xl tracking-tight">
              {language === "zh" ? "需要持续多久？" : "How long?"}
            </h3>
          </div>
          <div className="space-y-2">
            {LONGEVITY_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => onChange({ ...data, longevity: option.id })}
                className={cn(
                  "flex w-full items-center justify-between border px-4 py-3 transition-all duration-300",
                  data.longevity === option.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="text-sm">{option.nameZh}</span>
                <span className="text-xs">{option.name}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="border border-border bg-card p-8">
          <div className="mb-6">
            <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.projection}</span>
            <h3 className="mt-2 font-serif text-xl tracking-tight">
              {language === "zh" ? "扩散范围？" : "How far?"}
            </h3>
          </div>
          <div className="space-y-2">
            {SILLAGE_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => onChange({ ...data, sillage: option.id })}
                className={cn(
                  "flex w-full items-center justify-between border px-4 py-3 transition-all duration-300",
                  data.sillage === option.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="text-sm">{option.nameZh}</span>
                <span className="text-xs">{option.name}</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      {/* Concentration & Budget */}
      <div className="grid gap-6 md:grid-cols-2">
        <section className="border border-border bg-card p-8">
          <div className="mb-6">
            <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.concentration}</span>
            <h3 className="mt-2 font-serif text-xl tracking-tight">
              {language === "zh" ? "香水浓度" : "Perfume strength"}
            </h3>
          </div>
          <div className="space-y-2">
            {CONCENTRATION_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => onChange({ ...data, concentration: option.id })}
                className={cn(
                  "flex w-full items-center justify-between border px-4 py-3 transition-all duration-300",
                  data.concentration === option.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="text-sm">{option.nameZh}</span>
                <span className="text-xs">{option.name}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="border border-border bg-card p-8">
          <div className="mb-6">
            <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.budget}</span>
            <h3 className="mt-2 font-serif text-xl tracking-tight">
              {language === "zh" ? "预算范围" : "Investment level"}
            </h3>
          </div>
          <div className="space-y-2">
            {BUDGET_OPTIONS.map((option) => (
              <button
                key={option.id}
                onClick={() => onChange({ ...data, budget_level: option.id })}
                className={cn(
                  "flex w-full items-center justify-between border px-4 py-3 transition-all duration-300",
                  data.budget_level === option.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="text-sm">{option.nameZh}</span>
                <span className="text-xs opacity-60">{option.range}</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      {/* Time of Day */}
      <section className="border border-border bg-card p-8 md:p-10">
        <div className="mb-8">
          <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.timeOfDay}</span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight">
            {language === "zh" ? "主要使用时段？" : "When do you wear it most?"}
          </h3>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {TIME_OPTIONS.map((option) => (
            <button
              key={option.id}
              onClick={() => onChange({ ...data, time_of_day: option.id })}
              className={cn(
                "border px-4 py-4 text-center transition-all duration-300",
                data.time_of_day === option.id
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
              )}
            >
              <span className="block font-serif text-lg">{option.nameZh}</span>
              <span className="mt-1 block text-xs uppercase tracking-wider">{option.name}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Free Description */}
      <section className="border border-border bg-card p-8 md:p-10">
        <div className="mb-8">
          <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{t.additional}</span>
          <h3 className="mt-2 font-serif text-2xl tracking-tight">
            {language === "zh" ? "还有什么想说的？" : "Anything else?"}
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {language === "zh" 
              ? "用您自己的话分享任何特定的愿望或偏好" 
              : "Share any specific desires or preferences in your own words"}
          </p>
        </div>
        <Textarea
          value={data.free_description}
          onChange={(e) => onChange({ ...data, free_description: e.target.value })}
          placeholder={t.additionalPlaceholder}
          className="min-h-[140px] border-border bg-transparent px-0 text-base leading-relaxed placeholder:text-muted-foreground/50 focus:border-foreground focus-visible:ring-0"
        />
      </section>
    </div>
  )
}
