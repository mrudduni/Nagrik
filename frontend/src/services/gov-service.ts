import type { CivicIssue, DepartmentPerformance, DuplicateCluster, GovKpi, IssueStatus, PredictiveAlert, TrendPoint, WardStat, CategoryBreakdown } from "@/types"
import { MOCK_DEPARTMENTS } from "@/lib/mock/departments"
import { GOV_KPIS, ISSUE_TREND_30D, CATEGORY_BREAKDOWN, WARD_STATS, PREDICTIVE_ALERTS, DUPLICATE_CLUSTERS } from "@/lib/mock/analytics"
import { request } from "./_client"
import { listIssues } from "./issue-service"

export async function getKpis(): Promise<GovKpi[]> {
  return request(() => GOV_KPIS)
}

export async function getDepartments(): Promise<DepartmentPerformance[]> {
  return request(() => MOCK_DEPARTMENTS)
}

export async function getIssueTrend(): Promise<TrendPoint[]> {
  return request(() => ISSUE_TREND_30D)
}

export async function getCategoryBreakdown(): Promise<CategoryBreakdown[]> {
  return request(() => CATEGORY_BREAKDOWN)
}

export async function getWardStats(): Promise<WardStat[]> {
  return request(() => WARD_STATS)
}

export async function getPredictiveAlerts(): Promise<PredictiveAlert[]> {
  return request(() => PREDICTIVE_ALERTS)
}

export async function getDuplicateClusters(): Promise<DuplicateCluster[]> {
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
  return listIssues({
    query: filters.query,
    status: filters.status,
    department: filters.department,
    ward: filters.ward,
    severity: filters.severity as never,
  })
}

export async function updateComplaintStatus(id: string, status: IssueStatus): Promise<void> {
  const issues = await listIssues()
  const target = issues.find((i) => i.id === id)
  if (!target) return
  return request(() => {
    target.status = status
    target.lastUpdated = new Date().toISOString()
  }, 500)
}
