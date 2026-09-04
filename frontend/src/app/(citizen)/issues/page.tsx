"use client"

import * as React from "react"
import Link from "next/link"
import { MapPinned, Plus } from "lucide-react"
import { PageHeader } from "@/components/shared/page-header"
import { EmptyState } from "@/components/shared/empty-state"
import { CardGridSkeleton } from "@/components/shared/loading-state"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { IssueCard } from "@/components/citizen/issues/issue-card"
import { useApp } from "@/context/app-provider"
import { listIssues } from "@/services/issue-service"
import type { CivicIssue } from "@/types"

const FILTERS = [
  { id: "all", label: "All" },
  { id: "open", label: "Open" },
  { id: "resolved", label: "Resolved" },
]

export default function IssuesPage() {
  const { session } = useApp()
  const citizen = session?.citizen
  const [issues, setIssues] = React.useState<CivicIssue[] | null>(null)
  const [nearby, setNearby] = React.useState<CivicIssue[] | null>(null)
  const [filter, setFilter] = React.useState("all")
  const [view, setView] = React.useState<"mine" | "nearby">("mine")

  React.useEffect(() => {
    if (citizen) {
      listIssues({ citizenId: citizen.id }).then(setIssues)
      listIssues({ ward: citizen.address.ward }).then((all) => setNearby(all.filter((i) => i.reportedBy !== citizen.id)))
    }
  }, [citizen])

  const source = view === "mine" ? issues : nearby
  const filtered = source?.filter((i) => {
    if (filter === "all") return true
    if (filter === "resolved") return i.status === "resolved" || i.status === "closed"
    return i.status !== "resolved" && i.status !== "closed"
  })

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <PageHeader
        title="Civic Issues"
        description="Report problems in your neighbourhood and track resolution - from pothole to power cut."
        actions={
          <Button asChild className="gap-1.5">
            <Link href="/issues/new">
              <Plus className="size-4" /> Report an Issue
            </Link>
          </Button>
        }
      />

      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Tabs value={view} onValueChange={(v) => setView(v as "mine" | "nearby")}>
          <TabsList>
            <TabsTrigger value="mine">My Complaints</TabsTrigger>
            <TabsTrigger value="nearby">Nearby Reports</TabsTrigger>
          </TabsList>
        </Tabs>
        <Tabs value={filter} onValueChange={setFilter}>
          <TabsList>
            {FILTERS.map((f) => (
              <TabsTrigger key={f.id} value={f.id}>{f.label}</TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {!source && <CardGridSkeleton count={4} />}

      {filtered && filtered.length === 0 && (
        <EmptyState
          icon={MapPinned}
          title={view === "mine" ? "No complaints reported yet" : "No nearby reports found"}
          description={view === "mine" ? "Report a civic issue and track it right here." : "There are no community reports in your ward matching this filter."}
          action={
            view === "mine" ? (
              <Button asChild size="sm">
                <Link href="/issues/new">Report an Issue</Link>
              </Button>
            ) : undefined
          }
        />
      )}

      {filtered && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((i) => (
            <IssueCard key={i.id} issue={i} />
          ))}
        </div>
      )}
    </div>
  )
}
