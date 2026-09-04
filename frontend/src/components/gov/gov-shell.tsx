"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { LandmarkIcon } from "lucide-react"
import { useApp } from "@/context/app-provider"
import { GovSidebar } from "./gov-sidebar"
import { GovTopbar } from "./gov-topbar"

export function GovShell({ children }: { children: React.ReactNode }) {
  const { session, isAuthLoading } = useApp()
  const router = useRouter()

  React.useEffect(() => {
    if (!isAuthLoading && (!session || session.role !== "officer")) {
      router.replace("/login?portal=gov")
    }
  }, [isAuthLoading, session, router])

  if (isAuthLoading || !session || session.role !== "officer") {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center gap-3 bg-background">
        <div className="flex size-12 animate-pulse items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <LandmarkIcon className="size-6" />
        </div>
        <p className="text-sm text-muted-foreground">Loading Government Portal...</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-svh bg-background">
      <GovSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <GovTopbar />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  )
}
