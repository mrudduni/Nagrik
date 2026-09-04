"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { LandmarkIcon } from "lucide-react"
import { useApp } from "@/context/app-provider"
import { CitizenSidebar } from "./citizen-sidebar"
import { CitizenTopbar } from "./citizen-topbar"
import { CitizenBottomNav } from "./citizen-bottom-nav"

export function CitizenShell({ children }: { children: React.ReactNode }) {
  const { session, isAuthLoading } = useApp()
  const router = useRouter()

  React.useEffect(() => {
    if (!isAuthLoading && (!session || session.role !== "citizen")) {
      router.replace("/login")
    }
  }, [isAuthLoading, session, router])

  if (isAuthLoading || !session || session.role !== "citizen") {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center gap-3 bg-background">
        <div className="flex size-12 animate-pulse items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <LandmarkIcon className="size-6" />
        </div>
        <p className="text-sm text-muted-foreground">Loading NAGRIK...</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-svh bg-background">
      <CitizenSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <CitizenTopbar />
        <main className="flex-1 pb-20 lg:pb-0">{children}</main>
      </div>
      <CitizenBottomNav />
    </div>
  )
}
