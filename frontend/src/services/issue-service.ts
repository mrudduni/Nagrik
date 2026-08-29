import type { CivicIssue, IssueCategory, IssueSeverity, IssueStatus } from "@/types"
import { MOCK_ISSUES } from "@/lib/mock/issues"
import { WARDS } from "@/lib/mock/wards"
import { request } from "./_client"

const store: CivicIssue[] = MOCK_ISSUES.map((i) => ({ ...i, timeline: [...i.timeline] }))

export interface IssueFilters {
  citizenId?: string
  query?: string
  status?: IssueStatus | "All"
  category?: IssueCategory | "All"
  severity?: IssueSeverity | "All"
  ward?: string | "All"
  department?: string | "All"
}

export async function listIssues(filters: IssueFilters = {}): Promise<CivicIssue[]> {
  return request(() => {
    let results = [...store]
    if (filters.citizenId) results = results.filter((i) => i.reportedBy === filters.citizenId)
    if (filters.query) {
      const q = filters.query.toLowerCase()
      results = results.filter(
        (i) => i.title.toLowerCase().includes(q) || i.referenceNumber.toLowerCase().includes(q) || i.description.toLowerCase().includes(q),
      )
    }
    if (filters.status && filters.status !== "All") results = results.filter((i) => i.status === filters.status)
    if (filters.category && filters.category !== "All") results = results.filter((i) => i.category === filters.category)
    if (filters.severity && filters.severity !== "All") results = results.filter((i) => i.severity === filters.severity)
    if (filters.ward && filters.ward !== "All") results = results.filter((i) => i.ward === filters.ward)
    if (filters.department && filters.department !== "All") results = results.filter((i) => i.department === filters.department)

    return results.sort((a, b) => (a.reportedOn < b.reportedOn ? 1 : -1))
  })
}

export async function getIssue(id: string): Promise<CivicIssue | undefined> {
  return request(() => store.find((i) => i.id === id))
}

export interface ClassificationPreview {
  category: IssueCategory
  confidence: number
  suggestedDepartment: string
  suggestedSeverity: IssueSeverity
}

const CATEGORY_KEYWORDS: { keywords: RegExp; category: IssueCategory; department: string }[] = [
  { keywords: /pothole|road|footpath|tar|asphalt/i, category: "Roads & Potholes", department: "Public Works Department (Roads)" },
  { keywords: /water|pipeline|tap|tanker|supply/i, category: "Water Supply", department: "Water Supply & Sewerage" },
  { keywords: /drain|sewage|overflow|clog/i, category: "Drainage", department: "Water Supply & Sewerage" },
  { keywords: /light|streetlight|lamp|bulb/i, category: "Street Lighting", department: "Electricity & Street Lighting" },
  { keywords: /transformer|electric|wire|shock|power cut/i, category: "Electricity", department: "Electricity & Street Lighting" },
  { keywords: /garbage|waste|trash|bin|dump/i, category: "Sanitation & Garbage", department: "Sanitation & Waste Management" },
  { keywords: /encroach|vendor|footpath block|illegal/i, category: "Encroachment", department: "Encroachment & Public Safety" },
  { keywords: /park|tree|garden|playground/i, category: "Parks & Environment", department: "Parks & Horticulture" },
  { keywords: /noise|loud|construction hours/i, category: "Noise Pollution", department: "Encroachment & Public Safety" },
  { keywords: /dog|safety|stray|harassment|unsafe/i, category: "Public Safety", department: "Sanitation & Waste Management" },
]

export async function classifyIssueText(description: string): Promise<ClassificationPreview> {
  return request(() => {
    const match = CATEGORY_KEYWORDS.find((k) => k.keywords.test(description))
    const severity: IssueSeverity = /urgent|danger|accident|critical|emergency|spark|fire/i.test(description)
      ? "critical"
      : /block|overflow|broken|unsafe/i.test(description)
        ? "high"
        : "medium"

    return {
      category: match?.category ?? "Roads & Potholes",
      confidence: match ? 0.86 + Math.random() * 0.12 : 0.55,
      suggestedDepartment: match?.department ?? "Public Works Department (Roads)",
      suggestedSeverity: severity,
    }
  }, 1100)
}

export async function reportIssue(params: {
  citizenId: string
  title: string
  description: string
  category: IssueCategory
  severity: IssueSeverity
  department: string
  address: string
}): Promise<CivicIssue> {
  return request(() => {
    const id = `civ-${Math.floor(9000 + Math.random() * 999)}`
    const now = new Date().toISOString()
    const ward = WARDS[Math.floor(Math.random() * WARDS.length)]
    const issue: CivicIssue = {
      id,
      referenceNumber: `CIV/${new Date().getFullYear()}/${id.slice(4)}`,
      title: params.title,
      description: params.description,
      category: params.category,
      aiSuggestedCategory: params.category,
      aiConfidence: 0.9,
      severity: params.severity,
      status: "submitted",
      department: params.department,
      ward: ward.ward,
      district: ward.district,
      location: { lat: ward.lat, lng: ward.lng, address: params.address || ward.ward },
      reportedBy: params.citizenId,
      reportedOn: now,
      lastUpdated: now,
      upvotes: 0,
      timeline: [
        { id: "e1", label: "Reported", description: "Submitted via Civic Issues portal", timestamp: now, actor: "citizen", status: "completed" },
        { id: "e2", label: "AI classified", description: `Classified as ${params.category}, ${params.severity} severity`, timestamp: now, actor: "ai", status: "current" },
        { id: "e3", label: "Department acknowledgement", description: "", timestamp: "", actor: "officer", status: "upcoming" },
        { id: "e4", label: "Resolved", description: "", timestamp: "", actor: "system", status: "upcoming" },
      ],
      slaHours: params.severity === "critical" ? 24 : params.severity === "high" ? 48 : 72,
      hoursElapsed: 0,
    }
    store.unshift(issue)
    return issue
  }, 900)
}

export function statusMeta(status: IssueStatus): { label: string; tone: "default" | "success" | "warning" | "destructive" | "info" } {
  switch (status) {
    case "submitted":
      return { label: "Submitted", tone: "default" }
    case "acknowledged":
      return { label: "Acknowledged", tone: "info" }
    case "assigned":
      return { label: "Assigned", tone: "info" }
    case "in-progress":
      return { label: "In Progress", tone: "warning" }
    case "resolved":
      return { label: "Resolved", tone: "success" }
    case "closed":
      return { label: "Closed", tone: "success" }
    case "reopened":
      return { label: "Reopened", tone: "destructive" }
    default:
      return { label: status, tone: "default" }
  }
}

export function severityMeta(severity: IssueSeverity): { label: string; tone: "default" | "success" | "warning" | "destructive" | "info" } {
  switch (severity) {
    case "low":
      return { label: "Low", tone: "default" }
    case "medium":
      return { label: "Medium", tone: "info" }
    case "high":
      return { label: "High", tone: "warning" }
    case "critical":
      return { label: "Critical", tone: "destructive" }
  }
}
