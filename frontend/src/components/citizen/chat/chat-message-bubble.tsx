import Link from "next/link"
import { LandmarkIcon, FileText, Image as ImageIcon, Mic, ExternalLink, ArrowRight } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import type { ChatMessage } from "@/types"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"
import { useApp } from "@/context/app-provider"
import { initials } from "@/lib/format"

const ATTACHMENT_ICON = { image: ImageIcon, document: FileText, voice: Mic }

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"
  const { session } = useApp()
  const AttachmentIcon = message.attachment ? ATTACHMENT_ICON[message.attachment.type] : null

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <Avatar className="size-8 shrink-0">
        {isUser ? (
          <AvatarFallback className="bg-secondary text-secondary-foreground text-xs">
            {session?.citizen ? initials(session.citizen.name) : "You"}
          </AvatarFallback>
        ) : (
          <AvatarFallback className="bg-primary text-primary-foreground">
            <LandmarkIcon className="size-4" />
          </AvatarFallback>
        )}
      </Avatar>

      <div className={cn("flex max-w-[85%] flex-col gap-2 sm:max-w-[75%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
            isUser ? "rounded-tr-sm bg-primary text-primary-foreground" : "rounded-tl-sm bg-muted text-foreground",
          )}
        >
          {message.attachment && AttachmentIcon && (
            <div className={cn("mb-2 flex items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs", isUser ? "border-primary-foreground/20 bg-primary-foreground/10" : "border-border bg-background")}>
              <AttachmentIcon className="size-3.5" />
              {message.attachment.name}
            </div>
          )}
          {message.content}
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.sources.map((s, i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2 py-0.5 text-[11px] text-muted-foreground">
                <ExternalLink className="size-2.5" />
                {s.label}
              </span>
            ))}
          </div>
        )}

        {message.suggestedActions && message.suggestedActions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.suggestedActions.map((a, i) => (
              <Button key={i} variant="outline" size="sm" className="h-7 gap-1 rounded-full text-xs" asChild>
                <Link href={a.href}>
                  {a.label} <ArrowRight className="size-3" />
                </Link>
              </Button>
            ))}
          </div>
        )}

        {message.timestamp && (
          <span className="px-1 text-[11px] text-muted-foreground">{formatDateTime(message.timestamp)}</span>
        )}
      </div>
    </div>
  )
}
