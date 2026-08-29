"use client"

import * as React from "react"
import Link from "next/link"
import { FileStack, History, MapPinned } from "lucide-react"
import { Card } from "@/components/ui/card"
import { ListSkeleton } from "@/components/shared/loading-state"
import { EmptyState } from "@/components/shared/empty-state"
import { StatusBadge } from "@/components/shared/status-badge"
import { computeStatusMeta } from "@/services/application-service"
import { statusMeta } from "@/services/issue-service"
import { listApplications } from "@/services/application-service"
import { listIssues } from "@/services/issue-service"
import { useApp } from "@/context/app-provider"
import { formatDate } from "@/lib/format"
import type { Application, CivicIssue } from "@/types"

type HistoryEntry =
  | { kind: "application"; item: Application; date: string }
  | { kind: "issue"; item: CivicIssue; date: string }

export function ServiceHistory() {
  const { session } = useApp()
  const citizen = session?.citizen
  const [entries, setEntries] = React.useState<HistoryEntry[] | null>(null)

  React.useEffect(() => {
    if (!citizen) return
    Promise.all([listApplications(citizen.id), listIssues({ citizenId: citizen.id })]).then(([apps, issues]) => {
      const combined: HistoryEntry[] = [
        ...apps.map((a): HistoryEntry => ({ kind: "application", item: a, date: a.submittedOn ?? a.lastUpdated })),
        ...issues.map((i): HistoryEntry => ({ kind: "issue", item: i, date: i.reportedOn })),
      ].sort((a, b) => (a.date < b.date ? 1 : -1))
      setEntries(combined)
    })
  }, [citizen])

  if (!entries) return <ListSkeleton count={5} />

  if (entries.length === 0) {
    return <EmptyState icon={History} title="No activity yet" description="Your applications and civic reports will show up here." />
  }

  return (
    <div className="space-y-3">
      {entries.map((entry, i) => (
        <Link key={i} href={entry.kind === "application" ? `/applications/${entry.item.id}` : `/issues/${entry.item.id}`}>
          <Card className="flex items-center gap-4 p-4 transition-colors hover:bg-muted/40">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-muted">
              {entry.kind === "application" ? <FileStack className="size-4 text-muted-foreground" /> : <MapPinned className="size-4 text-muted-foreground" />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{entry.kind === "application" ? entry.item.schemeTitle : entry.item.title}</p>
              <p className="text-xs text-muted-foreground">
                {entry.kind === "application" ? "Scheme Application" : "Civic Issue Report"} · {formatDate(entry.date)}
              </p>
            </div>
            <StatusBadge {...(entry.kind === "application" ? computeStatusMeta(entry.item.status) : statusMeta(entry.item.status))} className="shrink-0" />
          </Card>
        </Link>
      ))}
    </div>
  )
}
