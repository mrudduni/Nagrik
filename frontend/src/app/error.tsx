"use client"

import * as React from "react"
import Link from "next/link"
import { AlertTriangle, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  React.useEffect(() => {
    // In production this is where the error would be forwarded to the
    // monitoring backend.
    console.error(error)
  }, [error])

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-5 bg-muted/30 px-4 text-center">
      <div className="flex size-12 items-center justify-center rounded-xl bg-destructive/10">
        <AlertTriangle className="size-6 text-destructive" />
      </div>
      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold tracking-tight">Something went wrong</h1>
        <p className="mx-auto max-w-md text-sm text-muted-foreground">
          We hit an unexpected problem loading this part of NAGRIK. You can retry, or head back to the assistant.
        </p>
        {error.digest && <p className="font-mono text-xs text-muted-foreground/70">Reference: {error.digest}</p>}
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        <Button onClick={reset} className="gap-1.5">
          <RotateCcw className="size-4" /> Try again
        </Button>
        <Button asChild variant="outline">
          <Link href="/">Back to AI Assistant</Link>
        </Button>
      </div>
    </div>
  )
}
