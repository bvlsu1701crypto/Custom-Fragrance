"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Header } from "@/components/header"
import { fetchIngredients } from "@/lib/api/service"
import type { FormulaNote, Ingredient } from "@/lib/api/schemas"
import { useLanguage } from "@/lib/language-context"
import { useRecommendation } from "@/lib/recommendation-context"

type LayerKey = "top" | "middle" | "base"

interface LayerConfig {
  key: LayerKey
  labelZh: string
  labelEn: string
  hintZh: string
  hintEn: string
}

const LAYERS: LayerConfig[] = [
  {
    key: "top",
    labelZh: "前调",
    labelEn: "Top Notes",
    hintZh: "初次接触时感受到的香气，持续 15-30 分钟",
    hintEn: "First impression, lasts 15-30 minutes",
  },
  {
    key: "middle",
    labelZh: "中调",
    labelEn: "Heart Notes",
    hintZh: "香水的核心与灵魂，持续 2-4 小时",
    hintEn: "Core of the fragrance, lasts 2-4 hours",
  },
  {
    key: "base",
    labelZh: "后调",
    labelEn: "Base Notes",
    hintZh: "持久留香的基底，持续 4-8+ 小时",
    hintEn: "Foundation, lasts 4-8+ hours",
  },
]

function sumPct(notes: FormulaNote[]): number {
  return Math.round(notes.reduce((acc, n) => acc + (n.percentage ?? 0), 0))
}

function IngredientRow({
  note,
  ingredient,
  language,
}: {
  note: FormulaNote
  ingredient?: Ingredient
  language: "zh" | "en"
}) {
  const displayName = ingredient?.name_cn || note.name
  const englishName = ingredient?.name
  const fn = ingredient?.function
  const desc = ingredient?.description
  const usage = ingredient?.usage
  const intensity = ingredient?.intensity
  const caution = ingredient?.caution_level

  return (
    <div className="grid gap-3 border-b border-border py-5 last:border-b-0 md:grid-cols-[minmax(0,2fr)_auto_minmax(0,3fr)]">
      {/* Name + percentage */}
      <div className="flex flex-col">
        <div className="flex items-baseline gap-2">
          <span className="font-serif text-lg">{displayName}</span>
          {englishName && englishName !== displayName && (
            <span className="text-xs text-muted-foreground">{englishName}</span>
          )}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <Badge variant="secondary" className="text-[10px] uppercase tracking-wider">
            {note.percentage}%
          </Badge>
          <span className="text-xs text-muted-foreground">
            {language === "zh" ? "扩散 " : "Diffusion "}
            {note.diffusion_distance}
          </span>
          {intensity && (
            <span className="text-xs text-muted-foreground">
              {language === "zh" ? "强度 " : "Intensity "}
              {intensity}
            </span>
          )}
          {caution && caution !== "推荐" && (
            <Badge
              variant="outline"
              className="border-destructive/40 text-[10px] uppercase tracking-wider text-destructive"
            >
              {caution}
            </Badge>
          )}
        </div>
      </div>

      {/* Percentage bar */}
      <div className="hidden md:flex md:items-center">
        <div className="h-1 w-20 overflow-hidden bg-secondary">
          <div
            className="h-full bg-foreground"
            style={{ width: `${Math.min(100, note.percentage)}%` }}
          />
        </div>
      </div>

      {/* Function + description */}
      <div className="space-y-1 text-sm">
        {fn && (
          <p>
            <span className="text-muted-foreground">
              {language === "zh" ? "功能：" : "Function: "}
            </span>
            <span>{fn}</span>
          </p>
        )}
        {desc && (
          <p>
            <span className="text-muted-foreground">
              {language === "zh" ? "描述：" : "Description: "}
            </span>
            <span>{desc}</span>
          </p>
        )}
        {usage && (
          <p className="text-xs text-muted-foreground">
            {language === "zh" ? "气味：" : "Scent: "}
            {usage}
          </p>
        )}
        {!fn && !desc && !usage && (
          <p className="text-xs italic text-muted-foreground">
            {language === "zh" ? "无额外说明" : "No additional detail"}
          </p>
        )}
      </div>
    </div>
  )
}

