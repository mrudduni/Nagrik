import type { ComponentType } from "react"
import {
  Sparkles,
  LayoutGrid,
  FileStack,
  UserRound,
  MapPinned,
  LayoutDashboard,
  ListChecks,
  BarChart3,
  Map,
  Building2,
  ShieldAlert,
} from "lucide-react"

export interface NavItem {
  label: string
  href: string
  icon: ComponentType<{ className?: string }>
  matchPrefix?: boolean
}

export const CITIZEN_NAV: NavItem[] = [
  { label: "AI Assistant", href: "/", icon: Sparkles },
  { label: "Government Services", href: "/services", icon: LayoutGrid, matchPrefix: true },
  { label: "My Applications", href: "/applications", icon: FileStack, matchPrefix: true },
  { label: "Civic Issues", href: "/issues", icon: MapPinned, matchPrefix: true },
  { label: "Profile & Vault", href: "/profile", icon: UserRound, matchPrefix: true },
]

export const GOV_NAV: NavItem[] = [
  { label: "Overview", href: "/gov", icon: LayoutDashboard },
  { label: "Complaints", href: "/gov/complaints", icon: ListChecks, matchPrefix: true },
  { label: "Analytics", href: "/gov/analytics", icon: BarChart3, matchPrefix: true },
  { label: "Heatmap", href: "/gov/heatmap", icon: Map, matchPrefix: true },
  { label: "Departments", href: "/gov/departments", icon: Building2, matchPrefix: true },
  { label: "Risk Alerts", href: "/gov/alerts", icon: ShieldAlert, matchPrefix: true },
]
