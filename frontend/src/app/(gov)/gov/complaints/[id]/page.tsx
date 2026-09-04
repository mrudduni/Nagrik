"use client"

import * as React from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import {
  AlertCircle,
  Bot,
  Building2,
  CheckCircle2,
  Clock,
  Layers,
  MapPin,
  Send,
  ShieldAlert,
  Sparkles,
  User2,
  UserCheck,
  Users2,
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { ErrorState } from "@/components/shared/error-state"
import { Timeline } from "@/components/shared/timeline"
import { getIssue, statusMeta, severityMeta } from "@/services/issue-service"
import {
  updateComplaintStatus,
  getDuplicateClusters,
  acknowledgeComplaint,
  assignOfficer,
  resolveComplaint,
} from "@/services/gov-service"
import { formatDate, formatDateTime } from "@/lib/format"
import type { CivicIssue, DuplicateCluster, IssueStatus } from "@/types"
import { cn } from "@/lib/utils"

const STATUS_FLOW: IssueStatus[] = [
  "submitted",
  "acknowledged",
  "assigned",
  "in-progress",
  "resolved",
  "closed",
  "reopened",
]

export default function GovComplaintDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const [issue, setIssue] = React.useState<CivicIssue | null | undefined>(undefined)
  const [cluster, setCluster] = React.useState<DuplicateCluster | null>(null)
  const [isUpdating, setIsUpdating] = React.useState(false)

  // Action Panel State
  const [officerName, setOfficerName] = React.useState("")
  const [resolutionNotes, setResolutionNotes] = React.useState("")
  const [isSubmittingAction, setIsSubmittingAction] = React.useState(false)

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

  async function handleAcknowledge() {
    if (!issue) return
    setIsSubmittingAction(true)
    const ok = await acknowledgeComplaint(issue.id)
    if (!ok) {
      await updateComplaintStatus(issue.id, "acknowledged")
    }
    setIsSubmittingAction(false)
    toast.success("Complaint acknowledged by department")
    refresh()
  }

  async function handleAssignOfficer(e: React.FormEvent) {
    e.preventDefault()
    if (!issue || !officerName.trim()) return
    setIsSubmittingAction(true)
    const ok = await assignOfficer(issue.id, officerName.trim())
    if (!ok) {
      await updateComplaintStatus(issue.id, "assigned")
      issue.assignedOfficer = officerName.trim()
    }
    setIsSubmittingAction(false)
    toast.success(`Assigned to ${officerName.trim()}`)
    setOfficerName("")
    refresh()
  }

  async function handleResolve(e: React.FormEvent) {
    e.preventDefault()
    if (!issue || !resolutionNotes.trim()) return
    setIsSubmittingAction(true)
    const ok = await resolveComplaint(issue.id, resolutionNotes.trim())
    if (!ok) {
      await updateComplaintStatus(issue.id, "resolved")
    }
    setIsSubmittingAction(false)
    toast.success("Resolution claimed. Citizen verification requested.")
    setResolutionNotes("")
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
          <div className="flex items-center gap-2">
            <Select value={issue.status} onValueChange={(v) => handleStatusChange(v as IssueStatus)} disabled={isUpdating}>
              <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
              <SelectContent>
                {STATUS_FLOW.map((s) => (
                  <SelectItem key={s} value={s}>{statusMeta(s).label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
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
        <Card className="mb-6 flex items-center gap-3 border-destructive/30 bg-destructive/5 p-4">
          <ShieldAlert className="size-5 shrink-0 text-destructive" />
          <div>
            <p className="text-sm font-medium text-destructive">SLA Breached — Escalation Flag Active</p>
            <p className="text-xs text-muted-foreground">Target resolution window was {issue.slaHours} hours. Notification dispatched to supervisory authority.</p>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Main Description */}
          <Card className="p-5">
            <h2 className="mb-2 text-sm font-semibold">Description</h2>
            <p className="text-sm leading-relaxed text-muted-foreground">{issue.description}</p>
          </Card>

          {/* AI Intelligence & Routing */}
          <Card className="p-5">
            <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold">
              <Bot className="size-4 text-primary" /> AI Classification & Routing
            </h2>
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

          {/* Official Action Panel */}
          <Card className="border-primary/20 bg-primary/[0.02] p-5">
            <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold">
              <UserCheck className="size-4 text-primary" /> Government Action Panel
            </h2>

            {issue.status === "submitted" && (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">
                  This complaint is pending initial departmental acknowledgement.
                </p>
                <Button size="sm" onClick={handleAcknowledge} disabled={isSubmittingAction}>
                  <CheckCircle2 className="mr-1.5 size-4" /> Acknowledge Complaint
                </Button>
              </div>
            )}

            {(issue.status === "acknowledged" || issue.status === "submitted" || !issue.assignedOfficer || issue.assignedOfficer === "Unassigned") && (
              <form onSubmit={handleAssignOfficer} className="mt-3 space-y-2 border-t border-border pt-3">
                <label className="text-xs font-medium text-foreground">Assign Field Engineer or Officer</label>
                <div className="flex gap-2">
                  <Input
                    placeholder="e.g. Eng. Rajesh Kumar (Roads Div)"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    className="h-9 text-xs"
                    disabled={isSubmittingAction}
                  />
                  <Button type="submit" size="sm" disabled={isSubmittingAction || !officerName.trim()}>
                    Assign
                  </Button>
                </div>
              </form>
            )}

            {(issue.status === "in-progress" || issue.status === "assigned") && (
              <form onSubmit={handleResolve} className="mt-4 space-y-2 border-t border-border pt-3">
                <label className="text-xs font-medium text-foreground">Claim Resolution & Notify Citizen</label>
                <Textarea
                  placeholder="Detail the work carried out (e.g., Road resurfaced, drain unblocked)..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="min-h-[70px] text-xs"
                  disabled={isSubmittingAction}
                />
                <Button type="submit" size="sm" variant="default" className="bg-success text-success-foreground hover:bg-success/90" disabled={isSubmittingAction || !resolutionNotes.trim()}>
                  <Send className="mr-1.5 size-3.5" /> Submit Resolution Claim
                </Button>
              </form>
            )}

            {issue.status === "resolved" && (
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="size-4 text-warning" />
                <span>Resolution claimed. Awaiting citizen verification to close ticket.</span>
              </div>
            )}

            {issue.status === "closed" && (
              <div className="mt-3 flex items-center gap-2 text-xs text-success">
                <CheckCircle2 className="size-4" />
                <span>Ticket verified by citizen and closed successfully.</span>
              </div>
            )}
          </Card>

          {/* Timeline */}
          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold">Resolution Timeline</h2>
            <Timeline events={issue.timeline} />
          </Card>
        </div>

        {/* Right Sidebar */}
        <div className="space-y-4">
          <Card className="space-y-4 p-5">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
                <span>SLA Countdown</span>
                <span className={cn(isOverdue && "font-medium text-destructive")}>
                  {issue.hoursElapsed}h / {issue.slaHours}h
                </span>
              </div>
              <Progress value={slaPercent} className={cn("h-1.5", isOverdue && "[&>div]:bg-destructive")} />
            </div>
            <dl className="space-y-3 text-sm">
              <Row icon={Building2} label="Department" value={issue.department} />
              <Row icon={MapPin} label="Ward" value={issue.ward} />
              <Row icon={Clock} label="Reported" value={formatDateTime(issue.reportedOn)} />
              <Row icon={User2} label="Assigned Officer" value={issue.assignedOfficer ?? "Unassigned"} />
              {issue.duplicateCount && issue.duplicateCount > 0 && (
                <Row icon={Layers} label="Cluster Size" value={`${issue.duplicateCount} linked reports`} />
              )}
            </dl>
          </Card>

          <Card className="space-y-2 p-4">
            <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              <Sparkles className="size-3.5 text-primary" /> Recommended Action
            </p>
            <p className="text-xs leading-relaxed text-muted-foreground">
              {issue.severity === "critical"
                ? "Dispatch emergency field crew within 2 hours to prevent physical hazards and public escalation."
                : issue.severity === "high"
                  ? "Schedule site inspection within 24 hours and post daily progress updates on the citizen portal."
                  : "Standard queue processing — resolve within departmental SLA window."}
            </p>
            <p className="text-[11px] text-muted-foreground">Last updated {formatDate(issue.lastUpdated)}</p>
          </Card>
        </div>
      </div>
    </div>
  )
}

function Row({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <Icon className="size-3.5" /> {label}
      </span>
      <span className="max-w-[60%] text-right font-medium">{value}</span>
    </div>
  )
}
