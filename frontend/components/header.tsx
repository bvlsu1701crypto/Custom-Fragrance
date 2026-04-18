"use client"

import { useState } from "react"
import { useLanguage } from "@/lib/language-context"
import { SignUpModal } from "@/components/sign-up-modal"
import { Globe } from "lucide-react"

export function Header() {
  const { language, setLanguage, t } = useLanguage()
  const [showSignUp, setShowSignUp] = useState(false)

  const toggleLanguage = () => {
    setLanguage(language === "zh" ? "en" : "zh")
  }

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/95 backdrop-blur-sm">
        <div className="mx-auto flex h-20 max-w-6xl items-center justify-between px-6">
          <a href="/" className="flex items-baseline gap-3">
            <span className="font-serif text-2xl tracking-wide">ScentMind</span>
            <span className="text-xs tracking-[0.3em] text-muted-foreground">香气智能</span>
          </a>
          <nav className="hidden items-center gap-10 md:flex">
            <a href="#" className="text-xs uppercase tracking-[0.2em] text-muted-foreground transition-colors hover:text-foreground">
              {t.philosophy}
            </a>
            <a href="#" className="text-xs uppercase tracking-[0.2em] text-muted-foreground transition-colors hover:text-foreground">
              {t.collection}
            </a>
            <a href="#" className="text-xs uppercase tracking-[0.2em] text-muted-foreground transition-colors hover:text-foreground">
              {t.consultation}
            </a>
          </nav>
          <div className="flex items-center gap-4">
            {/* Language Switch */}
            <button 
              onClick={toggleLanguage}
              className="flex items-center gap-1.5 text-xs uppercase tracking-[0.15em] text-muted-foreground transition-colors hover:text-foreground"
              aria-label="Switch language"
            >
              <Globe className="h-4 w-4" />
              <span>{language === "zh" ? "EN" : "中文"}</span>
            </button>
            
            <div className="h-4 w-px bg-border" />
            
            <button className="text-xs uppercase tracking-[0.15em] text-muted-foreground transition-colors hover:text-foreground">
              {t.signIn}
            </button>
            <button 
              onClick={() => setShowSignUp(true)}
              className="border border-foreground px-6 py-2.5 text-xs uppercase tracking-[0.15em] transition-colors hover:bg-foreground hover:text-background"
            >
              {t.signUp}
            </button>
          </div>
        </div>
      </header>

      <SignUpModal 
        open={showSignUp} 
        onOpenChange={setShowSignUp}
        onSwitchToSignIn={() => setShowSignUp(false)}
      />
    </>
  )
}
