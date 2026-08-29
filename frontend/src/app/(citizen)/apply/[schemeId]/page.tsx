"use client"

import * as React from "react"
import { useParams, useRouter } from "next/navigation"
import { toast } from "sonner"
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  Mic,
  ShieldCheck,
  Sparkles,
  Square,
  Upload,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { PageHeader } from "@/components/shared/page-header"
import { ErrorState } from "@/components/shared/error-state"
import { ApplyStepper } from "@/components/citizen/apply/apply-stepper"
import { DynamicField } from "@/components/citizen/apply/dynamic-field"
import { useApp } from "@/context/app-provider"
import { getScheme, checkEligibility } from "@/services/scheme-service"
import { createApplication, saveDraftApplication, uploadDocument } from "@/services/application-service"
import { generateApplicationForm, getPrefillValue } from "@/lib/application-form-generator"
import type { CitizenProfile, DynamicFormSection, EligibilityResult, Scheme } from "@/types"
import { cn } from "@/lib/utils"

const STEPS = [
  { id: "eligibility", label: "Eligibility" },
  { id: "details", label: "Details" },
  { id: "documents", label: "Documents" },
  { id: "review", label: "Review" },
]

const VOICE_SAMPLE_ANSWERS: Record<string, string> = {
  address: "24, Green Park Extension, Ward 12, South Delhi, Delhi - 110016",
  loanAmount: "2500000",
  landholdingAcres: "2.5",
  landRecordId: "DL-KH-33210",
  institutionName: "Delhi Technological University",
  courseName: "B.Tech Computer Science",
  businessName: "Kansal Agro Traders",
  businessPlan: "Setting up a small-scale organic produce distribution unit serving 3 local markets.",
  bankAccountNumber: "038501012345",
  ifscCode: "SBIN0007621",
  rooftopArea: "420",
}

