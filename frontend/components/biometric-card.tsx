"use client"

import { Slider } from "@/components/ui/slider"
import { type BiometricData, ACTIVITY_LEVELS } from "@/lib/types"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/lib/language-context"

interface BiometricCardProps {
  data: BiometricData
  onChange: (data: BiometricData) => void
}

export function BiometricCard({ data, onChange }: BiometricCardProps) {
  const { language, t } = useLanguage()

  return (
    <div className="border border-border bg-card p-8 md:p-10">
      <div className="space-y-12">
        {/* Body Temperature */}
        <section>
          <div className="mb-6 flex items-baseline justify-between">
            <div>
              <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {t.bodyTemperature}
              </span>
            </div>
            <span className="font-serif text-3xl tabular-nums">
              {data.body_temperature.toFixed(1)}
              <span className="ml-1 text-base text-muted-foreground">°C</span>
            </span>
          </div>
          <Slider
            value={[data.body_temperature]}
            onValueChange={([value]) => onChange({ ...data, body_temperature: value })}
            min={35.5}
            max={38.5}
            step={0.1}
            className="[&_[role=slider]]:h-3 [&_[role=slider]]:w-3 [&_[role=slider]]:border-foreground [&_[role=slider]]:bg-foreground"
          />
          <div className="mt-3 flex justify-between text-xs text-muted-foreground">
            <span>35.5°C</span>
            <span className={cn(
              "uppercase tracking-wider",
              data.body_temperature > 37 ? "text-destructive" : "text-muted-foreground"
            )}>
              {data.body_temperature > 37 ? t.elevated : t.normal}
            </span>
            <span>38.5°C</span>
          </div>
        </section>

        {/* Heart Rate */}
        <section>
          <div className="mb-6 flex items-baseline justify-between">
            <div>
              <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {language === "zh" ? "心率 · Heart Rate" : "Heart Rate"}
              </span>
            </div>
            <span className="font-serif text-3xl tabular-nums">
              {data.heart_rate}
              <span className="ml-1 text-base text-muted-foreground">bpm</span>
            </span>
          </div>
          <Slider
            value={[data.heart_rate]}
            onValueChange={([value]) => onChange({ ...data, heart_rate: value })}
            min={50}
            max={180}
            step={1}
            className="[&_[role=slider]]:h-3 [&_[role=slider]]:w-3 [&_[role=slider]]:border-foreground [&_[role=slider]]:bg-foreground"
          />
          <div className="mt-3 flex justify-between text-xs text-muted-foreground">
            <span>50 bpm</span>
            <span className={cn(
              "uppercase tracking-wider",
              data.heart_rate > 100 ? "text-accent" : "text-muted-foreground"
            )}>
              {data.heart_rate > 100 ? t.active : t.resting}
            </span>
            <span>180 bpm</span>
          </div>
        </section>

        {/* Activity Level */}
        <section>
          <div className="mb-6">
            <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {t.activityLevel}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {ACTIVITY_LEVELS.map((level) => (
              <button
                key={level.id}
                onClick={() => onChange({ ...data, activity_level: level.id })}
                className={cn(
                  "group relative border px-5 py-4 text-left transition-all duration-300",
                  data.activity_level === level.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="block text-xs uppercase tracking-[0.15em]">{level.nameZh}</span>
                <span className="mt-1 block text-sm">{level.name}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
