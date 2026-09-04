"use client"

import * as React from "react"
import { toast } from "sonner"
import { Loader2, Pencil, ShieldCheck } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useApp } from "@/context/app-provider"
import { updateProfile } from "@/services/profile-service"
import { formatDate, initials } from "@/lib/format"
import type { CitizenProfile } from "@/types"

export function ProfileOverview({ profile, onUpdate }: { profile: CitizenProfile; onUpdate: (p: CitizenProfile) => void }) {
  const { session } = useApp()
  const [editing, setEditing] = React.useState(false)
  const [form, setForm] = React.useState(profile)
  const [saving, setSaving] = React.useState(false)

  function startEditing() {
    // Seed the draft from the current profile at the moment editing begins,
    // rather than mirroring the prop into state on every render pass.
    setForm(profile)
    setEditing(true)
  }

  async function handleSave() {
    setSaving(true)
    const updated = await updateProfile(form)
    setSaving(false)
    setEditing(false)
    onUpdate(updated)
    toast.success("Profile updated")
  }

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <Avatar className="size-16">
              <AvatarFallback className="bg-primary text-lg text-primary-foreground">{initials(profile.name)}</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-base font-semibold">{profile.name}</h2>
              <p className="text-sm text-muted-foreground">Member since {formatDate(profile.memberSince)}</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {profile.aadhaarLinked && (
                  <Badge variant="outline" className="gap-1 text-[10px]"><ShieldCheck className="size-2.5" /> Aadhaar Linked</Badge>
                )}
                {profile.digilockerLinked && (
                  <Badge variant="outline" className="gap-1 text-[10px]"><ShieldCheck className="size-2.5" /> DigiLocker Linked</Badge>
                )}
              </div>
            </div>
          </div>
          <div className="w-full sm:w-48">
            <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
              <span>Profile completeness</span>
              <span>{profile.completeness}%</span>
            </div>
            <Progress value={profile.completeness} className="h-1.5" />
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Personal Details</h3>
          {!editing ? (
            <Button size="sm" variant="outline" className="gap-1.5" onClick={startEditing}>
              <Pencil className="size-3.5" /> Edit
            </Button>
          ) : (
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setForm(profile) }}>Cancel</Button>
              <Button size="sm" className="gap-1.5" onClick={handleSave} disabled={saving}>
                {saving && <Loader2 className="size-3.5 animate-spin" />} Save
              </Button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Full Name" value={form.name} editing={editing} onChange={(v) => setForm({ ...form, name: v })} />
          <Field label="Email" value={form.email} editing={editing} onChange={(v) => setForm({ ...form, email: v })} />
          <Field label="Phone" value={form.phone} editing={editing} onChange={(v) => setForm({ ...form, phone: v })} />
          <Field label="Date of Birth" value={form.dob} editing={editing} type="date" onChange={(v) => setForm({ ...form, dob: v })} />
          <Field label="Occupation" value={form.occupation ?? ""} editing={editing} onChange={(v) => setForm({ ...form, occupation: v })} />
          <Field
            label="Annual Income (₹)"
            value={String(form.income ?? "")}
            editing={editing}
            type="number"
            onChange={(v) => setForm({ ...form, income: Number(v) })}
          />
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Category</Label>
            {editing ? (
              <Select value={form.category ?? "General"} onValueChange={(v) => setForm({ ...form, category: v as CitizenProfile["category"] })}>
                <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["General", "OBC", "SC", "ST", "EWS"].map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm font-medium">{form.category}</p>
            )}
          </div>
          <Field
            label="Family Size"
            value={String(form.familySize ?? "")}
            editing={editing}
            type="number"
            onChange={(v) => setForm({ ...form, familySize: Number(v) })}
          />
          <div className="sm:col-span-2 space-y-1.5">
            <Label className="text-xs text-muted-foreground">Address</Label>
            {editing ? (
              <Input value={form.address.line1} onChange={(e) => setForm({ ...form, address: { ...form.address, line1: e.target.value } })} />
            ) : (
              <p className="text-sm font-medium">
                {form.address.line1}, {form.address.ward}, {form.address.district}, {form.address.state} - {form.address.pincode}
              </p>
            )}
          </div>
        </div>
      </Card>

      {session?.citizen && (
        <Card className="p-5">
          <h3 className="mb-1 text-sm font-semibold">Account</h3>
          <p className="text-sm text-muted-foreground">Citizen ID: {session.citizen.id}</p>
        </Card>
      )}
    </div>
  )
}

function Field({
  label,
  value,
  editing,
  onChange,
  type = "text",
}: {
  label: string
  value: string
  editing: boolean
  onChange: (v: string) => void
  type?: string
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      {editing ? (
        <Input type={type} value={value} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <p className="text-sm font-medium">{value || "-"}</p>
      )}
    </div>
  )
}
