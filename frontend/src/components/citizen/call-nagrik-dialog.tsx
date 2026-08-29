"use client"

import * as React from "react"
import { Phone, PhoneCall, Clock, Languages } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"

export function CallNagrikDialog({ children }: { children?: React.ReactNode }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        {children ?? (
          <Button variant="outline" className="gap-2">
            <Phone className="size-4" />
            Call Nagrik
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <div className="mb-1 flex size-11 items-center justify-center rounded-full bg-primary/10">
            <PhoneCall className="size-5 text-primary" />
          </div>
          <DialogTitle>Call Nagrik</DialogTitle>
          <DialogDescription>Speak to the AI voice assistant or a human agent over a phone call - no internet required.</DialogDescription>
        </DialogHeader>
        <div className="space-y-3 rounded-lg border border-border bg-muted/40 p-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Toll-free number</span>
            <span className="font-semibold tabular-nums">1800-11-NAGRIK</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="size-3.5" />
            Available 24x7, including holidays
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Languages className="size-3.5" />
            Supports 8 Indian languages via IVR
          </div>
        </div>
        <DialogFooter className="sm:justify-start">
          <p className="text-xs text-muted-foreground">
            This is a demo entry point. In production this places a real call through your device&apos;s dialer.
          </p>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
