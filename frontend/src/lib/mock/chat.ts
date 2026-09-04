export const SUGGESTED_QUERIES: string[] = [
  "Which schemes am I eligible for?",
  "Track my PMAY housing application",
  "How do I get an Ayushman Bharat health card?",
  "Report a pothole near my house",
  "What documents do I need for PM-KISAN?",
  "Compare housing subsidy schemes",
]

interface CannedResponse {
  match: RegExp
  content: string
  sources?: { label: string; href: string }[]
  suggestedActions?: { label: string; href: string }[]
}

export const CANNED_RESPONSES: CannedResponse[] = [
  {
    match: /eligible|eligibility|qualify/i,
    content:
      "Based on your profile (annual income ₹3,80,000, South Delhi resident, general category), you match strongly with 4 schemes: PM Surya Ghar rooftop solar (98% match), PMAY-U housing subsidy (91% match), PM-KISAN (not applicable - no landholding on record), and Atal Pension Yojana (87% match). Would you like a detailed eligibility breakdown for any of these?",
    sources: [{ label: "Eligibility computed from profile + scheme rules", href: "/profile" }],
    suggestedActions: [
      { label: "View recommended schemes", href: "/services?tab=recommended" },
      { label: "See PM Surya Ghar details", href: "/services/sch-solar-rooftop" },
    ],
  },
  {
    match: /pmay|housing|home loan/i,
    content:
      "Your PMAY-U application (PMAY/2026/DL/90021) is currently at 60% progress. It's in the 'Documents Pending' stage - the bank verification team needs your Property Sale Agreement to link the subsidy with your home loan. I can help you upload it now.",
    suggestedActions: [{ label: "Go to application", href: "/applications/app-90021" }],
  },
  {
    match: /ayushman|health card|pmjay/i,
    content:
      "To get your Ayushman Bharat (PM-JAY) health card, your household needs to be listed under the SECC 2011 deprivation criteria. Your previous application was not approved because your household wasn't found in that list. I can guide you through an alternate verification process using your ration card - want to start a new application?",
    sources: [{ label: "pmjay.gov.in - Eligibility criteria", href: "https://pmjay.gov.in" }],
    suggestedActions: [{ label: "Check eligibility again", href: "/services/sch-ayushman" }],
  },
  {
    match: /pothole|report|complaint|issue/i,
    content:
      "I can help you report this. You can describe the issue in your own words, attach a photo, and I'll auto-detect the location and suggest the right department. Shall we start a new civic issue report?",
    suggestedActions: [{ label: "Report an issue", href: "/issues/new" }],
  },
  {
    match: /pm-kisan|farmer|kisan/i,
    content:
      "For PM-KISAN, you'll need: Aadhaar Card, Land Ownership Records (Khatauni/7-12 extract), and Bank Account details linked to Aadhaar. Since our records show no landholding under your profile, you may not currently qualify - but I can check again if you've recently acquired agricultural land.",
    sources: [{ label: "pmkisan.gov.in - Document checklist", href: "https://pmkisan.gov.in" }],
  },
  {
    match: /compare|housing subsidy|which scheme/i,
    content:
      "Here's a quick comparison: PMAY-U gives an interest subsidy (up to ₹2.67L) applicable when taking a home loan, while PM Surya Ghar gives a one-time solar subsidy (up to ₹78K) for existing homeowners and reduces monthly electricity costs. They're not mutually exclusive - you can apply for both.",
    suggestedActions: [{ label: "Open scheme comparison", href: "/services/compare" }],
  },
]

export const DEFAULT_RESPONSE =
  "I looked through government scheme records and civic service data related to your question. Could you tell me a bit more - for example, are you asking about a specific scheme, tracking an application, or reporting a civic issue? I can also connect you to a human agent via Call Nagrik if this needs deeper assistance."
