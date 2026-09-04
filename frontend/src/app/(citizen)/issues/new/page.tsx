"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Loader2,
  Locate,
  Mic,
  Sparkles,
  Square,
  X,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { PageHeader } from "@/components/shared/page-header"
import { StatusBadge } from "@/components/shared/status-badge"
import { useApp } from "@/context/app-provider"
import { classifyIssueText, reportIssue, severityMeta, type ClassificationPreview } from "@/services/issue-service"
import type { IssueCategory, IssueSeverity } from "@/types"

const CATEGORIES: IssueCategory[] = [
  "Roads & Potholes",
  "Water Supply",
  "Electricity",
  "Sanitation & Garbage",
  "Street Lighting",
  "Drainage",
  "Public Safety",
  "Encroachment",
  "Parks & Environment",
  "Noise Pollution",
]

export default function ReportIssuePage() {
  const router = useRouter()
  const { session } = useApp()
  const citizen = session?.citizen

  const [title, setTitle] = React.useState("")
  const [description, setDescription] = React.useState("")
  const [address, setAddress] = React.useState("")
  const [isLocating, setIsLocating] = React.useState(false)
  const [isRecording, setIsRecording] = React.useState(false)
  const [imageAttached, setImageAttached] = React.useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = React.useState(false)
  const [classification, setClassification] = React.useState<ClassificationPreview | null>(null)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  function handleLocate() {
    setIsLocating(true)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const addr = citizen
            ? `Near ${citizen.address.line1}, ${citizen.address.ward}`
            : `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`
          setAddress(addr)
          setIsLocating(false)
          toast.success("Location detected")
        },
        () => {
          // Geolocation denied — fall back to profile address
          setAddress(citizen ? `Near ${citizen.address.line1}, ${citizen.address.ward}` : "")
          setIsLocating(false)
          toast.success("Location set from profile")
        },
      )
    } else {
      setTimeout(() => {
        setAddress(citizen ? `Near ${citizen.address.line1}, ${citizen.address.ward}` : "")
        setIsLocating(false)
        toast.success("Location set from profile")
      }, 600)
    }
  }

  async function handleVoiceDescribe() {
    if (!navigator.mediaDevices?.getUserMedia) {
      toast.error("Microphone not supported in this browser")
      return
    }
    setIsRecording(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find(
        (t) => MediaRecorder.isTypeSupported(t),
      ) || ""
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)
      const chunks: Blob[] = []
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data) }
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" })
        if (blob.size === 0) { setIsRecording(false); return }
        try {
          const reader = new FileReader()
          const base64: string = await new Promise((res, rej) => {
            reader.onload = () => res((reader.result as string).split(",")[1])
            reader.onerror = rej
            reader.readAsDataURL(blob)
          })
          const { sendVoiceMessage } = await import("@/services/chat-service")
          const sessionId = sessionStorage.getItem("nagrik.chat.session_id") ?? `sess_${Date.now()}`
          const result = await sendVoiceMessage(base64, sessionId, citizen?.id ?? "frontend-citizen")
          const transcript = result.userMessage?.content ?? result.assistantMessage.content ?? ""
          if (transcript) {
            setDescription((prev) => prev ? `${prev} ${transcript}` : transcript)
            if (!title && transcript.length < 100) setTitle(transcript.slice(0, 80))
            toast.success("Voice transcribed")
          }
        } catch (err) {
          console.error("STT error:", err)
          toast.error("Could not transcribe voice. Please type the description.")
        } finally {
          setIsRecording(false)
        }
      }
      recorder.start()
      // Auto-stop after 10 seconds
      setTimeout(() => {
        if (recorder.state !== "inactive") recorder.stop()
      }, 10000)
    } catch {
      setIsRecording(false)
      toast.error("Microphone access denied. Please allow and try again.")
    }
  }

  function handleFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) setImageAttached(file.name)
    e.target.value = ""
  }

  async function handleAnalyze() {
    if (!description.trim()) {
      toast.error("Please describe the issue first")
      return
    }
    setIsAnalyzing(true)
    const result = await classifyIssueText(description)
    setIsAnalyzing(false)
    setClassification(result)
  }

  async function handleSubmit() {
    if (!citizen || !classification || !title.trim()) return
    setIsSubmitting(true)
    try {
      const issue = await reportIssue({
        citizenId: citizen.id,
        title: title.trim(),
        description,
        category: classification.category,
        severity: classification.suggestedSeverity,
        department: classification.suggestedDepartment,
        address,
      })
      toast.success("Issue reported successfully", { description: `Reference: ${issue.referenceNumber}` })
      router.push(`/issues/${issue.id}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
      <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChosen} />
      <PageHeader
        breadcrumbs={[{ label: "Civic Issues", href: "/issues" }, { label: "Report" }]}
        title="Report a Civic Issue"
        description="Describe the problem in your own words, in text or voice, and NAGRIK AI will route it to the right department."
      />

      <div className="space-y-5">
        <Card className="space-y-4 p-5">
          <div className="space-y-1.5">
            <Label htmlFor="title">Title</Label>
            <Input id="title" placeholder="e.g. Pothole near market entrance" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="description">Describe the issue</Label>
              <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs" onClick={handleVoiceDescribe} disabled={isRecording}>
                {isRecording ? <Square className="size-3 animate-pulse fill-current" /> : <Mic className="size-3" />}
                {isRecording ? "Listening..." : "Describe with Voice"}
              </Button>
            </div>
            <Textarea
              id="description"
              rows={4}
              placeholder="What's the issue? Where exactly is it? How long has it been there?"
              value={description}
              onChange={(e) => {
                setDescription(e.target.value)
                setClassification(null)
              }}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Photo evidence</Label>
            {imageAttached ? (
              <div className="flex w-fit items-center gap-2 rounded-lg border border-border bg-muted px-3 py-2 text-sm">
                <Camera className="size-4 text-muted-foreground" /> {imageAttached}
                <button onClick={() => setImageAttached(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="size-3.5" />
                </button>
              </div>
            ) : (
              <Button variant="outline" className="gap-2" onClick={() => fileInputRef.current?.click()}>
                <Camera className="size-4" /> Attach Photo
              </Button>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="address">Location</Label>
            <div className="flex gap-2">
              <Input id="address" placeholder="Address or landmark" value={address} onChange={(e) => setAddress(e.target.value)} className="flex-1" />
              <Button variant="outline" className="shrink-0 gap-1.5" onClick={handleLocate} disabled={isLocating}>
                {isLocating ? <Loader2 className="size-4 animate-spin" /> : <Locate className="size-4" />}
                Detect
              </Button>
            </div>
          </div>
        </Card>

        {!classification ? (
          <Button className="w-full gap-1.5" onClick={handleAnalyze} disabled={isAnalyzing}>
            {isAnalyzing ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            {isAnalyzing ? "Analyzing with AI..." : "Analyze with AI"}
          </Button>
        ) : (
          <Card className="space-y-4 border-info/30 bg-info/5 p-5">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="size-4 text-info" /> AI Classification Preview
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Category</Label>
                <Select value={classification.category} onValueChange={(v) => setClassification({ ...classification, category: v as IssueCategory })}>
                  <SelectTrigger className="w-full bg-background"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Severity</Label>
                <Select value={classification.suggestedSeverity} onValueChange={(v) => setClassification({ ...classification, suggestedSeverity: v as IssueSeverity })}>
                  <SelectTrigger className="w-full bg-background"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(["low", "medium", "high", "critical"] as IssueSeverity[]).map((s) => (
                      <SelectItem key={s} value={s}>{severityMeta(s).label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="gap-1 bg-background text-foreground border-border">
                <CheckCircle2 className="size-3" /> {Math.round(classification.confidence * 100)}% confidence
              </Badge>
              <StatusBadge label={`Routed to: ${classification.suggestedDepartment}`} tone="info" />
            </div>
            {classification.suggestedSeverity === "critical" && (
              <div className="flex items-start gap-2 rounded-lg bg-destructive/10 p-3 text-xs text-destructive">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
                This looks urgent. Consider using Call Nagrik for immediate assistance in addition to filing this report.
              </div>
            )}
          </Card>
        )}

        {classification && (
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setClassification(null)}>Re-analyze</Button>
            <Button onClick={handleSubmit} disabled={!title.trim() || isSubmitting} className="gap-1.5">
              {isSubmitting && <Loader2 className="size-4 animate-spin" />}
              Submit Report
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
