"use client"

import { LogOut, Settings, UserRound } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { LanguageSelector } from "@/components/shared/language-selector"
import { NotificationsPopover } from "@/components/shared/notifications-popover"
import { SearchCommand } from "@/components/shared/search-command"
import { useApp } from "@/context/app-provider"
import { initials } from "@/lib/format"
import { GovMobileNav } from "./gov-mobile-nav"

export function GovTopbar() {
  const { session, logout } = useApp()
  const officer = session?.officer

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur supports-backdrop-filter:bg-background/80 sm:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
        <GovMobileNav />
        <SearchCommand scope="gov" />
        <Badge variant="outline" className="hidden gap-1.5 text-muted-foreground sm:flex">
          <span className="size-1.5 rounded-full bg-success" /> Live data
        </Badge>
      </div>
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <LanguageSelector />
        <NotificationsPopover />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="ml-1 flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="size-8">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                  {officer ? initials(officer.name) : "OF"}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel className="font-normal">
              <p className="text-sm font-medium">{officer?.name ?? "Officer"}</p>
              <p className="text-xs text-muted-foreground">{officer?.designation}</p>
              <p className="text-xs text-muted-foreground">{officer?.department}</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <UserRound /> My Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings /> Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive" onClick={logout}>
              <LogOut /> Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
