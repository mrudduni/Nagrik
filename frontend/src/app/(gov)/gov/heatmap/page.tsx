"use client"

import * as React from "react"
import { MapPin } from "lucide-react"
import { Card } from "@/components/ui/card"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import * as govService from "@/services/gov-service"
import type { WardStat } from "@/types"
import { cn } from "@/lib/utils"

const PADDING = 12

function riskColor(score: number): string {
  if (score >= 75) return "var(--destructive)"
  if (score >= 55) return "var(--warning)"
  return "var(--success)"
}

export default function HeatmapPage() {
  const [wardStats, setWardStats] = React.useState<WardStat[] | null>(null)
  const [selected, setSelected] = React.useState<WardStat | null>(null)

  React.useEffect(() => {
    govService.getWardStats().then((stats) => {
      setWardStats(stats)
      setSelected(stats[0] ?? null)
    })
  }, [])

  const bounds = React.useMemo(() => {
    if (!wardStats) return null
    const lats = wardStats.map((w) => w.lat)
    const lngs = wardStats.map((w) => w.lng)
    return { minLat: Math.min(...lats), maxLat: Math.max(...lats), minLng: Math.min(...lngs), maxLng: Math.max(...lngs) }
  }, [wardStats])

  function project(w: WardStat) {
    if (!bounds) return { x: 50, y: 50 }
    const x = PADDING + ((w.lng - bounds.minLng) / (bounds.maxLng - bounds.minLng || 1)) * (100 - PADDING * 2)
    const y = PADDING + (1 - (w.lat - bounds.minLat) / (bounds.maxLat - bounds.minLat || 1)) * (100 - PADDING * 2)
    return { x, y }
  }

  const sortedByRisk = wardStats ? [...wardStats].sort((a, b) => b.riskScore - a.riskScore) : []

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <PageHeader title="Complaint Heatmap" description="Geographic visualisation of civic issue density and risk concentration across wards." />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="relative aspect-[4/3] overflow-hidden p-0 lg:col-span-2">
          {!wardStats ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">Loading map data...</div>
          ) : (
            <svg viewBox="0 0 100 75" className="size-full" preserveAspectRatio="xMidYMid meet">
              <rect width="100" height="75" className="fill-muted/40" />
              {Array.from({ length: 10 }).map((_, i) => (
                <line key={`v${i}`} x1={i * 10} y1={0} x2={i * 10} y2={75} className="stroke-border" strokeWidth={0.15} />
              ))}
              {Array.from({ length: 8 }).map((_, i) => (
                <line key={`h${i}`} x1={0} y1={i * 10} x2={100} y2={i * 10} className="stroke-border" strokeWidth={0.15} />
              ))}
              {wardStats.map((w) => {
                const { x, y } = project(w)
                const yScaled = y * 0.75
                const radius = 2 + (w.totalIssues / 110) * 6
                const isSelected = selected?.ward === w.ward
                return (
                  <g key={w.ward} onClick={() => setSelected(w)} className="cursor-pointer">
                    <circle cx={x} cy={yScaled} r={radius + 3} fill={riskColor(w.riskScore)} opacity={0.15} />
                    <circle
                      cx={x}
                      cy={yScaled}
                      r={radius}
                      fill={riskColor(w.riskScore)}
                      opacity={0.75}
                      stroke={isSelected ? "var(--foreground)" : "transparent"}
                      strokeWidth={isSelected ? 0.6 : 0}
                    />
                  </g>
                )
              })}
            </svg>
          )}
          <div className="absolute bottom-3 left-3 flex items-center gap-3 rounded-lg border border-border bg-background/90 px-3 py-1.5 text-[11px] backdrop-blur">
            <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-success" /> Low risk</span>
            <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-warning" /> Medium</span>
            <span className="flex items-center gap-1"><span className="size-2 rounded-full bg-destructive" /> High risk</span>
          </div>
        </Card>

        <div className="space-y-4">
          {selected && (
            <Card className="space-y-3 p-5">
              <div className="flex items-center gap-1.5 text-sm font-semibold">
                <MapPin className="size-4" /> {selected.ward}
              </div>
              <p className="text-xs text-muted-foreground">{selected.district}</p>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Stat label="Total Issues" value={String(selected.totalIssues)} />
                <Stat label="Resolved" value={String(selected.resolvedIssues)} />
                <Stat label="Avg Resolution" value={`${selected.avgResolutionDays}d`} />
                <Stat label="Population" value={selected.population.toLocaleString("en-IN")} />
              </div>
              <StatusBadge
                label={`Risk Score: ${selected.riskScore}`}
                tone={selected.riskScore >= 75 ? "destructive" : selected.riskScore >= 55 ? "warning" : "success"}
              />
            </Card>
          )}

          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold">Highest Risk Wards</h3>
            <div className="space-y-2">
              {sortedByRisk.slice(0, 6).map((w) => (
                <button
                  key={w.ward}
                  onClick={() => setSelected(w)}
                  className={cn(
                    "flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-xs transition-colors hover:bg-muted",
                    selected?.ward === w.ward && "bg-muted",
                  )}
                >
                  <span className="truncate">{w.ward}</span>
                  <span className="flex shrink-0 items-center gap-1.5">
                    <span className="size-1.5 rounded-full" style={{ backgroundColor: riskColor(w.riskScore) }} />
                    {w.riskScore}
                  </span>
                </button>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  )
}
