import type { CitizenProfile, OfficerProfile } from "@/types"

export const MOCK_CITIZEN: CitizenProfile = {
  id: "cz-10234",
  name: "Ravish Kansal",
  email: "ravish.kansal@example.com",
  phone: "+91 98765 43210",
  avatarUrl: undefined,
  dob: "1992-04-18",
  gender: "male",
  address: {
    line1: "24, Green Park Extension",
    ward: "Ward 12 - Green Park",
    district: "South Delhi",
    state: "Delhi",
    pincode: "110016",
  },
  income: 380000,
  occupation: "Software Engineer",
  category: "General",
  disabilityStatus: false,
  familySize: 4,
  preferredLanguage: "en",
  digilockerLinked: true,
  aadhaarLinked: true,
  completeness: 82,
  memberSince: "2023-11-02",
}

export const MOCK_OFFICER: OfficerProfile = {
  id: "of-5521",
  name: "Anjali Mehta",
  email: "anjali.mehta@ulb.gov.in",
  designation: "Zonal Sanitary Officer",
  department: "Sanitation & Waste Management",
  ward: "Ward 12",
  district: "South Delhi",
  avatarUrl: undefined,
}