export default function ApplyPage() {
  const params = useParams<{ schemeId: string }>()
  const router = useRouter()
  const { session } = useApp()
  const citizen = session?.citizen

  const [scheme, setScheme] = React.useState<Scheme | null | undefined>(undefined)
  const [eligibility, setEligibility] = React.useState<EligibilityResult | null>(null)
  const [errors, setErrors] = React.useState<Record<string, string>>({})
  const [stepIndex, setStepIndex] = React.useState(0)
  const [isRecording, setIsRecording] = React.useState(false)
  const [uploadedDocs, setUploadedDocs] = React.useState<Record<string, string>>({})
  const [confirmed, setConfirmed] = React.useState(false)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const pendingDocRef = React.useRef<string | null>(null)

  React.useEffect(() => {
    getScheme(params.schemeId).then((s) => setScheme(s ?? null))
  }, [params.schemeId])

  React.useEffect(() => {
    if (scheme && citizen) checkEligibility(scheme.id, citizen).then(setEligibility)
  }, [scheme, citizen])

  // The form structure and its profile prefills are derived from the scheme and
  // the citizen - they are not independent state. Only the citizen's own edits
  // and AI/voice fills are tracked as state, and merged over the prefills.
  const sections: DynamicFormSection[] = React.useMemo(
    () => (scheme && citizen ? generateApplicationForm(scheme) : []),
    [scheme, citizen],
  )

  const initialValues = React.useMemo(() => {
    const initial: Record<string, string> = {}
    if (!citizen) return initial
    sections.forEach((sec) =>
      sec.fields.forEach((f) => {
        initial[f.id] = f.prefillFromProfile ? getPrefillValue(f, citizen as CitizenProfile) : ""
      }),
    )
    return initial
  }, [sections, citizen])

  const [edits, setEdits] = React.useState<Record<string, string>>({})
  const [voiceConfidence, setVoiceConfidence] = React.useState<Record<string, number>>({})
  const values = React.useMemo(() => ({ ...initialValues, ...edits }), [initialValues, edits])

  if (scheme === undefined || !citizen) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-6 sm:px-6">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (scheme === null) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <ErrorState title="Scheme not found" onRetry={() => router.push("/services")} />
      </div>
    )
  }

  function setFieldValue(id: string, value: string) {
    setEdits((prev) => ({ ...prev, [id]: value }))
    setErrors((prev) => {
      if (!prev[id]) return prev
      const next = { ...prev }
      delete next[id]
      return next
    })
  }

  function validateDetailsStep(): boolean {
    const nextErrors: Record<string, string> = {}
    sections.forEach((sec) => sec.fields.forEach((f) => {
      if (f.required && !values[f.id]?.trim()) nextErrors[f.id] = "This field is required"
    }))
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      toast.error(`${Object.keys(nextErrors).length} field(s) need your attention`, {
        description: "Please fill in the missing required information.",
      })
      return false
    }
    return true
  }

  function simulateVoiceFill() {
    setIsRecording(true)
    setTimeout(() => {
      setIsRecording(false)

      // Computed outside the state updaters: updater functions must be pure,
      // and React invokes them twice in development StrictMode.
      const filled: string[] = []
      const newEdits: Record<string, string> = {}
      const newConfidence: Record<string, number> = {}
      sections.forEach((sec) =>
        sec.fields.forEach((f) => {
          if (!values[f.id] && VOICE_SAMPLE_ANSWERS[f.id]) {
            newEdits[f.id] = VOICE_SAMPLE_ANSWERS[f.id]
            newConfidence[f.id] = 0.88
            filled.push(f.label)
          }
        }),
      )

      if (filled.length > 0) {
        setEdits((prev) => ({ ...prev, ...newEdits }))
        setVoiceConfidence((prev) => ({ ...prev, ...newConfidence }))
      }

      if (filled.length > 0) {
        toast.success(`Filled ${filled.length} field(s) from your voice input`, { description: filled.join(", ") })
      } else {
        toast.info("No matching fields detected to fill from voice.")
      }
    }, 1800)
  }

  function triggerUpload(docName: string) {
    pendingDocRef.current = docName
    fileInputRef.current?.click()
  }

  function handleFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    const docName = pendingDocRef.current
    if (file && docName) {
      setUploadedDocs((prev) => ({ ...prev, [docName]: file.name }))
      toast.success(`${docName} uploaded`, { description: file.name })
    }
    e.target.value = ""
  }

  async function handleSaveDraft() {
    if (!citizen || !scheme) return
    await saveDraftApplication({ citizenId: citizen.id, schemeId: scheme.id, formData: values })
    toast.success("Draft saved", { description: "You can continue this application anytime from My Applications." })
    router.push("/applications")
  }

  async function handleSubmit() {
    if (!citizen || !scheme || !confirmed) return
    setIsSubmitting(true)
    try {
      const app = await createApplication({ citizenId: citizen.id, schemeId: scheme.id, formData: values })
      for (const docName of Object.keys(uploadedDocs)) {
        await uploadDocument(app.id, docName)
      }
      toast.success("Application submitted successfully!", { description: `Reference number: ${app.referenceNumber}` })
      router.push(`/applications/${app.id}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const requiredDocs = scheme.documentsRequired
  const uploadedCount = Object.keys(uploadedDocs).length

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileChosen} />
      <PageHeader
        breadcrumbs={[{ label: "Government Services", href: "/services" }, { label: scheme.title, href: `/services/${scheme.id}` }, { label: "Apply" }]}
        title="AI Application Assistant"
        description={scheme.title}
      />

      <Card className="mb-6 p-5">
        <ApplyStepper steps={STEPS} currentIndex={stepIndex} />
      </Card>

      {stepIndex === 0 && eligibility && (
        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-4 flex items-center gap-3">
              <div className={cn("flex size-11 items-center justify-center rounded-full", eligibility.status === "not-eligible" ? "bg-destructive/10" : "bg-success/10")}>
                {eligibility.status === "not-eligible" ? (
                  <AlertCircle className="size-5 text-destructive" />
                ) : (
                  <CheckCircle2 className="size-5 text-success" />
                )}
              </div>
              <div>
                <p className="text-sm font-semibold">
                  {eligibility.status === "eligible" && "You appear eligible for this scheme"}
                  {eligibility.status === "partial" && "You may be partially eligible"}
                  {eligibility.status === "not-eligible" && "You may not meet all eligibility criteria"}
                </p>
                <p className="text-xs text-muted-foreground">AI match score: {eligibility.matchScore}%</p>
              </div>
            </div>
            <div className="space-y-2">
              {eligibility.reasons.map((r, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <CheckCircle2 className={cn("mt-0.5 size-3.5 shrink-0", r.met ? "text-success" : "text-muted-foreground")} />
                  <span className="text-muted-foreground">{r.explanation}</span>
                </div>
              ))}
            </div>
            {eligibility.status === "not-eligible" && (
              <p className="mt-4 rounded-lg bg-warning/10 p-3 text-xs text-warning-foreground">
                You can still proceed - a case officer will do a final manual verification, and some criteria may not be fully reflected in your profile.
              </p>
            )}
          </Card>
          <div className="flex justify-end">
            <Button onClick={() => setStepIndex(1)} className="gap-1.5">
              Continue to Details <ArrowRight className="size-4" />
            </Button>
          </div>
        </div>
      )}

      {stepIndex === 1 && (
        <div className="space-y-5">
          <Card className="flex items-center justify-between gap-3 border-info/30 bg-info/5 p-4">
            <div className="flex items-center gap-2.5 text-xs text-foreground">
              <Sparkles className="size-4 text-info shrink-0" />
              Answer out loud and I&apos;ll fill in the remaining blank fields for you.
            </div>
            <Button size="sm" variant="outline" className="shrink-0 gap-1.5" onClick={simulateVoiceFill} disabled={isRecording}>
              {isRecording ? <Square className="size-3.5 animate-pulse fill-current" /> : <Mic className="size-3.5" />}
              {isRecording ? "Listening..." : "Fill with Voice"}
            </Button>
          </Card>

          {sections.map((section) => (
            <Card key={section.id} className="space-y-4 p-5">
              <div>
                <h3 className="text-sm font-semibold">{section.title}</h3>
                {section.description && <p className="text-xs text-muted-foreground">{section.description}</p>}
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {section.fields.map((field) => (
                  <div key={field.id} className={cn(field.type === "textarea" && "sm:col-span-2")}>
                    <DynamicField
                      field={voiceConfidence[field.id] ? { ...field, aiConfidence: voiceConfidence[field.id] } : field}
                      value={values[field.id] ?? ""}
                      onChange={(v) => setFieldValue(field.id, v)}
                      error={errors[field.id]}
                    />
                  </div>
                ))}
              </div>
            </Card>
          ))}

          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStepIndex(0)} className="gap-1.5">
              <ArrowLeft className="size-4" /> Back
            </Button>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleSaveDraft}>Save Draft</Button>
              <Button
                onClick={() => {
                  if (validateDetailsStep()) setStepIndex(2)
                }}
                className="gap-1.5"
              >
                Continue to Documents <ArrowRight className="size-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {stepIndex === 2 && (
        <div className="space-y-5">
          <Card className="p-5">
            <h3 className="mb-1 text-sm font-semibold">Upload Required Documents</h3>
            <p className="mb-4 text-xs text-muted-foreground">{uploadedCount} of {requiredDocs.length} documents uploaded</p>
            <div className="space-y-2">
              {requiredDocs.map((doc) => {
                const uploaded = uploadedDocs[doc]
                return (
                  <div key={doc} className="flex items-center justify-between gap-3 rounded-lg border border-border p-3">
                    <div className="flex items-center gap-2.5">
                      <FileText className="size-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{doc}</p>
                        {uploaded && <p className="text-xs text-muted-foreground">{uploaded}</p>}
                      </div>
                    </div>
                    {uploaded ? (
                      <span className="flex items-center gap-1 text-xs font-medium text-success">
                        <CheckCircle2 className="size-3.5" /> Uploaded
                      </span>
                    ) : (
                      <Button size="sm" variant="outline" className="gap-1.5" onClick={() => triggerUpload(doc)}>
                        <Upload className="size-3.5" /> Upload
                      </Button>
                    )}
                  </div>
                )
              })}
            </div>
          </Card>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStepIndex(1)} className="gap-1.5">
              <ArrowLeft className="size-4" /> Back
            </Button>
            <Button onClick={() => setStepIndex(3)} className="gap-1.5">
              Continue to Review <ArrowRight className="size-4" />
            </Button>
          </div>
        </div>
      )}

      {stepIndex === 3 && (
        <div className="space-y-5">
          {sections.map((section) => (
            <Card key={section.id} className="p-5">
              <h3 className="mb-3 text-sm font-semibold">{section.title}</h3>
              <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {section.fields.map((f) => (
                  <div key={f.id}>
                    <dt className="text-xs text-muted-foreground">{f.label}</dt>
                    <dd className="text-sm font-medium">{values[f.id] || <span className="text-muted-foreground">Not provided</span>}</dd>
                  </div>
                ))}
              </dl>
            </Card>
          ))}
          <Card className="p-5">
            <h3 className="mb-3 text-sm font-semibold">Documents</h3>
            <ul className="space-y-1.5 text-sm">
              {requiredDocs.map((doc) => (
                <li key={doc} className="flex items-center gap-2">
                  {uploadedDocs[doc] ? (
                    <CheckCircle2 className="size-3.5 text-success" />
                  ) : (
                    <AlertCircle className="size-3.5 text-warning" />
                  )}
                  {doc} {!uploadedDocs[doc] && <span className="text-xs text-muted-foreground">(pending - can upload later)</span>}
                </li>
              ))}
            </ul>
          </Card>
          <Card className="flex items-start gap-3 p-5">
            <Checkbox id="confirm" checked={confirmed} onCheckedChange={(v) => setConfirmed(!!v)} className="mt-0.5" />
            <Label htmlFor="confirm" className="text-sm font-normal leading-relaxed text-muted-foreground">
              <ShieldCheck className="mb-1 inline size-3.5 text-primary" /> I confirm that the information provided above is accurate to the best of my
              knowledge and I authorize NAGRIK to submit this application to {scheme.department} on my behalf.
            </Label>
          </Card>
          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStepIndex(2)} className="gap-1.5">
              <ArrowLeft className="size-4" /> Back
            </Button>
            <Button onClick={handleSubmit} disabled={!confirmed || isSubmitting} className="gap-1.5">
              {isSubmitting && <Loader2 className="size-4 animate-spin" />}
              Submit Application <ArrowRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
