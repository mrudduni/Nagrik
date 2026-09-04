"use client"

import * as React from "react"
import Link from "next/link"
import { FileStack, LayoutGrid } from "lucide-react"
import { PageHeader } from "@/components/shared/page-header"
import { EmptyState } from "@/components/shared/empty-state"
import { CardGridSkeleton } from "@/components/shared/loading-state"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ApplicationCard } from "@/components/citizen/applications/application-card"
import { useApp } from "@/context/app-provider"
import { listApplications } from "@/services/application-service"
import type { Application, ApplicationStatus } from "@/types"

const FILTERS: { id: string; label: string; statuses?: ApplicationStatus[] }[] = [
  { id: "all", label: "All" },
  { id: "active", label: "Active", statuses: ["submitted", "under-review", "documents-pending", "additional-info-required"] },
  { id: "approved", label: "Approved", statuses: ["approved", "disbursed"] },
  { id: "draft", label: "Drafts", statuses: ["draft"] },
  { id: "rejected", label: "Rejected", statuses: ["rejected"] },
]

export default function ApplicationsPage() {
  const { session } = useApp()
  const citizen = session?.citizen
  const [applications, setApplications] = React.useState<Application[] | null>(null)
  const [filter, setFilter] = React.useState("all")

  React.useEffect(() => {
    if (citizen) listApplications(citizen.id).then(setApplications)
  }, [citizen])

  const activeFilter = FILTERS.find((f) => f.id === filter)
  const filtered = applications?.filter((a) => !activeFilter?.statuses || activeFilter.statuses.includes(a.status))

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <PageHeader
        title="My Applications"
        description="Track the progress of every government scheme application you've submitted through NAGRIK."
        actions={
          <Button asChild className="gap-1.5">
            <Link href="/services">
              <LayoutGrid className="size-4" /> Browse Schemes
            </Link>
          </Button>
        }
      />

      <Tabs value={filter} onValueChange={setFilter} className="mb-5">
        <TabsList>
          {FILTERS.map((f) => (
            <TabsTrigger key={f.id} value={f.id}>{f.label}</TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {!applications && <CardGridSkeleton count={4} />}

      {filtered && filtered.length === 0 && (
        <EmptyState
          icon={FileStack}
          title="No applications here yet"
          description="Applications you submit will appear here so you can track their progress in real time."
          action={
            <Button asChild size="sm">
              <Link href="/services">Explore Schemes</Link>
            </Button>
          }
        />
      )}

      {filtered && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((a) => (
            <ApplicationCard key={a.id} application={a} />
          ))}
        </div>
      )}
    </div>
  )
}
