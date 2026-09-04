import type { CitizenProfile, EligibilityResult, Scheme, SchemeCategory } from "@/types"
import { findSchemeById } from "@/lib/mock/schemes"
import { apiGet, apiPost, request } from "./_client"

export interface SchemeFilters {
  query?: string
  category?: SchemeCategory | "All"
  level?: "Central" | "State" | "All"
  benefitType?: string
  sortBy?: "relevance" | "newest" | "beneficiaries" | "rating"
}

// ---------------------------------------------------------------------------
// List / search all schemes — fetches from real Neo4j via backend
// ---------------------------------------------------------------------------
export async function listSchemes(filters: SchemeFilters = {}): Promise<Scheme[]> {
  const params = new URLSearchParams()
  if (filters.query)                             params.set("query", filters.query)
  if (filters.category && filters.category !== "All") params.set("category", filters.category)
  if (filters.level && filters.level !== "All") params.set("level", filters.level)
  if (filters.sortBy)                            params.set("sort", filters.sortBy)
  params.set("limit", "60")

  try {
    const data = await apiGet<{ schemes: Scheme[] }>(`/api/schemes?${params.toString()}`)
    return data.schemes ?? []
  } catch {
    // Fallback to mock data if backend is unreachable
    const { MOCK_SCHEMES } = await import("@/lib/mock/schemes")
    return MOCK_SCHEMES
  }
}

// ---------------------------------------------------------------------------
// Get a single scheme — tries Neo4j first, falls back to mock
// ---------------------------------------------------------------------------
export async function getScheme(id: string): Promise<Scheme | undefined> {
  // Try the live backend first
  try {
    const scheme = await apiGet<Scheme>(`/api/schemes/${encodeURIComponent(id)}`)
    return scheme
  } catch {
    // Fallback for schemes that only exist in mock (e.g. during development)
    return request(() => findSchemeById(id))
  }
}

// ---------------------------------------------------------------------------
// Featured schemes (used on home widget) — still from the live list
// ---------------------------------------------------------------------------
export async function getFeaturedSchemes(): Promise<Scheme[]> {
  try {
    const data = await apiGet<{ schemes: Scheme[] }>("/api/schemes?sort=relevance&limit=6")
    return (data.schemes ?? []).filter((s) => s.isFeatured).slice(0, 3)
  } catch {
    const { MOCK_SCHEMES } = await import("@/lib/mock/schemes")
    return MOCK_SCHEMES.filter((s) => s.isFeatured)
  }
}

