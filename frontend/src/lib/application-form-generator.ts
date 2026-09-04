import type { CitizenProfile, DynamicFormField, DynamicFormSection, Scheme, SchemeCategory } from "@/types"

function personalDetailsSection(): DynamicFormSection {
  return {
    id: "personal",
    title: "Personal Information",
    description: "Pre-filled from your NAGRIK profile. Review and edit if needed.",
    fields: [
      { id: "applicantName", label: "Full Name", type: "text", required: true, prefillFromProfile: "name", aiConfidence: 0.98 },
      { id: "dob", label: "Date of Birth", type: "date", required: true, prefillFromProfile: "dob", aiConfidence: 0.98 },
      { id: "phone", label: "Mobile Number", type: "phone", required: true, prefillFromProfile: "phone", aiConfidence: 0.95 },
      { id: "email", label: "Email Address", type: "text", required: false, prefillFromProfile: "email", aiConfidence: 0.95 },
      {
        id: "address",
        label: "Residential Address",
        type: "textarea",
        required: true,
        aiConfidence: 0.9,
      },
      {
        id: "annualIncome",
        label: "Annual Household Income (₹)",
        type: "number",
        required: true,
        prefillFromProfile: "income",
        aiConfidence: 0.85,
      },
    ],
  }
}

const CATEGORY_FIELDS: Record<SchemeCategory, DynamicFormField[]> = {
  Housing: [
    { id: "propertyOwned", label: "Do you currently own a pucca house?", type: "radio", required: true, options: [{ label: "Yes", value: "true" }, { label: "No", value: "false" }] },
    { id: "loanAmount", label: "Requested Loan Amount (₹)", type: "number", required: true, placeholder: "e.g. 2500000" },
  ],
  Agriculture: [
    { id: "landholdingAcres", label: "Landholding Size (acres)", type: "number", required: true, placeholder: "e.g. 2.5" },
    { id: "landRecordId", label: "Land Record / Khatauni ID", type: "text", required: true, placeholder: "e.g. DL-KH-33210" },
  ],
  Education: [
    { id: "institutionName", label: "Institution Name", type: "text", required: true, placeholder: "e.g. Delhi University" },
    { id: "courseName", label: "Course / Class", type: "text", required: true, placeholder: "e.g. B.Tech Computer Science" },
    { id: "admissionYear", label: "Admission Year", type: "date", required: true },
  ],
  Health: [
    { id: "familySize", label: "Number of Family Members", type: "number", required: true, prefillFromProfile: "familySize" },
    { id: "existingConditions", label: "Pre-existing Conditions (if any)", type: "textarea", required: false },
  ],
  Employment: [
    { id: "currentOccupation", label: "Current Occupation", type: "text", required: true, prefillFromProfile: "occupation" },
    { id: "skillArea", label: "Skill / Trade Area", type: "text", required: true, placeholder: "e.g. Tailoring, Electrician" },
  ],
  "Social Welfare": [
    { id: "householdCategory", label: "Household Category", type: "select", required: true, options: [{ label: "BPL", value: "bpl" }, { label: "APL", value: "apl" }, { label: "AAY", value: "aay" }] },
  ],
  "Women & Child": [
    { id: "beneficiaryName", label: "Beneficiary Name (child/dependent)", type: "text", required: true },
    { id: "beneficiaryDob", label: "Beneficiary Date of Birth", type: "date", required: true },
  ],
  Pension: [
    { id: "nomineeName", label: "Nominee Name", type: "text", required: true },
    { id: "nomineeRelation", label: "Relationship with Nominee", type: "text", required: true, placeholder: "e.g. Spouse, Son" },
  ],
  "Business & MSME": [
    { id: "businessName", label: "Business / Enterprise Name", type: "text", required: true },
    { id: "businessPlan", label: "Brief Business Plan", type: "textarea", required: true, placeholder: "Describe your business idea and fund usage" },
  ],
  Energy: [
    { id: "rooftopArea", label: "Available Rooftop Area (sq. ft)", type: "number", required: true, placeholder: "e.g. 400" },
    {
      id: "sanctionedLoad",
      label: "Sanctioned Electricity Load",
      type: "select",
      required: true,
      options: [
        { label: "1 kW", value: "1kW" },
        { label: "3 kW", value: "3kW" },
        { label: "5 kW", value: "5kW" },
        { label: "10 kW+", value: "10kW" },
      ],
    },
  ],
}

function schemeDetailsSection(scheme: Scheme): DynamicFormSection {
  return {
    id: "scheme-details",
    title: "Scheme-Specific Details",
    description: `Additional information required for ${scheme.title}.`,
    fields: CATEGORY_FIELDS[scheme.category] ?? [
      { id: "additionalNotes", label: "Additional Notes", type: "textarea", required: false },
    ],
  }
}

function declarationSection(): DynamicFormSection {
  return {
    id: "declaration",
    title: "Bank & Declaration Details",
    fields: [
      { id: "bankAccountNumber", label: "Bank Account Number", type: "text", required: true, placeholder: "e.g. 001234567890" },
      { id: "ifscCode", label: "IFSC Code", type: "text", required: true, placeholder: "e.g. SBIN0001234" },
    ],
  }
}

export function generateApplicationForm(scheme: Scheme): DynamicFormSection[] {
  return [personalDetailsSection(), schemeDetailsSection(scheme), declarationSection()]
}

export function getPrefillValue(field: DynamicFormField, profile: CitizenProfile): string {
  if (!field.prefillFromProfile) return ""
  const value = profile[field.prefillFromProfile]
  if (value === undefined || value === null) return ""
  return String(value)
}
