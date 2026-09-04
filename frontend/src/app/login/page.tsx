"use client"

import * as React from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { LandmarkIcon, ShieldCheck, Sparkles, UserRound, Building2, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useApp } from "@/context/app-provider"
import type { UserRole } from "@/types"

function LoginPageInner() {
  const { login, session } = useApp()
  const router = useRouter()
  const params = useSearchParams()
  const initialPortal = params.get("portal") === "gov" ? "officer" : "citizen"

  const [role, setRole] = React.useState<UserRole>(initialPortal as UserRole)
  const [loading, setLoading] = React.useState<"form" | "demo" | null>(null)

  React.useEffect(() => {
    if (session) router.replace(session.role === "officer" ? "/gov" : "/")
  }, [session, router])

  async function handleLogin(e?: React.FormEvent) {
    e?.preventDefault()
    setLoading("form")
    await login(role)
    router.push(role === "officer" ? "/gov" : "/")
  }

  async function handleDemo() {
    setLoading("demo")
    await login(role)
    router.push(role === "officer" ? "/gov" : "/")
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <LandmarkIcon className="size-6" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">NAGRIK</h1>
          <p className="text-sm text-muted-foreground">Smart Civic Platform - digital services, made human.</p>
        </div>

        <Card className="p-6">
          <Tabs value={role} onValueChange={(v) => setRole(v as UserRole)} className="mb-5">
            <TabsList className="w-full">
              <TabsTrigger value="citizen" className="gap-1.5">
                <UserRound className="size-3.5" /> Citizen
              </TabsTrigger>
              <TabsTrigger value="officer" className="gap-1.5">
                <Building2 className="size-3.5" /> Government Officer
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="identifier">{role === "citizen" ? "Mobile number or Aadhaar-linked ID" : "Official email ID"}</Label>
              <Input
                id="identifier"
                placeholder={role === "citizen" ? "+91 98765 43210" : "officer@ulb.gov.in"}
                defaultValue={role === "citizen" ? "+91 98765 43210" : "anjali.mehta@ulb.gov.in"}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="otp">{role === "citizen" ? "OTP" : "Password"}</Label>
              <Input id="otp" type="password" placeholder="••••••" defaultValue="123456" />
            </div>
            <Button type="submit" className="w-full" disabled={loading !== null}>
              {loading === "form" && <Loader2 className="size-4 animate-spin" />}
              {role === "citizen" ? "Verify & Continue" : "Sign in to Officer Portal"}
            </Button>
          </form>

          <div className="my-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <Button variant="secondary" className="w-full gap-2" onClick={handleDemo} disabled={loading !== null}>
            {loading === "demo" ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Continue in Demo Mode
          </Button>
          <p className="mt-3 flex items-center justify-center gap-1.5 text-center text-xs text-muted-foreground">
            <ShieldCheck className="size-3.5" /> No real credentials needed - explore with sample data.
          </p>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          Built for Smart India Hackathon - NAGRIK prototype. All data shown is illustrative.
        </p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <React.Suspense fallback={null}>
      <LoginPageInner />
    </React.Suspense>
  )
}
