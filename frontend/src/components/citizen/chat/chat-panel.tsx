"use client"

import * as React from "react"
import { LandmarkIcon } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { sendMessage, sendVoiceMessage, type BackendNavigationAction } from "@/services/chat-service"
import type { ChatMessage } from "@/types"
import { ChatMessageBubble } from "./chat-message-bubble"
import { ChatComposer, type PendingAttachment } from "./chat-composer"
import { useApp } from "@/context/app-provider"
import { ttsPlayer } from "@/lib/tts-player"

// ─── Stable session helpers ───────────────────────────────────────────────────

const SESSION_STORAGE_KEY = "nagrik.chat.session_id"

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return `sess_${Date.now()}`
  const stored = sessionStorage.getItem(SESSION_STORAGE_KEY)
  if (stored) return stored
  const id = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  sessionStorage.setItem(SESSION_STORAGE_KEY, id)
  return id
}

// ─── Suggested action helper ──────────────────────────────────────────────────
// Instead of automatically hijacking the screen with router.push, we present
// any navigation suggestions as clickable action chips under the assistant message.

function getSuggestedActionFromNavigation(
  nav: BackendNavigationAction | undefined,
): { label: string; href: string } | null {
  if (!nav || !nav.action || nav.action === "none") return null
  switch (nav.action) {
    case "open_scheme_page":
      if (nav.target_id) {
        return {
          label: "View Scheme Details",
          href: `/services/${nav.target_id}`,
        }
      }
      return null
    case "open_comparison":
      return {
        label: "Compare Schemes",
        href: "/services/compare",
      }
    case "open_application_form":
      if (nav.target_id) {
        return {
          label: "Apply for Scheme",
          href: `/apply/${nav.target_id}`,
        }
      }
      return null
    case "open_complaint_status":
      return {
        label: "View Grievance Status",
        href: "/issues",
      }
    case "open_profile":
      return {
        label: "View Profile",
        href: "/profile",
      }
    default:
      return null
  }
}

// ─── Welcome message ──────────────────────────────────────────────────────────

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Namaste! I'm your NAGRIK AI assistant. I can help you discover government schemes, check eligibility, fill out applications, track their status, or report a civic issue — in text or voice. What would you like help with today?",
  timestamp: "",
}

// ─── Error messages ───────────────────────────────────────────────────────────

function makeErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const msg = error.message.toLowerCase()
    if (msg.includes("timeout") || msg.includes("abort")) {
      return "The request took too long. Please try again."
    }
    if (
      msg.includes("network") ||
      msg.includes("fetch") ||
      msg.includes("failed to fetch")
    ) {
      return "Could not reach the NAGRIK backend. Please make sure the server is running and try again."
    }
    if (msg.includes("500") || msg.includes("internal server")) {
      return "The server encountered an error. Please try a different question or try again shortly."
    }
    if (msg.includes("400") || msg.includes("bad request")) {
      return "Your message could not be processed. Please check your input and try again."
    }
  }
  return "Sorry, something went wrong. Please try again."
}

// ─── ChatPanel ────────────────────────────────────────────────────────────────

export function ChatPanel() {
  const { session } = useApp()

  const [messages, setMessages] = React.useState<ChatMessage[]>([WELCOME_MESSAGE])
  const [isTyping, setIsTyping] = React.useState(false)
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const idCounter = React.useRef(0)

  // Stable session ID — persists across navigation within the same tab session
  const sessionIdRef = React.useRef<string>("")
  React.useEffect(() => {
    sessionIdRef.current = getOrCreateSessionId()
  }, [])

  const citizenId = session?.citizen?.id ?? "frontend-citizen"

  React.useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [messages, isTyping])

  async function handleSend(text: string, attachment?: PendingAttachment) {
    if (!text.trim() && !attachment) return

    idCounter.current += 1
    const userMsg: ChatMessage = {
      id: `u-${idCounter.current}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
      attachment,
    }
    setMessages((prev) => [...prev, userMsg])
    setIsTyping(true)

    try {
      const result = await sendMessage(
        text,
        sessionIdRef.current,
        citizenId,
        null,
        attachment,
      )
      const suggestedAction = getSuggestedActionFromNavigation(result.navigation)
      const assistantMsg: ChatMessage = {
        ...result.message,
        suggestedActions: [
          ...(result.message.suggestedActions || []),
          ...(suggestedAction ? [suggestedAction] : []),
        ],
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (error) {
      console.error("Message failed:", error)
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: makeErrorMessage(error),
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setIsTyping(false)
    }
  }

  async function handleVoiceSend({
    audioBase64,
    mimeType,
  }: {
    audioBase64: string
    mimeType: string
    duration: number
  }) {
    if (!audioBase64) return
    setIsTyping(true)
    try {
      const result = await sendVoiceMessage(
        audioBase64,
        sessionIdRef.current,
        citizenId,
        null,
        mimeType,
      )
      const suggestedAction = getSuggestedActionFromNavigation(result.navigation)
      const assistantMsg: ChatMessage = {
        ...result.assistantMessage,
        suggestedActions: [
          ...(result.assistantMessage.suggestedActions || []),
          ...(suggestedAction ? [suggestedAction] : []),
        ],
      }
      setMessages((prev) => [
        ...prev,
        ...(result.userMessage ? [result.userMessage] : []),
        assistantMsg,
      ])
      // Play TTS with start/pause/resume capabilities
      ttsPlayer.start(
        assistantMsg.id,
        assistantMsg.content,
        assistantMsg.audioBase64,
      )
    } catch (error) {
      console.error("Voice message failed:", error)
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: makeErrorMessage(error),
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 space-y-5 overflow-y-auto px-1 py-2"
      >
        {messages.map((message) => (
          <ChatMessageBubble key={message.id} message={message} />
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex gap-3">
            <Avatar className="size-8 shrink-0">
              <AvatarFallback className="bg-primary text-primary-foreground">
                <LandmarkIcon className="size-4" />
              </AvatarFallback>
            </Avatar>
            <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60"
                  style={{ animationDelay: `${i * 120}ms` }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="border-t border-border bg-background pt-3">
        <ChatComposer
          onSend={handleSend}
          onVoiceSend={handleVoiceSend}
          disabled={isTyping}
        />
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          NAGRIK AI can make mistakes. Always verify critical information from
          official sources.
        </p>
      </div>
    </div>
  )
}
