"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowRight, FileStack, MapPinned, Sparkles } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { StatusBadge } from "@/components/shared/status-badge"
import { useApp } from "@/context/app-provider"
import { listApplications, computeStatusMeta } from "@/services/application-service"
import { getRecommendedSchemes } from "@/services/scheme-service"
import { listIssues, statusMeta } from "@/services/issue-service"
import type { Application, CivicIssue, Scheme } from "@/types"

export function HomeWidgets() {
  const { session, t } = useApp()
  const citizen = session?.citizen
  const [applications, setApplications] = React.useState<Application[] | null>(null)
  const [schemes, setSchemes] = React.useState<Scheme[] | null>(null)
  const [issues, setIssues] = React.useState<CivicIssue[] | null>(null)

  React.useEffect(() => {
    if (!citizen) return
    listApplications(citizen.id).then(setApplications)
    getRecommendedSchemes(citizen).then(setSchemes)
    listIssues({ citizenId: citizen.id }).then(setIssues)
  }, [citizen])

  const activeApp = applications?.find((a) => a.status !== "approved" && a.status !== "rejected" && a.status !== "disbursed") ?? applications?.[0]
  const topScheme = schemes?.[0]
  const recentIssue = issues?.[0]

  return (
    <div className="space-y-4">
      <WidgetCard
        icon={FileStack}
        title={t.nav.applications}
        href="/applications"
        loading={!applications}
      >
        {activeApp && (
          <div className="space-y-2">
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium leading-snug">{activeApp.schemeTitle}</p>
              <StatusBadge {...computeStatusMeta(activeApp.status)} className="shrink-0" />
            </div>
            <Progress value={activeApp.progress} className="h-1.5" />
            <p className="text-xs text-muted-foreground">{applications?.length} total applications</p>
          </div>
        )}
        {!activeApp && applications && <p className="text-sm text-muted-foreground">{t.widgets.no_applications}</p>}
      </WidgetCard>

      <WidgetCard icon={Sparkles} title={t.widgets.recommended_schemes} href="/services?tab=recommended" loading={!schemes}>
        {topScheme && (
          <div className="space-y-1.5">
            <p className="text-sm font-medium leading-snug">{topScheme.title}</p>
            <p className="line-clamp-2 text-xs text-muted-foreground">{topScheme.shortDescription}</p>
            <StatusBadge label={topScheme.benefitAmount ?? topScheme.benefitType} tone="info" withDot={false} />
          </div>
        )}
      </WidgetCard>

      <WidgetCard icon={MapPinned} title={t.nav.issues} href="/issues" loading={!issues}>
        {recentIssue ? (
          <div className="space-y-2">
            <p className="text-sm font-medium leading-snug">{recentIssue.title}</p>
            <StatusBadge {...statusMeta(recentIssue.status)} />
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">{t.widgets.no_issues}</p>
        )}
      </WidgetCard>
    </div>
  )
}

function WidgetCard({
  icon: Icon,
  title,
  href,
  loading,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>
  title: string
  href: string
  loading?: boolean
  children: React.ReactNode
}) {
  return (
    <Card className="p-4">
      <Link href={href} className="mb-3 flex items-center justify-between text-xs font-medium text-muted-foreground hover:text-foreground">
        <span className="flex items-center gap-1.5">
          <Icon className="size-3.5" /> {title}
        </span>
        <ArrowRight className="size-3.5" />
      </Link>
      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-4 w-4/5" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      ) : (
        children
      )}
    </Card>
  )
}
