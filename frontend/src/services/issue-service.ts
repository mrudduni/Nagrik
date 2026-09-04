/**
 * Civic issue service.
 *
 * classify and file now call the real nagrik-agent-backend.
 * Listing/lookup uses an in-memory store seeded from mock data — sufficient
 * for hackathon demo since there is no citizen-facing persistence layer yet.
 *
 * TODO: Replace the in-memory list store with real backend endpoints once
 *       the complaint service database is available.
 */
import type { CivicIssue, IssueCategory, IssueSeverity, IssueStatus } from "@/types"
import { MOCK_ISSUES } from "@/lib/mock/issues"
import { WARDS } from "@/lib/mock/wards"
import { request, apiPost, apiGet, ApiError } from "./_client"

// In-memory store seeded from mock data (list/lookup only)
const store: CivicIssue[] = MOCK_ISSUES.map((i) => ({
  ...i,
  timeline: [...i.timeline],
}))

/** Map backend category codes → frontend IssueCategory labels */
const CATEGORY_CODE_MAP: Record<string, IssueCategory> = {
  POTHOLE:          "Roads & Potholes",
  WATER_SUPPLY:     "Water Supply",
  DRAINAGE:         "Drainage",
  GARBAGE:          "Sanitation & Garbage",
  STREETLIGHT:      "Street Lighting",
  POLLUTION:        "Parks & Environment",
  NOISE:            "Noise Pollution",
  ENCROACHMENT:     "Encroachment",
  TRAFFIC:          "Roads & Potholes",
  ELECTRICITY:      "Electricity",
  PUBLIC_TRANSPORT: "Roads & Potholes",
  SANITATION:       "Sanitation & Garbage",
  OTHER:            "Public Safety",
}

interface BackendComplaintStatusRecord {
  id: string
  reference_number: string
  category: string
  priority: string
  department: string
  status: string
  sla_hours: number
  created_at: string
  address?: string | null
}

/** Convert a backend complaint record to the frontend CivicIssue shape */
function _backendRecordToIssue(r: BackendComplaintStatusRecord, citizenId: string): CivicIssue {
  const ward = WARDS[0]
  const priority = r.priority?.toUpperCase() ?? "LOW"
  const severity: IssueSeverity =
    priority === "CRITICAL" ? "critical"
    : priority === "HIGH" ? "high"
    : priority === "MEDIUM" ? "medium"
    : "low"
  const statusRaw = r.status?.toUpperCase() ?? "SUBMITTED"
  const status: IssueStatus =
    statusRaw === "ACKNOWLEDGED" ? "acknowledged"
    : statusRaw === "ASSIGNED" ? "assigned"
    : statusRaw === "IN_PROGRESS" ? "in-progress"
    : statusRaw === "RESOLVED" ? "resolved"
    : statusRaw === "CLOSED" ? "closed"
    : "submitted"

  return {
    id: r.id,
    referenceNumber: r.reference_number,
    title: r.reference_number,
    description: r.address ?? "",
    category: (CATEGORY_CODE_MAP[r.category] ?? "Public Safety") as IssueCategory,
    aiConfidence: 0.88,
    severity,
    status,
    department: r.department,
    ward: ward.ward,
    district: ward.district,
    location: { lat: ward.lat, lng: ward.lng, address: r.address ?? "Not specified" },
    reportedBy: citizenId,
    reportedOn: r.created_at,
    lastUpdated: r.created_at,
    upvotes: 0,
    timeline: [
      { id: "e1", label: "Reported", description: "Filed via NAGRIK", timestamp: r.created_at, actor: "citizen", status: "completed" },
      { id: "e2", label: "Classification", description: `${r.category}, priority ${r.priority}`, timestamp: r.created_at, actor: "ai", status: "current" },
      { id: "e3", label: "Department acknowledgement", description: "", timestamp: "", actor: "officer", status: "upcoming" },
      { id: "e4", label: "Resolved", description: "", timestamp: "", actor: "system", status: "upcoming" },
    ],
    slaHours: r.sla_hours,
    hoursElapsed: Math.round((Date.now() - new Date(r.created_at).getTime()) / 3_600_000),
  }
}

