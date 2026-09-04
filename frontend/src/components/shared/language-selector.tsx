"use client"

import { Check, Languages } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { LANGUAGES } from "@/lib/mock/languages"
import { useApp } from "@/context/app-provider"
import { cn } from "@/lib/utils"

export function LanguageSelector({ variant = "ghost" }: { variant?: "ghost" | "outline" }) {
  const { language, setLanguage } = useApp()
  const current = LANGUAGES.find((l) => l.code === language) ?? LANGUAGES[0]

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant={variant} size="sm" className="gap-1.5 text-muted-foreground">
          <Languages className="size-4" />
          <span className="hidden sm:inline">{current.nativeLabel}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel>Choose language</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {LANGUAGES.map((lang) => (
          <DropdownMenuItem key={lang.code} onClick={() => setLanguage(lang.code)} className="justify-between">
            <span>
              {lang.nativeLabel} <span className="text-muted-foreground">({lang.label})</span>
            </span>
            <Check className={cn("size-3.5", lang.code === language ? "opacity-100" : "opacity-0")} />
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
