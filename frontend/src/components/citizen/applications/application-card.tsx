import Link from "next/link"
import { ArrowRight, AlertCircle } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { StatusBadge } from "@/components/shared/status-badge"
import { computeStatusMeta } from "@/services/application-service"
import { formatDate } from "@/lib/format"
import type { Application } from "@/types"

export function ApplicationCard({ application }: { application: Application }) {
  const meta = computeStatusMeta(application.status)
  return (
    <Link href={`/applications/${application.id}`}>
      <Card className="group flex flex-col gap-3 p-5 transition-shadow hover:shadow-md">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-0.5">
            <p className="text-xs text-muted-foreground">{application.referenceNumber}</p>
            <h3 className="text-sm font-semibold leading-snug tracking-tight group-hover:text-primary transition-colors">
              {application.schemeTitle}
            </h3>
          </div>
          <StatusBadge {...meta} className="shrink-0" />
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{application.progress}%</span>
          </div>
          <Progress value={application.progress} className="h-1.5" />
        </div>

        <div className="flex items-center justify-between pt-1 text-xs text-muted-foreground">
          <span>{application.department}</span>
          <span>Updated {formatDate(application.lastUpdated)}</span>
        </div>

        {application.requiredActions.length > 0 && (
          <div className="flex items-center gap-1.5 rounded-lg bg-warning/10 px-2.5 py-1.5 text-xs font-medium text-warning-foreground">
            <AlertCircle className="size-3.5 shrink-0" /> {application.requiredActions[0].label}
          </div>
        )}

        <div className="flex items-center justify-end gap-1 text-xs font-medium text-primary opacity-0 transition-opacity group-hover:opacity-100">
          View details <ArrowRight className="size-3" />
        </div>
      </Card>
    </Link>
  )
}
