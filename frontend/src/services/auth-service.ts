import type { AuthSession, UserRole } from "@/types"
import { MOCK_CITIZEN, MOCK_OFFICER } from "@/lib/mock/users"
import { request } from "./_client"

export async function login(role: UserRole): Promise<AuthSession> {
  return request(() => {
    if (role === "officer") return { role, officer: MOCK_OFFICER }
    return { role: "citizen", citizen: MOCK_CITIZEN }
  }, 700)
}

export async function demoLogin(role: UserRole): Promise<AuthSession> {
  return login(role)
}
