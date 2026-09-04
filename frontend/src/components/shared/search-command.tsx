"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { FileStack, LayoutGrid, MapPinned, Search, Sparkles, UserRound, ListChecks, Map as MapIcon, ShieldAlert } from "lucide-react"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import { Button } from "@/components/ui/button"
import { listSchemes } from "@/services/scheme-service"
import { listApplications } from "@/services/application-service"
import { listIssues } from "@/services/issue-service"
import { listAllComplaints } from "@/services/gov-service"
import { useApp } from "@/context/app-provider"
import type { Application, CivicIssue, Scheme } from "@/types"

export function SearchCommand({ scope = "citizen" }: { scope?: "citizen" | "gov" }) {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()
  const { session, t } = useApp()
  const citizenId = session?.citizen?.id

  const [schemes, setSchemes] = React.useState<Scheme[]>([])
  const [applications, setApplications] = React.useState<Application[]>([])
  const [issues, setIssues] = React.useState<CivicIssue[]>([])

  // Load the search index lazily, the first time the palette is opened.
  React.useEffect(() => {
    if (!open) return
    if (scope === "citizen") {
      listSchemes().then(setSchemes)
      if (citizenId) {
        listApplications(citizenId).then(setApplications)
        listIssues({ citizenId }).then(setIssues)
      }
    } else {
      listAllComplaints().then(setIssues)
    }
  }, [open, scope, citizenId])

  React.useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [])

  const go = (href: string) => {
    setOpen(false)
    router.push(href)
  }

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setOpen(true)}
        className="h-9 w-full max-w-sm justify-start gap-2 text-muted-foreground sm:w-64"
      >
        <Search className="size-4" />
        <span className="hidden sm:inline">{t.topbar.search_placeholder}</span>
        <span className="sm:hidden">Search...</span>
        <kbd className="ml-auto hidden rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] sm:inline">⌘K</kbd>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen} title={t.topbar.search_placeholder} description="Search schemes, applications, and civic issues">
        <CommandInput placeholder={scope === "gov" ? "Search complaints, wards, departments..." : t.topbar.search_placeholder} />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>

          {scope === "citizen" && (
            <>
              <CommandGroup heading="Quick actions">
                <CommandItem onSelect={() => go("/")} keywords={["chat", "ai", "assistant", "ask"]}>
                  <Sparkles /> Ask the AI Assistant
                </CommandItem>
                <CommandItem onSelect={() => go("/issues/new")} keywords={["complaint", "pothole", "report", "civic"]}>
                  <MapPinned /> Report a civic issue
                </CommandItem>
                <CommandItem onSelect={() => go("/services/compare")} keywords={["compare", "difference"]}>
                  <LayoutGrid /> Compare schemes
                </CommandItem>
                <CommandItem onSelect={() => go("/profile?tab=vault")} keywords={["documents", "digilocker", "vault"]}>
                  <UserRound /> Open Document Vault
                </CommandItem>
              </CommandGroup>

              {schemes.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading="Government Schemes">
                    {schemes.map((s) => (
                      <CommandItem
                        key={s.id}
                        value={`${s.title} ${s.category} ${s.department}`}
                        keywords={[...s.tags, s.category, s.benefitType, s.department]}
                        onSelect={() => go(`/services/${s.id}`)}
                      >
                        <LayoutGrid />
                        <span className="truncate">{s.title}</span>
                        <span className="ml-auto shrink-0 text-xs text-muted-foreground">{s.category}</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}

              {applications.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading="My Applications">
                    {applications.map((a) => (
                      <CommandItem
                        key={a.id}
                        value={`${a.schemeTitle} ${a.referenceNumber}`}
                        keywords={[a.referenceNumber, a.status, a.department]}
                        onSelect={() => go(`/applications/${a.id}`)}
                      >
                        <FileStack />
                        <span className="truncate">{a.schemeTitle}</span>
                        <span className="ml-auto shrink-0 font-mono text-xs text-muted-foreground">{a.referenceNumber}</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}

              {issues.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading="My Complaints">
                    {issues.map((i) => (
                      <CommandItem
                        key={i.id}
                        value={`${i.title} ${i.referenceNumber}`}
                        keywords={[i.referenceNumber, i.category, i.ward, i.status]}
                        onSelect={() => go(`/issues/${i.id}`)}
                      >
                        <MapPinned />
                        <span className="truncate">{i.title}</span>
                        <span className="ml-auto shrink-0 font-mono text-xs text-muted-foreground">{i.referenceNumber}</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}
            </>
          )}

          {scope === "gov" && (
            <>
              <CommandGroup heading="Quick actions">
                <CommandItem onSelect={() => go("/gov/complaints")} keywords={["complaints", "list"]}>
                  <ListChecks /> View all complaints
                </CommandItem>
                <CommandItem onSelect={() => go("/gov/heatmap")} keywords={["map", "geography", "ward"]}>
                  <MapIcon /> Open complaint heatmap
                </CommandItem>
                <CommandItem onSelect={() => go("/gov/alerts")} keywords={["predictive", "risk", "forecast"]}>
                  <ShieldAlert /> Predictive risk alerts
                </CommandItem>
                <CommandItem onSelect={() => go("/gov/departments")} keywords={["sla", "performance"]}>
                  <FileStack /> Department performance
                </CommandItem>
              </CommandGroup>

              {issues.length > 0 && (
                <>
                  <CommandSeparator />
                  <CommandGroup heading="Complaints">
                    {issues.map((i) => (
                      <CommandItem
                        key={i.id}
                        value={`${i.title} ${i.referenceNumber}`}
                        keywords={[i.referenceNumber, i.category, i.ward, i.department, i.severity, i.status]}
                        onSelect={() => go(`/gov/complaints/${i.id}`)}
                      >
                        <MapPinned />
                        <span className="truncate">{i.title}</span>
                        <span className="ml-auto shrink-0 text-xs text-muted-foreground">{i.ward}</span>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </>
              )}
            </>
          )}
        </CommandList>
      </CommandDialog>
    </>
  )
}