export default function DetailPage() {
  const router = useRouter()
  const { language } = useLanguage()
  const { raw } = useRecommendation()
  const [ingredientMap, setIngredientMap] = useState<Map<number, Ingredient>>(new Map())
  const [loadFailed, setLoadFailed] = useState(false)

  useEffect(() => {
    if (!raw) {
      router.replace("/")
      return
    }
    let cancelled = false
    fetchIngredients()
      .then((list) => {
        if (cancelled) return
        const m = new Map<number, Ingredient>()
        for (const ing of list) {
          if (typeof ing.id === "number") m.set(ing.id, ing)
        }
        setIngredientMap(m)
      })
      .catch((err) => {
        if (cancelled) return
        setLoadFailed(true)
        toast.error(
          `${language === "zh" ? "原料详情加载失败：" : "Failed to load ingredient detail: "}${
            (err as Error).message
          }`,
        )
      })
    return () => {
      cancelled = true
    }
  }, [raw, router, language])

  if (!raw) return null

  const { formula, volume_ml, concentration_percentage, estimated_longevity_hours,
          selection_rationale, scent_description } = raw

  const byLayer: Record<LayerKey, FormulaNote[]> = {
    top: formula.top_notes ?? [],
    middle: formula.middle_notes ?? [],
    base: formula.base_notes ?? [],
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-5xl px-6 pb-24 pt-28">
        {/* Top bar */}
        <div className="mb-12 flex items-center justify-between">
          <Link href="/">
            <Button variant="ghost" className="gap-2 text-xs uppercase tracking-[0.15em]">
              <ArrowLeft className="h-4 w-4" />
              {language === "zh" ? "返回结果" : "Back to Result"}
            </Button>
          </Link>
          <div className="text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {language === "zh" ? "配方详情" : "Formula Detail"}
            </p>
            <h1 className="mt-1 font-serif text-2xl tracking-tight">
              {language === "zh" ? "完整成分表" : "Full Composition"}
            </h1>
          </div>
          <div className="w-[140px]" />
        </div>

        {loadFailed && (
          <div className="mb-8 border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
            {language === "zh"
              ? "原料详情服务暂时不可用，仅展示配方与占比。"
              : "Ingredient detail service is unavailable. Showing formula and percentages only."}
          </div>
        )}

        {/* Layer tables */}
        <div className="space-y-12">
          {LAYERS.map((layer) => {
            const notes = byLayer[layer.key]
            if (notes.length === 0) return null
            return (
              <section key={layer.key} className="border border-border bg-card p-8 md:p-10">
                <div className="mb-6 flex flex-wrap items-baseline justify-between gap-2 border-b border-border pb-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                      {language === "zh" ? layer.labelZh : layer.labelEn}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {language === "zh" ? layer.hintZh : layer.hintEn}
                    </p>
                  </div>
                  <span className="font-serif text-sm text-muted-foreground">
                    {language === "zh" ? "合计 " : "Total "}
                    {sumPct(notes)}%
                  </span>
                </div>

                <div>
                  {notes.map((n, idx) => (
                    <IngredientRow
                      key={`${layer.key}-${idx}`}
                      note={n}
                      ingredient={n.ingredient_id ? ingredientMap.get(n.ingredient_id) : undefined}
                      language={language as "zh" | "en"}
                    />
                  ))}
                </div>
              </section>
            )
          })}
        </div>

        {/* Spec card */}
        <section className="mt-12 grid grid-cols-1 gap-px bg-border md:grid-cols-3">
          <div className="bg-card p-8 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {language === "zh" ? "建议总量" : "Volume"}
            </p>
            <p className="mt-3 font-serif text-3xl tabular-nums">
              {volume_ml}
              <span className="ml-1 text-base text-muted-foreground">ml</span>
            </p>
          </div>
          <div className="bg-card p-8 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {language === "zh" ? "香精浓度" : "Concentration"}
            </p>
            <p className="mt-3 font-serif text-3xl tabular-nums">
              {concentration_percentage}
              <span className="ml-1 text-base text-muted-foreground">%</span>
            </p>
          </div>
          <div className="bg-card p-8 text-center">
            <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {language === "zh" ? "预估留香" : "Longevity"}
            </p>
            <p className="mt-3 font-serif text-3xl tabular-nums">
              {estimated_longevity_hours}
              <span className="ml-1 text-base text-muted-foreground">
                {language === "zh" ? "小时" : "h"}
              </span>
            </p>
          </div>
        </section>

        {/* Rationale + description */}
        <section className="mt-12 border border-border bg-card p-8 md:p-10">
          <p className="mb-6 text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {language === "zh" ? "选配理由 · Why this formula" : "Why this formula"}
          </p>
          {selection_rationale && (
            <p className="font-serif text-lg leading-relaxed">{selection_rationale}</p>
          )}
          {scent_description && (
            <>
              <div className="my-6 h-px w-full bg-border" />
              <p className="text-sm leading-relaxed text-muted-foreground">{scent_description}</p>
            </>
          )}
        </section>
      </main>
    </div>
  )
}
