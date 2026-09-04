"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import { AlertCircle, CheckCircle2, Clock, FileText, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { ErrorState } from "@/components/shared/error-state"
import { Timeline } from "@/components/shared/timeline"
import { getApplication, computeStatusMeta, uploadDocument } from "@/services/application-service"
import { formatDate } from "@/lib/format"
import type { Application } from "@/types"
import { cn } from "@/lib/utils"

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const [application, setApplication] = React.useState<Application | null | undefined>(undefined)
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const pendingDocRef = React.useRef<string | null>(null)

  const refresh = React.useCallback(() => {
    getApplication(params.id).then((a) => setApplication(a ?? null))
  }, [params.id])

  React.useEffect(() => {
    refresh()
  }, [refresh])

  function triggerUpload(docName: string) {
    pendingDocRef.current = docName
    fileInputRef.current?.click()
  }

  async function handleFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    const docName = pendingDocRef.current
    if (file && docName && application) {
      await uploadDocument(application.id, docName)
      toast.success(`${docName} uploaded successfully`)
      refresh()
    }
    e.target.value = ""
  }

  if (application === undefined) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-6 sm:px-6">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  if (application === null) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <ErrorState title="Application not found" onRetry={() => router.push("/applications")} />
      </div>
    )
  }

  const meta = computeStatusMeta(application.status)

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileChosen} />
      <PageHeader
        breadcrumbs={[{ label: "My Applications", href: "/applications" }, { label: application.referenceNumber }]}
        title={application.schemeTitle}
        description={`Reference: ${application.referenceNumber} · ${application.department}`}
        actions={<StatusBadge {...meta} className="text-sm" />}
      />

      {application.requiredActions.length > 0 && (
        <div className="mb-6 space-y-2">
          {application.requiredActions.map((ra) => (
            <Card key={ra.id} className="flex items-start gap-3 border-warning/30 bg-warning/5 p-4">
              <AlertCircle className="mt-0.5 size-4 shrink-0 text-warning-foreground" />
              <div className="flex-1">
                <p className="text-sm font-medium">{ra.label}</p>
                <p className="text-xs text-muted-foreground">{ra.description}</p>
                {ra.dueDate && <p className="mt-1 text-xs font-medium text-warning-foreground">Due by {formatDate(ra.dueDate)}</p>}
              </div>
            </Card>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold">Application Timeline</h2>
            <Timeline events={application.timeline} />
          </Card>

          <Card className="p-5">
            <h2 className="mb-4 text-sm font-semibold">Documents</h2>
            <div className="space-y-2">
              {application.documents.length === 0 && <p className="text-sm text-muted-foreground">No documents added yet.</p>}
              {application.documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
                  <div className="flex items-center gap-2.5">
                    <FileText className="size-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{doc.name}</p>
                      {doc.uploadedOn && <p className="text-xs text-muted-foreground">Uploaded {formatDate(doc.uploadedOn)}</p>}
                    </div>
                  </div>
                  {doc.status === "verified" && (
                    <span className="flex items-center gap-1 text-xs font-medium text-success">
                      <CheckCircle2 className="size-3.5" /> Verified
                    </span>
                  )}
                  {doc.status === "pending" && <StatusBadge label="Pending Review" tone="warning" />}
                  {doc.status === "rejected" && <StatusBadge label="Rejected" tone="destructive" />}
                  {doc.status === "requested" && (
                    <Button size="sm" variant="outline" className="gap-1.5" onClick={() => triggerUpload(doc.name)}>
                      <Upload className="size-3.5" /> Upload
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="space-y-4 p-5">
            <div>
              <p className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
                <span>Overall Progress</span> <span>{application.progress}%</span>
              </p>
              <Progress value={application.progress} className="h-1.5" />
            </div>
            <dl className="space-y-3 text-sm">
              <Row label="Submitted On" value={application.submittedOn ? formatDate(application.submittedOn) : "Not yet submitted"} />
              <Row label="Last Updated" value={formatDate(application.lastUpdated)} />
              {application.estimatedCompletion && <Row label="Est. Completion" value={formatDate(application.estimatedCompletion)} />}
              <Row label="Department" value={application.department} />
            </dl>
          </Card>

          {application.estimatedCompletion && (
            <Card className="flex items-start gap-2.5 p-4 text-xs text-muted-foreground">
              <Clock className="mt-0.5 size-3.5 shrink-0" />
              Estimated processing window based on similar applications in your department. Actual timelines may vary.
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn("text-right font-medium")}>{value}</dd>
    </div>
  )
}
