"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Building2, LandmarkIcon, Loader2 } from "lucide-react"
import { CITIZEN_NAV } from "@/lib/nav-config"
import { cn } from "@/lib/utils"
import { useApp } from "@/context/app-provider"

export function CitizenSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { login } = useApp()
  const [switching, setSwitching] = React.useState(false)

  const handleSwitchToGov = async () => {
    setSwitching(true)
    try {
      await login("officer")
      router.push("/gov")
    } catch {
      setSwitching(false)
    }
  }

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card lg:flex">
      <div className="flex h-16 items-center gap-2 border-b border-border px-5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <LandmarkIcon className="size-4.5" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-tight">NAGRIK</p>
          <p className="text-[11px] text-muted-foreground">Smart Civic Platform</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {CITIZEN_NAV.map((item) => {
          const active = item.matchPrefix ? pathname.startsWith(item.href) && item.href !== "/" : pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon className="size-4.5" />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-border p-3">
        <button
          type="button"
          onClick={handleSwitchToGov}
          disabled={switching}
          className="flex w-full items-center gap-2 rounded-lg border border-dashed border-border px-3 py-2.5 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
        >
          {switching ? (
            <Loader2 className="size-3.5 animate-spin text-primary" />
          ) : (
            <Building2 className="size-3.5 text-primary" />
          )}
          <span>{switching ? "Switching to Gov..." : "Switch to Government Portal"}</span>
        </button>
      </div>
    </aside>
  )
}
