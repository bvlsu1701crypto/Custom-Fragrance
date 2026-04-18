"use client"

import { useLanguage } from "@/lib/language-context"

const content = {
  zh: {
    eyebrow: "产品设计理念",
    title: "每个人都是一座孤岛。",
    subtitle: "而我们想做的，不是打断你的沉默，而是在你疲惫的时候，替你留一盏温柔的灯。",
    lead:
      "我们相信，人最需要被看见的时刻，往往不是意气风发的时候，而是撑了很久、终于感到疲惫的时候。",
    paragraph1:
      "隔着屏幕，我们无法真正替你承担现实的重量，也无法假装比你更懂你的处境。",
    paragraph2:
      "但我们愿意认真感受你每一次停顿、每一分犹豫、每一个想要休息却还在向前的瞬间。",
    paragraph3:
      "如果此刻的你正有一点无助，愿 ScentMind 至少替你驱散一半疲惫，让香气成为一段短暂却真实的陪伴。",
    supportTitle: "我们想提供的，不只是推荐。",
    support1: "是一种可以慢下来、被轻轻接住的体验。",
    support2: "是一种不用解释太多，也能被理解的安静关怀。",
    support3: "是一段即使不能陪在你身边，也愿意与你同频的路程。",
    closing:
      "愿我们无法真正站在你身侧的时候，也仍能隔着光、隔着屏幕，陪你走一小段路。",
    signature: "愿与你同行。",
    sideNote: "For the tired heart, with quiet care.",
  },
  en: {
    eyebrow: "Design Philosophy",
    title: "Every person is an island.",
    subtitle:
      "What we hope to offer is not interruption, but a gentle light kept on for you when you are tired.",
    lead:
      "We believe the moments people most need to be seen are rarely the triumphant ones, but the quiet hours after they have already held too much for too long.",
    paragraph1:
      "Through a screen, we cannot fully carry the weight of your reality, nor should we pretend to understand your life better than you do.",
    paragraph2:
      "But we can choose to stay attentive to your pauses, your hesitation, and the small moments when you want rest while still trying to move forward.",
    paragraph3:
      "If you happen to feel a little helpless right now, we hope ScentMind can ease even half of that heaviness, letting scent become a brief but sincere form of companionship.",
    supportTitle: "We want to offer more than a recommendation.",
    support1: "A quieter experience that lets you slow down and feel gently held.",
    support2: "A form of care that does not demand explanation before it can begin to understand.",
    support3: "A small stretch of road we are willing to walk with you, even from the other side of a screen.",
    closing:
      "Even when we cannot truly stand beside you, we still hope to accompany you for a little while through light, scent, and attention.",
    signature: "We walk with you.",
    sideNote: "For the tired heart, with quiet care.",
  },
} as const

export function CompanionManifestoSection() {
  const { language } = useLanguage()
  const t = content[language]

  return (
    <section className="relative overflow-hidden border border-border bg-[linear-gradient(135deg,rgba(255,255,255,0.72),rgba(243,237,227,0.94))] px-6 py-16 md:px-10 md:py-20">
      <div className="pointer-events-none absolute -top-20 right-[-5rem] h-64 w-64 rounded-full bg-accent/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-[-7rem] left-[-4rem] h-72 w-72 rounded-full bg-chart-2/8 blur-3xl" />

      <div className="relative grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:gap-16">
        <div>
          <p className="text-[11px] uppercase tracking-[0.34em] text-muted-foreground">{t.eyebrow}</p>
          <h2 className="mt-4 max-w-3xl font-serif text-4xl leading-tight tracking-tight sm:text-5xl">
            {t.title}
          </h2>
          <p className="mt-4 max-w-2xl text-base leading-8 text-foreground/72 md:text-lg">
            {t.subtitle}
          </p>

          <div className="mt-10 max-w-3xl space-y-5 text-[15px] leading-8 text-foreground/78 md:text-base">
            <p className="font-serif text-xl leading-9 text-foreground/92">{t.lead}</p>
            <p>{t.paragraph1}</p>
            <p>{t.paragraph2}</p>
            <p>{t.paragraph3}</p>
          </div>
        </div>

        <div className="flex flex-col justify-between gap-8">
          <div className="relative border border-foreground/10 bg-background/70 p-7 shadow-[0_20px_80px_rgba(120,104,74,0.08)] backdrop-blur-sm">
            <div className="mb-6 flex items-center gap-3">
              <div className="h-px w-10 bg-foreground/20" />
              <p className="text-[11px] uppercase tracking-[0.3em] text-muted-foreground">{t.sideNote}</p>
            </div>
            <p className="font-serif text-2xl leading-10 tracking-tight text-foreground/92 md:text-3xl">
              {t.supportTitle}
            </p>
            <div className="mt-8 space-y-4">
              <div className="border-l border-foreground/15 pl-4">
                <p className="text-sm leading-7 text-foreground/76">{t.support1}</p>
              </div>
              <div className="border-l border-foreground/15 pl-4">
                <p className="text-sm leading-7 text-foreground/76">{t.support2}</p>
              </div>
              <div className="border-l border-foreground/15 pl-4">
                <p className="text-sm leading-7 text-foreground/76">{t.support3}</p>
              </div>
            </div>
          </div>

          <div className="border-t border-border pt-6 lg:pl-8">
            <p className="max-w-xl text-sm leading-7 text-muted-foreground">{t.closing}</p>
            <p className="mt-5 font-serif text-2xl tracking-tight">{t.signature}</p>
          </div>
        </div>
      </div>
    </section>
  )
}