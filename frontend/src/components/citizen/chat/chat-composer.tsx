"use client"

import * as React from "react"
import {
  ArrowUp,
  ImagePlus,
  Mic,
  Paperclip,
  Square,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

export interface PendingAttachment {
  type: "image" | "document"
  name: string
  base64_data: string
  mime_type: string
}

interface VoiceMessage {
  audioBase64: string
  mimeType: string
  duration: number
}

export function ChatComposer({
  onSend,
  onVoiceSend,
  disabled,
}: {
  onSend: (
    text: string,
    attachment?: PendingAttachment,
  ) => void
  onVoiceSend?: (voice: VoiceMessage) => void
  disabled?: boolean
}) {
  const [value, setValue] = React.useState("")
  const [attachment, setAttachment] =
    React.useState<PendingAttachment | undefined>()

  const [isRecording, setIsRecording] = React.useState(false)
  const [recordSeconds, setRecordSeconds] = React.useState(0)
  const [isProcessingVoice, setIsProcessingVoice] =
    React.useState(false)

  const fileInputRef =
    React.useRef<HTMLInputElement>(null)
  const docInputRef =
    React.useRef<HTMLInputElement>(null)

  const mediaRecorderRef =
    React.useRef<MediaRecorder | null>(null)

  const audioChunksRef =
    React.useRef<Blob[]>([])

  const recordingStartRef =
    React.useRef<number>(0)

  React.useEffect(() => {
    if (!isRecording) return

    const interval = setInterval(() => {
      setRecordSeconds(
        Math.floor(
          (Date.now() - recordingStartRef.current) / 1000,
        ),
      )
    }, 250)

    return () => clearInterval(interval)
  }, [isRecording])

  // -----------------------------
  // VOICE RECORDING
  // -----------------------------

  async function startRecording() {
    if (disabled || isProcessingVoice) return

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        alert(
          "Microphone recording is not supported in this browser.",
        )
        return
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        })

      const mimeType = getSupportedMimeType()

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)

      audioChunksRef.current = []

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop())

        const duration = Math.floor(
          (Date.now() - recordingStartRef.current) / 1000,
        )

        const blob = new Blob(
          audioChunksRef.current,
          {
            type:
              recorder.mimeType ||
              "audio/webm",
          },
        )

        audioChunksRef.current = []

        if (
          duration <= 0 ||
          blob.size === 0
        ) {
          setIsProcessingVoice(false)
          alert("Recording was too short. Please hold the button and speak clearly.")
          return
        }

        try {
          setIsProcessingVoice(true)

          const audioBase64 =
            await blobToBase64(blob)

          onVoiceSend?.({
            audioBase64,
            mimeType: blob.type,
            duration,
          })
        } catch (error) {
          console.error(
            "Voice processing error:",
            error,
          )

          alert(
            "Could not process the voice recording.",
          )
        } finally {
          setIsProcessingVoice(false)
        }
      }

      mediaRecorderRef.current = recorder

      recordingStartRef.current =
        Date.now()

      recorder.start()

      setRecordSeconds(0)
      setIsRecording(true)
    } catch (error) {
      console.error(
        "Microphone permission error:",
        error,
      )

      alert(
        "Microphone access was denied. Please allow microphone access and try again.",
      )
    }
  }

  function stopRecording(send: boolean) {
    const recorder =
      mediaRecorderRef.current

    if (
      !recorder ||
      recorder.state === "inactive"
    ) {
      setIsRecording(false)
      return
    }

    if (!send) {
      audioChunksRef.current = []
    }

    setIsRecording(false)

    recorder.stop()

    mediaRecorderRef.current = null

    if (!send) {
      setRecordSeconds(0)
    }
  }

  // -----------------------------
  // TEXT / ATTACHMENT SEND
  // -----------------------------

  function handleSend() {
    if (disabled) return

    if (
      !value.trim() &&
      !attachment
    ) {
      return
    }

    onSend(
      value.trim(),
      attachment,
    )

    setValue("")
    setAttachment(undefined)
  }

  // -----------------------------
  // FILE UPLOAD (with validation)
  // -----------------------------

  async function onFileChosen(
    e: React.ChangeEvent<HTMLInputElement>,
    type: "image" | "document",
  ) {
    const file = e.target.files?.[0]

    if (!file) {
      e.target.value = ""
      return
    }

    // Size check: 10 MB limit
    const MAX_BYTES = 10 * 1024 * 1024
    if (file.size > MAX_BYTES) {
      alert("File is too large. Maximum allowed size is 10 MB.")
      e.target.value = ""
      return
    }

    // MIME type check
    const ALLOWED_IMAGE_MIMES = [
      "image/jpeg", "image/png", "image/gif",
      "image/webp", "image/heic", "image/heif",
    ]
    const ALLOWED_DOC_MIMES = ["application/pdf"]

    const mime = file.type.toLowerCase()
    if (type === "image" && !ALLOWED_IMAGE_MIMES.includes(mime)) {
      alert(`Unsupported image format: ${file.type}. Please use JPEG, PNG, GIF, or WebP.`)
      e.target.value = ""
      return
    }
    if (type === "document" && !ALLOWED_DOC_MIMES.includes(mime)) {
      alert("Only PDF documents are supported. Please upload a PDF file.")
      e.target.value = ""
      return
    }

    try {
      const base64_data = await fileToBase64(file)
      setAttachment({
        type,
        name: file.name,
        base64_data,
        mime_type: file.type,
      })
    } catch (error) {
      console.error("File conversion failed:", error)
      alert("Could not read this file. Please try again.")
    }

    e.target.value = ""
  }

  // -----------------------------
  // RECORDING UI
  // -----------------------------

  if (isRecording) {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 px-4 py-3">
        <span className="relative flex size-2.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-destructive opacity-75" />
          <span className="relative inline-flex size-2.5 rounded-full bg-destructive" />
        </span>

        <div className="flex flex-1 items-center gap-0.5">
          {Array.from({
            length: 24,
          }).map((_, i) => (
            <span
              key={i}
              className="w-0.5 shrink-0 rounded-full bg-destructive/60"
              style={{
                height: `${
                  8 +
                  Math.abs(
                    Math.sin(
                      i + recordSeconds,
                    ),
                  ) *
                    18
                }px`,
              }}
            />
          ))}
        </div>

        <span className="text-sm tabular-nums text-muted-foreground">
          {String(
            Math.floor(
              recordSeconds / 60,
            ),
          ).padStart(2, "0")}
          :
          {String(
            recordSeconds % 60,
          ).padStart(2, "0")}
        </span>

        <Button
          size="icon"
          variant="ghost"
          className="text-muted-foreground"
          onClick={() =>
            stopRecording(false)
          }
        >
          <X className="size-4" />
        </Button>

        <Button
          size="icon"
          className="bg-destructive text-white hover:bg-destructive/90"
          onClick={() =>
            stopRecording(true)
          }
        >
          <Square className="size-3.5 fill-current" />
        </Button>
      </div>
    )
  }

  // -----------------------------
  // NORMAL COMPOSER
  // -----------------------------

  return (
    <div className="space-y-2">

      {/* Attachment preview */}
      {attachment && (
        <div className="flex w-fit items-center gap-2 rounded-lg border border-border bg-muted px-2.5 py-1.5 text-xs">
          {attachment.type === "image" ? (
            <ImagePlus className="size-3.5" />
          ) : (
            <Paperclip className="size-3.5" />
          )}

          <span className="max-w-60 truncate">
            {attachment.name}
          </span>

          <button
            onClick={() =>
              setAttachment(undefined)
            }
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="size-3" />
          </button>
        </div>
      )}

      {isProcessingVoice && (
        <div className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">
          Processing your voice message...
        </div>
      )}

      <div className="flex items-end gap-2 rounded-2xl border border-border bg-card p-2 shadow-sm focus-within:ring-2 focus-within:ring-ring/30">

        {/* Image input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) =>
            onFileChosen(
              e,
              "image",
            )
          }
        />

        {/* Document input */}
        <input
          ref={docInputRef}
          type="file"
          accept=".pdf,.doc,.docx,application/pdf"
          className="hidden"
          onChange={(e) =>
            onFileChosen(
              e,
              "document",
            )
          }
        />

        {/* Image button */}
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 text-muted-foreground"
          onClick={() =>
            fileInputRef.current?.click()
          }
          disabled={disabled}
          title="Attach image"
        >
          <ImagePlus className="size-4.5" />
        </Button>

        {/* Document button */}
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 text-muted-foreground"
          onClick={() =>
            docInputRef.current?.click()
          }
          disabled={disabled}
          title="Attach document"
        >
          <Paperclip className="size-4.5" />
        </Button>

        {/* Text input */}
        <Textarea
          value={value}
          onChange={(e) =>
            setValue(e.target.value)
          }
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              !e.shiftKey
            ) {
              e.preventDefault()
              handleSend()
            }
          }}
          placeholder="Ask about schemes, applications, or report an issue..."
          className="max-h-32 min-h-9 flex-1 resize-none border-0 bg-transparent p-1.5 shadow-none focus-visible:ring-0"
          rows={1}
          disabled={disabled}
        />

        {/* Microphone */}
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 text-muted-foreground"
          onClick={startRecording}
          disabled={
            disabled ||
            isProcessingVoice
          }
          title="Voice input"
        >
          <Mic className="size-4.5" />
        </Button>

        {/* Send */}
        <Button
          size="icon"
          className={cn(
            "shrink-0 rounded-xl",
            !value.trim() &&
              !attachment &&
              "opacity-50",
          )}
          onClick={handleSend}
          disabled={
            disabled ||
            (!value.trim() &&
              !attachment)
          }
        >
          <ArrowUp className="size-4.5" />
        </Button>
      </div>
    </div>
  )
}

