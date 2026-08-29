"use client"

import * as React from "react"
import Link from "next/link"
import { ArrowRight, GitCompareArrows, Star, X } from "lucide-react"
import { PageHeader } from "@/components/shared/page-header"
import { EmptyState } from "@/components/shared/empty-state"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { MOCK_SCHEMES } from "@/lib/mock/schemes"
import { formatCompactNumber, formatDate } from "@/lib/format"
import { cn } from "@/lib/utils"

const MAX_COMPARE = 3

export default function CompareSchemesPage() {
  const [selectedIds, setSelectedIds] = React.useState<string[]>(["sch-pmay-u", "sch-solar-rooftop"])

  const selectedSchemes = selectedIds.map((id) => MOCK_SCHEMES.find((s) => s.id === id)).filter((s): s is (typeof MOCK_SCHEMES)[number] => !!s)

  function updateSlot(index: number, id: string) {
    const next = [...selectedIds]
    next[index] = id
    setSelectedIds(next)
  }

  function removeSlot(index: number) {
    setSelectedIds(selectedIds.filter((_, i) => i !== index))
  }

  function addSlot() {
    const unused = MOCK_SCHEMES.find((s) => !selectedIds.includes(s.id))
    if (unused) setSelectedIds([...selectedIds, unused.id])
  }

  const rows: { label: string; render: (s: (typeof MOCK_SCHEMES)[number]) => React.ReactNode }[] = [
    { label: "Category", render: (s) => s.category },
    { label: "Level", render: (s) => s.level },
    { label: "Benefit", render: (s) => <span className="font-medium text-primary">{s.benefitAmount ?? s.benefitType}</span> },
    { label: "Benefit Type", render: (s) => s.benefitType },
    { label: "Department", render: (s) => s.department },
    { label: "Processing Time", render: (s) => `${s.processingTimeDays} days` },
    { label: "Documents Required", render: (s) => `${s.documentsRequired.length} documents` },
    { label: "Deadline", render: (s) => (s.deadline ? formatDate(s.deadline) : "Rolling / No deadline") },
    { label: "Rating", render: (s) => (
      <span className="flex items-center gap-1"><Star className="size-3.5 fill-current text-amber-500" /> {s.rating} / 5</span>
    ) },
    { label: "Beneficiaries", render: (s) => formatCompactNumber(s.beneficiariesCount) },
  ]

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <PageHeader
        breadcrumbs={[{ label: "Government Services", href: "/services" }, { label: "Compare" }]}
        title="Compare Schemes"
        description="Compare benefits, eligibility, and processing details side by side to decide which schemes to apply for."
      />

      {selectedSchemes.length === 0 ? (
        <EmptyState icon={GitCompareArrows} title="Add schemes to compare" description="Select at least two schemes below to see a side-by-side comparison." />
      ) : (
        <div className="overflow-x-auto">
          <div
            className="grid min-w-[640px] gap-4"
            style={{ gridTemplateColumns: `160px repeat(${Math.min(selectedSchemes.length + (selectedSchemes.length < MAX_COMPARE ? 1 : 0), MAX_COMPARE)}, 1fr)` }}
          >
            <div />
            {selectedIds.map((id, i) => (
              <Card key={i} className="relative space-y-2 p-4">
                {selectedIds.length > 1 && (
                  <button onClick={() => removeSlot(i)} className="absolute right-2 top-2 text-muted-foreground hover:text-foreground">
                    <X className="size-3.5" />
                  </button>
                )}
                <Select value={id} onValueChange={(v) => updateSlot(i, v)}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {MOCK_SCHEMES.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.title}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button asChild size="sm" variant="outline" className="w-full gap-1">
                  <Link href={`/services/${id}`}>
                    View <ArrowRight className="size-3" />
                  </Link>
                </Button>
              </Card>
            ))}
            {selectedSchemes.length < MAX_COMPARE && (
              <button
                onClick={addSlot}
                className="flex min-h-[100px] items-center justify-center rounded-xl border border-dashed border-border text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground"
              >
                + Add scheme
              </button>
            )}

            {rows.map((row) => (
              <React.Fragment key={row.label}>
                <div className="flex items-center py-3 text-xs font-medium text-muted-foreground">{row.label}</div>
                {selectedSchemes.map((s, i) => (
                  <div key={s.id + i} className={cn("flex items-center border-t border-border py-3 text-sm")}>
                    {row.render(s)}
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
