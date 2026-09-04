"use client"

import * as React from "react"
import { AlertTriangle, TrendingDown, TrendingUp } from "lucide-react"
import { Card } from "@/components/ui/card"
import { StatGridSkeleton } from "@/components/shared/loading-state"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { IssueTrendChart } from "@/components/gov/charts/issue-trend-chart"
import { CategoryBreakdownChart } from "@/components/gov/charts/category-breakdown-chart"
import * as govService from "@/services/gov-service"
import type { CategoryBreakdown, TrendPoint, WardStat } from "@/types"
import { cn } from "@/lib/utils"

export default function AnalyticsPage() {
  const [trend, setTrend] = React.useState<TrendPoint[] | null>(null)
  const [breakdown, setBreakdown] = React.useState<CategoryBreakdown[] | null>(null)
  const [wardStats, setWardStats] = React.useState<WardStat[] | null>(null)

  React.useEffect(() => {
    govService.getIssueTrend().then(setTrend)
    govService.getCategoryBreakdown().then(setBreakdown)
    govService.getWardStats().then(setWardStats)
  }, [])

  const anomalies = breakdown?.filter((c) => Math.abs(c.percentChange) >= 12) ?? []

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <PageHeader title="Analytics & Trends" description="Issue trends, category shifts, and ward-level performance across the city." />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <Card className="p-5 lg:col-span-3">
          <h2 className="mb-3 text-sm font-semibold">30-Day Complaint Volume</h2>
          {trend ? <IssueTrendChart data={trend} /> : <div className="h-64 animate-pulse rounded-lg bg-muted" />}
        </Card>
        <Card className="p-5 lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold">Category Breakdown</h2>
          {breakdown ? <CategoryBreakdownChart data={breakdown} /> : <div className="h-72 animate-pulse rounded-lg bg-muted" />}
        </Card>
      </div>

      <Card className="mt-6 p-5">
        <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold">
          <AlertTriangle className="size-4 text-warning-foreground" /> Anomaly Detection
        </h2>
        {anomalies.length === 0 ? (
          <p className="text-sm text-muted-foreground">No significant anomalies detected in the current period.</p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {anomalies.map((a, i) => (
              <div key={`${a.category}-${i}`} className="flex items-center justify-between rounded-lg border border-border p-3">
                <div>
                  <p className="text-sm font-medium">{a.category}</p>
                  <p className="text-xs text-muted-foreground">{a.count} complaints this period</p>
                </div>
                <span className={cn("flex items-center gap-1 text-sm font-semibold", a.percentChange > 0 ? "text-destructive" : "text-success")}>
                  {a.percentChange > 0 ? <TrendingUp className="size-3.5" /> : <TrendingDown className="size-3.5" />}
                  {a.percentChange > 0 ? "+" : ""}{a.percentChange}%
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="mt-6 overflow-hidden p-0">
        <div className="p-5 pb-0">
          <h2 className="text-sm font-semibold">Ward-Level Performance</h2>
        </div>
        {!wardStats ? (
          <div className="p-5"><StatGridSkeleton count={4} /></div>
        ) : (
          <div className="overflow-x-auto p-5 pt-3">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ward</TableHead>
                  <TableHead>Total Issues</TableHead>
                  <TableHead>Resolved</TableHead>
                  <TableHead>Resolution Rate</TableHead>
                  <TableHead>Avg. Resolution (days)</TableHead>
                  <TableHead>Risk Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {wardStats.map((w) => {
                  const rate = Math.round((w.resolvedIssues / w.totalIssues) * 100)
                  return (
                    <TableRow key={w.ward}>
                      <TableCell className="font-medium">{w.ward}</TableCell>
                      <TableCell>{w.totalIssues}</TableCell>
                      <TableCell>{w.resolvedIssues}</TableCell>
                      <TableCell>{rate}%</TableCell>
                      <TableCell>{w.avgResolutionDays}</TableCell>
                      <TableCell>
                        <StatusBadge
                          label={`${w.riskScore}`}
                          tone={w.riskScore >= 75 ? "destructive" : w.riskScore >= 55 ? "warning" : "success"}
                        />
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </Card>
    </div>
  )
}
