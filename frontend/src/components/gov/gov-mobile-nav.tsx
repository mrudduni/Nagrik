"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { LandmarkIcon, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { GOV_NAV } from "@/lib/nav-config"
import { cn } from "@/lib/utils"

/**
 * Navigation drawer for the officer portal below the `lg` breakpoint, where
 * GovSidebar is hidden. Without this the government portal has no navigation
 * on phones and tablets.
 */
export function GovMobileNav() {
  const pathname = usePathname()
  const [open, setOpen] = React.useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground lg:hidden" aria-label="Open navigation menu">
          <Menu className="size-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 bg-sidebar p-0 text-sidebar-foreground">
        <SheetHeader className="border-b border-sidebar-border px-5 py-4">
          <SheetTitle className="flex items-center gap-2 text-sidebar-foreground">
            <span className="flex size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              <LandmarkIcon className="size-4.5" />
            </span>
            <span className="leading-tight">
              <span className="block text-sm font-semibold tracking-tight">NAGRIK Gov</span>
              <span className="block text-[11px] font-normal text-sidebar-foreground/60">Civic Intelligence Portal</span>
            </span>
          </SheetTitle>
        </SheetHeader>

        <nav className="space-y-1 p-3">
          {GOV_NAV.map((item) => {
            const active = item.matchPrefix ? pathname.startsWith(item.href) && item.href !== "/gov" : pathname === item.href
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
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

        <div className="mt-auto border-t border-sidebar-border p-3">
          <Link
            href="/"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-lg border border-dashed border-sidebar-border px-3 py-2.5 text-xs text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent"
          >
            Switch to Citizen App
          </Link>
        </div>
      </SheetContent>
    </Sheet>
  )
}
