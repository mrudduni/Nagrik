"use client"

import * as React from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Layers, ListChecks, MapPin, Search } from "lucide-react"
import { PageHeader } from "@/components/shared/page-header"
import { EmptyState } from "@/components/shared/empty-state"
import { ListSkeleton } from "@/components/shared/loading-state"
import { StatusBadge } from "@/components/shared/status-badge"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import * as govService from "@/services/gov-service"
import { statusMeta, severityMeta } from "@/services/issue-service"
import { MOCK_DEPARTMENTS } from "@/lib/mock/departments"
import { WARDS } from "@/lib/mock/wards"
import { formatDate } from "@/lib/format"
import type { CivicIssue, DuplicateCluster, IssueStatus } from "@/types"

const STATUS_OPTIONS: (IssueStatus | "All")[] = ["All", "submitted", "acknowledged", "assigned", "in-progress", "resolved", "closed", "reopened"]

function ComplaintsPageInner() {
  const searchParams = useSearchParams()
  const [tab, setTab] = React.useState(searchParams.get("tab") === "clusters" ? "clusters" : "all")
  const [query, setQuery] = React.useState("")
  const [status, setStatus] = React.useState<IssueStatus | "All">("All")
  const [department, setDepartment] = React.useState("All")
  const [ward, setWard] = React.useState("All")
  const [complaints, setComplaints] = React.useState<CivicIssue[] | null>(null)
  const [clusters, setClusters] = React.useState<DuplicateCluster[] | null>(null)
  const [issueMap, setIssueMap] = React.useState<Record<string, CivicIssue>>({})

  React.useEffect(() => {
    govService.listAllComplaints({ query, status, department, ward }).then(setComplaints)
  }, [query, status, department, ward])

  React.useEffect(() => {
    govService.getDuplicateClusters().then(setClusters)
    govService.listAllComplaints().then((all) => setIssueMap(Object.fromEntries(all.map((i) => [i.id, i]))))
  }, [])

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <PageHeader
        title="Complaint Management"
        description="AI-classified, prioritised complaints routed to the right department for fast resolution."
      />

      <Tabs value={tab} onValueChange={setTab} className="mb-5">
        <TabsList>
          <TabsTrigger value="all" className="gap-1.5"><ListChecks className="size-3.5" /> All Complaints</TabsTrigger>
          <TabsTrigger value="clusters" className="gap-1.5"><Layers className="size-3.5" /> Duplicate Clusters</TabsTrigger>
        </TabsList>
      </Tabs>

      {tab === "all" && (
        <>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search by title or reference number..." className="pl-9" value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Select value={status} onValueChange={(v) => setStatus(v as IssueStatus | "All")}>
                <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((s) => (
                    <SelectItem key={s} value={s}>{s === "All" ? "All Statuses" : statusMeta(s).label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={department} onValueChange={setDepartment}>
                <SelectTrigger className="w-48"><SelectValue placeholder="Department" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All Departments</SelectItem>
                  {MOCK_DEPARTMENTS.map((d) => (
                    <SelectItem key={d.id} value={d.name}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={ward} onValueChange={setWard}>
                <SelectTrigger className="w-44"><SelectValue placeholder="Ward" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="All">All Wards</SelectItem>
                  {WARDS.map((w) => (
                    <SelectItem key={w.ward} value={w.ward}>{w.ward}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {!complaints && <ListSkeleton count={6} />}
          {complaints && complaints.length === 0 && (
            <EmptyState icon={ListChecks} title="No complaints match your filters" description="Try adjusting the search or filter criteria." />
          )}
          {complaints && complaints.length > 0 && (
            <Card className="overflow-hidden p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Reference</TableHead>
                      <TableHead>Issue</TableHead>
                      <TableHead>Ward</TableHead>
                      <TableHead>Severity</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Reported</TableHead>
                      <TableHead>Assigned</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {complaints.map((c) => (
                      <TableRow key={c.id} className="cursor-pointer">
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5 font-mono text-xs text-muted-foreground">
                            {c.referenceNumber}
                          </Link>
                        </TableCell>
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5 max-w-64">
                            <p className="truncate text-sm font-medium">{c.title}</p>
                            <p className="text-xs text-muted-foreground">{c.category}</p>
                          </Link>
                        </TableCell>
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5 text-xs text-muted-foreground">{c.ward}</Link>
                        </TableCell>
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5"><StatusBadge {...severityMeta(c.severity)} withDot={false} /></Link>
                        </TableCell>
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5"><StatusBadge {...statusMeta(c.status)} /></Link>
                        </TableCell>
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5 text-xs text-muted-foreground">{formatDate(c.reportedOn)}</Link>
                        </TableCell>
                        <TableCell className="p-0">
                          <Link href={`/gov/complaints/${c.id}`} className="block p-2.5 text-xs text-muted-foreground">{c.assignedOfficer ?? "Unassigned"}</Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </Card>
          )}
        </>
      )}

      {tab === "clusters" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {!clusters && <ListSkeleton count={3} />}
          {clusters?.map((cluster) => (
            <Card key={cluster.id} className="space-y-3 p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold">{cluster.centerLabel}</p>
                  <p className="text-xs text-muted-foreground">{cluster.ward}</p>
                </div>
                <StatusBadge label={`${cluster.count} reports`} tone="warning" />
              </div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <MapPin className="size-3.5" /> Clustered within {cluster.radius} · {cluster.category}
              </div>
              <div className="space-y-1.5 border-t border-border pt-3">
                {cluster.issueIds.map((id) => {
                  const issue = issueMap[id]
                  if (!issue) return null
                  return (
                    <Link key={id} href={`/gov/complaints/${id}`} className="flex items-center justify-between text-xs hover:text-primary">
                      <span className="truncate">{issue.title}</span>
                      <StatusBadge {...statusMeta(issue.status)} />
                    </Link>
                  )
                })}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ComplaintsPage() {
  return (
    <React.Suspense fallback={null}>
      <ComplaintsPageInner />
    </React.Suspense>
  )
}
