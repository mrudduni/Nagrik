"use client"

import * as React from "react"
import { ArrowDown, ArrowUp, Minus } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { CardGridSkeleton } from "@/components/shared/loading-state"
import * as govService from "@/services/gov-service"
import type { DepartmentPerformance } from "@/types"
import { cn } from "@/lib/utils"

export default function DepartmentsPage() {
  const [departments, setDepartments] = React.useState<DepartmentPerformance[] | null>(null)

  React.useEffect(() => {
    govService.getDepartments().then(setDepartments)
  }, [])

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <PageHeader title="Department Performance" description="Resolution throughput and SLA compliance across every civic department." />

      {!departments && <CardGridSkeleton count={6} />}

      {departments && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {departments.map((d) => {
            const TrendIcon = d.trend === "up" ? ArrowUp : d.trend === "down" ? ArrowDown : Minus
            return (
              <Card key={d.id} className="space-y-4 p-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold leading-snug">{d.name}</h3>
                    <p className="text-xs text-muted-foreground">Head: {d.headOfficer}</p>
                  </div>
                  <span
                    className={cn(
                      "flex shrink-0 items-center gap-0.5 text-xs font-medium",
                      d.trend === "up" ? "text-success" : d.trend === "down" ? "text-destructive" : "text-muted-foreground",
                    )}
                  >
                    <TrendIcon className="size-3" />
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-muted/50 py-2">
                    <p className="text-lg font-semibold">{d.totalComplaints}</p>
                    <p className="text-[10px] text-muted-foreground">Total</p>
                  </div>
                  <div className="rounded-lg bg-muted/50 py-2">
                    <p className="text-lg font-semibold text-success">{d.resolved}</p>
                    <p className="text-[10px] text-muted-foreground">Resolved</p>
                  </div>
                  <div className="rounded-lg bg-muted/50 py-2">
                    <p className="text-lg font-semibold text-warning-foreground">{d.pending}</p>
                    <p className="text-[10px] text-muted-foreground">Pending</p>
                  </div>
                </div>

                <div>
                  <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
                    <span>SLA Compliance</span>
                    <span>{d.slaCompliance}%</span>
                  </div>
                  <Progress value={d.slaCompliance} className={cn("h-1.5", d.slaCompliance < 65 && "[&>div]:bg-destructive", d.slaCompliance >= 65 && d.slaCompliance < 80 && "[&>div]:bg-warning")} />
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Avg. Resolution Time</span>
                  <StatusBadge label={`${d.avgResolutionHours} hrs`} tone={d.avgResolutionHours > 80 ? "destructive" : d.avgResolutionHours > 50 ? "warning" : "success"} />
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
