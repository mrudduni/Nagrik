import Link from "next/link"
import { ArrowUpCircle, Clock, MapPin } from "lucide-react"
import { Card } from "@/components/ui/card"
import { StatusBadge } from "@/components/shared/status-badge"
import { statusMeta, severityMeta } from "@/services/issue-service"
import { formatDate } from "@/lib/format"
import type { CivicIssue } from "@/types"

export function IssueCard({ issue }: { issue: CivicIssue }) {
  return (
    <Link href={`/issues/${issue.id}`}>
      <Card className="group flex flex-col gap-3 p-5 transition-shadow hover:shadow-md">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-0.5">
            <p className="text-xs text-muted-foreground">{issue.referenceNumber}</p>
            <h3 className="text-sm font-semibold leading-snug tracking-tight group-hover:text-primary transition-colors">{issue.title}</h3>
          </div>
          <StatusBadge {...statusMeta(issue.status)} className="shrink-0" />
        </div>

        <p className="line-clamp-2 text-xs text-muted-foreground">{issue.description}</p>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <StatusBadge {...severityMeta(issue.severity)} withDot={false} />
          <span className="text-muted-foreground">{issue.category}</span>
        </div>

        <div className="flex items-center justify-between border-t border-border pt-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <MapPin className="size-3" /> {issue.ward}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="size-3" /> {formatDate(issue.reportedOn)}
          </span>
          <span className="flex items-center gap-1">
            <ArrowUpCircle className="size-3" /> {issue.upvotes}
          </span>
        </div>
      </Card>
    </Link>
  )
}
