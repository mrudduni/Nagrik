"use client"

import * as React from "react"
import Link from "next/link"
import {
  LandmarkIcon,
  FileText,
  Image as ImageIcon,
  Mic,
  ExternalLink,
  ArrowRight,
  BookOpen,
  Play,
  Pause,
  Square,
  Volume2,
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import type { ChatMessage } from "@/types"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"
import { useApp } from "@/context/app-provider"
import { initials } from "@/lib/format"
import { ttsPlayer } from "@/lib/tts-player"

import { FormattedMessage } from "./formatted-message"

const ATTACHMENT_ICON = {
  image: ImageIcon,
  document: FileText,
  voice: Mic,
}

export function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"
  const { session } = useApp()
  const AttachmentIcon =
    message.attachment ? ATTACHMENT_ICON[message.attachment.type] : null

  const [activeId, setActiveId] = React.useState<string | null>(ttsPlayer.activeId)
  const [isPlaying, setIsPlaying] = React.useState<boolean>(ttsPlayer.isPlaying)
  const [isPaused, setIsPaused] = React.useState<boolean>(ttsPlayer.isPaused)

  React.useEffect(() => {
    return ttsPlayer.subscribe(() => {
      setActiveId(ttsPlayer.activeId)
      setIsPlaying(ttsPlayer.isPlaying)
      setIsPaused(ttsPlayer.isPaused)
    })
  }, [])

  const isCurrentPlaying = activeId === message.id && isPlaying
  const isCurrentPaused = activeId === message.id && isPaused
  const isCurrentActive = activeId === message.id && (isPlaying || isPaused)

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

      <div
        className={cn(
          "flex max-w-[85%] flex-col gap-2 sm:max-w-[75%]",
          isUser && "items-end",
        )}
      >
        {/* Message bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-primary text-primary-foreground"
              : "rounded-tl-sm border border-border/60 bg-muted/60 text-foreground shadow-xs",
          )}
        >
          {message.attachment && AttachmentIcon && (
            <div
              className={cn(
                "mb-2 flex items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs",
                isUser
                  ? "border-primary-foreground/20 bg-primary-foreground/10"
                  : "border-border bg-background",
              )}
            >
              <AttachmentIcon className="size-3.5" />
              {message.attachment.name}
            </div>
          )}
          <FormattedMessage content={message.content} isUser={isUser} />

          {/* TTS Player Controls (Start, Pause in between, Resume, Stop) */}
          {!isUser && (
            <div className="mt-2.5 flex items-center gap-1.5 border-t border-border/40 pt-2">
              {isCurrentPlaying ? (
                <>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => ttsPlayer.pause()}
                    className="h-6 px-2 gap-1 rounded-full text-[11px] bg-primary/15 text-primary hover:bg-primary/25 font-medium transition-colors"
                    title="Pause voice"
                  >
                    <Pause className="size-3 fill-current" />
                    Pause
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => ttsPlayer.stop()}
                    className="h-6 px-1.5 rounded-full text-[11px] text-muted-foreground hover:text-foreground"
                    title="Stop speaking"
                  >
                    <Square className="size-2.5 fill-current" />
                  </Button>
                  <span className="flex items-center gap-1 text-[11px] text-primary font-medium pl-1">
                    <span className="flex gap-0.5 items-center">
                      <span className="h-2 w-0.5 animate-pulse bg-primary rounded-full" />
                      <span className="h-3 w-0.5 animate-pulse delay-75 bg-primary rounded-full" />
                      <span className="h-2 w-0.5 animate-pulse delay-150 bg-primary rounded-full" />
                    </span>
                    Speaking...
                  </span>
                </>
              ) : isCurrentPaused ? (
                <>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => ttsPlayer.resume()}
                    className="h-6 px-2 gap-1 rounded-full text-[11px] bg-amber-500/15 text-amber-700 dark:text-amber-400 hover:bg-amber-500/25 font-medium transition-colors"
                    title="Resume voice"
                  >
                    <Play className="size-3 fill-current" />
                    Resume
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => ttsPlayer.stop()}
                    className="h-6 px-1.5 rounded-full text-[11px] text-muted-foreground hover:text-foreground"
                    title="Stop speaking"
                  >
                    <Square className="size-2.5 fill-current" />
                  </Button>
                  <span className="text-[11px] text-amber-600 dark:text-amber-400 font-medium pl-1">
                    Paused
                  </span>
                </>
              ) : (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    ttsPlayer.start(
                      message.id,
                      message.content,
                      message.audioBase64,
                    )
                  }
                  className="h-6 px-2 gap-1 rounded-full text-[11px] text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  title="Read aloud"
                >
                  <Volume2 className="size-3" />
                  Listen
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Rich source cards */}
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-col gap-1.5 w-full">
            <p className="px-1 text-[11px] font-medium text-muted-foreground uppercase tracking-wide">
              Sources
            </p>
            <div className="flex flex-col gap-1.5">
              {message.sources.map((s, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-border bg-background px-3 py-2 text-xs"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex min-w-0 items-start gap-1.5">
                      <BookOpen className="mt-0.5 size-3 shrink-0 text-primary" />
                      <div className="min-w-0">
                        <p className="font-medium text-foreground truncate">
                          {s.label}
                        </p>
                        {s.sublabel && (
                          <p className="text-muted-foreground truncate">
                            {s.sublabel}
                          </p>
                        )}
                        {s.pageRef && (
                          <p className="text-muted-foreground">{s.pageRef}</p>
                        )}
                        {s.snippet && (
                          <p className="mt-1 text-muted-foreground line-clamp-2 leading-relaxed">
                            {s.snippet}
                          </p>
                        )}
                      </div>
                    </div>
                    {s.href && s.href !== "#" && (
                      <Link
                        href={s.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="shrink-0 text-primary hover:underline"
                      >
                        <ExternalLink className="size-3" />
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested actions */}
        {message.suggestedActions && message.suggestedActions.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.suggestedActions.map((a, i) => (
              <Button
                key={i}
                variant="outline"
                size="sm"
                className="h-7 gap-1 rounded-full text-xs"
                asChild
              >
                <Link href={a.href}>
                  {a.label} <ArrowRight className="size-3" />
                </Link>
              </Button>
            ))}
          </div>
        )}

        {message.timestamp && (
          <span className="px-1 text-[11px] text-muted-foreground">
            {formatDateTime(message.timestamp)}
          </span>
        )}
      </div>
    </div>
  )
}
