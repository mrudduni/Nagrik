import type { CitizenProfile, EligibilityResult, Scheme, SchemeCategory } from "@/types"
import { MOCK_SCHEMES, findSchemeById } from "@/lib/mock/schemes"
import { request } from "./_client"

export interface SchemeFilters {
  query?: string
  category?: SchemeCategory | "All"
  level?: "Central" | "State" | "All"
  benefitType?: string
  sortBy?: "relevance" | "newest" | "beneficiaries" | "rating"
}

export async function listSchemes(filters: SchemeFilters = {}): Promise<Scheme[]> {
  return request(() => {
    let results = [...MOCK_SCHEMES]

    if (filters.query) {
      const q = filters.query.toLowerCase()
      results = results.filter(
        (s) =>
          s.title.toLowerCase().includes(q) ||
          s.shortDescription.toLowerCase().includes(q) ||
          s.tags.some((t) => t.toLowerCase().includes(q)) ||
          s.department.toLowerCase().includes(q),
      )
    }
    if (filters.category && filters.category !== "All") {
      results = results.filter((s) => s.category === filters.category)
    }
    if (filters.level && filters.level !== "All") {
      results = results.filter((s) => s.level === filters.level)
    }
    if (filters.benefitType) {
      results = results.filter((s) => s.benefitType === filters.benefitType)
    }

    switch (filters.sortBy) {
      case "newest":
        results.sort((a, b) => (a.launchedOn < b.launchedOn ? 1 : -1))
        break
      case "beneficiaries":
        results.sort((a, b) => b.beneficiariesCount - a.beneficiariesCount)
        break
      case "rating":
        results.sort((a, b) => b.rating - a.rating)
        break
      default:
        results.sort((a, b) => Number(b.isFeatured) - Number(a.isFeatured))
    }

    return results
  })
}

export async function getScheme(id: string): Promise<Scheme | undefined> {
  return request(() => findSchemeById(id))
}

export async function getFeaturedSchemes(): Promise<Scheme[]> {
  return request(() => MOCK_SCHEMES.filter((s) => s.isFeatured))
}

export async function getRecommendedSchemes(profile: CitizenProfile): Promise<Scheme[]> {
  return request(() => {
    return MOCK_SCHEMES.map((s) => ({ scheme: s, score: computeEligibility(s, profile).matchScore }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 6)
      .map((r) => r.scheme)
  })
}

export async function checkEligibility(schemeId: string, profile: CitizenProfile): Promise<EligibilityResult> {
  return request(() => {
    const scheme = findSchemeById(schemeId)
    if (!scheme) throw new Error("Scheme not found")
    return computeEligibility(scheme, profile)
  })
}

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
        // Rules requiring data not present on the profile default to "needs verification"
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
