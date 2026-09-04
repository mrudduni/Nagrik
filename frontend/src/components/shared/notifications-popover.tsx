"use client"

import Link from "next/link"
import type { ComponentType } from "react"
import { Bell, FileText, MapPin, Sparkles, AlertCircle, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { useApp } from "@/context/app-provider"
import { formatRelativeTime } from "@/lib/format"
import { cn } from "@/lib/utils"
import { EmptyState } from "./empty-state"
import type { NotificationType } from "@/types"

const ICON_MAP: Record<NotificationType, ComponentType<{ className?: string }>> = {
  "application-update": FileText,
  "document-request": FileText,
  "issue-update": MapPin,
  "scheme-recommendation": Sparkles,
  system: Settings,
  deadline: AlertCircle,
}

export function NotificationsPopover() {
  const { notifications, unreadCount, markNotificationRead, markAllNotificationsRead } = useApp()

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative text-muted-foreground">
          <Bell className="size-4.5" />
          {unreadCount > 0 && (
            <span className="absolute right-1.5 top-1.5 flex size-2 rounded-full bg-destructive ring-2 ring-background" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-0">
        <div className="flex items-center justify-between px-4 py-3">
          <p className="text-sm font-semibold">Notifications</p>
          {unreadCount > 0 && (
            <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={() => markAllNotificationsRead()}>
              Mark all read
            </Button>
          )}
        </div>
        <Separator />
        {notifications.length === 0 ? (
          <EmptyState icon={Bell} title="No notifications yet" className="border-0" />
        ) : (
          <ScrollArea className="h-96">
            <div className="divide-y divide-border">
              {notifications.map((n) => {
                const Icon = ICON_MAP[n.type]
                return (
                  <Link
                    key={n.id}
                    href={n.href ?? "#"}
                    onClick={() => markNotificationRead(n.id)}
                    className={cn("flex gap-3 px-4 py-3 hover:bg-muted/50 transition-colors", !n.read && "bg-accent/40")}
                  >
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <Icon className="size-4 text-muted-foreground" />
                    </div>
                    <div className="min-w-0 flex-1 space-y-0.5">
                      <p className={cn("text-sm leading-snug", !n.read && "font-medium")}>{n.title}</p>
                      <p className="line-clamp-2 text-xs text-muted-foreground">{n.message}</p>
                      <p className="text-[11px] text-muted-foreground/70">{formatRelativeTime(n.timestamp)}</p>
                    </div>
                    {!n.read && <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-info" />}
                  </Link>
                )
              })}
            </div>
          </ScrollArea>
        )}
      </PopoverContent>
    </Popover>
  )
}
