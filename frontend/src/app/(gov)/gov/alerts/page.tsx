"use client"

import * as React from "react"
import { AlertTriangle, Calendar, MapPin, Sparkles, Users2, Workflow } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { ListSkeleton } from "@/components/shared/loading-state"
import * as govService from "@/services/gov-service"
import { formatDate } from "@/lib/format"
import type { PredictiveAlert } from "@/types"
import { cn } from "@/lib/utils"

const RISK_TONE = { low: "info", medium: "warning", high: "warning", critical: "destructive" } as const

export default function AlertsPage() {
  const [alerts, setAlerts] = React.useState<PredictiveAlert[] | null>(null)
  const [acknowledged, setAcknowledged] = React.useState<Set<string>>(new Set())

  React.useEffect(() => {
    govService.getPredictiveAlerts().then(setAlerts)
  }, [])

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <PageHeader
        title="Predictive Risk Alerts"
        description="AI-forecasted civic risks based on complaint patterns, seasonal trends, and infrastructure data - act before issues escalate."
      />

      <div className="mb-6 flex items-center justify-between rounded-lg border border-primary/20 bg-primary/[0.03] p-3 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Workflow className="size-4 text-primary shrink-0" />
          <span>Automated Escalation Workflows: Connected via <strong>n8n Webhook</strong> triggers for real-time municipal notification.</span>
        </div>
        <Badge variant="outline" className="hidden sm:flex border-primary/30 text-primary text-[11px] gap-1 font-normal">
          <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" /> n8n Live
        </Badge>
      </div>

      {!alerts && <ListSkeleton count={4} />}

      <div className="space-y-4">
        {alerts?.map((alert) => {
          const isAck = acknowledged.has(alert.id)
          return (
            <Card key={alert.id} className={cn("space-y-4 p-5", isAck && "opacity-60")}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className={cn("mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full", alert.riskLevel === "critical" || alert.riskLevel === "high" ? "bg-destructive/10" : "bg-warning/15")}>
                    <AlertTriangle className={cn("size-4", alert.riskLevel === "critical" || alert.riskLevel === "high" ? "text-destructive" : "text-warning-foreground")} />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold">{alert.title}</h3>
                    <p className="mt-0.5 text-xs text-muted-foreground">{alert.description}</p>
                  </div>
                </div>
                <StatusBadge label={alert.riskLevel} tone={RISK_TONE[alert.riskLevel]} className="shrink-0" />
              </div>

              <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1"><MapPin className="size-3.5" /> {alert.ward}</span>
                <span className="flex items-center gap-1"><Calendar className="size-3.5" /> Predicted for {formatDate(alert.predictedFor)}</span>
                <span className="flex items-center gap-1"><Users2 className="size-3.5" /> ~{alert.affectedPopulationEstimate.toLocaleString("en-IN")} residents affected</span>
                <span className="flex items-center gap-1"><Sparkles className="size-3.5" /> {Math.round(alert.confidence * 100)}% confidence</span>
              </div>

              <div className="rounded-lg bg-muted/50 p-3">
                <p className="text-xs font-medium">Recommended Action</p>
                <p className="text-xs text-muted-foreground">{alert.recommendedAction}</p>
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  size="sm"
                  variant={isAck ? "outline" : "default"}
                  onClick={() => setAcknowledged((prev) => {
                    const next = new Set(prev)
                    if (next.has(alert.id)) next.delete(alert.id)
                    else next.add(alert.id)
                    return next
                  })}
                >
                  {isAck ? "Acknowledged" : "Acknowledge & Assign"}
                </Button>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
