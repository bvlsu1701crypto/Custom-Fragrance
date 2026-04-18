"use client"

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react"
import type { FinalOutput } from "@/lib/api/schemas"
import type { RecommendationOutput } from "@/lib/types"

interface RecommendationContextValue {
  result: RecommendationOutput | null
  raw: FinalOutput | null
  setRecommendation: (result: RecommendationOutput, raw: FinalOutput) => void
  clear: () => void
}

const RecommendationContext = createContext<RecommendationContextValue | null>(null)

export function RecommendationProvider({ children }: { children: ReactNode }) {
  const [result, setResult] = useState<RecommendationOutput | null>(null)
  const [raw, setRaw] = useState<FinalOutput | null>(null)

  const setRecommendation = useCallback((r: RecommendationOutput, rawOutput: FinalOutput) => {
    setResult(r)
    setRaw(rawOutput)
  }, [])

  const clear = useCallback(() => {
    setResult(null)
    setRaw(null)
  }, [])

  const value = useMemo<RecommendationContextValue>(
    () => ({ result, raw, setRecommendation, clear }),
    [result, raw, setRecommendation, clear],
  )

  return <RecommendationContext.Provider value={value}>{children}</RecommendationContext.Provider>
}

export function useRecommendation(): RecommendationContextValue {
  const ctx = useContext(RecommendationContext)
  if (!ctx) {
    throw new Error("useRecommendation must be used inside <RecommendationProvider>")
  }
  return ctx
}
