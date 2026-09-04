"use client"

import * as React from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import {
  ArrowRight,
  BadgeCheck,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  ShieldCheck,
  Star,
  Users,
  XCircle,
  HelpCircle,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { ErrorState } from "@/components/shared/error-state"
import { Skeleton } from "@/components/ui/skeleton"
import { useApp } from "@/context/app-provider"
import { getScheme, checkEligibility, trackSchemeView } from "@/services/scheme-service"
import { formatCompactNumber, formatDate } from "@/lib/format"
import type { EligibilityResult, Scheme } from "@/types"
import { cn } from "@/lib/utils"

export default function SchemeDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const { session } = useApp()
  const [scheme, setScheme] = React.useState<Scheme | null | undefined>(undefined)
  const [eligibility, setEligibility] = React.useState<EligibilityResult | null>(null)

  React.useEffect(() => {
    getScheme(params.id).then((s) => setScheme(s ?? null))
  }, [params.id])

  React.useEffect(() => {
    if (scheme && session?.citizen) {
      checkEligibility(scheme.id, session.citizen).then(setEligibility)
      // Track this view in the knowledge graph (feeds recommendations)
      trackSchemeView(scheme.id, session.citizen.id)
    }
  }, [scheme, session])

  if (scheme === undefined) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 px-4 py-6 sm:px-6">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (scheme === null) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <ErrorState title="Scheme not found" description="This scheme may have been removed or the link is incorrect." onRetry={() => router.push("/services")} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <PageHeader
        breadcrumbs={[{ label: "Government Services", href: "/services" }, { label: scheme.title }]}
        title={scheme.title}
        description={scheme.shortDescription}
        actions={
          <Button asChild size="lg" className="gap-1.5">
            <Link href={`/apply/${scheme.id}`}>
              Start Application <ArrowRight className="size-4" />
            </Link>
          </Button>
        }
      />

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Badge variant="outline">{scheme.category}</Badge>
        <Badge variant="outline">{scheme.level}</Badge>
        <Badge variant="outline">{scheme.benefitType}</Badge>
        {scheme.deadline && (
          <Badge className="gap-1 bg-warning/20 text-warning-foreground border-warning/30">
            <Clock className="size-3" /> Deadline {formatDate(scheme.deadline)}
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card className="p-5">
            <h2 className="mb-2 text-sm font-semibold">About this scheme</h2>
            <p className="text-sm leading-relaxed text-muted-foreground">{scheme.description}</p>
          </Card>

          {eligibility && (
            <Card className="p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold">Your Eligibility</h2>
                <StatusBadge
                  label={
                    eligibility.status === "eligible"
                      ? "You're Eligible"
                      : eligibility.status === "partial"
                        ? "Partially Eligible"
                        : "Not Eligible"
                  }
                  tone={eligibility.status === "eligible" ? "success" : eligibility.status === "partial" ? "warning" : "destructive"}
                />
              </div>
              <div className="space-y-2.5">
                {eligibility.reasons.map((r, i) => (
                  <div key={i} className="flex items-start gap-2.5 rounded-lg border border-border bg-muted/30 p-3">
                    {r.met ? (
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" />
                    ) : (
                      <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" />
                    )}
                    <div className="space-y-0.5">
                      <p className="text-xs font-medium">{r.rule}</p>
                      <p className="text-xs text-muted-foreground">{r.explanation}</p>
                    </div>
                  </div>
                ))}
                {eligibility.reasons.length === 0 && (
                  <div className="flex items-start gap-2.5 rounded-lg border border-border bg-muted/30 p-3">
                    <HelpCircle className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    <p className="text-xs text-muted-foreground">General criteria apply. Full verification happens during application.</p>
                  </div>
                )}
              </div>
            </Card>
          )}

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold">General Eligibility Criteria</h2>
            <ul className="space-y-2">
              {scheme.eligibilitySummary.map((e, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-primary" /> {e}
                </li>
              ))}
            </ul>
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold">Documents Required</h2>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {scheme.documentsRequired.map((d, i) => (
                <div key={i} className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm">
                  <FileText className="size-3.5 shrink-0 text-muted-foreground" /> {d}
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold">Application Process</h2>
            <ol className="space-y-3">
              {scheme.applicationSteps.map((step, i) => (
                <li key={i} className="flex gap-3 text-sm">
                  <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
                    {i + 1}
                  </span>
                  <span className="text-muted-foreground">{step}</span>
                </li>
              ))}
            </ol>
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="space-y-4 p-5">
            <div>
              <p className="text-xs text-muted-foreground">Benefit</p>
              <p className="text-lg font-semibold text-primary">{scheme.benefitAmount ?? scheme.benefitType}</p>
            </div>
            <Separator />
            <div className="space-y-3 text-sm">
              <InfoRow icon={Building2} label="Department" value={scheme.department} />
              <InfoRow icon={ShieldCheck} label="Ministry" value={scheme.ministry} />
              <InfoRow icon={Clock} label="Processing Time" value={`${scheme.processingTimeDays} days (avg)`} />
              <InfoRow icon={Calendar} label="Launched" value={formatDate(scheme.launchedOn)} />
              <InfoRow icon={Users} label="Beneficiaries" value={formatCompactNumber(scheme.beneficiariesCount)} />
              <InfoRow icon={Star} label="Citizen Rating" value={`${scheme.rating} / 5`} />
            </div>
            <Separator />
            <Button asChild className="w-full gap-1.5">
              <Link href={`/apply/${scheme.id}`}>
                Start Application <ArrowRight className="size-4" />
              </Link>
            </Button>
          </Card>

          <Card className="space-y-2 p-5">
            <div className="flex items-center gap-1.5 text-xs font-medium text-success">
              <BadgeCheck className="size-3.5" /> Verified Official Source
            </div>
            <p className="text-xs text-muted-foreground">Last verified on {formatDate(scheme.lastVerified)}</p>
            <a
              href={scheme.officialSourceUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
            >
              {scheme.officialSourceName} <ExternalLink className="size-3" />
            </a>
          </Card>
        </div>
      </div>
    </div>
  )
}

function InfoRow({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className={cn("flex items-center gap-1.5 text-muted-foreground")}>
        <Icon className="size-3.5" /> {label}
      </span>
      <span className="text-right font-medium">{value}</span>
    </div>
  )
}
