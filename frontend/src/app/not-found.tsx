import Link from "next/link"
import { Compass, LandmarkIcon } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-5 bg-muted/30 px-4 text-center">
      <div className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
        <LandmarkIcon className="size-6" />
      </div>
      <div className="space-y-1.5">
        <p className="text-sm font-medium text-muted-foreground">Error 404</p>
        <h1 className="text-2xl font-semibold tracking-tight">This page could not be found</h1>
        <p className="mx-auto max-w-md text-sm text-muted-foreground">
          The page you are looking for may have been moved, or the link you followed is no longer valid.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        <Button asChild>
          <Link href="/">Back to AI Assistant</Link>
        </Button>
        <Button asChild variant="outline" className="gap-1.5">
          <Link href="/services">
            <Compass className="size-4" /> Browse Services
          </Link>
        </Button>
      </div>
    </div>
  )
}