// ─── Filters ─────────────────────────────────────────────────────────────────

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
  // If filtering by citizen, try to fetch their real backend complaints and
  // prepend them before the mock data so they appear at the top.
  let backendIssues: CivicIssue[] = []
  if (filters.citizenId) {
    try {
      const records = await apiGet<BackendComplaintStatusRecord[]>(
        `/complaints?citizen_id=${encodeURIComponent(filters.citizenId)}`,
      )
      backendIssues = records.map((r) =>
        _backendRecordToIssue(r, filters.citizenId!),
      )
    } catch {
      // Backend unavailable or no complaints yet — silently continue
    }
  }

  return request(() => {
    // Merge: backend complaints first (real), then mock store (demo/nearby)
    const backendIds = new Set(backendIssues.map((i) => i.id))
    let results = [
      ...backendIssues,
      ...store.filter((i) => !backendIds.has(i.id)),
    ]

    if (filters.citizenId)
      results = results.filter((i) => i.reportedBy === filters.citizenId || backendIds.has(i.id))
    if (filters.query) {
      const q = filters.query.toLowerCase()
      results = results.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          i.referenceNumber.toLowerCase().includes(q) ||
          i.description.toLowerCase().includes(q),
      )
    }
    if (filters.status && filters.status !== "All")
      results = results.filter((i) => i.status === filters.status)
    if (filters.category && filters.category !== "All")
      results = results.filter((i) => i.category === filters.category)
    if (filters.severity && filters.severity !== "All")
      results = results.filter((i) => i.severity === filters.severity)
    if (filters.ward && filters.ward !== "All")
      results = results.filter((i) => i.ward === filters.ward)
    if (filters.department && filters.department !== "All")
      results = results.filter((i) => i.department === filters.department)
    return results.sort((a, b) => (a.reportedOn < b.reportedOn ? 1 : -1))
  })
}

const API_BASE = process.env.NEXT_PUBLIC_COMPLAINT_API_URL || "http://localhost:8002/api/v1"

const BACKEND_TO_UI_CAT: Record<string, IssueCategory> = {
  POTHOLE: "Roads & Potholes",
  WATER_SUPPLY: "Water Supply",
  DRAINAGE: "Drainage",
  GARBAGE: "Sanitation & Garbage",
  STREETLIGHT: "Street Lighting",
  POLLUTION: "Parks & Environment",
  NOISE: "Noise Pollution",
  ENCROACHMENT: "Encroachment",
  TRAFFIC: "Public Safety",
  ELECTRICITY: "Electricity",
  PUBLIC_TRANSPORT: "Public Safety",
  SANITATION: "Sanitation & Garbage",
  OTHER: "Public Safety",
}

export async function getIssue(id: string): Promise<CivicIssue | undefined> {
  // 1. Try agent backend first for NGR-prefixed IDs
  if (id.toUpperCase().startsWith("NGR-")) {
    try {
      const record = await apiGet<BackendComplaintStatusRecord>(
        `/complaints/${encodeURIComponent(id.toUpperCase())}`,
      )
      return _backendRecordToIssue(record, "")
    } catch {
      // Fall through
    }
  }

  // 2. Try Person 3 complaint service backend (UUIDs or direct complaints)
  try {
    const res = await fetch(`${API_BASE}/complaints/${id}`, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const c = await res.json()
      let timeline: any[] = []
      try {
        const tlRes = await fetch(`${API_BASE}/complaints/${id}/timeline`, { cache: "no-store", signal: AbortSignal.timeout(1500) })
        if (tlRes.ok) {
          const events = await tlRes.json()
          timeline = events.map((e: any) => ({
            id: e.id,
            label: e.event_type.replace(/_/g, " "),
            description: e.details || "",
            timestamp: e.created_at,
            actor: e.actor.toLowerCase(),
            status: "completed",
          }))
        }
      } catch {
        // Timeline fallback
      }

      if (timeline.length === 0) {
        timeline = [
          {
            id: "ev_1",
            label: "Reported",
            description: "Complaint registered via Nagrik digital citizen assistant",
            timestamp: c.created_at,
            actor: "citizen",
            status: "completed",
          },
        ]
      }

      const category = BACKEND_TO_UI_CAT[c.category] || "Roads & Potholes"
      const statusMap: Record<string, IssueStatus> = {
        SUBMITTED: "submitted",
        ACKNOWLEDGED: "acknowledged",
        ASSIGNED: "assigned",
        IN_PROGRESS: "in-progress",
        RESOLUTION_CLAIMED: "resolved",
        CITIZEN_VERIFIED: "closed",
        CLOSED: "closed",
        REOPENED: "reopened",
      }

      return {
        id: c.id,
        referenceNumber: `NAG/${new Date(c.created_at || Date.now()).getFullYear()}/${c.id.slice(0, 8).toUpperCase()}`,
        title: c.title,
        description: c.description,
        category,
        aiSuggestedCategory: category,
        aiConfidence: 0.94,
        severity: c.severity >= 5 ? "critical" : c.severity >= 4 ? "high" : c.severity >= 3 ? "medium" : "low",
        status: statusMap[c.status] || "submitted",
        department: c.department_code || "Municipal Works",
        ward: c.ward || "Central Ward",
        district: c.district || "Bengaluru Urban",
        location: {
          lat: c.latitude || 12.9345,
          lng: c.longitude || 77.6265,
          address: `${c.ward || "Ward"}, ${c.district || "Bengaluru"}`,
        },
        reportedBy: c.citizen_id,
        reportedOn: c.created_at,
        lastUpdated: c.updated_at || c.created_at,
        imageUrls: c.evidence_urls || [],
        upvotes: 0,
        duplicateCount: c.cluster_id ? 4 : 0,
        timeline,
        slaHours: c.severity >= 4 ? 48 : 120,
        hoursElapsed: Math.min(
          120,
          Math.max(1, Math.round((Date.now() - new Date(c.created_at).getTime()) / (1000 * 60 * 60)))
        ),
        assignedOfficer: c.assigned_officer || "Unassigned",
      }
    }
  } catch (err) {
    // Fall through to mock store
  }

  // 3. Fallback to in-memory mock store
  return request(() => store.find((i) => i.id === id))
}

