import type { CitizenProfile } from "@/types"
import { MOCK_CITIZEN } from "@/lib/mock/users"
import { request } from "./_client"

let profile: CitizenProfile = { ...MOCK_CITIZEN }

export async function getProfile(): Promise<CitizenProfile> {
  return request(() => ({ ...profile }))
}

export async function updateProfile(patch: Partial<CitizenProfile>): Promise<CitizenProfile> {
  return request(() => {
    profile = { ...profile, ...patch }
    return { ...profile }
  }, 600)
}
