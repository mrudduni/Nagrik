"use client"

import * as React from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import { Bot, Building2, Clock, Layers, MapPin, Sparkles, User2, Users2 } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { ErrorState } from "@/components/shared/error-state"
import { Timeline } from "@/components/shared/timeline"
import { getIssue, statusMeta, severityMeta } from "@/services/issue-service"
import { updateComplaintStatus, getDuplicateClusters } from "@/services/gov-service"
import { formatDate, formatDateTime } from "@/lib/format"
import type { CivicIssue, DuplicateCluster, IssueStatus } from "@/types"
import { cn } from "@/lib/utils"

const STATUS_FLOW: IssueStatus[] = ["submitted", "acknowledged", "assigned", "in-progress", "resolved", "closed"]

export default function GovComplaintDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const [issue, setIssue] = React.useState<CivicIssue | null | undefined>(undefined)
  const [cluster, setCluster] = React.useState<DuplicateCluster | null>(null)
  const [isUpdating, setIsUpdating] = React.useState(false)

  const refresh = React.useCallback(() => {
    getIssue(params.id).then((i) => setIssue(i ?? null))
  }, [params.id])

  React.useEffect(() => {
    refresh()
  }, [refresh])

  React.useEffect(() => {
    getDuplicateClusters().then((clusters) => {
      const match = clusters.find((c) => c.issueIds.includes(params.id))
      setCluster(match ?? null)
    })
  }, [params.id])

  async function handleStatusChange(status: IssueStatus) {
    if (!issue) return
    setIsUpdating(true)
    await updateComplaintStatus(issue.id, status)
    setIsUpdating(false)
    toast.success(`Status updated to ${statusMeta(status).label}`)
    refresh()
  }

  if (issue === undefined) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-6 sm:px-6">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (issue === null) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <ErrorState title="Complaint not found" onRetry={() => router.push("/gov/complaints")} />
      </div>
    )
  }

  const slaPercent = Math.min(100, Math.round((issue.hoursElapsed / issue.slaHours) * 100))
  const isOverdue = issue.hoursElapsed > issue.slaHours && issue.status !== "resolved" && issue.status !== "closed"

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <PageHeader
        breadcrumbs={[{ label: "Complaints", href: "/gov/complaints" }, { label: issue.referenceNumber }]}
        title={issue.title}
        description={`${issue.referenceNumber} · Reported by citizen ${issue.reportedBy}`}
        actions={
          <Select value={issue.status} onValueChange={(v) => handleStatusChange(v as IssueStatus)} disabled={isUpdating}>
            <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
            <SelectContent>
              {STATUS_FLOW.map((s) => (
                <SelectItem key={s} value={s}>{statusMeta(s).label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      {cluster && (
        <Card className="mb-6 flex items-start gap-3 border-info/30 bg-info/5 p-4">
          <Users2 className="mt-0.5 size-4 shrink-0 text-info" />
          <div className="flex-1">
            <p className="text-sm font-medium">Part of a duplicate cluster</p>
            <p className="text-xs text-muted-foreground">
              {cluster.count} similar reports near {cluster.centerLabel} ({cluster.radius} radius) are being tracked together.
            </p>
          </div>
          <Link href="/gov/complaints?tab=clusters" className="shrink-0 text-xs font-medium text-primary hover:underline">
            View cluster
          </Link>
        </Card>
      )}

      {isOverdue && (
        <Card className="mb-6 border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm font-medium text-destructive">SLA breached - priority follow-up required.</p>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-5">
            <h2 className="mb-2 text-sm font-semibold">Description</h2>
            <p className="text-sm leading-relaxed text-muted-foreground">{issue.description}</p>
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold"><Bot className="size-4" /> AI Classification & Routing</h2>
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-xs text-muted-foreground">Category</p>
                <p className="font-medium">{issue.aiSuggestedCategory ?? issue.category}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Confidence</p>
                <p className="font-medium">{issue.aiConfidence ? `${Math.round(issue.aiConfidence * 100)}%` : "-"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Severity</p>
                <StatusBadge {...severityMeta(issue.severity)} withDot={false} />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Routed To</p>
                <p className="font-medium">{issue.department}</p>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold">Resolution Timeline</h2>
            <Timeline events={issue.timeline} />
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="space-y-4 p-5">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
                <span>SLA Timer</span>
                <span className={cn(isOverdue && "font-medium text-destructive")}>{issue.hoursElapsed}h / {issue.slaHours}h</span>
              </div>
              <Progress value={slaPercent} className={cn("h-1.5", isOverdue && "[&>div]:bg-destructive")} />
            </div>
            <dl className="space-y-3 text-sm">
              <Row icon={Building2} label="Department" value={issue.department} />
              <Row icon={MapPin} label="Ward" value={issue.ward} />
              <Row icon={Clock} label="Reported" value={formatDateTime(issue.reportedOn)} />
              <Row icon={User2} label="Assigned Officer" value={issue.assignedOfficer ?? "Unassigned"} />
              {issue.duplicateCount && <Row icon={Layers} label="Linked Reports" value={String(issue.duplicateCount)} />}
            </dl>
          </Card>

          <Card className="space-y-2 p-4">
            <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"><Sparkles className="size-3.5" /> Recommended Action</p>
            <p className="text-xs text-muted-foreground">
              {issue.severity === "critical"
                ? "Dispatch emergency field crew within 2 hours to prevent escalation."
                : issue.severity === "high"
                  ? "Schedule field inspection within 24 hours and notify ward councillor."
                  : "Standard queue processing - resolve within department SLA window."}
            </p>
            <p className="text-[11px] text-muted-foreground">Last updated {formatDate(issue.lastUpdated)}</p>
          </Card>
        </div>
      </div>
    </div>
  )
}

function Row({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <Icon className="size-3.5" /> {label}
      </span>
      <span className="max-w-[60%] text-right font-medium">{value}</span>
    </div>
  )
}
