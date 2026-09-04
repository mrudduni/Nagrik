"use client"

import * as React from "react"
import { useSearchParams } from "next/navigation"
import { toast } from "sonner"
import { Check, Globe, ShieldCheck } from "lucide-react"
import { PageHeader } from "@/components/shared/page-header"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { ProfileOverview } from "@/components/citizen/profile/profile-overview"
import { VaultGrid } from "@/components/citizen/profile/vault-grid"
import { ServiceHistory } from "@/components/citizen/profile/service-history"
import { LANGUAGES } from "@/lib/mock/languages"
import { useApp } from "@/context/app-provider"
import { getProfile } from "@/services/profile-service"
import type { CitizenProfile } from "@/types"

function ProfilePageInner() {
  const searchParams = useSearchParams()
  const { language, setLanguage } = useApp()
  const [profile, setProfile] = React.useState<CitizenProfile | null>(null)
  const tab = searchParams.get("tab") ?? "profile"

  React.useEffect(() => {
    getProfile().then(setProfile)
  }, [])

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
      <PageHeader title="Profile & Digital Twin" description="Manage your identity, preferences, documents, and service history in one place." />

      <Tabs defaultValue={tab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
          <TabsTrigger value="vault">Document Vault</TabsTrigger>
          <TabsTrigger value="history">Service History</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          {profile ? <ProfileOverview profile={profile} onUpdate={setProfile} /> : <Skeleton className="h-96 w-full" />}
        </TabsContent>

        <TabsContent value="preferences" className="space-y-4">
          <Card className="p-5">
            <h3 className="mb-1 flex items-center gap-2 text-sm font-semibold">
              <Globe className="size-4" /> Language
            </h3>
            <p className="mb-4 text-xs text-muted-foreground">Choose the language for the AI assistant, notifications, and interface.</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm transition-colors ${
                    language === lang.code ? "border-primary bg-primary/5 text-foreground" : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {lang.nativeLabel}
                  {language === lang.code && <Check className="size-3.5 text-primary" />}
                </button>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck className="size-4" /> Notification Preferences
            </h3>
            <div className="space-y-4">
              {[
                { id: "app-updates", label: "Application status updates", defaultOn: true },
                { id: "issue-updates", label: "Civic issue updates", defaultOn: true },
                { id: "scheme-reco", label: "New scheme recommendations", defaultOn: true },
                { id: "deadlines", label: "Deadline reminders", defaultOn: false },
              ].map((pref) => (
                <div key={pref.id} className="flex items-center justify-between">
                  <Label htmlFor={pref.id} className="text-sm font-normal">{pref.label}</Label>
                  <Switch id={pref.id} defaultChecked={pref.defaultOn} onCheckedChange={() => toast.success("Preference updated")} />
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="vault">
          <VaultGrid />
        </TabsContent>

        <TabsContent value="history">
          <ServiceHistory />
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default function ProfilePage() {
  return (
    <React.Suspense fallback={null}>
      <ProfilePageInner />
    </React.Suspense>
  )
}
