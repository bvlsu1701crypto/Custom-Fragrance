"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/lib/language-context"
import type { RecommendationOutput } from "@/lib/types"
import { Share2, Download, Copy, Check, Twitter, MessageCircle } from "lucide-react"

interface ShareCardProps {
  result: RecommendationOutput
}

export function ShareCard({ result }: ShareCardProps) {
  const { language } = useLanguage()
  const [copied, setCopied] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)

  const shareText = language === "zh" 
    ? `我的专属香氛档案 | ScentMind\n\n香调结构:\n前调: ${result.fragrance_notes.topNotes.join(", ")}\n中调: ${result.fragrance_notes.middleNotes.join(", ")}\n后调: ${result.fragrance_notes.baseNotes.join(", ")}\n\n推荐香调: ${result.scent_preference.join(", ")}\n场合: ${result.occasion}\n浓度: ${result.concentration}\n\n${result.fragrance_description.zh.substring(0, 100)}...`
    : `My Fragrance Profile | ScentMind\n\nFragrance Notes:\nTop: ${result.fragrance_notes.topNotes.join(", ")}\nHeart: ${result.fragrance_notes.middleNotes.join(", ")}\nBase: ${result.fragrance_notes.baseNotes.join(", ")}\n\nRecommended Scents: ${result.scent_preference.join(", ")}\nOccasion: ${result.occasion}\nConcentration: ${result.concentration}\n\n${(result.fragrance_description.en ?? result.fragrance_description.zh).substring(0, 100)}...`

  const handleCopy = async () => {
    await navigator.clipboard.writeText(shareText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleTwitterShare = () => {
    const text = language === "zh" 
      ? `我通过 ScentMind 发现了专属香氛档案！推荐香调: ${result.scent_preference.slice(0, 3).join(", ")} 🌸`
      : `I discovered my fragrance profile with ScentMind! Recommended scents: ${result.scent_preference.slice(0, 3).join(", ")} 🌸`
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank")
  }

  const handleWeChatShare = () => {
    handleCopy()
    alert(language === "zh" ? "内容已复制，请粘贴到微信分享" : "Content copied, please paste to share on WeChat")
  }

  return (
    <section className="mt-16 border border-border bg-gradient-to-b from-card to-secondary/20 p-8 md:p-12">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mb-4 flex items-center justify-center gap-3">
            <Share2 className="h-5 w-5 text-accent" />
            <h3 className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
              {language === "zh" ? "分享你的香氛档案" : "Share Your Fragrance Profile"}
            </h3>
          </div>
          <p className="text-sm text-muted-foreground">
            {language === "zh" 
              ? "保存或分享你的专属香氛推荐给朋友" 
              : "Save or share your personalized fragrance recommendation with friends"}
          </p>
        </div>

        {/* Share Card Preview */}
        <div 
          ref={cardRef}
          className="mb-8 overflow-hidden border border-border bg-card"
        >
          {/* Card Header */}
          <div className="border-b border-border bg-secondary/30 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-serif text-lg tracking-tight">ScentMind</p>
                <p className="text-xs text-muted-foreground">
                  {language === "zh" ? "香气智能" : "Biometric Fragrance Intelligence"}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-muted-foreground">
                  {new Date().toLocaleDateString(language === "zh" ? "zh-CN" : "en-US")}
                </p>
              </div>
            </div>
          </div>

          {/* Card Content */}
          <div className="p-6">
            {/* Fragrance Notes */}
            <div className="mb-6">
              <p className="mb-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {language === "zh" ? "香调结构" : "Fragrance Notes"}
              </p>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="border border-border/50 bg-secondary/20 p-3">
                  <p className="mb-1 text-[10px] uppercase tracking-wider text-accent">
                    {language === "zh" ? "前调" : "Top"}
                  </p>
                  <p className="text-xs">{result.fragrance_notes.topNotes.join(" · ")}</p>
                </div>
                <div className="border border-border/50 bg-secondary/20 p-3">
                  <p className="mb-1 text-[10px] uppercase tracking-wider text-chart-2">
                    {language === "zh" ? "中调" : "Heart"}
                  </p>
                  <p className="text-xs">{result.fragrance_notes.middleNotes.join(" · ")}</p>
                </div>
                <div className="border border-border/50 bg-secondary/20 p-3">
                  <p className="mb-1 text-[10px] uppercase tracking-wider text-chart-4">
                    {language === "zh" ? "后调" : "Base"}
                  </p>
                  <p className="text-xs">{result.fragrance_notes.baseNotes.join(" · ")}</p>
                </div>
              </div>
            </div>

            {/* Recommended Scents */}
            <div className="mb-6">
              <p className="mb-3 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                {language === "zh" ? "推荐香调" : "Recommended Profile"}
              </p>
              <div className="flex flex-wrap gap-2">
                {result.scent_preference.map((scent) => (
                  <span 
                    key={scent}
                    className="border border-foreground/30 bg-card px-3 py-1 text-xs"
                  >
                    {scent}
                  </span>
                ))}
              </div>
            </div>

            {/* Key Parameters */}
            <div className="grid grid-cols-3 gap-4 border-t border-border pt-4 text-center">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {language === "zh" ? "场合" : "Occasion"}
                </p>
                <p className="mt-1 text-sm">{result.occasion}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {language === "zh" ? "浓度" : "Concentration"}
                </p>
                <p className="mt-1 text-sm">{result.concentration}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {language === "zh" ? "扩散" : "Sillage"}
                </p>
                <p className="mt-1 text-sm">{result.sillage}</p>
              </div>
            </div>
          </div>

          {/* Card Footer */}
          <div className="border-t border-border bg-secondary/20 px-6 py-3">
            <p className="text-center text-[10px] text-muted-foreground">
              {language === "zh" 
                ? "由 ScentMind 香气智能生成 · 基于生物识别与环境数据" 
                : "Generated by ScentMind · Powered by Biometric & Environmental Data"}
            </p>
          </div>
        </div>

        {/* Share Actions */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            className="gap-2 text-xs uppercase tracking-[0.1em]"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4" />
                {language === "zh" ? "已复制" : "Copied"}
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                {language === "zh" ? "复制文本" : "Copy Text"}
              </>
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleTwitterShare}
            className="gap-2 text-xs uppercase tracking-[0.1em]"
          >
            <Twitter className="h-4 w-4" />
            Twitter
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleWeChatShare}
            className="gap-2 text-xs uppercase tracking-[0.1em]"
          >
            <MessageCircle className="h-4 w-4" />
            {language === "zh" ? "微信" : "WeChat"}
          </Button>

          <Button
            variant="default"
            size="sm"
            onClick={() => window.print()}
            className="gap-2 border border-foreground bg-foreground text-background text-xs uppercase tracking-[0.1em]"
          >
            <Download className="h-4 w-4" />
            {language === "zh" ? "保存图片" : "Save Image"}
          </Button>
        </div>

        {/* Tip */}
        <p className="mt-6 text-center text-xs text-muted-foreground">
          {language === "zh" 
            ? "提示：点击「保存图片」将以打印模式保存您的香氛档案" 
            : "Tip: Click 'Save Image' to save your fragrance profile in print mode"}
        </p>
      </div>
    </section>
  )
}
