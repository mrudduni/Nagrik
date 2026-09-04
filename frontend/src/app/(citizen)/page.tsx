"use client"

import { useApp } from "@/context/app-provider"
import { ChatPanel } from "@/components/citizen/chat/chat-panel"
import { HomeWidgets } from "@/components/citizen/home/home-widgets"

export default function CitizenHomePage() {
  const { session, t } = useApp()
  const firstName = session?.citizen?.name.split(" ")[0]

  return (
    <div className="mx-auto flex max-w-7xl flex-col px-4 py-4 sm:px-6 lg:h-[calc(100svh-4rem)] lg:flex-row lg:gap-6 lg:py-6">
      <div className="flex h-[70svh] min-h-[420px] flex-col lg:h-auto lg:min-h-0 lg:flex-1">
        <div className="mb-3 shrink-0">
          <h1 className="text-lg font-semibold tracking-tight">
            {firstName ? `${t.chat.greeting}, ${firstName}` : t.chat.greeting} <span className="wave">👋</span>
          </h1>
          <p className="text-sm text-muted-foreground">{t.chat.subtitle}</p>
        </div>
        <div className="min-h-0 flex-1">
          <ChatPanel />
        </div>
      </div>
      <div className="mt-6 w-full shrink-0 lg:mt-0 lg:w-80 lg:overflow-y-auto">
        <HomeWidgets />
      </div>
    </div>
  )
}
