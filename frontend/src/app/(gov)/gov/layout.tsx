import { GovShell } from "@/components/gov/gov-shell"

export default function GovLayout({ children }: { children: React.ReactNode }) {
  return <GovShell>{children}</GovShell>
}