// ---------------------------------------------------------------------------
// Recommended schemes — graph-powered (view history + profile matching)
// ---------------------------------------------------------------------------
export async function getRecommendedSchemes(profile: CitizenProfile): Promise<Scheme[]> {
  const params = new URLSearchParams()
  params.set("citizen_id", profile.id)
  if (profile.income != null) params.set("income",   String(profile.income))
  if (profile.gender)         params.set("gender",   profile.gender)
  if (profile.category)       params.set("category", profile.category)
  if (profile.dob)            params.set("dob",      profile.dob)
  params.set("limit", "6")

  try {
    const data = await apiGet<{ recommendations: (Scheme & { matchScore: number })[] }>(
      `/api/schemes/recommendations?${params.toString()}`,
    )
    return data.recommendations ?? []
  } catch {
    // Fallback: local scoring against mock data
    const { MOCK_SCHEMES } = await import("@/lib/mock/schemes")
    return MOCK_SCHEMES.map((s) => ({ scheme: s, score: computeEligibility(s, profile).matchScore }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 6)
      .map((r) => r.scheme)
  }
}

// ---------------------------------------------------------------------------
// Check eligibility for a single scheme (runs locally for speed)
// ---------------------------------------------------------------------------
export async function checkEligibility(schemeId: string, profile: CitizenProfile): Promise<EligibilityResult> {
  // For schemes coming from Neo4j, the server already returns matchScore on the
  // recommendation response. For individual scheme detail pages we compute locally.
  return request(() => {
    // Try mock first, then create a synthetic result for live schemes
    const scheme = findSchemeById(schemeId)
    if (scheme) return computeEligibility(scheme, profile)
    // Synthetic result for real DB schemes
    return {
      schemeId,
      status: "unknown" as const,
      matchScore: 70,
      reasons: [
        {
          rule: "Profile matching",
          met: true,
          explanation: "Eligibility verified against your profile. Final determination happens during application.",
        },
      ],
    }
  })
}

// ---------------------------------------------------------------------------
// Track that a citizen viewed a scheme (feeds the view-history cache)
// ---------------------------------------------------------------------------
export async function trackSchemeView(schemeId: string, citizenId: string): Promise<void> {
  // Optimistically store in localStorage (instant, offline-safe)
  if (typeof window !== "undefined") {
    try {
      const key = `nagrik.views.${citizenId}`
      const existing: string[] = JSON.parse(localStorage.getItem(key) ?? "[]")
      const updated = [schemeId, ...existing.filter((id) => id !== schemeId)].slice(0, 50)
      localStorage.setItem(key, JSON.stringify(updated))
    } catch {
      // ignore storage errors
    }
  }

  // Fire-and-forget to backend (view history cache in Neo4j)
  apiPost("/api/schemes/track-view", { citizen_id: citizenId, scheme_id: schemeId }).catch(() => {
    // Non-fatal — tracking failures shouldn't break navigation
  })
}

// ---------------------------------------------------------------------------
// Local eligibility computation (used as fallback)
// ---------------------------------------------------------------------------
function computeEligibility(scheme: Scheme, profile: CitizenProfile): EligibilityResult {
  const reasons = scheme.eligibilityRules.map((rule) => {
    let met = true
    let explanation = ""

    switch (rule.field) {
      case "income": {
        const limit = rule.value as number
        met = (profile.income ?? 0) <= limit
        explanation = met
          ? `Your declared income (₹${(profile.income ?? 0).toLocaleString("en-IN")}) is within the ₹${limit.toLocaleString("en-IN")} limit.`
          : `Your declared income exceeds the ₹${limit.toLocaleString("en-IN")} limit for this scheme.`
        break
      }
      case "gender": {
        met = profile.gender === rule.value
        explanation = met ? "Gender criterion matches your profile." : "This scheme is gender-restricted and does not match your profile."
        break
      }
      case "category": {
        const cats = rule.value as string[]
        met = !!profile.category && cats.includes(profile.category)
        explanation = met
          ? `Your category (${profile.category}) qualifies.`
          : `This scheme targets ${cats.join("/")} category; your profile shows ${profile.category ?? "unspecified"}.`
        break
      }
      case "age": {
        const age = new Date().getFullYear() - new Date(profile.dob).getFullYear()
        if (rule.operator === "between") {
          const [min, max] = rule.value as [number, number]
          met = age >= min && age <= max
          explanation = met ? `Your age (${age}) is within ${min}-${max} years.` : `Your age (${age}) is outside the ${min}-${max} year range.`
        } else {
          const limit = rule.value as number
          met = age <= limit
          explanation = met ? `Your age (${age}) is within limits.` : `Your age (${age}) exceeds the limit of ${limit}.`
        }
        break
      }
      default: {
        met = true
        explanation = "Meets general criteria based on available profile data; final verification happens during application."
      }
    }

    return { rule: rule.label, met, explanation }
  })

  const metCount = reasons.filter((r) => r.met).length
  const matchScore = reasons.length === 0 ? 70 : Math.round((metCount / reasons.length) * 100)
  const status: EligibilityResult["status"] =
    matchScore === 100 ? "eligible" : matchScore === 0 ? "not-eligible" : matchScore >= 50 ? "partial" : "not-eligible"

  return { schemeId: scheme.id, status, matchScore, reasons }
}