// -----------------------------
// HELPERS
// -----------------------------

function getSupportedMimeType(): string {
  const types = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
  ]

  return (
    types.find((type) =>
      MediaRecorder.isTypeSupported(
        type,
      ),
    ) || ""
  )
}

function blobToBase64(
  blob: Blob,
): Promise<string> {
  return new Promise(
    (resolve, reject) => {
      const reader =
        new FileReader()

      reader.onloadend = () => {
        const result =
          reader.result

        if (
          typeof result !==
          "string"
        ) {
          reject(
            new Error(
              "Failed to convert audio to base64",
            ),
          )
          return
        }

        const base64 =
          result.split(",")[1]

        if (!base64) {
          reject(
            new Error(
              "Invalid base64 audio",
            ),
          )
          return
        }

        resolve(base64)
      }

      reader.onerror = reject

      reader.readAsDataURL(blob)
    },
  )
}

function fileToBase64(
  file: File,
): Promise<string> {
  return new Promise(
    (resolve, reject) => {
      const reader =
        new FileReader()

      reader.onload = () => {
        const result =
          reader.result

        if (
          typeof result !==
          "string"
        ) {
          reject(
            new Error(
              "Failed to convert file to base64",
            ),
          )
          return
        }

        const base64 =
          result.split(",")[1]

        if (!base64) {
          reject(
            new Error(
              "Invalid base64 file",
            ),
          )
          return
        }

        resolve(base64)
      }

      reader.onerror = reject

      reader.readAsDataURL(file)
    },
  )
}