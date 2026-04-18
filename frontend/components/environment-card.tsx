"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { type EnvironmentData, WORLD_CITIES } from "@/lib/types"
import { useLanguage } from "@/lib/language-context"

interface EnvironmentCardProps {
  data: EnvironmentData
  onChange: (data: EnvironmentData) => void
}

export function EnvironmentCard({ data, onChange }: EnvironmentCardProps) {
  const { language } = useLanguage()

  return (
    <div className="border border-border bg-card p-8 md:p-10">
      <div className="space-y-10">
        {/* City */}
        <section>
          <div className="mb-4">
            <span className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {language === "zh" ? "所在城市 · City" : "Your City"}
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

        {/* Auto-fetch notice */}
        <section className="border border-dashed border-border/60 bg-secondary/30 p-6">
          <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
            {language === "zh" ? "自动获取 · Auto-fetched" : "Auto-fetched"}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {language === "zh"
              ? "根据所选城市，当前气温、湿度、天气状况与季节将由系统自动联网获取，无需手动填写。"
              : "Current temperature, humidity, weather and season will be fetched automatically from the selected city."}
          </p>
        </section>
      </div>
    </div>
  )
}
