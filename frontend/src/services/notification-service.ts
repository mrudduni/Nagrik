import type { AppNotification } from "@/types"
import { MOCK_NOTIFICATIONS } from "@/lib/mock/notifications"
import { apiGet, apiPost } from "./_client"

const mockStore: AppNotification[] = [...MOCK_NOTIFICATIONS]
const DEFAULT_CITIZEN_ID = "cz-10234"

interface BackendCrawlerNotification {
  scheme_id: string
  scheme_name: string
  summary: string
  source_url: string
  message: string
  created_at: string
  is_read: boolean
  match_reason: string
}

interface CrawlerNotificationResponse {
  citizen_id: string
  unread_count: number
  notifications: BackendCrawlerNotification[]
}

export async function listNotifications(citizenId: string = DEFAULT_CITIZEN_ID): Promise<AppNotification[]> {
  try {
    const res = await apiGet<CrawlerNotificationResponse>(
      `/api/crawler/notifications?citizen_id=${encodeURIComponent(citizenId)}&unread_only=false`
    )

    const crawlerNotifs: AppNotification[] = (res.notifications || []).map((n) => ({
      id: `crawler-${n.scheme_id}`,
      type: "scheme-recommendation",
      title: `New Scheme: ${n.scheme_name}`,
      message: n.message || n.summary,
      timestamp: n.created_at,
      read: n.is_read,
      href: `/schemes/${n.scheme_id}`,
    }))

    // Combine crawler notifications with other mock notifications
    const all = [...crawlerNotifs, ...mockStore]
    return all.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1))
  } catch {
    // If backend is unreachable, gracefully fall back to local store
    return [...mockStore].sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1))
  }
}

export async function markAsRead(id: string, citizenId: string = DEFAULT_CITIZEN_ID): Promise<void> {
  const local = mockStore.find((x) => x.id === id)
  if (local) local.read = true

  if (id.startsWith("crawler-")) {
    const schemeId = id.replace("crawler-", "")
    try {
      await apiPost("/api/crawler/notifications/read", {
        citizen_id: citizenId,
        scheme_ids: [schemeId],
      })
    } catch {
      // Best-effort
    }
  }
}

export async function markAllAsRead(citizenId: string = DEFAULT_CITIZEN_ID): Promise<void> {
  mockStore.forEach((n) => (n.read = true))

  try {
    await apiPost("/api/crawler/notifications/read", {
      citizen_id: citizenId,
      scheme_ids: [],
    })
  } catch {
    // Best-effort
  }
}