// ─── Classification ───────────────────────────────────────────────────────────

export interface ClassificationPreview {
  category: IssueCategory
  confidence: number
  suggestedDepartment: string
  suggestedSeverity: IssueSeverity
}

interface BackendClassifyResponse {
  category: string
  category_code: string
  confidence: number
  suggested_department: string
  suggested_severity: IssueSeverity
  severity_level: number
}

/** Map backend category codes → frontend IssueCategory labels (used by classifyIssueText) */
export async function classifyIssueText(
  description: string,
): Promise<ClassificationPreview> {
  try {
    const resp = await apiPost<BackendClassifyResponse>(
      "/complaints/classify",
      { description },
    )
    const category: IssueCategory =
      CATEGORY_CODE_MAP[resp.category_code] ?? "Public Safety"

    return {
      category,
      confidence: resp.confidence,
      suggestedDepartment: resp.suggested_department,
      suggestedSeverity: resp.suggested_severity,
    }
  } catch (err) {
    // If backend is unavailable fall back to local keyword heuristic
    if (err instanceof ApiError && !err.status) {
      console.warn("classify endpoint unavailable, using local fallback")
      return _localClassify(description)
    }
    throw err
  }
}

// Local fallback (same keywords as backend, so results are consistent)
function _localClassify(description: string): ClassificationPreview {
  const t = description.toLowerCase()
  let category: IssueCategory = "Public Safety"
  let dept = "General Grievance Cell"

  if (/pothole|road|crater|asphalt/i.test(t)) {
    category = "Roads & Potholes"
    dept = "Municipal Corporation — Roads & Infrastructure"
  } else if (/water|paani|tap|pipeline|leak/i.test(t)) {
    category = "Water Supply"
    dept = "Water Supply & Sanitation Department"
  } else if (/drain|sewage|nala|overflow/i.test(t)) {
    category = "Drainage"
    dept = "Water Supply & Sewerage Board"
  } else if (/garbage|trash|kachra|dustbin/i.test(t)) {
    category = "Sanitation & Garbage"
    dept = "Sanitation & Waste Management Department"
  } else if (/light|streetlight|bulb|dark/i.test(t)) {
    category = "Street Lighting"
    dept = "Electricity & Street Lighting Department"
  } else if (/electricity|power|transformer|bijli/i.test(t)) {
    category = "Electricity"
    dept = "Electricity Distribution Company"
  } else if (/noise|loud|loudspeaker/i.test(t)) {
    category = "Noise Pollution"
    dept = "Encroachment & Public Safety"
  } else if (/encroach|vendor|footpath|illegal/i.test(t)) {
    category = "Encroachment"
    dept = "Encroachment & Public Safety"
  }

  const severity: IssueSeverity =
    /urgent|danger|accident|critical|emergency|spark|fire|flood/i.test(t)
      ? "critical"
      : /block|overflow|broken|unsafe|fallen/i.test(t)
        ? "high"
        : "medium"

  return {
    category,
    confidence: 0.72,
    suggestedDepartment: dept,
    suggestedSeverity: severity,
  }
}

