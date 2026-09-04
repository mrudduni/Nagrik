"use client"

import { Sparkles } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { DynamicFormField } from "@/types"
import { cn } from "@/lib/utils"

export function DynamicField({
  field,
  value,
  onChange,
  error,
}: {
  field: DynamicFormField
  value: string
  onChange: (value: string) => void
  error?: string
}) {
  const isAiFilled = !!field.aiConfidence && value !== ""

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <Label htmlFor={field.id} className="text-xs font-medium text-foreground">
          {field.label} {field.required && <span className="text-destructive">*</span>}
        </Label>
        {isAiFilled && (
          <span className="flex items-center gap-1 rounded-full bg-info/10 px-2 py-0.5 text-[10px] font-medium text-info">
            <Sparkles className="size-2.5" /> AI-filled ({Math.round((field.aiConfidence ?? 0) * 100)}%)
          </span>
        )}
      </div>

      {field.type === "textarea" ? (
        <Textarea
          id={field.id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={cn(error && "border-destructive")}
          rows={3}
        />
      ) : field.type === "select" ? (
        <Select value={value} onValueChange={onChange}>
          <SelectTrigger className={cn("w-full", error && "border-destructive")}>
            <SelectValue placeholder={field.placeholder ?? "Select an option"} />
          </SelectTrigger>
          <SelectContent>
            {field.options?.map((o) => (
              <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : field.type === "radio" ? (
        <RadioGroup value={value} onValueChange={onChange} className="flex gap-4">
          {field.options?.map((o) => (
            <div key={o.value} className="flex items-center gap-2">
              <RadioGroupItem value={o.value} id={`${field.id}-${o.value}`} />
              <Label htmlFor={`${field.id}-${o.value}`} className="font-normal">{o.label}</Label>
            </div>
          ))}
        </RadioGroup>
      ) : (
        <Input
          id={field.id}
          type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder}
          className={cn(error && "border-destructive")}
        />
      )}
      {field.helpText && !error && <p className="text-[11px] text-muted-foreground">{field.helpText}</p>}
      {error && <p className="text-[11px] text-destructive">{error}</p>}
    </div>
  )
}
