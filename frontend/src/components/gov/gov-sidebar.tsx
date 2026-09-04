"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { LandmarkIcon, Loader2, UserRound } from "lucide-react"
import { GOV_NAV } from "@/lib/nav-config"
import { cn } from "@/lib/utils"
import { useApp } from "@/context/app-provider"

export function GovSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { login } = useApp()
  const [switching, setSwitching] = React.useState(false)

  const handleSwitchToCitizen = async () => {
    setSwitching(true)
    try {
      await login("citizen")
      router.push("/")
    } catch {
      setSwitching(false)
    }
  }

  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground lg:flex">
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
          <LandmarkIcon className="size-4.5" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-tight">NAGRIK Gov</p>
          <p className="text-[11px] text-sidebar-foreground/60">Civic Intelligence Portal</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {GOV_NAV.map((item) => {
          const active = item.matchPrefix ? pathname.startsWith(item.href) && item.href !== "/gov" : pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className="size-4.5" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-sidebar-border p-3">
        <button
          type="button"
          onClick={handleSwitchToCitizen}
          disabled={switching}
          className="flex w-full items-center gap-2 rounded-lg border border-dashed border-sidebar-border px-3 py-2.5 text-xs text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors cursor-pointer"
        >
          {switching ? (
            <Loader2 className="size-3.5 animate-spin text-sidebar-primary" />
          ) : (
            <UserRound className="size-3.5 text-sidebar-primary" />
          )}
          <span>{switching ? "Switching to Citizen..." : "Switch to Citizen App"}</span>
        </button>
      </div>
    </aside>
  )
}