// ─── File complaint ───────────────────────────────────────────────────────────

// BackendComplaintResponse re-uses the BackendComplaintStatusRecord declared above
type BackendComplaintResponse = BackendComplaintStatusRecord & { category_code?: string }

export async function reportIssue(params: {
  citizenId: string
  title: string
  description: string
  category: IssueCategory
  severity: IssueSeverity
  department: string
  address: string
}): Promise<CivicIssue> {
  // Map severity label to backend format
  const severityMap: Record<IssueSeverity, string> = {
    low: "low",
    medium: "medium",
    high: "high",
    critical: "critical",
  }

  let backendResp: BackendComplaintResponse | null = null
  try {
    backendResp = await apiPost<BackendComplaintResponse>("/complaints", {
      citizen_id: params.citizenId,
      title: params.title,
      description: params.description,
      category: params.category,
      severity: severityMap[params.severity],
      department: params.department,
      address: params.address,
    })
  } catch (err) {
    if (err instanceof ApiError && !err.status) {
      console.warn("complaints endpoint unavailable, using local store")
    } else {
      throw err
    }
  }

  // Build the frontend CivicIssue record
  const id = backendResp?.id ?? `civ-${Math.floor(9000 + Math.random() * 999)}`
  const referenceNumber =
    backendResp?.reference_number ??
    `CIV/${new Date().getFullYear()}/${id.slice(4)}`
  const now = new Date().toISOString()
  const ward = WARDS[Math.floor(Math.random() * WARDS.length)]

  const issue: CivicIssue = {
    id,
    referenceNumber,
    title: params.title,
    description: params.description,
    category: params.category,
    aiSuggestedCategory: params.category,
    aiConfidence: backendResp ? 0.88 : 0.72,
    severity: params.severity,
    status: "submitted",
    department: backendResp?.department ?? params.department,
    ward: ward.ward,
    district: ward.district,
    location: {
      lat: ward.lat,
      lng: ward.lng,
      address: params.address || ward.ward,
    },
    reportedBy: params.citizenId,
    reportedOn: now,
    lastUpdated: now,
    upvotes: 0,
    timeline: [
      {
        id: "e1",
        label: "Reported",
        description: "Submitted via Civic Issues portal",
        timestamp: now,
        actor: "citizen",
        status: "completed",
      },
      {
        id: "e2",
        label: "AI classified",
        description: `Classified as ${params.category}, ${params.severity} severity`,
        timestamp: now,
        actor: "ai",
        status: "current",
      },
      {
        id: "e3",
        label: "Department acknowledgement",
        description: "",
        timestamp: "",
        actor: "officer",
        status: "upcoming",
      },
      {
        id: "e4",
        label: "Resolved",
        description: "",
        timestamp: "",
        actor: "system",
        status: "upcoming",
      },
    ],
    slaHours:
      params.severity === "critical"
        ? 24
        : params.severity === "high"
          ? 48
          : 72,
    hoursElapsed: 0,
  }
  store.unshift(issue)
  return issue
}

// ─── Display helpers ──────────────────────────────────────────────────────────

export function statusMeta(status: IssueStatus): {
  label: string
  tone: "default" | "success" | "warning" | "destructive" | "info"
} {
  switch (status) {
    case "submitted":     return { label: "Submitted",   tone: "default" }
    case "acknowledged":  return { label: "Acknowledged", tone: "info" }
    case "assigned":      return { label: "Assigned",    tone: "info" }
    case "in-progress":   return { label: "In Progress", tone: "warning" }
    case "resolved":      return { label: "Resolved",    tone: "success" }
    case "closed":        return { label: "Closed",      tone: "success" }
    case "reopened":      return { label: "Reopened",    tone: "destructive" }
    default:              return { label: status,        tone: "default" }
  }
}

export function severityMeta(severity: IssueSeverity): {
  label: string
  tone: "default" | "success" | "warning" | "destructive" | "info"
} {
  switch (severity) {
    case "low":      return { label: "Low",      tone: "default" }
    case "medium":   return { label: "Medium",   tone: "info" }
    case "high":     return { label: "High",     tone: "warning" }
    case "critical": return { label: "Critical", tone: "destructive" }
  }
}
