"use client"

import { Slider } from "@/components/ui/slider"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { type EnvironmentData, WEATHER_CONDITIONS, SEASONS, WORLD_CITIES } from "@/lib/types"
import { cn } from "@/lib/utils"
import { useLanguage } from "@/lib/language-context"

interface EnvironmentCardProps {
  data: EnvironmentData
  onChange: (data: EnvironmentData) => void
}

export function EnvironmentCard({ data, onChange }: EnvironmentCardProps) {
  const { language, t } = useLanguage()

  return (
    <div className="border border-border bg-card p-8 md:p-10">
      <div className="space-y-12">
        {/* City */}
        <section>
          <div className="mb-4">
            <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {t.city}
            </span>
          </div>
          <Select
            value={data.city}
            onValueChange={(value) => onChange({ ...data, city: value })}
          >
            <SelectTrigger className="border-border bg-transparent text-lg focus:ring-0 focus:ring-offset-0">
              <SelectValue placeholder={language === "zh" ? "选择城市" : "Select a city"} />
            </SelectTrigger>
            <SelectContent className="max-h-[300px]">
              {WORLD_CITIES.map((city) => (
                <SelectItem key={city.id} value={city.name}>
                  <span className="flex items-center gap-2">
                    <span className="font-serif">{city.nameZh}</span>
                    <span className="text-muted-foreground">·</span>
                    <span>{city.name}</span>
                    <span className="text-xs text-muted-foreground">({city.country})</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </section>

        {/* Temperature */}
        <section>
          <div className="mb-6 flex items-baseline justify-between">
            <div>
              <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {t.temperature}
              </span>
            </div>
            <span className="font-serif text-3xl tabular-nums">
              {data.temperature}
              <span className="ml-1 text-base text-muted-foreground">°C</span>
            </span>
          </div>
          <Slider
            value={[data.temperature]}
            onValueChange={([value]) => onChange({ ...data, temperature: value })}
            min={-10}
            max={45}
            step={1}
            className="[&_[role=slider]]:h-3 [&_[role=slider]]:w-3 [&_[role=slider]]:border-foreground [&_[role=slider]]:bg-foreground"
          />
          <div className="mt-3 flex justify-between text-xs text-muted-foreground">
            <span>-10°C</span>
            <span className={cn(
              "uppercase tracking-wider",
              data.temperature > 28 ? "text-accent" : 
              data.temperature < 15 ? "text-chart-2" : "text-muted-foreground"
            )}>
              {data.temperature > 28 ? t.hot : data.temperature < 15 ? t.cold : t.comfortable}
            </span>
            <span>45°C</span>
          </div>
        </section>

        {/* Humidity */}
        <section>
          <div className="mb-6 flex items-baseline justify-between">
            <div>
              <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {t.humidity}
              </span>
            </div>
            <span className="font-serif text-3xl tabular-nums">
              {data.humidity}
              <span className="ml-1 text-base text-muted-foreground">%</span>
            </span>
          </div>
          <Slider
            value={[data.humidity]}
            onValueChange={([value]) => onChange({ ...data, humidity: value })}
            min={10}
            max={100}
            step={1}
            className="[&_[role=slider]]:h-3 [&_[role=slider]]:w-3 [&_[role=slider]]:border-foreground [&_[role=slider]]:bg-foreground"
          />
          <div className="mt-3 flex justify-between text-xs text-muted-foreground">
            <span>10%</span>
            <span className={cn(
              "uppercase tracking-wider",
              data.humidity > 70 ? "text-chart-2" : 
              data.humidity < 40 ? "text-accent" : "text-muted-foreground"
            )}>
              {data.humidity > 70 ? t.humid : data.humidity < 40 ? t.dry : t.moderate}
            </span>
            <span>100%</span>
          </div>
        </section>

        {/* Weather */}
        <section>
          <div className="mb-4">
            <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {t.weather}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {WEATHER_CONDITIONS.map((condition) => (
              <button
                key={condition.id}
                onClick={() => onChange({ ...data, condition: condition.id })}
                className={cn(
                  "border px-4 py-4 text-center transition-all duration-300",
                  data.condition === condition.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="block text-xs uppercase tracking-[0.15em]">{condition.nameZh}</span>
                <span className="mt-1 block text-sm">{condition.name}</span>
              </button>
            ))}
          </div>
        </section>

        {/* Season */}
        <section>
          <div className="mb-4">
            <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {t.season}
            </span>
          </div>
          <div className="grid grid-cols-4 gap-3">
            {SEASONS.map((season) => (
              <button
                key={season.id}
                onClick={() => onChange({ ...data, season: season.id })}
                className={cn(
                  "border px-3 py-4 text-center transition-all duration-300",
                  data.season === season.id
                    ? "border-foreground bg-foreground text-background"
                    : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
                )}
              >
                <span className="block font-serif text-lg">{season.nameZh}</span>
                <span className="mt-1 block text-xs uppercase tracking-wider">{season.name}</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
