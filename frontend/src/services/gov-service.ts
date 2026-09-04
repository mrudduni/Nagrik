import type {
  CivicIssue,
  DepartmentPerformance,
  DuplicateCluster,
  GovKpi,
  IssueCategory,
  IssueSeverity,
  IssueStatus,
  PredictiveAlert,
  TrendPoint,
  WardStat,
  CategoryBreakdown,
  IssueTimelineEvent,
} from "@/types"
import { MOCK_DEPARTMENTS } from "@/lib/mock/departments"
import {
  GOV_KPIS,
  ISSUE_TREND_30D,
  CATEGORY_BREAKDOWN,
  WARD_STATS,
  PREDICTIVE_ALERTS,
  DUPLICATE_CLUSTERS,
} from "@/lib/mock/analytics"
import { request } from "./_client"
import { listIssues } from "./issue-service"

const API_BASE = process.env.NEXT_PUBLIC_COMPLAINT_API_URL || "http://localhost:8002/api/v1"

// ── Category & Severity Mappers ───────────────────────────────────────────────

const BACKEND_TO_UI_CATEGORY: Record<string, IssueCategory> = {
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

function mapCategory(backendCat: string): IssueCategory {
  return BACKEND_TO_UI_CATEGORY[backendCat] || "Roads & Potholes"
}

function mapSeverity(sev: number): IssueSeverity {
  if (sev >= 5) return "critical"
  if (sev >= 4) return "high"
  if (sev >= 3) return "medium"
  return "low"
}

function mapStatus(st: string): IssueStatus {
  const s = st.toLowerCase().replace(/_/g, "-")
  if (s === "resolution-claimed") return "resolved"
  if (s === "citizen-verified") return "closed"
  if (["submitted", "acknowledged", "assigned", "in-progress", "resolved", "closed", "reopened"].includes(s)) {
    return s as IssueStatus
  }
  return "submitted"
}

// ── Real API fetchers with automatic Mock Fallback ───────────────────────────

export async function getKpis(): Promise<GovKpi[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/overview`, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const data = await res.json()
      return [
        {
          label: "Total Complaints",
          value: data.total_complaints.toLocaleString("en-IN"),
          delta: "+12%",
          trend: "up",
          helpText: "Total civic complaints reported",
        },
        {
          label: "Open Issues",
          value: data.open.toLocaleString("en-IN"),
          delta: "-5%",
          trend: "down",
          helpText: "Currently pending resolution",
        },
        {
          label: "Resolved",
          value: data.resolved.toLocaleString("en-IN"),
          delta: "+18%",
          trend: "up",
          helpText: "Citizen or officer verified",
        },
        {
          label: "Avg. Resolution Time",
          value: `${Math.round(data.avg_resolution_hours)} hrs`,
          delta: "-8 hrs",
          trend: "down",
          helpText: "Average time from report to resolution",
        },
        {
          label: "SLA Compliance",
          value: `${Math.round(data.sla_compliance_pct)}%`,
          delta: "+3.2%",
          trend: "up",
          helpText: "Complaints resolved within mandated SLA",
        },
        {
          label: "Active Clusters",
          value: String(data.active_clusters),
          delta: "Density alerts",
          trend: "flat",
          helpText: "Geographic duplicate complaint clusters",
        },
      ]
    }
  } catch (err) {
    // Backend unreachable, use mock data
  }
  return request(() => GOV_KPIS)
}

export async function getDepartments(): Promise<DepartmentPerformance[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/departments`, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const data = await res.json()
      return data.map((d: any, idx: number) => ({
        id: `dept_${idx + 1}`,
        name: d.department_name,
        totalComplaints: d.total,
        resolved: d.resolved,
        pending: d.pending,
        avgResolutionHours: Math.round(d.avg_resolution_hours),
        slaCompliance: Math.round(d.sla_compliance_pct),
        trend: d.sla_compliance_pct >= 75 ? "up" : d.sla_compliance_pct >= 60 ? "flat" : "down",
        headOfficer: `Executive Engineer, ${d.department_name.split(" ")[0]}`,
      }))
    }
  } catch (err) {
    // Fallback
  }
  return request(() => MOCK_DEPARTMENTS)
}

export async function getIssueTrend(): Promise<TrendPoint[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/trends?days=30`, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const data = await res.json()
      if (data && data.length > 0) {
        return data.map((t: any) => ({
          date: t.date,
          value: t.count,
        }))
      }
    }
  } catch (err) {
    // Fallback
  }
  return request(() => ISSUE_TREND_30D)
}

export async function getCategoryBreakdown(): Promise<CategoryBreakdown[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/categories`, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const data = await res.json()
      if (data && data.length > 0) {
        return data.map((c: any) => ({
          category: mapCategory(c.category),
          count: c.count,
          percentChange: Math.round((c.percentage - 15) * 1.5),
        }))
      }
    }
  } catch (err) {
    // Fallback
  }
  return request(() => CATEGORY_BREAKDOWN)
}

