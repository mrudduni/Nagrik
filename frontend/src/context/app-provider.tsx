"use client"

import * as React from "react"
import type { AppNotification, AuthSession, LanguageCode, UserRole } from "@/types"
import * as authService from "@/services/auth-service"
import * as notificationService from "@/services/notification-service"
import { getTranslation, type TranslationDictionary } from "@/lib/i18n"

interface AppContextValue {
  session: AuthSession | null
  isAuthLoading: boolean
  login: (role: UserRole) => Promise<void>
  logout: () => void
  language: LanguageCode
  setLanguage: (lang: LanguageCode) => void
  t: TranslationDictionary
  translations: TranslationDictionary
  notifications: AppNotification[]
  unreadCount: number
  refreshNotifications: () => Promise<void>
  markNotificationRead: (id: string) => Promise<void>
  markAllNotificationsRead: () => Promise<void>
}

const AppContext = React.createContext<AppContextValue | null>(null)

const SESSION_KEY = "nagrik.session.role"
const LANGUAGE_KEY = "nagrik.language"

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = React.useState<AuthSession | null>(null)
  const [isAuthLoading, setIsAuthLoading] = React.useState(true)
  const [language, setLanguageState] = React.useState<LanguageCode>("en")
  const [notifications, setNotifications] = React.useState<AppNotification[]>([])

  // Restoring the persisted session/language must happen *after* mount: reading
  // localStorage during render would make the server and client markup diverge
  // and break hydration. The setState here is therefore intentional.
  React.useEffect(() => {
    const storedRole = typeof window !== "undefined" ? (window.localStorage.getItem(SESSION_KEY) as UserRole | null) : null
    const storedLang = typeof window !== "undefined" ? (window.localStorage.getItem(LANGUAGE_KEY) as LanguageCode | null) : null
    // eslint-disable-next-line react-hooks/set-state-in-effect -- hydration-safe restore, see above
    if (storedLang) setLanguageState(storedLang)
    if (storedRole) {
      authService.login(storedRole).then((s) => {
        setSession(s)
        setIsAuthLoading(false)
      })
    } else {
      setIsAuthLoading(false)
    }
  }, [])

  const refreshNotifications = React.useCallback(async () => {
    const list = await notificationService.listNotifications()
    setNotifications(list)
  }, [])

  // Load the notification feed whenever a session is established. This is a
  // fetch-on-mount; when the FastAPI backend lands this becomes a subscription.
  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- async data load, resolves after await
    if (session) refreshNotifications()
  }, [session, refreshNotifications])

  const login = React.useCallback(async (role: UserRole) => {
    const s = await authService.login(role)
    setSession(s)
    if (typeof window !== "undefined") window.localStorage.setItem(SESSION_KEY, role)
  }, [])

  const logout = React.useCallback(() => {
    setSession(null)
    setNotifications([])
    if (typeof window !== "undefined") window.localStorage.removeItem(SESSION_KEY)
  }, [])

  const setLanguage = React.useCallback((lang: LanguageCode) => {
    setLanguageState(lang)
    if (typeof window !== "undefined") window.localStorage.setItem(LANGUAGE_KEY, lang)
  }, [])

  const markNotificationRead = React.useCallback(async (id: string) => {
    await notificationService.markAsRead(id)
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)))
  }, [])

  const markAllNotificationsRead = React.useCallback(async () => {
    await notificationService.markAllAsRead()
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length
  const translations = React.useMemo(() => getTranslation(language), [language])

  const value: AppContextValue = {
    session,
    isAuthLoading,
    login,
    logout,
    language,
    setLanguage,
    t: translations,
    translations,
    notifications,
    unreadCount,
    refreshNotifications,
    markNotificationRead,
    markAllNotificationsRead,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = React.useContext(AppContext)
  if (!ctx) throw new Error("useApp must be used within AppProvider")
  return ctx
}
