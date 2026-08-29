"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowRight, ShieldAlert, TrendingUp, Users2 } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatGridSkeleton } from "@/components/shared/loading-state"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { KpiCard } from "@/components/gov/kpi-card"
import { IssueTrendChart } from "@/components/gov/charts/issue-trend-chart"
import { CategoryBreakdownChart } from "@/components/gov/charts/category-breakdown-chart"
import { statusMeta, severityMeta } from "@/services/issue-service"
import * as govService from "@/services/gov-service"
import { useApp } from "@/context/app-provider"
import { formatDate } from "@/lib/format"
import type { CategoryBreakdown, CivicIssue, DuplicateCluster, GovKpi, PredictiveAlert, TrendPoint } from "@/types"
import { listAllComplaints } from "@/services/gov-service"

export default function GovOverviewPage() {
  const { session } = useApp()
  const officer = session?.officer
  const [kpis, setKpis] = React.useState<GovKpi[] | null>(null)
  const [trend, setTrend] = React.useState<TrendPoint[] | null>(null)
  const [breakdown, setBreakdown] = React.useState<CategoryBreakdown[] | null>(null)
  const [urgent, setUrgent] = React.useState<CivicIssue[] | null>(null)
  const [alerts, setAlerts] = React.useState<PredictiveAlert[] | null>(null)
  const [clusters, setClusters] = React.useState<DuplicateCluster[] | null>(null)

  React.useEffect(() => {
    govService.getKpis().then(setKpis)
    govService.getIssueTrend().then(setTrend)
    govService.getCategoryBreakdown().then(setBreakdown)
    govService.getPredictiveAlerts().then(setAlerts)
    govService.getDuplicateClusters().then(setClusters)
    listAllComplaints().then((all) => setUrgent(all.filter((i) => i.severity === "critical" || i.severity === "high").slice(0, 5)))
  }, [])

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <PageHeader
        title={`Welcome back, ${officer?.name.split(" ")[0] ?? "Officer"}`}
        description="Citywide civic intelligence overview - complaints, performance, and predictive risk in one view."
      />

      {!kpis && <StatGridSkeleton count={6} />}
      {kpis && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
          {kpis.map((k) => (
            <KpiCard key={k.label} kpi={k} />
          ))}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-5">
        <Card className="p-5 lg:col-span-3">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="flex items-center gap-1.5 text-sm font-semibold"><TrendingUp className="size-4" /> Complaint Volume (30 Days)</h2>
            <Link href="/gov/analytics" className="text-xs text-primary hover:underline">View analytics</Link>
          </div>
          {trend ? <IssueTrendChart data={trend} /> : <div className="h-64 animate-pulse rounded-lg bg-muted" />}
        </Card>
        <Card className="p-5 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold">Complaints by Category</h2>
          {breakdown ? <CategoryBreakdownChart data={breakdown} /> : <div className="h-72 animate-pulse rounded-lg bg-muted" />}
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-5 lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">High Priority Complaints</h2>
            <Link href="/gov/complaints" className="text-xs text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="size-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {!urgent && Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-14 animate-pulse rounded-lg bg-muted" />)}
            {urgent?.map((issue) => (
              <Link key={issue.id} href={`/gov/complaints/${issue.id}`}>
                <div className="flex items-center justify-between gap-3 rounded-lg border border-border p-3 hover:bg-muted/40 transition-colors">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{issue.title}</p>
                    <p className="text-xs text-muted-foreground">{issue.ward} · {formatDate(issue.reportedOn)}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <StatusBadge {...severityMeta(issue.severity)} withDot={false} />
                    <StatusBadge {...statusMeta(issue.status)} />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="flex items-center gap-1.5 text-sm font-semibold"><ShieldAlert className="size-4 text-destructive" /> Risk Alerts</h2>
              <Link href="/gov/alerts" className="text-xs text-primary hover:underline">View all</Link>
            </div>
            <div className="space-y-3">
              {alerts?.slice(0, 2).map((a) => (
                <div key={a.id} className="space-y-1 rounded-lg border border-border p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium">{a.title}</p>
                    <StatusBadge
                      label={a.riskLevel}
                      tone={a.riskLevel === "critical" ? "destructive" : a.riskLevel === "high" ? "warning" : "info"}
                    />
                  </div>
                  <p className="text-[11px] text-muted-foreground">{a.ward}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold"><Users2 className="size-4" /> Duplicate Clusters</h2>
            <div className="space-y-2">
              {clusters?.map((c) => (
                <div key={c.id} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{c.centerLabel}</span>
                  <span className="font-medium">{c.count} reports</span>
                </div>
              ))}
            </div>
            <Button variant="outline" size="sm" className="mt-3 w-full" asChild>
              <Link href="/gov/complaints?tab=clusters">Review clusters</Link>
            </Button>
          </Card>
        </div>
      </div>
    </div>
  )
}
