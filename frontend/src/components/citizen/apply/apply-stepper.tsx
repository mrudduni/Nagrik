import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ApplyStep {
  id: string
  label: string
}

export function ApplyStepper({ steps, currentIndex }: { steps: ApplyStep[]; currentIndex: number }) {
  return (
    <div className="flex items-center">
      {steps.map((step, i) => (
        <div key={step.id} className="flex flex-1 items-center last:flex-none">
          <div className="flex flex-col items-center gap-1.5">
            <div
              className={cn(
                "flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold transition-colors",
                i < currentIndex && "border-primary bg-primary text-primary-foreground",
                i === currentIndex && "border-primary bg-primary/10 text-primary",
                i > currentIndex && "border-border bg-muted text-muted-foreground",
              )}
            >
              {i < currentIndex ? <Check className="size-4" /> : i + 1}
            </div>
            <span className={cn("hidden text-[11px] font-medium sm:block", i === currentIndex ? "text-foreground" : "text-muted-foreground")}>
              {step.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={cn("mx-2 h-0.5 flex-1 rounded-full", i < currentIndex ? "bg-primary" : "bg-border")} />
          )}
        </div>
      ))}
    </div>
  )
}
