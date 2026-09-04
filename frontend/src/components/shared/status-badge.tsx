import { cn } from "@/lib/utils"

export type StatusTone = "default" | "success" | "warning" | "destructive" | "info"

const TONE_CLASSES: Record<StatusTone, string> = {
  default: "bg-muted text-muted-foreground border-transparent",
  success: "bg-success/15 text-success border-success/20 dark:text-success",
  warning: "bg-warning/20 text-warning-foreground border-warning/30",
  destructive: "bg-destructive/10 text-destructive border-destructive/20",
  info: "bg-info/12 text-info border-info/20 dark:text-info",
}

const DOT_CLASSES: Record<StatusTone, string> = {
  default: "bg-muted-foreground",
  success: "bg-success",
  warning: "bg-warning",
  destructive: "bg-destructive",
  info: "bg-info",
}

export function StatusBadge({
  label,
  tone = "default",
  withDot = true,
  className,
}: {
  label: string
  tone?: StatusTone
  withDot?: boolean
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        TONE_CLASSES[tone],
        className,
      )}
    >
      {withDot && <span className={cn("size-1.5 rounded-full", DOT_CLASSES[tone])} />}
      {label}
    </span>
  )
}
