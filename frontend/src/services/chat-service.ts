import type { ChatMessage } from "@/types"
import { CANNED_RESPONSES, DEFAULT_RESPONSE } from "@/lib/mock/chat"
import { request } from "./_client"

let counter = 1000

export async function sendMessage(userText: string): Promise<ChatMessage> {
  const match = CANNED_RESPONSES.find((r) => r.match.test(userText))
  return request(
    () => ({
      id: `msg-${counter++}`,
      role: "assistant" as const,
      content: match?.content ?? DEFAULT_RESPONSE,
      timestamp: new Date().toISOString(),
      sources: match?.sources,
      suggestedActions: match?.suggestedActions,
    }),
    1200,
  )
}
