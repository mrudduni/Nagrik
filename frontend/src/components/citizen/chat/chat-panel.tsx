"use client"

import * as React from "react"
import { LandmarkIcon } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { SUGGESTED_QUERIES } from "@/lib/mock/chat"
import { sendMessage } from "@/services/chat-service"
import type { ChatMessage } from "@/types"
import { ChatMessageBubble } from "./chat-message-bubble"
import { ChatComposer, type PendingAttachment } from "./chat-composer"

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Namaste! I'm your NAGRIK AI assistant. I can help you discover government schemes, check eligibility, fill out applications, track their status, or report a civic issue - in text or voice. What would you like help with today?",
  // No timestamp: this message is server-rendered, and a generated "now" would
  // differ between server and client and break hydration.
  timestamp: "",
}

export function ChatPanel() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([WELCOME_MESSAGE])
  const [isTyping, setIsTyping] = React.useState(false)
  const scrollRef = React.useRef<HTMLDivElement>(null)
  const idCounter = React.useRef(0)

  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isTyping])

  async function handleSend(text: string, attachment?: PendingAttachment) {
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
    const reply = await sendMessage(text)
    setIsTyping(false)
    setMessages((prev) => [...prev, reply])
  }

  const showSuggestions = messages.length === 1

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-1 py-2">
        {messages.map((m) => (
          <ChatMessageBubble key={m.id} message={m} />
        ))}

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

        {showSuggestions && (
          <div className="flex flex-wrap gap-2 pl-11">
            {SUGGESTED_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => handleSend(q)}
                className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-border bg-background pt-3">
        <ChatComposer onSend={handleSend} disabled={isTyping} />
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          NAGRIK AI can make mistakes. Always verify critical information from official sources.
        </p>
      </div>
    </div>
  )
}
