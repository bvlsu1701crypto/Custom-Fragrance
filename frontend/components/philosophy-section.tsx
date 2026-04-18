"use client"

import { useLanguage } from "@/lib/language-context"

export function PhilosophySection() {
  const { language } = useLanguage()

  const content: Record<"zh" | "en", {
    intro: string
    introSub: string
    introHighlight: string
    quote: string
    section1Title: string
    section1Sub: string
    section1Text1: string
    section1Text2: string
    section1Text3: string
    section2Title: string
    section2Text1: string
    section2Text2: string
    section2Text3: string
    section2Text4: string
    section2Highlight: string
    section2HighlightSub: string
    section3Title: string
    section3Sub: string
    section3Text1: string
    section3Text2: string
    section3Text3: string
    section3Text4: string
    section3Note: string
    section3NoteSub: string
    section3NoteEnd: string
    section4Title: string
    section4Stat1: string
    section4Stat2: string
    section4Stat3: string
    section4StatHighlight: string
    section5Title: string
    section5Sub: string
    section5Highlight: string
    section6Title: string
    section6Sub: string
    section6Note: string
    section6NoteHighlight: string
    section6NoteSub: string
    state1: string
    state1Sub: string
    state2: string
    state2Sub: string
    state3: string
    state3Sub: string
    section7Title: string
    section7Sub: string
    section7Highlight: string
    section7Text: string
    section7TextSub: string
    section7TextHighlight: string
    section8Title: string
    section8Sub: string
    section8Text: string
    section8Highlight: string
    tagline: string
    brand: string
  }> = {
    zh: {
      intro: "AI 调香师来了。",
      introSub: "但这一次，它不是在制造香水。",
      introHighlight: "它在理解你。",
      quote: "「Smell is a word, perfume is literature.」",
      section1Title: "嗅觉，是一种语言。",
      section1Sub: "而香气，是你未说出口的那一部分。",
      section1Text1: "在 ScentMind，我们相信——",
      section1Text2: "气味，不该被品牌定义。",
      section1Text3: "而应该，回到你本身。",
      section2Title: "我们创造了一种新的方式，去「阅读」人。",
      section2Text1: "不是通过标签，",
      section2Text2: "也不是通过简单的性格分类。",
      section2Text3: "而是通过你的选择、停顿、犹豫，",
      section2Text4: "甚至是你思考的时间。",
      section2Highlight: "AI 不只是计算。",
      section2HighlightSub: "它在感知。",
      section3Title: "当你进入 ScentMind，",
      section3Sub: "你不会被问「你喜欢什么味道」。",
      section3Text1: "你会被问——",
      section3Text2: "你想去哪里？",
      section3Text3: "你最近在想什么？",
      section3Text4: "什么让你停下来？",
      section3Note: "这些答案，不会直接变成气味。",
      section3NoteSub: "它们会被拆解，",
      section3NoteEnd: "成为一个个「Scent Modules」。",
      section4Title: "我们构建了属于 ScentMind 的气味语言。",
      section4Stat1: "46 种基础结构，",
      section4Stat2: "数千种原料，",
      section4Stat3: "以及——",
      section4StatHighlight: "超过 5,000 亿种可能性。",
      section5Title: "但我们并不追求「更多」。",
      section5Sub: "我们只在寻找一件事：",
      section5Highlight: "那个最像你的气味。",
      section6Title: "几分钟后，",
      section6Sub: "三种不同的状态，被生成。",
      section6Note: "不是香水。",
      section6NoteHighlight: "而是——",
      section6NoteSub: "你此刻的三种存在方式。",
      state1: "RESET",
      state1Sub: "A Moment of Nothingness",
      state2: "DRIFT",
      state2Sub: "Drift Without Thought",
      state3: "FOCUS",
      state3Sub: "Clarity from Within",
      section7Title: "你可以选择。",
      section7Sub: "也可以调整。",
      section7Highlight: "甚至改变它。",
      section7Text: "因为在这里——",
      section7TextSub: "调香的主控权，不在品牌。",
      section7TextHighlight: "在你。",
      section8Title: "这不是关于科技。",
      section8Sub: "也不是关于效率。",
      section8Text: "这是关于一件更安静的事情：",
      section8Highlight: "让大脑，慢慢回到自己。",
      tagline: "Still the Mind.",
      brand: "ScentMind",
    },
    en: {
      intro: "The AI perfumer has arrived.",
      introSub: "But this time, it's not making perfume.",
      introHighlight: "It's understanding you.",
      quote: "「Smell is a word, perfume is literature.」",
      section1Title: "Scent is a language.",
      section1Sub: "And fragrance is the part of you left unspoken.",
      section1Text1: "At ScentMind, we believe—",
      section1Text2: "Scent should not be defined by brands.",
      section1Text3: "It should return to you.",
      section2Title: "We've created a new way to 'read' people.",
      section2Text1: "Not through labels,",
      section2Text2: "nor through simple personality types.",
      section2Text3: "But through your choices, pauses, hesitations,",
      section2Text4: "even the time you take to think.",
      section2Highlight: "AI doesn't just calculate.",
      section2HighlightSub: "It perceives.",
      section3Title: "When you enter ScentMind,",
      section3Sub: "you won't be asked 'what scents do you like?'",
      section3Text1: "You'll be asked—",
      section3Text2: "Where do you want to go?",
      section3Text3: "What's been on your mind?",
      section3Text4: "What makes you pause?",
      section3Note: "These answers won't directly become scents.",
      section3NoteSub: "They'll be deconstructed,",
      section3NoteEnd: "into individual 'Scent Modules'.",
      section4Title: "We've built ScentMind's own scent language.",
      section4Stat1: "46 foundational structures,",
      section4Stat2: "thousands of raw materials,",
      section4Stat3: "and—",
      section4StatHighlight: "over 500 billion possibilities.",
      section5Title: "But we don't pursue 'more'.",
      section5Sub: "We're only searching for one thing:",
      section5Highlight: "The scent that is most like you.",
      section6Title: "Minutes later,",
      section6Sub: "three different states are generated.",
      section6Note: "Not perfumes.",
      section6NoteHighlight: "But rather—",
      section6NoteSub: "three ways of existing in this moment.",
      state1: "RESET",
      state1Sub: "A Moment of Nothingness",
      state2: "DRIFT",
      state2Sub: "Drift Without Thought",
      state3: "FOCUS",
      state3Sub: "Clarity from Within",
      section7Title: "You can choose.",
      section7Sub: "You can adjust.",
      section7Highlight: "You can even change it.",
      section7Text: "Because here—",
      section7TextSub: "the control of fragrance creation isn't with the brand.",
      section7TextHighlight: "It's with you.",
      section8Title: "This isn't about technology.",
      section8Sub: "Nor about efficiency.",
      section8Text: "It's about something quieter:",
      section8Highlight: "Letting the mind slowly return to itself.",
      tagline: "Still the Mind.",
      brand: "ScentMind",
    },
  }

  const t = language === "zh" ? content.zh : content.en

  return (
    <section className="py-24">
      {/* Opening */}
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-lg text-muted-foreground">{t.intro}</p>
        <p className="mt-1 text-lg text-muted-foreground">{t.introSub}</p>
        <p className="mt-6 font-serif text-3xl tracking-tight">{t.introHighlight}</p>
      </div>

      {/* Divider */}
      <div className="my-16 flex items-center justify-center">
        <div className="h-px w-16 bg-border" />
      </div>

      {/* Quote */}
      <div className="mx-auto max-w-2xl text-center">
        <p className="font-serif text-xl italic text-muted-foreground">{t.quote}</p>
      </div>

      {/* Section 1 */}
      <div className="mx-auto mt-20 max-w-2xl">
        <h3 className="font-serif text-2xl tracking-tight">{t.section1Title}</h3>
        <p className="mt-2 text-muted-foreground">{t.section1Sub}</p>
        <div className="mt-8 space-y-2 border-l-2 border-accent pl-6">
          <p className="text-sm text-muted-foreground">{t.section1Text1}</p>
          <p className="font-medium">{t.section1Text2}</p>
          <p className="font-medium">{t.section1Text3}</p>
        </div>
      </div>

      {/* Section 2 */}
      <div className="mx-auto mt-20 max-w-2xl">
        <h3 className="font-serif text-2xl tracking-tight">{t.section2Title}</h3>
        <div className="mt-6 space-y-1 text-muted-foreground">
          <p>{t.section2Text1}</p>
          <p>{t.section2Text2}</p>
          <p className="mt-4">{t.section2Text3}</p>
          <p>{t.section2Text4}</p>
        </div>
        <div className="mt-8 bg-secondary/50 p-6">
          <p className="font-medium">{t.section2Highlight}</p>
          <p className="mt-1 font-serif text-xl">{t.section2HighlightSub}</p>
        </div>
      </div>

      {/* Section 3 */}
      <div className="mx-auto mt-20 max-w-2xl">
        <h3 className="font-serif text-2xl tracking-tight">{t.section3Title}</h3>
        <p className="mt-2 text-muted-foreground">{t.section3Sub}</p>
        <div className="mt-8 space-y-3">
          <p className="text-sm text-muted-foreground">{t.section3Text1}</p>
          <p className="font-medium">{t.section3Text2}</p>
          <p className="font-medium">{t.section3Text3}</p>
          <p className="font-medium">{t.section3Text4}</p>
        </div>
        <div className="mt-8 border-t border-border pt-6">
          <p className="text-sm text-muted-foreground">{t.section3Note}</p>
          <p className="mt-2 text-muted-foreground">{t.section3NoteSub}</p>
          <p className="mt-1 font-serif text-lg">{t.section3NoteEnd}</p>
        </div>
      </div>

      {/* Section 4 - Stats */}
      <div className="mx-auto mt-20 max-w-2xl">
        <h3 className="font-serif text-2xl tracking-tight">{t.section4Title}</h3>
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          <div className="border border-border p-4 text-center">
            <p className="text-2xl font-light">46</p>
            <p className="mt-1 text-xs text-muted-foreground">{t.section4Stat1}</p>
          </div>
          <div className="border border-border p-4 text-center">
            <p className="text-2xl font-light">1000+</p>
            <p className="mt-1 text-xs text-muted-foreground">{t.section4Stat2}</p>
          </div>
          <div className="border border-border p-4 text-center">
            <p className="text-2xl font-light">500B+</p>
            <p className="mt-1 text-xs text-muted-foreground">{t.section4StatHighlight}</p>
          </div>
        </div>
      </div>

      {/* Section 5 */}
      <div className="mx-auto mt-20 max-w-2xl text-center">
        <p className="text-muted-foreground">{t.section5Title}</p>
        <p className="mt-2 text-muted-foreground">{t.section5Sub}</p>
        <p className="mt-6 font-serif text-3xl tracking-tight">{t.section5Highlight}</p>
      </div>

      {/* Section 6 - States */}
      <div className="mx-auto mt-20 max-w-2xl">
        <p className="text-muted-foreground">{t.section6Title}</p>
        <p className="text-muted-foreground">{t.section6Sub}</p>
        <p className="mt-4 text-sm text-muted-foreground">{t.section6Note}</p>
        <p className="font-serif text-xl">{t.section6NoteHighlight}</p>
        <p className="text-muted-foreground">{t.section6NoteSub}</p>

        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          <div className="border border-border bg-card p-6 text-center">
            <p className="text-xs tracking-[0.3em] text-muted-foreground">{t.state1}</p>
            <p className="mt-2 text-sm italic">{t.state1Sub}</p>
          </div>
          <div className="border border-border bg-card p-6 text-center">
            <p className="text-xs tracking-[0.3em] text-muted-foreground">{t.state2}</p>
            <p className="mt-2 text-sm italic">{t.state2Sub}</p>
          </div>
          <div className="border border-border bg-card p-6 text-center">
            <p className="text-xs tracking-[0.3em] text-muted-foreground">{t.state3}</p>
            <p className="mt-2 text-sm italic">{t.state3Sub}</p>
          </div>
        </div>
      </div>

      {/* Section 7 */}
      <div className="mx-auto mt-20 max-w-2xl">
        <p className="text-muted-foreground">{t.section7Title}</p>
        <p className="text-muted-foreground">{t.section7Sub}</p>
        <p className="mt-2 font-medium">{t.section7Highlight}</p>
        <div className="mt-6 border-l-2 border-accent pl-6">
          <p className="text-sm text-muted-foreground">{t.section7Text}</p>
          <p className="text-muted-foreground">{t.section7TextSub}</p>
          <p className="mt-2 font-serif text-xl">{t.section7TextHighlight}</p>
        </div>
      </div>

      {/* Section 8 - Closing */}
      <div className="mx-auto mt-20 max-w-2xl text-center">
        <p className="text-muted-foreground">{t.section8Title}</p>
        <p className="text-muted-foreground">{t.section8Sub}</p>
        <p className="mt-6 text-muted-foreground">{t.section8Text}</p>
        <p className="mt-4 font-serif text-2xl tracking-tight">{t.section8Highlight}</p>
      </div>

      {/* Divider */}
      <div className="my-16 flex items-center justify-center">
        <div className="h-px w-16 bg-border" />
      </div>

      {/* Tagline */}
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-xs tracking-[0.4em] text-muted-foreground">{t.tagline}</p>
        <p className="mt-4 font-serif text-4xl tracking-tight">{t.brand}</p>
      </div>
    </section>
  )
}
