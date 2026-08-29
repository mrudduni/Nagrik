import type { AppNotification } from "@/types"
import { MOCK_NOTIFICATIONS } from "@/lib/mock/notifications"
import { request } from "./_client"

const store: AppNotification[] = [...MOCK_NOTIFICATIONS]

export async function listNotifications(): Promise<AppNotification[]> {
  return request(() => [...store].sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1)), 250)
}

export async function markAsRead(id: string): Promise<void> {
  return request(() => {
    const n = store.find((x) => x.id === id)
    if (n) n.read = true
  }, 150)
}

export async function markAllAsRead(): Promise<void> {
  return request(() => {
    store.forEach((n) => (n.read = true))
  }, 200)
}
