"use client"

import * as React from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { GitCompareArrows, LayoutGrid } from "lucide-react"
import { PageHeader } from "@/components/shared/page-header"
import { CardGridSkeleton } from "@/components/shared/loading-state"
import { EmptyState } from "@/components/shared/empty-state"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SchemeFiltersBar } from "@/components/citizen/services/scheme-filters"
import { SchemeCard } from "@/components/citizen/services/scheme-card"
import { useApp } from "@/context/app-provider"
import { listSchemes, getRecommendedSchemes, type SchemeFilters } from "@/services/scheme-service"
import type { Scheme } from "@/types"

function ServicesPageInner() {
  const searchParams = useSearchParams()
  const { session } = useApp()
  const citizen = session?.citizen
  const [tab, setTab] = React.useState(searchParams.get("tab") === "recommended" ? "recommended" : "all")
  const [filters, setFilters] = React.useState<SchemeFilters>({ category: "All", level: "All", sortBy: "relevance" })
  const [schemes, setSchemes] = React.useState<Scheme[] | null>(null)
  const [matchScores, setMatchScores] = React.useState<Record<string, number>>({})

  function changeTab(next: string) {
    setSchemes(null)
    setTab(next)
  }

  function changeFilters(next: SchemeFilters) {
    setSchemes(null)
    setFilters(next)
  }

  // Clearing results to show the skeleton happens in the change handlers below,
  // not here, so this effect only writes state from its async results.
  React.useEffect(() => {
    let active = true
    if (tab === "recommended" && citizen) {
      getRecommendedSchemes(citizen).then((list) => {
        if (!active) return
        setSchemes(list)
        // The backend already embeds matchScore on each recommendation object
        const scores: Record<string, number> = {}
        list.forEach((s) => {
          const ms = (s as Scheme & { matchScore?: number }).matchScore
          if (ms != null) scores[s.id] = ms
        })
        if (active) setMatchScores(scores)
      })
    } else {
      listSchemes(filters).then((list) => active && setSchemes(list))
    }
    return () => {
      active = false
    }
  }, [tab, filters, citizen])

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <PageHeader
        title="Government Services"
        description="Discover, compare, and apply for central and state government schemes tailored to you."
        actions={
          <Button variant="outline" asChild className="gap-1.5">
            <Link href="/services/compare">
              <GitCompareArrows className="size-4" /> Compare Schemes
            </Link>
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={changeTab} className="mb-5">
        <TabsList>
          <TabsTrigger value="all">All Schemes</TabsTrigger>
          <TabsTrigger value="recommended">Recommended For You</TabsTrigger>
        </TabsList>
      </Tabs>

      {tab === "all" && (
        <div className="mb-6">
          <SchemeFiltersBar filters={filters} onChange={changeFilters} />
        </div>
      )}

      {!schemes && <CardGridSkeleton count={6} />}

      {schemes && schemes.length === 0 && (
        <EmptyState
          icon={LayoutGrid}
          title="No schemes match your filters"
          description="Try adjusting your search or filters to find relevant schemes."
        />
      )}

      {schemes && schemes.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {schemes.map((s) => (
            <SchemeCard key={s.id} scheme={s} matchScore={tab === "recommended" ? matchScores[s.id] : undefined} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function ServicesPage() {
  return (
    <React.Suspense fallback={null}>
      <ServicesPageInner />
    </React.Suspense>
  )
}
