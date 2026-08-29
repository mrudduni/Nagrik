"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import { AlertTriangle, ArrowUpCircle, Building2, Clock, MapPin, Users } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { ErrorState } from "@/components/shared/error-state"
import { Timeline } from "@/components/shared/timeline"
import { getIssue, statusMeta, severityMeta } from "@/services/issue-service"
import { formatDate, formatDateTime } from "@/lib/format"
import type { CivicIssue } from "@/types"
import { cn } from "@/lib/utils"

export default function IssueDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const [issue, setIssue] = React.useState<CivicIssue | null | undefined>(undefined)

  React.useEffect(() => {
    getIssue(params.id).then((i) => setIssue(i ?? null))
  }, [params.id])

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
        <ErrorState title="Issue not found" onRetry={() => router.push("/issues")} />
      </div>
    )
  }

  const slaPercent = Math.min(100, Math.round((issue.hoursElapsed / issue.slaHours) * 100))
  const isOverdue = issue.hoursElapsed > issue.slaHours && issue.status !== "resolved" && issue.status !== "closed"

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <PageHeader
        breadcrumbs={[{ label: "Civic Issues", href: "/issues" }, { label: issue.referenceNumber }]}
        title={issue.title}
        description={`Reference: ${issue.referenceNumber}`}
        actions={<StatusBadge {...statusMeta(issue.status)} className="text-sm" />}
      />

      {issue.isDuplicateOf && (
        <Card className="mb-6 flex items-start gap-3 border-info/30 bg-info/5 p-4">
          <Users className="mt-0.5 size-4 shrink-0 text-info" />
          <p className="text-sm text-foreground">
            This report was automatically linked to an existing cluster of similar reports in the same area and is being tracked together for faster resolution.
          </p>
        </Card>
      )}

      {isOverdue && (
        <Card className="mb-6 flex items-start gap-3 border-destructive/30 bg-destructive/5 p-4">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
          <p className="text-sm text-foreground">This issue has exceeded its expected SLA resolution window and has been flagged for priority follow-up.</p>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-5">
            <h2 className="mb-2 text-sm font-semibold">Description</h2>
            <p className="text-sm leading-relaxed text-muted-foreground">{issue.description}</p>
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold">Resolution Timeline</h2>
            <Timeline events={issue.timeline} />
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="space-y-4 p-5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Severity</span>
              <StatusBadge {...severityMeta(issue.severity)} />
            </div>
            <div>
              <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
                <span>SLA Timer</span>
                <span className={cn(isOverdue && "font-medium text-destructive")}>
                  {issue.hoursElapsed}h / {issue.slaHours}h
                </span>
              </div>
              <Progress value={slaPercent} className={cn("h-1.5", isOverdue && "[&>div]:bg-destructive")} />
            </div>
            <dl className="space-y-3 text-sm">
              <Row icon={Building2} label="Department" value={issue.department} />
              <Row icon={MapPin} label="Location" value={issue.location.address} />
              <Row icon={Clock} label="Reported" value={formatDateTime(issue.reportedOn)} />
              <Row icon={ArrowUpCircle} label="Community Upvotes" value={String(issue.upvotes)} />
            </dl>
            {issue.assignedOfficer && (
              <p className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">Assigned to <span className="font-medium text-foreground">{issue.assignedOfficer}</span></p>
            )}
          </Card>

          <Card className="p-5">
            <h3 className="mb-2 text-sm font-semibold">AI Classification</h3>
            <div className="space-y-2 text-xs text-muted-foreground">
              <p>Category: <span className="font-medium text-foreground">{issue.category}</span></p>
              {issue.aiConfidence && <p>Confidence: <span className="font-medium text-foreground">{Math.round(issue.aiConfidence * 100)}%</span></p>}
              <p>Last updated: {formatDate(issue.lastUpdated)}</p>
            </div>
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
