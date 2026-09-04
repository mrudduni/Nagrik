"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { CITIZEN_NAV } from "@/lib/nav-config"
import { cn } from "@/lib/utils"
import { useApp } from "@/context/app-provider"

export function CitizenBottomNav() {
  const pathname = usePathname()
  const { t } = useApp()

  const getNavLabel = (href: string, fallback: string) => {
    if (href === "/") return t.nav.ai_assistant
    if (href === "/services") return t.nav.services
    if (href === "/applications") return t.nav.applications
    if (href === "/issues") return t.nav.issues
    if (href === "/profile") return t.nav.profile
    return fallback
  }

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-card/95 backdrop-blur supports-backdrop-filter:bg-card/80 lg:hidden">
      {CITIZEN_NAV.map((item) => {
        const active = item.matchPrefix ? pathname.startsWith(item.href) && item.href !== "/" : pathname === item.href
        const Icon = item.icon
        const label = getNavLabel(item.href, item.label)
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-1 flex-col items-center gap-1 py-2.5 text-[10.5px] font-medium",
              active ? "text-primary" : "text-muted-foreground",
            )}
          >
            <Icon className="size-5" />
            <span className="max-w-[64px] truncate">{label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
