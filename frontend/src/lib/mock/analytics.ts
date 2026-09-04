import type {
  CategoryBreakdown,
  DuplicateCluster,
  GovKpi,
  PredictiveAlert,
  TrendPoint,
  WardStat,
} from "@/types"
import { WARDS } from "./wards"

export const GOV_KPIS: GovKpi[] = [
  { label: "Total Complaints (30d)", value: "1,860", delta: "+8.2%", trend: "up", helpText: "vs previous 30 days" },
  { label: "Resolution Rate", value: "76.4%", delta: "+3.1%", trend: "up", helpText: "complaints resolved within SLA" },
  { label: "Avg Resolution Time", value: "54 hrs", delta: "-6 hrs", trend: "up", helpText: "faster than last month" },
  { label: "Active Risk Alerts", value: "7", delta: "+2", trend: "down", helpText: "predictive alerts needing attention" },
  { label: "Citizen Satisfaction", value: "4.2 / 5", delta: "+0.2", trend: "up", helpText: "post-resolution survey score" },
  { label: "Duplicate Clusters", value: "23", delta: "-4", trend: "up", helpText: "auto-merged this month" },
]

export const ISSUE_TREND_30D: TrendPoint[] = Array.from({ length: 30 }).map((_, i) => {
  const day = i + 1
  const base = 55 + Math.sin(i / 4) * 12 + (i > 20 ? 10 : 0)
  return { date: `Aug ${day}`, value: Math.round(base + (i % 5) * 2) }
})

export const CATEGORY_BREAKDOWN: CategoryBreakdown[] = [
  { category: "Sanitation & Garbage", count: 501, percentChange: 12 },
  { category: "Roads & Potholes", count: 412, percentChange: -4 },
  { category: "Water Supply", count: 356, percentChange: 18 },
  { category: "Electricity", count: 289, percentChange: -8 },
  { category: "Encroachment", count: 174, percentChange: 5 },
  { category: "Parks & Environment", count: 128, percentChange: -2 },
]

export const WARD_STATS: WardStat[] = WARDS.map((w, i) => ({
  ward: w.ward,
  district: w.district,
  totalIssues: [64, 91, 48, 55, 87, 103, 39, 76][i],
  resolvedIssues: [48, 62, 40, 47, 58, 71, 33, 54][i],
  avgResolutionDays: [2.1, 3.4, 1.8, 2.0, 2.9, 3.8, 1.5, 2.6][i],
  riskScore: [62, 81, 40, 45, 74, 88, 30, 58][i],
  lat: w.lat,
  lng: w.lng,
  population: w.population,
}))

export const PREDICTIVE_ALERTS: PredictiveAlert[] = [
  {
    id: "pa-1",
    title: "Water main failure risk - Malviya Nagar",
    description:
      "Complaint velocity and pipeline age data suggest a 78% probability of a major water supply disruption in the next 10 days.",
    ward: "Ward 14 - Malviya Nagar",
    category: "Water Supply",
    riskLevel: "critical",
    predictedFor: "2026-09-05",
    confidence: 0.78,
    recommendedAction: "Schedule preventive pipeline inspection and pre-position tanker capacity.",
    affectedPopulationEstimate: 18500,
  },
  {
    id: "pa-2",
    title: "Waterlogging risk ahead of monsoon spell - Kalkaji",
    description:
      "Drainage complaint clusters combined with forecasted rainfall indicate high waterlogging risk in low-lying pockets.",
    ward: "Ward 5 - Kalkaji",
    category: "Drainage",
    riskLevel: "high",
    predictedFor: "2026-09-02",
    confidence: 0.71,
    recommendedAction: "Deploy desilting crews to identified drain segments before next rainfall window.",
    affectedPopulationEstimate: 12300,
  },
  {
    id: "pa-3",
    title: "Road safety hotspot forming - Green Park",
    description:
      "Repeated pothole reports and 2 accident-linked complaints within 500m indicate an emerging accident hotspot.",
    ward: "Ward 12 - Green Park",
    category: "Roads & Potholes",
    riskLevel: "high",
    predictedFor: "2026-08-30",
    confidence: 0.83,
    recommendedAction: "Prioritise emergency patch repair and place temporary warning signage.",
    affectedPopulationEstimate: 6200,
  },
  {
    id: "pa-4",
    title: "Sanitation SLA breach risk - Citywide",
    description:
      "Sanitation department SLA compliance has dropped 9 points in 2 weeks; volume growth outpaces crew capacity.",
    ward: "Multiple wards",
    category: "Sanitation & Garbage",
    riskLevel: "medium",
    predictedFor: "2026-09-10",
    confidence: 0.65,
    recommendedAction: "Reallocate 2 additional collection crews from low-load zones for 2 weeks.",
    affectedPopulationEstimate: 94000,
  },
  {
    id: "pa-5",
    title: "Encroachment recurrence - Lajpat Nagar market",
    description: "Historical pattern shows encroachment complaints recur within 30 days of enforcement action 60% of the time.",
    ward: "Ward 33 - Lajpat Nagar",
    category: "Encroachment",
    riskLevel: "medium",
    predictedFor: "2026-09-20",
    confidence: 0.6,
    recommendedAction: "Schedule follow-up inspection 20 days post-notice and consider permanent vendor zoning.",
    affectedPopulationEstimate: 8800,
  },
]

export const DUPLICATE_CLUSTERS: DuplicateCluster[] = [
  {
    id: "dc-1",
    category: "Roads & Potholes",
    ward: "Ward 12 - Green Park",
    centerLabel: "Green Park Market Main Rd",
    issueIds: ["civ-9981", "civ-9982", "civ-9983"],
    count: 3,
    radius: "180m",
  },
  {
    id: "dc-2",
    category: "Sanitation & Garbage",
    ward: "Ward 5 - Kalkaji",
    centerLabel: "Kalkaji Metro Gate 2",
    issueIds: ["civ-9877", "civ-9878"],
    count: 2,
    radius: "120m",
  },
  {
    id: "dc-3",
    category: "Water Supply",
    ward: "Ward 14 - Malviya Nagar",
    centerLabel: "Block C, Malviya Nagar",
    issueIds: ["civ-9950"],
    count: 9,
    radius: "450m",
  },
]
