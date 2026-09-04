// ---------------------------------------------------------------------------
// NAGRIK shared domain types.
// This file is the contract between UI and the service layer (src/services).
// When the real FastAPI backend is wired up, these types should match the
// OpenAPI schema and the service layer swapped from mock to fetch calls.
// ---------------------------------------------------------------------------

export type LanguageCode = "en" | "hi" | "bn" | "ta" | "te" | "mr" | "gu" | "kn"

export interface Language {
  code: LanguageCode
  label: string
  nativeLabel: string
}

export type UserRole = "citizen" | "officer" | "admin"

export interface CitizenProfile {
  id: string
  name: string
  email: string
  phone: string
  avatarUrl?: string
  dob: string
  gender: "male" | "female" | "other"
  address: {
    line1: string
    ward: string
    district: string
    state: string
    pincode: string
  }
  income?: number
  occupation?: string
  category?: "General" | "OBC" | "SC" | "ST" | "EWS"
  disabilityStatus?: boolean
  familySize?: number
  preferredLanguage: LanguageCode
  digilockerLinked: boolean
  aadhaarLinked: boolean
  completeness: number // profile completeness %
  memberSince: string
}

export interface OfficerProfile {
  id: string
  name: string
  email: string
  designation: string
  department: string
  ward?: string
  district: string
  avatarUrl?: string
}

export interface AuthSession {
  role: UserRole
  citizen?: CitizenProfile
  officer?: OfficerProfile
}

// --- Government Schemes -----------------------------------------------------

export type SchemeCategory =
  | "Agriculture"
  | "Education"
  | "Health"
  | "Housing"
  | "Employment"
  | "Social Welfare"
  | "Women & Child"
  | "Pension"
  | "Business & MSME"
  | "Energy"

export type SchemeLevel = "Central" | "State"

export interface EligibilityRule {
  field: string
  label: string
  operator: "eq" | "lte" | "gte" | "in" | "between"
  value: string | number | [number, number] | string[]
}

export interface Scheme {
  id: string
  title: string
  shortDescription: string
  description: string
  category: SchemeCategory
  level: SchemeLevel
  department: string
  ministry: string
  benefitAmount?: string
  benefitType: "Cash Transfer" | "Subsidy" | "Insurance" | "Loan" | "Service" | "Pension" | "Scholarship"
  tags: string[]
  eligibilityRules: EligibilityRule[]
  eligibilitySummary: string[]
  documentsRequired: string[]
  applicationSteps: string[]
  officialSourceUrl: string
  officialSourceName: string
  lastVerified: string
  launchedOn: string
  beneficiariesCount: number
  rating: number
  processingTimeDays: number
  deadline?: string
  isFeatured?: boolean
  imageColor: string
}

export interface EligibilityResult {
  schemeId: string
  status: "eligible" | "not-eligible" | "partial" | "unknown"
  matchScore: number
  reasons: { rule: string; met: boolean; explanation: string }[]
}

// --- Applications -------------------------------------------------------------

export type ApplicationStatus =
  | "draft"
  | "submitted"
  | "under-review"
  | "documents-pending"
  | "additional-info-required"
  | "approved"
  | "rejected"
  | "disbursed"

export interface ApplicationTimelineEvent {
  id: string
  label: string
  description: string
  timestamp: string
  actor: "citizen" | "system" | "officer" | "ai"
  status: "completed" | "current" | "upcoming"
}

export interface ApplicationDocument {
  id: string
  name: string
  type: string
  status: "verified" | "pending" | "rejected" | "requested"
  uploadedOn?: string
  sizeKb?: number
}

export interface RequiredAction {
  id: string
  label: string
  description: string
  dueDate?: string
  severity: "low" | "medium" | "high"
}

export interface Application {
  id: string
  schemeId: string
  schemeTitle: string
  citizenId: string
  status: ApplicationStatus
  progress: number
  submittedOn?: string
  lastUpdated: string
  referenceNumber: string
  department: string
  formData: Record<string, string | number | boolean>
  documents: ApplicationDocument[]
  timeline: ApplicationTimelineEvent[]
  requiredActions: RequiredAction[]
  estimatedCompletion?: string
}

// --- Dynamic AI Application Form ----------------------------------------------

export type FormFieldType =
  | "text"
  | "number"
  | "date"
  | "select"
  | "radio"
  | "checkbox"
  | "textarea"
  | "file"
  | "phone"
  | "aadhaar"

