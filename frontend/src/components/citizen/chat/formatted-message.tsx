import React from "react"
import { cn } from "@/lib/utils"
import { FileText, Gift, Info, ShieldCheck } from "lucide-react"

interface FormattedMessageProps {
  content: string
  className?: string
  isUser?: boolean
}

/**
 * Parses inline markdown:
 * - **bold text**
 * - *italic text*
 * - *(bracketed italic/region badge)*
 * - `code`
 * - ₹amount highlights
 * - [link text](url)
 */
function renderInline(text: string, isUser: boolean = false): React.ReactNode[] {
  // Regex tokens:
  // 1: bold: \*\*(.+?)\*\*
  // 2: region / bracket badge: \*\((.+?)\)\*
  // 3: italic: \*(.+?)\*
  // 4: inline code: `(.+?)`
  // 5: currency: (₹[\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore))?)
  // 6: link: \[(.+?)\]\((https?:\/\/[^\s)]+)\)
  const regex =
    /(\*\*(?:[^*]+?)\*\*|\*\((?:[^)]+?)\)\*|\*(?:[^*]+?)\*|`[^`]+`|₹[\d,]+(?:\.\d+)?(?:\s*(?:lakh|crore))?|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g

  const parts = text.split(regex)

  return parts.map((part, index) => {
    if (!part) return null

    // Bold: **text**
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      const inner = part.slice(2, -2)
      return (
        <strong
          key={index}
          className={cn(
            "font-semibold",
            isUser ? "text-primary-foreground font-semibold" : "text-foreground font-semibold",
          )}
        >
          {inner}
        </strong>
      )
    }

    // Bracketed badge: *(All India)* or *(Gujarat)*
    if (part.startsWith("*(") && part.endsWith(")*") && part.length >= 4) {
      const inner = part.slice(2, -2)
      return (
        <span
          key={index}
          className={cn(
            "mx-1 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
            isUser
              ? "bg-primary-foreground/20 text-primary-foreground"
              : "bg-primary/10 text-primary border border-primary/20",
          )}
        >
          {inner}
        </span>
      )
    }

    // Italic: *text*
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      const inner = part.slice(1, -1)
      return (
        <em
          key={index}
          className={cn(
            "italic",
            isUser ? "text-primary-foreground/90" : "text-muted-foreground",
          )}
        >
          {inner}
        </em>
      )
    }

    // Code: `code`
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      const inner = part.slice(1, -1)
      return (
        <code
          key={index}
          className={cn(
            "rounded px-1.5 py-0.5 font-mono text-xs",
            isUser
              ? "bg-primary-foreground/20 text-primary-foreground"
              : "bg-muted text-foreground border border-border/50",
          )}
        >
          {inner}
        </code>
      )
    }

    // Currency: ₹XX,XXX
    if (part.startsWith("₹")) {
      return (
        <span
          key={index}
          className={cn(
            "font-semibold tabular-nums",
            isUser
              ? "text-primary-foreground underline decoration-primary-foreground/40"
              : "text-emerald-600 dark:text-emerald-400 font-semibold",
          )}
        >
          {part}
        </span>
      )
    }

    // Links: [text](url)
    const linkMatch = part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/)
    if (linkMatch) {
      return (
        <a
          key={index}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "underline underline-offset-2 transition-colors",
            isUser
              ? "text-primary-foreground hover:text-white"
              : "text-primary hover:text-primary/80 font-medium",
          )}
        >
          {linkMatch[1]}
        </a>
      )
    }

    return <React.Fragment key={index}>{part}</React.Fragment>
  })
}

/**
 * Detects special scheme key-values like:
 * "- **Benefits:** text"
 * "- **Eligibility:** text"
 * "- **Required Documents:** text"
 */
function getBulletBadge(line: string) {
  const lower = line.toLowerCase()
  if (lower.includes("benefit")) {
    return {
      icon: Gift,
      color: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900/50",
    }
  }
  if (lower.includes("eligib")) {
    return {
      icon: ShieldCheck,
      color: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-900/50",
    }
  }
  if (lower.includes("document")) {
    return {
      icon: FileText,
      color: "text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-900/50",
    }
  }
  if (lower.includes("what it offers") || lower.includes("overview")) {
    return {
      icon: Info,
      color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900/50",
    }
  }
  return null
}

export function FormattedMessage({
  content,
  className,
  isUser = false,
}: FormattedMessageProps) {
  if (!content) return null

  // If message is from user, just render with inline markdown
  if (isUser) {
    return (
      <div className={cn("whitespace-pre-wrap leading-relaxed text-sm", className)}>
        {renderInline(content, true)}
      </div>
    )
  }

  // Split into lines for block parsing
  const lines = content.split("\n")
  const elements: React.ReactNode[] = []

  let i = 0
  while (i < lines.length) {
    const rawLine = lines[i]
    const line = rawLine.trim()

    // 1. Empty line
    if (!line) {
      i++
      continue
    }

    // 2. Horizontal divider
    if (line === "---" || line === "***" || line === "___") {
      elements.push(
        <hr
          key={`hr-${i}`}
          className="my-3 border-t border-border/60"
        />,
      )
      i++
      continue
    }

    // 3. Headings (### or ## or #)
    const headingMatch = line.match(/^(#{1,3})\s+(.*)$/)
    if (headingMatch) {
      const headingLevel = headingMatch[1].length
      const headingText = headingMatch[2]

      elements.push(
        <div
          key={`h-${i}`}
          className={cn(
            "font-semibold text-foreground tracking-tight",
            headingLevel === 1 && "mt-3 mb-1.5 text-base font-bold",
            headingLevel === 2 && "mt-2.5 mb-1 text-[15px] font-semibold",
            headingLevel === 3 && "mt-2 mb-1 text-sm font-semibold",
          )}
        >
          {renderInline(headingText, false)}
        </div>,
      )
      i++
      continue
    }

    // 4. Numbered scheme item, e.g. "1. **Scheme Name** *(All India)*"
    const numberedMatch = line.match(/^(\d+)\.\s+(.*)$/)
    if (numberedMatch) {
      const num = numberedMatch[1]
      const rest = numberedMatch[2]

      elements.push(
        <div
          key={`item-${i}`}
          className="mt-3 flex items-start gap-2.5 rounded-lg border border-border/70 bg-card/60 p-2.5 transition-colors hover:bg-card"
        >
          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
            {num}
          </span>
          <div className="flex-1 text-sm leading-snug">
            {renderInline(rest, false)}
          </div>
        </div>,
      )
      i++
      continue
    }

    // 5. Bullet list item, e.g. "- **Benefits:** ..." or "* **Eligibility:** ..."
    const bulletMatch = line.match(/^[-*•]\s+(.*)$/)
    if (bulletMatch) {
      const bulletContent = bulletMatch[1]
      const badge = getBulletBadge(bulletContent)

      elements.push(
        <div
          key={`bullet-${i}`}
          className="mt-1.5 flex items-start gap-2 pl-2 text-sm leading-relaxed"
        >
          {badge ? (
            <span
              className={cn(
                "mt-0.5 flex size-4 shrink-0 items-center justify-center rounded border",
                badge.color,
              )}
            >
              <badge.icon className="size-2.5" />
            </span>
          ) : (
            <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary/70" />
          )}
          <div className="flex-1 text-foreground/90">
            {renderInline(bulletContent, false)}
          </div>
        </div>,
      )
      i++
      continue
    }

    // 6. Regular paragraph
    elements.push(
      <p
        key={`p-${i}`}
        className="mt-1.5 text-sm leading-relaxed text-foreground/95 first:mt-0"
      >
        {renderInline(rawLine, false)}
      </p>,
    )
    i++
  }

  return (
    <div className={cn("space-y-1 text-sm", className)}>
      {elements}
    </div>
  )
}
