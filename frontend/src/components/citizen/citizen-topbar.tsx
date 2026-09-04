"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { Building2, LogOut, Phone, Settings, UserRound } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { LanguageSelector } from "@/components/shared/language-selector"
import { NotificationsPopover } from "@/components/shared/notifications-popover"
import { SearchCommand } from "@/components/shared/search-command"
import { useApp } from "@/context/app-provider"
import { initials } from "@/lib/format"
import { CallNagrikDialog } from "./call-nagrik-dialog"

export function CitizenTopbar() {
  const { session, logout, login } = useApp()
  const router = useRouter()
  const citizen = session?.citizen

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur supports-backdrop-filter:bg-background/80 sm:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <SearchCommand scope="citizen" />
      </div>
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <CallNagrikDialog>
          <Button variant="ghost" size="icon" className="text-muted-foreground">
            <Phone className="size-4.5" />
          </Button>
        </CallNagrikDialog>
        <LanguageSelector />
        <NotificationsPopover />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="ml-1 flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="size-8">
                <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                  {citizen ? initials(citizen.name) : "NG"}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <p className="text-sm font-medium">{citizen?.name ?? "Citizen"}</p>
              <p className="text-xs text-muted-foreground">{citizen?.email}</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile">
                <UserRound /> My Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/profile?tab=preferences">
                <Settings /> Preferences
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={async () => { await login("officer"); router.push("/gov") }}>
              <Building2 /> Switch to Government Portal
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
