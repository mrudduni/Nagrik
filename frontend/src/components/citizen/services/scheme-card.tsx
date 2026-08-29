import Link from "next/link"
import { ArrowRight, Star, Users, CheckCircle2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { formatCompactNumber } from "@/lib/format"
import type { Scheme } from "@/types"
import { cn } from "@/lib/utils"

export function SchemeCard({ scheme, matchScore }: { scheme: Scheme; matchScore?: number }) {
  return (
    <Card className="group flex flex-col gap-3 p-5 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div className={cn("flex size-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold text-primary", scheme.imageColor)}>
          {scheme.title.slice(0, 1)}
        </div>
        {matchScore !== undefined && (
          <Badge className="gap-1 bg-success/15 text-success border-success/20 hover:bg-success/15">
            <CheckCircle2 className="size-3" /> {matchScore}% match
          </Badge>
        )}
      </div>

      <div className="space-y-1.5">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="outline" className="text-[10px] font-normal">{scheme.category}</Badge>
          <Badge variant="outline" className="text-[10px] font-normal">{scheme.level}</Badge>
        </div>
        <Link href={`/services/${scheme.id}`}>
          <h3 className="text-sm font-semibold leading-snug tracking-tight group-hover:text-primary transition-colors">{scheme.title}</h3>
        </Link>
        <p className="line-clamp-2 text-xs text-muted-foreground">{scheme.shortDescription}</p>
      </div>

      <div className="mt-auto flex items-center justify-between pt-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">{scheme.benefitAmount ?? scheme.benefitType}</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Star className="size-3 fill-current text-amber-500" /> {scheme.rating}
          </span>
          <span className="flex items-center gap-1">
            <Users className="size-3" /> {formatCompactNumber(scheme.beneficiariesCount)}
          </span>
        </div>
      </div>

      <Link
        href={`/services/${scheme.id}`}
        className="flex items-center justify-center gap-1.5 rounded-lg border border-border py-2 text-xs font-medium text-foreground transition-colors group-hover:border-primary/40 group-hover:bg-primary/5"
      >
        View Details <ArrowRight className="size-3.5" />
      </Link>
    </Card>
  )
}
