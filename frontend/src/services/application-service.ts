import type { Application, ApplicationDocument, ApplicationTimelineEvent } from "@/types"
import { MOCK_APPLICATIONS } from "@/lib/mock/applications"
import { findSchemeById } from "@/lib/mock/schemes"
import { request } from "./_client"

// In-memory store seeded from mock data. Mutations persist for the session
// (survives navigation, resets on full page reload) - enough to make the
// demo feel real without a backend.
const store: Application[] = MOCK_APPLICATIONS.map((a) => ({ ...a, documents: [...a.documents], timeline: [...a.timeline], requiredActions: [...a.requiredActions] }))

export async function listApplications(citizenId: string): Promise<Application[]> {
  return request(() =>
    [...store]
      .filter((a) => a.citizenId === citizenId)
      .sort((a, b) => (a.lastUpdated < b.lastUpdated ? 1 : -1)),
  )
}

export async function getApplication(id: string): Promise<Application | undefined> {
  return request(() => store.find((a) => a.id === id))
}

export async function createApplication(params: {
  citizenId: string
  schemeId: string
  formData: Record<string, string | number | boolean>
}): Promise<Application> {
  return request(() => {
    const scheme = findSchemeById(params.schemeId)
    const id = `app-${Math.floor(90000 + Math.random() * 9999)}`
    const now = new Date().toISOString()
    const newApp: Application = {
      id,
      schemeId: params.schemeId,
      schemeTitle: scheme?.title ?? "Unknown Scheme",
      citizenId: params.citizenId,
      status: "submitted",
      progress: 20,
      submittedOn: now,
      lastUpdated: now,
      referenceNumber: `NGK/${new Date().getFullYear()}/${id.toUpperCase()}`,
      department: scheme?.department ?? "General",
      formData: params.formData,
      documents: (scheme?.documentsRequired ?? []).map((name, i) => ({
        id: `doc-new-${i}`,
        name,
        type: "General",
        status: "requested" as const,
      })),
      timeline: [
        {
          id: "t1",
          label: "Application submitted",
          description: "Submitted via AI Application Assistant",
          timestamp: now,
          actor: "citizen",
          status: "completed",
        },
        {
          id: "t2",
          label: "Initial AI screening",
          description: "Document checklist generated and eligibility re-verified",
          timestamp: now,
          actor: "ai",
          status: "current",
        },
        { id: "t3", label: "Officer review", description: "", timestamp: "", actor: "officer", status: "upcoming" },
        { id: "t4", label: "Decision", description: "", timestamp: "", actor: "system", status: "upcoming" },
      ],
      requiredActions: [],
    }
    store.unshift(newApp)
    return newApp
  }, 900)
}

export async function saveDraftApplication(params: {
  citizenId: string
  schemeId: string
  formData: Record<string, string | number | boolean>
}): Promise<Application> {
  return request(() => {
    const scheme = findSchemeById(params.schemeId)
    const id = `app-${Math.floor(90000 + Math.random() * 9999)}`
    const now = new Date().toISOString()
    const draft: Application = {
      id,
      schemeId: params.schemeId,
      schemeTitle: scheme?.title ?? "Unknown Scheme",
      citizenId: params.citizenId,
      status: "draft",
      progress: 25,
      lastUpdated: now,
      referenceNumber: `DRAFT/${id.toUpperCase()}`,
      department: scheme?.department ?? "General",
      formData: params.formData,
      documents: [],
      timeline: [
        {
          id: "t1",
          label: "Draft started",
          description: "AI Application Assistant pre-filled details from profile",
          timestamp: now,
          actor: "ai",
          status: "completed",
        },
      ],
      requiredActions: [],
    }
    store.unshift(draft)
    return draft
  })
}

export async function uploadDocument(applicationId: string, docName: string): Promise<ApplicationDocument> {
  return request(() => {
    const app = store.find((a) => a.id === applicationId)
    if (!app) throw new Error("Application not found")
    const existing = app.documents.find((d) => d.name === docName)
    const now = new Date().toISOString()
    if (existing) {
      existing.status = "verified"
      existing.uploadedOn = now
      existing.sizeKb = Math.floor(120 + Math.random() * 800)
      return existing
    }
    const newDoc: ApplicationDocument = {
      id: `doc-${Date.now()}`,
      name: docName,
      type: "General",
      status: "verified",
      uploadedOn: now,
      sizeKb: Math.floor(120 + Math.random() * 800),
    }
    app.documents.push(newDoc)
    app.lastUpdated = now

    const pendingCount = app.documents.filter((d) => d.status !== "verified").length
    if (pendingCount === 0 && app.status === "documents-pending") {
      app.status = "under-review"
      app.progress = Math.min(85, app.progress + 15)
      app.requiredActions = []
      app.timeline.push({
        id: `t-${Date.now()}`,
        label: "Documents verified",
        description: "All requested documents have been uploaded and verified",
        timestamp: now,
        actor: "system",
        status: "current",
      })
    }
    return newDoc
  }, 900)
}

export function computeStatusMeta(status: Application["status"]): { label: string; tone: "default" | "success" | "warning" | "destructive" | "info" } {
  switch (status) {
    case "draft":
      return { label: "Draft", tone: "default" }
    case "submitted":
      return { label: "Submitted", tone: "info" }
    case "under-review":
      return { label: "Under Review", tone: "info" }
    case "documents-pending":
      return { label: "Documents Pending", tone: "warning" }
    case "additional-info-required":
      return { label: "Action Required", tone: "warning" }
    case "approved":
      return { label: "Approved", tone: "success" }
    case "disbursed":
      return { label: "Disbursed", tone: "success" }
    case "rejected":
      return { label: "Rejected", tone: "destructive" }
    default:
      return { label: status, tone: "default" }
  }
}

export type { ApplicationTimelineEvent }
