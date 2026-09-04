import { CitizenShell } from "@/components/citizen/citizen-shell"

export default function CitizenLayout({ children }: { children: React.ReactNode }) {
  return <CitizenShell>{children}</CitizenShell>
}
