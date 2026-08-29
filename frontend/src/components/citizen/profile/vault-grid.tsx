"use client"

import * as React from "react"
import { toast } from "sonner"
import { CheckCircle2, Clock, FileText, FolderKey, Image as ImageIcon, Loader2, Plus, RefreshCw, ShieldCheck } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ListSkeleton } from "@/components/shared/loading-state"
import { EmptyState } from "@/components/shared/empty-state"
import { listVaultDocuments, addVaultDocument, syncDigiLocker } from "@/services/vault-service"
import { formatDate } from "@/lib/format"
import type { VaultDocument } from "@/types"

const CATEGORIES: VaultDocument["category"][] = ["Identity", "Address", "Income", "Education", "Property", "Other"]

export function VaultGrid() {
  const [docs, setDocs] = React.useState<VaultDocument[] | null>(null)
  const [isSyncing, setIsSyncing] = React.useState(false)
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [newName, setNewName] = React.useState("")
  const [newCategory, setNewCategory] = React.useState<VaultDocument["category"]>("Other")

  const refresh = React.useCallback(() => {
    listVaultDocuments().then(setDocs)
  }, [])

  React.useEffect(() => {
    refresh()
  }, [refresh])

  async function handleSync() {
    setIsSyncing(true)
    await syncDigiLocker()
    setIsSyncing(false)
    toast.success("DigiLocker sync complete", { description: "Your linked documents are up to date." })
    refresh()
  }

  async function handleAdd() {
    if (!newName.trim()) return
    await addVaultDocument({ name: newName.trim(), category: newCategory })
    setNewName("")
    setDialogOpen(false)
    toast.success("Document added to vault", { description: "Pending verification by the issuing authority." })
    refresh()
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FolderKey className="size-4" />
          {docs ? `${docs.length} documents secured in your vault` : "Loading vault..."}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleSync} disabled={isSyncing}>
            {isSyncing ? <Loader2 className="size-3.5 animate-spin" /> : <RefreshCw className="size-3.5" />}
            Sync DigiLocker
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="gap-1.5">
                <Plus className="size-3.5" /> Upload Document
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload a document</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="doc-name">Document name</Label>
                  <Input id="doc-name" placeholder="e.g. Rent Agreement" value={newName} onChange={(e) => setNewName(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label>Category</Label>
                  <Select value={newCategory} onValueChange={(v) => setNewCategory(v as VaultDocument["category"])}>
                    <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handleAdd} disabled={!newName.trim()}>Add to Vault</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {!docs && <ListSkeleton count={4} />}

      {docs && docs.length === 0 && (
        <EmptyState icon={FolderKey} title="Your vault is empty" description="Sync with DigiLocker or upload documents to build your Smart Document Vault." />
      )}

      {docs && docs.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc) => (
            <Card key={doc.id} className="space-y-3 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                  {doc.fileType === "image" ? <ImageIcon className="size-4 text-muted-foreground" /> : <FileText className="size-4 text-muted-foreground" />}
                </div>
                {doc.source === "DigiLocker" && (
                  <Badge variant="outline" className="gap-1 text-[10px]">
                    <ShieldCheck className="size-2.5" /> DigiLocker
                  </Badge>
                )}
              </div>
              <div>
                <p className="text-sm font-medium leading-snug">{doc.name}</p>
                <p className="text-xs text-muted-foreground">{doc.category} · {(doc.sizeKb / 1024).toFixed(1)} MB</p>
              </div>
              <div className="flex items-center justify-between text-xs">
                {doc.verified ? (
                  <span className="flex items-center gap-1 text-success"><CheckCircle2 className="size-3.5" /> Verified</span>
                ) : (
                  <span className="flex items-center gap-1 text-warning-foreground"><Clock className="size-3.5" /> Pending</span>
                )}
                <span className="text-muted-foreground">{formatDate(doc.addedOn)}</span>
              </div>
              {doc.linkedApplications.length > 0 && (
                <p className="text-[11px] text-muted-foreground">Linked to {doc.linkedApplications.length} application(s)</p>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
