"use client"

import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { SchemeCategory } from "@/types"
import type { SchemeFilters } from "@/services/scheme-service"

const CATEGORIES: (SchemeCategory | "All")[] = [
  "All",
  "Agriculture",
  "Education",
  "Health",
  "Housing",
  "Employment",
  "Social Welfare",
  "Women & Child",
  "Pension",
  "Business & MSME",
  "Energy",
]

export function SchemeFiltersBar({
  filters,
  onChange,
}: {
  filters: SchemeFilters
  onChange: (next: SchemeFilters) => void
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search schemes by name, benefit, or department..."
          className="pl-9"
          value={filters.query ?? ""}
          onChange={(e) => onChange({ ...filters, query: e.target.value })}
        />
      </div>
      <div className="flex gap-2">
        <Select value={filters.category ?? "All"} onValueChange={(v) => onChange({ ...filters, category: v as SchemeCategory | "All" })}>
          <SelectTrigger className="w-full sm:w-44"><SelectValue placeholder="Category" /></SelectTrigger>
          <SelectContent>
            {CATEGORIES.map((c) => (
              <SelectItem key={c} value={c}>{c === "All" ? "All Categories" : c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filters.level ?? "All"} onValueChange={(v) => onChange({ ...filters, level: v as SchemeFilters["level"] })}>
          <SelectTrigger className="w-full sm:w-36"><SelectValue placeholder="Level" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="All">All Levels</SelectItem>
            <SelectItem value="Central">Central</SelectItem>
            <SelectItem value="State">State</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.sortBy ?? "relevance"} onValueChange={(v) => onChange({ ...filters, sortBy: v as SchemeFilters["sortBy"] })}>
          <SelectTrigger className="w-full sm:w-40"><SelectValue placeholder="Sort" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="relevance">Relevance</SelectItem>
            <SelectItem value="newest">Newest</SelectItem>
            <SelectItem value="beneficiaries">Most Popular</SelectItem>
            <SelectItem value="rating">Top Rated</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
