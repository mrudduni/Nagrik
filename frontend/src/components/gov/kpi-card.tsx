import { ArrowDown, ArrowUp, Minus } from "lucide-react"
import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { GovKpi } from "@/types"

export function KpiCard({ kpi }: { kpi: GovKpi }) {
  const TrendIcon = kpi.trend === "up" ? ArrowUp : kpi.trend === "down" ? ArrowDown : Minus
  return (
    <Card className="space-y-1.5 p-5">
      <p className="text-xs font-medium text-muted-foreground">{kpi.label}</p>
      <div className="flex items-baseline gap-2">
        <p className="text-2xl font-semibold tracking-tight">{kpi.value}</p>
        <span className={cn("flex items-center gap-0.5 text-xs font-medium", kpi.trend === "up" ? "text-success" : kpi.trend === "down" ? "text-destructive" : "text-muted-foreground")}>
          <TrendIcon className="size-3" /> {kpi.delta}
        </span>
      </div>
      <p className="text-[11px] text-muted-foreground">{kpi.helpText}</p>
    </Card>
  )
}