export interface DynamicFormField {
  id: string
  label: string
  type: FormFieldType
  required: boolean
  placeholder?: string
  helpText?: string
  options?: { label: string; value: string }[]
  prefillFromProfile?: keyof CitizenProfile
  aiConfidence?: number // when AI auto-filled from voice/doc
}

export interface DynamicFormSection {
  id: string
  title: string
  description?: string
  fields: DynamicFormField[]
}

// --- Documents / Vault ---------------------------------------------------------

export interface VaultDocument {
  id: string
  name: string
  category: "Identity" | "Address" | "Income" | "Education" | "Property" | "Other"
  source: "DigiLocker" | "Uploaded"
  verified: boolean
  issuedBy?: string
  addedOn: string
  expiresOn?: string
  sizeKb: number
  fileType: "pdf" | "image"
  linkedApplications: string[]
}

// --- Civic Issues / Complaints --------------------------------------------------

export type IssueCategory =
  | "Roads & Potholes"
  | "Water Supply"
  | "Electricity"
  | "Sanitation & Garbage"
  | "Street Lighting"
  | "Drainage"
  | "Public Safety"
  | "Encroachment"
  | "Parks & Environment"
  | "Noise Pollution"

export type IssueSeverity = "low" | "medium" | "high" | "critical"

export type IssueStatus =
  | "submitted"
  | "acknowledged"
  | "assigned"
  | "in-progress"
  | "resolved"
  | "closed"
  | "reopened"

export interface IssueTimelineEvent {
  id: string
  label: string
  description: string
  timestamp: string
  actor: "citizen" | "system" | "officer" | "ai"
  status: "completed" | "current" | "upcoming"
}

export interface CivicIssue {
  id: string
  referenceNumber: string
  title: string
  description: string
  category: IssueCategory
  aiSuggestedCategory?: IssueCategory
  aiConfidence?: number
  severity: IssueSeverity
  status: IssueStatus
  department: string
  ward: string
  district: string
  location: { lat: number; lng: number; address: string }
  reportedBy: string
  reportedOn: string
  lastUpdated: string
  imageUrls?: string[]
  upvotes: number
  isDuplicateOf?: string
  duplicateCount?: number
  timeline: IssueTimelineEvent[]
  slaHours: number
  hoursElapsed: number
  assignedOfficer?: string
}

// --- Notifications -----------------------------------------------------------

export type NotificationType =
  | "application-update"
  | "document-request"
  | "issue-update"
  | "scheme-recommendation"
  | "system"
  | "deadline"

export interface AppNotification {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: string
  read: boolean
  href?: string
}

// --- AI Assistant Chat ----------------------------------------------------------

export type ChatRole = "user" | "assistant"
export type ChatAttachmentType = "image" | "document" | "voice"

export interface ChatAttachment {
  type: ChatAttachmentType
  name: string
}

export interface ChatSource {
  label: string
  href: string
  /** Ministry or department that owns the scheme */
  sublabel?: string
  /** Page reference within the source document */
  pageRef?: string
  /** Brief relevant snippet from the source */
  snippet?: string
}

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: string
  attachment?: ChatAttachment
  sources?: ChatSource[]
  suggestedActions?: { label: string; href: string }[]
  isVoice?: boolean
  audioBase64?: string
}

// --- Government Dashboard / Analytics ------------------------------------------

export interface DepartmentPerformance {
  id: string
  name: string
  totalComplaints: number
  resolved: number
  pending: number
  avgResolutionHours: number
  slaCompliance: number
  trend: "up" | "down" | "flat"
  headOfficer: string
}

export interface WardStat {
  ward: string
  district: string
  totalIssues: number
  resolvedIssues: number
  avgResolutionDays: number
  riskScore: number
  lat: number
  lng: number
  population: number
}

export interface TrendPoint {
  date: string
  value: number
}

export interface CategoryBreakdown {
  category: string
  count: number
  percentChange: number
}

export interface PredictiveAlert {
  id: string
  title: string
  description: string
  ward: string
  category: IssueCategory
  riskLevel: "low" | "medium" | "high" | "critical"
  predictedFor: string
  confidence: number
  recommendedAction: string
  affectedPopulationEstimate: number
}

export interface DuplicateCluster {
  id: string
  category: IssueCategory
  ward: string
  centerLabel: string
  issueIds: string[]
  count: number
  radius: string
}

export interface GovKpi {
  label: string
  value: string
  delta: string
  trend: "up" | "down" | "flat"
  helpText: string
}
