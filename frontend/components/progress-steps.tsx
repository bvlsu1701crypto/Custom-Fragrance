"use client"

import { cn } from "@/lib/utils"

interface ProgressStepsProps {
  currentStep: number
  steps: string[]
}

export function ProgressSteps({ currentStep, steps }: ProgressStepsProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-center gap-12">
        {steps.map((step, index) => (
          <div key={step} className="flex flex-col items-center">
            <span
              className={cn(
                "text-xs uppercase tracking-[0.15em] transition-colors",
                index === currentStep 
                  ? "text-foreground" 
                  : index < currentStep
                    ? "text-muted-foreground"
                    : "text-muted-foreground/50"
              )}
            >
              {step}
            </span>
            <div
              className={cn(
                "mt-2 h-px w-12 transition-colors",
                index === currentStep 
                  ? "bg-foreground" 
                  : index < currentStep
                    ? "bg-muted-foreground"
                    : "bg-border"
              )}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
