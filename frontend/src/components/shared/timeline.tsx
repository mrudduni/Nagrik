import { Bot, Check, User, UserCog, Circle } from "lucide-react"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

export interface TimelineEventLike {
  id: string
  label: string
  description: string
  timestamp: string
  actor: "citizen" | "system" | "officer" | "ai"
  status: "completed" | "current" | "upcoming"
}

const ACTOR_ICON = { citizen: User, system: Circle, officer: UserCog, ai: Bot }
const ACTOR_LABEL = { citizen: "You", system: "System", officer: "Officer", ai: "AI Assistant" }

export function Timeline({ events }: { events: TimelineEventLike[] }) {
  return (
    <div className="space-y-0">
      {events.map((event, i) => {
        const Icon = event.status === "completed" ? Check : ACTOR_ICON[event.actor]
        const isLast = i === events.length - 1
        return (
          <div key={event.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-full border-2",
                  event.status === "completed" && "border-success bg-success text-success-foreground",
                  event.status === "current" && "border-primary bg-primary/10 text-primary",
                  event.status === "upcoming" && "border-border bg-muted text-muted-foreground",
                )}
              >
                <Icon className="size-3.5" />
              </div>
              {!isLast && (
                <div className={cn("w-0.5 flex-1 min-h-8", event.status === "completed" ? "bg-success" : "bg-border")} />
              )}
            </div>
            <div className={cn("flex-1 pb-6", event.status === "upcoming" && "opacity-50")}>
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-0.5">
                <p className="text-sm font-medium">{event.label}</p>
                {event.timestamp && <span className="text-[11px] text-muted-foreground">{formatDateTime(event.timestamp)}</span>}
              </div>
              {event.description && <p className="mt-0.5 text-xs text-muted-foreground">{event.description}</p>}
              <span className="mt-1 inline-block text-[10px] font-medium uppercase tracking-wide text-muted-foreground/70">
                {ACTOR_LABEL[event.actor]}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
