import type { ChatMessage, ChatSource } from "@/types"
import { apiPost } from "./_client"

export interface ChatAttachment {
  type: "image" | "document" | "audio"
  name: string
  base64_data: string
  mime_type: string
}

// Navigation action as returned by the backend
export interface BackendNavigationAction {
  action:
    | "open_scheme_page"
    | "open_comparison"
    | "open_application_form"
    | "open_complaint_status"
    | "open_profile"
    | "none"
  target_id?: string | null
  params?: Record<string, unknown>
}

// Rich source as returned by the backend
interface BackendSource {
  // Legacy fields some older responses may still send
  title?: string
  scheme_name?: string
  content?: string
  score?: number
  distance?: number

  // Rich fields from ChatSource schema
  scheme?: string
  ministry?: string
  department?: string
  source_file?: string
  source_url?: string
  page?: number | null
  snippet?: string
}

interface BackendChatResponse {
  session_id?: string
  reply?: string
  reply_text?: string
  message?: string
  answer?: string
  content?: string
  language?: string
  intent?: string
  reply_audio_base64?: string
  transcribed_text?: string
  sources?: BackendSource[]
  navigation?: BackendNavigationAction
  extracted_fields?: Record<string, unknown>
  [key: string]: unknown
}

function getResponseContent(response: BackendChatResponse): string {
  return (
    response.reply ??
    response.reply_text ??
    response.message ??
    response.answer ??
    response.content ??
    "Sorry, I couldn't generate a response."
  )
}

/**
 * Maps backend ChatSource objects to frontend ChatSource display objects.
 * Prefers rich fields (scheme, ministry, snippet) over legacy title/content.
 * Never exposes internal file-system paths.
 */
function mapSources(sources?: BackendSource[]): ChatSource[] | undefined {
  if (!sources || sources.length === 0) return undefined

  return sources
    .filter((s) => {
      // Skip sources that are purely noise
      const hasLabel =
        s.scheme ?? s.scheme_name ?? s.title ?? s.ministry ?? s.department
      return !!hasLabel
    })
    .map((s) => {
      // Build a human-readable label
      const label =
        s.scheme ??
        s.scheme_name ??
        s.title ??
        s.ministry ??
        s.department ??
        "Government Source"

      // Sub-label: ministry / department info
      const sublabel = [s.ministry, s.department]
        .filter(Boolean)
        .join(" — ") || undefined

      // Page ref
      const pageRef =
        s.page != null ? `Page ${s.page}` : undefined

      // Snippet — sanitise: do not show internal paths
      const rawSnippet = s.snippet ?? s.content
      const snippet =
        rawSnippet && !_isInternalPath(rawSnippet)
          ? rawSnippet
          : undefined

      // href — only expose genuine government URLs
      const href =
        s.source_url && _isExternalGovUrl(s.source_url)
          ? s.source_url
          : "#"

      return {
        label,
        sublabel,
        pageRef,
        snippet,
        href,
      } satisfies ChatSource
    })
}

/** Returns true if the string looks like an internal/local path. */
function _isInternalPath(text: string): boolean {
  return (
    text.includes(":\\") ||
    text.includes("/data/") ||
    text.includes("chroma") ||
    text.startsWith("./") ||
    text.startsWith("/app/") ||
    text.startsWith("data\\")
  )
}

/** Returns true only for http(s) URLs that look like official government sites. */
function _isExternalGovUrl(url: string): boolean {
  if (!url.startsWith("http")) return false
  if (_isInternalPath(url)) return false
  // Accept any real URL — the backend already filters to official gov sources.
  return true
}

// ─── sendMessage ─────────────────────────────────────────────────────────────

export async function sendMessage(
  userText: string,
  sessionId: string,
  citizenId: string = "frontend-citizen",
  language: string | null = null,
  attachment?: ChatAttachment,
): Promise<{
  message: ChatMessage
  navigation?: BackendNavigationAction
  intent?: string
  extractedFields?: Record<string, unknown>
}> {
  const response = await apiPost<BackendChatResponse>("/chat", {
    session_id: sessionId,
    citizen_id: citizenId,
    message: userText || null,
    language,
    attachments: attachment
      ? [
          {
            type: attachment.type,
            base64_data: attachment.base64_data,
            mime_type: attachment.mime_type,
          },
        ]
      : [],
  })

  return {
    message: {
      id: `msg-${Date.now()}`,
      role: "assistant",
      content: getResponseContent(response),
      timestamp: new Date().toISOString(),
      sources: mapSources(response.sources),
    },
    navigation: response.navigation ?? undefined,
    intent: response.intent ?? undefined,
    extractedFields: response.extracted_fields ?? undefined,
  }
}

// ─── sendVoiceMessage ─────────────────────────────────────────────────────────

export async function sendVoiceMessage(
  audioBase64: string,
  sessionId: string,
  citizenId: string = "frontend-citizen",
  language: string | null = null,
  audioMimeType: string = "audio/webm",
): Promise<{
  userMessage?: ChatMessage
  assistantMessage: ChatMessage
  navigation?: BackendNavigationAction
  intent?: string
}> {
  const response = await apiPost<BackendChatResponse>("/chat/voice", {
    session_id: sessionId,
    citizen_id: citizenId,
    audio_base64: audioBase64,
    audio_mime_type: audioMimeType,
    language,
  })

  const assistantMessage: ChatMessage = {
    id: `voice-assistant-${Date.now()}`,
    role: "assistant",
    content: response.reply_text || "",
    timestamp: new Date().toISOString(),
    sources: mapSources(response.sources),
    audioBase64: response.reply_audio_base64 || undefined,
  }

  return {
    userMessage: response.transcribed_text
      ? {
          id: `voice-user-${Date.now()}`,
          role: "user",
          content: response.transcribed_text,
          timestamp: new Date().toISOString(),
          isVoice: true,
        }
      : undefined,
    assistantMessage,
    navigation: response.navigation ?? undefined,
    intent: response.intent ?? undefined,
  }
}

function playBase64Audio(base64: string, mimeType: string) {
  try {
    const audio = new Audio(`data:${mimeType};base64,${base64}`)
    audio.play().catch((error) => {
      console.error("Could not play TTS audio:", error)
    })
  } catch (error) {
    console.error("Could not create TTS audio:", error)
  }
}

function speakBrowserText(text: string, lang?: string | null) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return
  try {
    window.speechSynthesis.cancel()
    const cleanText = text
      .replace(/[*_#`~\[\]()]/g, " ")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/\s+/g, " ")
      .trim()
    if (!cleanText) return

    const utterance = new SpeechSynthesisUtterance(cleanText.slice(0, 500))
    if (lang && lang.includes("hi")) {
      utterance.lang = "hi-IN"
    } else {
      utterance.lang = "en-IN"
    }
    utterance.rate = 1.05
    window.speechSynthesis.speak(utterance)
  } catch (err) {
    console.warn("Browser speech synthesis error:", err)
  }
}
