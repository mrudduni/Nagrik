"use client"

import * as React from "react"
import { ArrowUp, ImagePlus, Mic, Paperclip, Square, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

export interface PendingAttachment {
  type: "image" | "document"
  name: string
}

export function ChatComposer({
  onSend,
  disabled,
}: {
  onSend: (text: string, attachment?: PendingAttachment) => void
  disabled?: boolean
}) {
  const [value, setValue] = React.useState("")
  const [attachment, setAttachment] = React.useState<PendingAttachment | undefined>()
  const [isRecording, setIsRecording] = React.useState(false)
  const [recordSeconds, setRecordSeconds] = React.useState(0)
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const docInputRef = React.useRef<HTMLInputElement>(null)

  React.useEffect(() => {
    if (!isRecording) return
    const interval = setInterval(() => setRecordSeconds((s) => s + 1), 1000)
    return () => clearInterval(interval)
  }, [isRecording])

  function handleSend() {
    if (disabled) return
    if (!value.trim() && !attachment) return
    onSend(value.trim() || "Sent an attachment", attachment)
    setValue("")
    setAttachment(undefined)
  }

  function startRecording() {
    setIsRecording(true)
    setRecordSeconds(0)
  }

  function stopRecording(send: boolean) {
    setIsRecording(false)
    if (send && recordSeconds > 0) {
      onSend(`[Voice message - ${recordSeconds}s] Transcribing...`, { type: "document", name: "voice-note.wav" })
    }
    setRecordSeconds(0)
  }

  function onFileChosen(e: React.ChangeEvent<HTMLInputElement>, type: "image" | "document") {
    const file = e.target.files?.[0]
    if (file) setAttachment({ type, name: file.name })
    e.target.value = ""
  }

  if (isRecording) {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 px-4 py-3">
        <span className="relative flex size-2.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-destructive opacity-75" />
          <span className="relative inline-flex size-2.5 rounded-full bg-destructive" />
        </span>
        <div className="flex flex-1 items-center gap-0.5">
          {Array.from({ length: 24 }).map((_, i) => (
            <span
              key={i}
              className="w-0.5 shrink-0 rounded-full bg-destructive/60"
              style={{ height: `${8 + Math.abs(Math.sin(i + recordSeconds)) * 18}px` }}
            />
          ))}
        </div>
        <span className="text-sm tabular-nums text-muted-foreground">
          {String(Math.floor(recordSeconds / 60)).padStart(2, "0")}:{String(recordSeconds % 60).padStart(2, "0")}
        </span>
        <Button size="icon" variant="ghost" className="text-muted-foreground" onClick={() => stopRecording(false)}>
          <X className="size-4" />
        </Button>
        <Button size="icon" className="bg-destructive text-white hover:bg-destructive/90" onClick={() => stopRecording(true)}>
          <Square className="size-3.5 fill-current" />
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {attachment && (
        <div className="flex w-fit items-center gap-2 rounded-lg border border-border bg-muted px-2.5 py-1.5 text-xs">
          {attachment.type === "image" ? <ImagePlus className="size-3.5" /> : <Paperclip className="size-3.5" />}
          {attachment.name}
          <button onClick={() => setAttachment(undefined)} className="text-muted-foreground hover:text-foreground">
            <X className="size-3" />
          </button>
        </div>
      )}
      <div className="flex items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm focus-within:ring-2 focus-within:ring-ring/30">
        <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={(e) => onFileChosen(e, "image")} />
        <input ref={docInputRef} type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={(e) => onFileChosen(e, "document")} />

        <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground" onClick={() => fileInputRef.current?.click()} title="Attach image">
          <ImagePlus className="size-4.5" />
        </Button>
        <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground" onClick={() => docInputRef.current?.click()} title="Attach document">
          <Paperclip className="size-4.5" />
        </Button>

        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Ask about schemes, applications, or report an issue..."
          className="max-h-32 min-h-9 flex-1 resize-none border-0 bg-transparent p-1.5 shadow-none focus-visible:ring-0"
          rows={1}
        />

        <Button variant="ghost" size="icon" className="shrink-0 text-muted-foreground" onClick={startRecording} title="Voice input">
          <Mic className="size-4.5" />
        </Button>
        <Button
          size="icon"
          className={cn("shrink-0 rounded-xl", !value.trim() && !attachment && "opacity-50")}
          onClick={handleSend}
          disabled={disabled}
        >
          <ArrowUp className="size-4.5" />
        </Button>
      </div>
    </div>
  )
}
