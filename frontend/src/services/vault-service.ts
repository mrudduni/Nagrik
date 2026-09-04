import type { VaultDocument } from "@/types"
import { MOCK_VAULT_DOCUMENTS } from "@/lib/mock/vault"
import { request } from "./_client"

const store: VaultDocument[] = [...MOCK_VAULT_DOCUMENTS]

export async function listVaultDocuments(): Promise<VaultDocument[]> {
  return request(() => [...store].sort((a, b) => (a.addedOn < b.addedOn ? 1 : -1)))
}

export async function addVaultDocument(params: { name: string; category: VaultDocument["category"] }): Promise<VaultDocument> {
  return request(() => {
    const doc: VaultDocument = {
      id: `vd-${Date.now()}`,
      name: params.name,
      category: params.category,
      source: "Uploaded",
      verified: false,
      addedOn: new Date().toISOString(),
      sizeKb: Math.floor(150 + Math.random() * 700),
      fileType: "pdf",
      linkedApplications: [],
    }
    store.unshift(doc)
    return doc
  }, 800)
}

export async function syncDigiLocker(): Promise<VaultDocument[]> {
  return request(() => [...store], 1400)
}