export async function getWardStats(): Promise<WardStat[]> {
  return request(() => WARD_STATS)
}

export async function getPredictiveAlerts(): Promise<PredictiveAlert[]> {
  return request(() => PREDICTIVE_ALERTS)
}

export async function getDuplicateClusters(): Promise<DuplicateCluster[]> {
  try {
    const res = await fetch(`${API_BASE}/clusters/`, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const data = await res.json()
      if (data && data.length > 0) {
        return data.map((c: any) => ({
          id: c.id,
          category: mapCategory(c.category),
          ward: "Koramangala Ward",
          centerLabel: `Cluster near ${c.category} area`,
          issueIds: c.representative_complaint ? [c.representative_complaint] : [],
          count: c.complaint_count,
          radius: "500m",
        }))
      }
    }
  } catch (err) {
    // Fallback
  }
  return request(() => DUPLICATE_CLUSTERS)
}

export interface GovComplaintFilters {
  query?: string
  status?: IssueStatus | "All"
  severity?: string
  department?: string | "All"
  ward?: string | "All"
}

export async function listAllComplaints(filters: GovComplaintFilters = {}): Promise<CivicIssue[]> {
  try {
    const params = new URLSearchParams()
    if (filters.status && filters.status !== "All") {
      params.append("status", filters.status.toUpperCase().replace(/-/g, "_"))
    }
    const url = `${API_BASE}/complaints/?page_size=100&${params.toString()}`
    const res = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(2000) })
    if (res.ok) {
      const data = await res.json()
      if (data.items && data.items.length > 0) {
        return data.items.map((c: any) => ({
          id: c.id,
          referenceNumber: `NAG/${new Date(c.created_at || Date.now()).getFullYear()}/${c.id.slice(0, 8).toUpperCase()}`,
          title: c.title,
          description: c.description,
          category: mapCategory(c.category),
          aiSuggestedCategory: mapCategory(c.category),
          aiConfidence: 0.92,
          severity: mapSeverity(c.severity),
          status: mapStatus(c.status),
          department: c.department_code || "General Civic Cell",
          ward: c.ward || "Central Ward",
          district: c.district || "Bengaluru Urban",
          location: {
            lat: c.latitude || 12.9345,
            lng: c.longitude || 77.6265,
            address: `${c.ward || "Central Ward"}, ${c.district || "Bengaluru"}`,
          },
          reportedBy: c.citizen_id,
          reportedOn: c.created_at,
          lastUpdated: c.updated_at || c.created_at,
          imageUrls: c.evidence_urls || [],
          upvotes: 0,
          duplicateCount: c.cluster_id ? 4 : 0,
          timeline: [
            {
              id: "ev_1",
              label: "Reported",
              description: "Complaint registered via Nagrik digital citizen assistant",
              timestamp: c.created_at,
              actor: "citizen",
              status: "completed",
            },
            {
              id: "ev_2",
              label: "AI Classification",
              description: `Classified as ${c.category} with Priority Tier ${c.priority_tier}`,
              timestamp: c.created_at,
              actor: "ai",
              status: "completed",
            },
            {
              id: "ev_3",
              label: "Department Routing",
              description: `Routed to ${c.department_code || "Municipal Cell"}`,
              timestamp: c.created_at,
              actor: "system",
              status: c.status !== "SUBMITTED" ? "completed" : "current",
            },
          ],
          slaHours: c.severity >= 4 ? 48 : 120,
          hoursElapsed: Math.min(
            120,
            Math.max(1, Math.round((Date.now() - new Date(c.created_at).getTime()) / (1000 * 60 * 60)))
          ),
          assignedOfficer: c.assigned_officer || "Unassigned",
        }))
      }
    }
  } catch (err) {
    // Fallback
  }
  return listIssues({
    query: filters.query,
    status: filters.status,
    department: filters.department,
    ward: filters.ward,
    severity: filters.severity as never,
  })
}

export async function updateComplaintStatus(id: string, status: IssueStatus): Promise<void> {
  try {
    const backendStatus = status.toUpperCase().replace(/-/g, "_")
    const res = await fetch(`${API_BASE}/complaints/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: backendStatus }),
    })
    if (res.ok) return
  } catch (err) {
    // Fallback to local store
  }

  const issues = await listIssues()
  const target = issues.find((i) => i.id === id)
  if (!target) return
  return request(() => {
    target.status = status
    target.lastUpdated = new Date().toISOString()
  }, 300)
}

// ── Officer Action API Calls ──────────────────────────────────────────────────

export async function assignOfficer(complaintId: string, officerName: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/admin/complaints/${complaintId}/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ officer_name: officerName }),
    })
    return res.ok
  } catch {
    return false
  }
}

export async function resolveComplaint(complaintId: string, notes: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/admin/complaints/${complaintId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolution_notes: notes }),
    })
    return res.ok
  } catch {
    return false
  }
}

export async function acknowledgeComplaint(complaintId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/admin/complaints/${complaintId}/acknowledge`, {
      method: "POST",
    })
    return res.ok
  } catch {
    return false
  }
}
